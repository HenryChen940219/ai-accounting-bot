from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from google import genai
from google.genai import types
import requests
import os
import json
import base64
import httpx
from dotenv import load_dotenv
from database import init_db, add_record, get_records, get_summary, get_daily, add_group_debts, get_group_debts, settle_debt, get_aa_history, upsert_group_member, get_group_members, get_conn, delete_record, delete_group_aa_event, get_group_member_debts, get_member_debt_detail, get_aa_event_detail
from rag import rag_answer

load_dotenv()
init_db()

app = FastAPI()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "receipt_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"


# ── LINE helpers ──────────────────────────────────────────────

def reply_to_line(reply_token: str, text: str):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    res = requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        json=body
    )
    print(f"[LINE Reply] status={res.status_code}, body={res.text}")


def get_line_member_profile(group_id: str, user_id: str) -> str:
    url = f"https://api.line.me/v2/bot/group/{group_id}/member/{user_id}"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json().get("displayName", "未知成員")
    except Exception:
        pass
    return "未知成員"


def get_all_group_member_ids(group_id: str) -> list[str]:
    """LINE API 取得群組所有成員 ID（不限於有說過話的）"""
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    member_ids = []
    next_token = None
    try:
        while True:
            params = {"start": next_token} if next_token else {}
            res = requests.get(
                f"https://api.line.me/v2/bot/group/{group_id}/members/ids",
                headers=headers, params=params, timeout=5
            )
            if res.status_code != 200:
                print(f"[群組成員ID] {res.status_code}: {res.text}")
                break
            data = res.json()
            member_ids.extend(data.get("memberIds", []))
            next_token = data.get("next")
            if not next_token:
                break
    except Exception as e:
        print(f"[群組成員ID] 例外: {e}")
    return member_ids


def get_line_image(message_id: str) -> bytes:
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    res = requests.get(url, headers=headers)
    return res.content


# ── Intent classification ─────────────────────────────────────

def classify_intent(text: str) -> str:
    prompt = f"""判斷以下訊息的意圖，只回傳一個英文單字：
- add_record：想要記帳（含金額）
- query：詢問花費、統計、查詢記錄
- aa：AA分帳、平均分攤費用（含「AA」、「分帳」、「平分」等關鍵字）
- other：其他

訊息：「{text}」

回傳（只能是 add_record / query / aa / other）："""
    res = client.models.generate_content(model=MODEL, contents=prompt)
    intent = res.text.strip().lower().replace(".", "")
    if intent not in ("add_record", "query", "aa"):
        intent = "other"
    print(f"[Intent] {intent}")
    return intent


# ── Group AA 分帳 ─────────────────────────────────────────────

def parse_aa_request(text: str) -> dict | None:
    prompt = f"""從以下分帳訊息中提取資訊，回傳 JSON（不要加 markdown）：
{{
  "total": 總金額（數字，必填），
  "people": 人數（數字，必填），
  "description": 說明（例如：聚餐、火鍋、電影），
  "names": 人名列表（如果有提到名字則列出，沒有則空陣列）
}}

訊息：「{text}」"""
    res = client.models.generate_content(model=MODEL, contents=prompt)
    raw = res.text.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except Exception:
        print(f"[ParseAA] JSON 解析失敗: {raw}")
        return None


def calculate_aa(text: str, user_id: str = None, group_id: str = None, extra_names: list = None) -> str:
    parsed = parse_aa_request(text)
    if not parsed:
        return "無法解析分帳內容，請試試：「AA 晚餐1200元 4人」"

    total = float(parsed.get("total", 0))
    people = int(parsed.get("people", 0))
    description = parsed.get("description", "費用")
    names = parsed.get("names", [])

    if total <= 0 or people <= 0:
        return "請提供有效的金額和人數，例如：「AA 聚餐1800元 6人」"

    per_person_rounded = round(total / people)

    # 優先使用 @提及的名字（最準確）
    if not names and extra_names:
        names = extra_names
        # 若 LLM 解析的人數 > @提及人數，代表發訊者也算在內（他是付款方）
        # 例：「三個人平分 @A @B」→ people=3，names=2，每人=total/3
        if people > len(names):
            per_person_rounded = round(total / people)
        else:
            people = len(names)
            per_person_rounded = round(total / people)

    # 群組中自動抓取所有成員（沒有任何名字時才用）
    if group_id and not names:
        member_ids = get_all_group_member_ids(group_id)
        if member_ids:
            fetched = []
            for uid in member_ids:
                name = get_line_member_profile(group_id, uid)
                upsert_group_member(group_id, uid, name)
                fetched.append(name)
            names = fetched
        else:
            # LINE API 失敗時 fallback 到 DB
            members = get_group_members(group_id)
            if members:
                names = [m["display_name"] for m in members]
        if names:
            people = len(names)
            per_person_rounded = round(total / people)

    debt_saved = False
    if names:
        name_lines = "\n".join(f"  • {name}：{per_person_rounded} 元" for name in names)
        detail = f"\n{name_lines}"
        if user_id:
            owner = group_id or user_id
            add_group_debts(owner, total, people, description, names)
            debt_saved = True
    else:
        detail = ""

    hint = "✅ 欠款已記錄，可至儀表板查看" if debt_saved else "💡 群組中使用此功能可自動記錄成員欠款"

    return (
        f"💰 AA 分帳結果\n"
        f"{'─' * 18}\n"
        f"📋 項目：{description}\n"
        f"💵 總金額：{total:.0f} 元\n"
        f"👥 人數：{people} 人\n"
        f"{'─' * 18}\n"
        f"➡️ 每人應付：{per_person_rounded} 元"
        f"{detail}\n"
        f"{'─' * 18}\n"
        f"{hint}"
    )


# ── Text accounting ───────────────────────────────────────────

def parse_record(text: str) -> dict | None:
    prompt = f"""從以下記帳訊息中提取資訊，回傳 JSON（不要加 markdown）：
{{
  "amount": 數字（必填，新台幣，負數代表支出、正數代表收入），
  "category": 類別（餐飲/交通/購物/娛樂/醫療/收入/其他 其中之一），
  "note": 簡短備註,
  "date": "YYYY-MM-DD" 或 null（無日期則 null）
}}

訊息：「{text}」"""
    res = client.models.generate_content(model=MODEL, contents=prompt)
    raw = res.text.strip().strip("```json").strip("```").strip()
    try:
        return json.loads(raw)
    except Exception:
        print(f"[ParseRecord] JSON 解析失敗: {raw}")
        return None


# ── Receipt recognition (VLM) ─────────────────────────────────

def parse_receipt_image(image_bytes: bytes) -> dict | None:
    prompt = """這張圖片可能是：收據、發票、或 LINE Pay 付款通知截圖。
請提取以下資訊並回傳 JSON（不要加 markdown）：
{
  "amount": 總金額（數字，新台幣），
  "category": 類別（餐飲/交通/購物/娛樂/醫療/收入/其他 其中之一，根據店名推斷），
  "note": 店名或簡短說明,
  "date": "YYYY-MM-DD" 或 null,
  "status": "success" 或 "cancelled"（LINE Pay 付款完成=success，取消付款=cancelled；收據/發票預設 success）
}
若圖片無法辨識為消費記錄則回傳 null。"""
    image_b64 = base64.b64encode(image_bytes).decode()
    res = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            types.Part.from_text(text=prompt)
        ]
    )
    raw = res.text.strip().strip("```json").strip("```").strip()
    if raw.lower() == "null":
        return None
    try:
        return json.loads(raw)
    except Exception:
        print(f"[ParseReceipt] JSON 解析失敗: {raw}")
        return None


# ── RAG + HyDE query ─────────────────────────────────────────

def build_context(user_id: str, days: int = 30) -> str:
    records = get_records(user_id, days)
    if not records:
        return "（尚無記帳記錄）"
    lines = []
    for r in records:
        sign = "-" if r["amount"] < 0 else "+"
        lines.append(f"{r['record_date']} {r['category']} {sign}{abs(r['amount'])}元 {r['note'] or ''}")
    return "\n".join(lines)


def answer_query(user_id: str, question: str) -> str:
    # HyDE：先讓 LLM 假設一個答案，再用真實資料修正
    hyde_prompt = f"假設使用者的記帳資料完整，請先預測「{question}」的回答格式和可能內容（2句話）："
    hyde_res = client.models.generate_content(model=MODEL, contents=hyde_prompt)
    hyde_answer = hyde_res.text.strip()

    context = build_context(user_id)
    summary = get_summary(user_id, 30)

    rag_prompt = f"""你是一個智慧記帳助理，請根據以下真實記帳記錄回答使用者的問題。

【記帳記錄（近30天）】
{context}

【統計】
近30天總支出：{abs(summary['total'])} 元
分類：{', '.join(f"{b['category']} {abs(b['total'])}元" for b in summary['breakdown'])}

【使用者問題】
{question}

請用繁體中文簡潔回答，如果記錄不足就如實說明："""

    res = client.models.generate_content(model=MODEL, contents=rag_prompt)
    return res.text.strip()


# ── Main webhook ─────────────────────────────────────────────

@app.post("/process")
async def process_message(request: Request):
    try:
        data = await request.json()
        print(f"[收到資料] {data}")

        def strip_eq(v):
            return v.lstrip("=") if isinstance(v, str) else v

        reply_token = strip_eq(data.get("replyToken", "")) or None
        event_type = strip_eq(data.get("eventType", "message"))
        message_type = strip_eq(data.get("messageType", "text"))
        user_message = strip_eq(data.get("text", ""))
        user_id = strip_eq(data.get("userId", "unknown"))
        message_id = strip_eq(data.get("messageId", ""))
        source_type = strip_eq(data.get("sourceType", "user"))
        group_id = strip_eq(data.get("groupId", "")) or None

        print(f"[訊息] type={message_type}, text={user_message}, userId={user_id}, sourceType={source_type}, groupId={group_id}")

        import re
        extra_names: list[str] = []  # @提及的分帳人名

        # 群組訊息處理
        if source_type == "group" and group_id and user_id and user_id != "unknown":
            # 記錄成員名稱
            display_name = get_line_member_profile(group_id, user_id)
            upsert_group_member(group_id, user_id, display_name)
            print(f"[群組成員] {display_name} ({user_id}) in {group_id}")

            # 沒有 @ 就完全不回應
            if "@" not in user_message:
                print("[群組靜音] 未被 @ 標記，略過")
                return {"status": "skipped"}

            # 移除 bot @mention（支援顯示名稱有空格，如 "@AI 智慧記帳助理"）
            msg_no_bot = re.sub(r"@AI\s*智慧記帳助理\s*", "", user_message, count=1)

            # 以 @ 分割取得所有人名（可含空格的完整顯示名稱）
            parts = msg_no_bot.split("@")
            command_text = parts[0].strip()
            extra_names = [p.strip() for p in parts[1:] if p.strip()]

            # 若 regex 未完整去除 bot 名稱前綴則清除殘留
            command_text = re.sub(r"^智慧記帳助理\s*", "", command_text).strip()
            user_message = command_text
            print(f"[群組指令] 去除@後: {user_message}, 分帳對象: {extra_names}")

        # 機器人加入群組事件
        if event_type == "join" and group_id and reply_token:
            welcome = (
                "👋 大家好！我是 AI 智慧記帳助理\n\n"
                "📋 群組使用說明：\n"
                "• 需要 @標記我 才會回應\n"
                "• 群組僅支援 AA 分帳功能\n\n"
                "💰 AA 分帳範例：\n"
                "@AI智慧記帳助理 AA 晚餐1200 4人\n"
                "@AI智慧記帳助理 火鍋2400 小明 小華 小美\n\n"
                "📊 查看群組分帳面板：\n"
                "@AI智慧記帳助理 查看面板\n\n"
                "個人記帳、查詢、報表請私訊使用 💬"
            )
            reply_to_line(reply_token, welcome)
            return {"status": "ok"}

        if not reply_token:
            print("[略過] 無 replyToken")
            return {"status": "skipped"}

        # Rich Menu 快捷按鈕（精確比對，不經過 LLM）
        if user_message in ("查看報表", "查看面板"):
            if group_id:
                url = f"{BASE_URL}/dashboard?uid={user_id}&group={group_id}"
                reply_to_line(reply_token, f"📊 群組分帳面板\n點擊連結查看：\n{url}")
            else:
                url = f"{BASE_URL}/dashboard?uid={user_id}"
                reply_to_line(reply_token,
                    f"📊 個人記帳儀表板\n點擊連結查看：\n{url}\n\n"
                    f"💡 群組分帳面板請在群組中說「@AI智慧記帳助理 查看面板」")
            return {"status": "ok"}

        if user_message == "快速記帳":
            reply_to_line(reply_token,
                "✏️ 快速記帳\n直接傳送消費訊息即可！\n\n"
                "範例：\n"
                "• 早餐80元\n"
                "• 捷運票50\n"
                "• 昨天晚餐320元\n"
                "• 收入：薪水45000\n\n"
                "📷 也可以直接拍收據或 LINE Pay 截圖！")
            return {"status": "ok"}

        if user_message == "拍收據":
            reply_to_line(reply_token,
                "📷 拍收據記帳\n直接傳送圖片即可自動辨識！\n\n"
                "支援：\n"
                "• 實體收據 / 發票\n"
                "• LINE Pay 付款截圖\n"
                "• 信用卡消費通知截圖\n\n"
                "辨識後會自動記入帳目 ✅")
            return {"status": "ok"}

        if user_message == "AA分帳":
            reply_to_line(reply_token,
                "💰 AA 分帳\n說出消費金額和人數即可！\n\n"
                "範例：\n"
                "• AA 晚餐1200 4人\n"
                "• 火鍋1800 小明 小華 小美\n"
                "• 聚餐2400元 三個人平分\n\n"
                "在群組中使用可自動記錄每位成員欠款 📋")
            return {"status": "ok"}

        if user_message == "本週報告":
            summary_7 = get_summary(user_id, days=7)
            summary_30 = get_summary(user_id, days=30)
            breakdown_lines = "\n".join(
                f"  • {b['category']}：{abs(b['total']):.0f} 元"
                for b in summary_7["breakdown"]
            ) or "  （本週無支出記錄）"
            report = (
                f"📊 本週消費報告\n"
                f"{'─' * 20}\n"
                f"📅 本週支出：{abs(summary_7['total']):.0f} 元\n"
                f"{breakdown_lines}\n\n"
                f"📅 本月累計：{abs(summary_30['total']):.0f} 元\n"
                f"{'─' * 20}\n"
                f"💡 可問我「本週花最多的是什麼？」"
            )
            reply_to_line(reply_token, report)
            return {"status": "ok"}

        if user_message == "使用說明":
            reply_to_line(reply_token,
                "❓ 使用說明\n\n"
                "📝 記帳：直接說消費內容\n"
                "   例：早餐80元、捷運50\n\n"
                "📷 拍收據：傳送圖片自動辨識\n"
                "   收據照片可在儀表板點擊查看\n\n"
                "🔍 查詢：用自然語言問\n"
                "   例：本週花多少？吃飯共花多少？\n\n"
                "💰 AA分帳：AA 晚餐1200 4人\n\n"
                "📊 報表：點「查看報表」開啟儀表板\n\n"
                "👥 群組功能：\n"
                "   需 @標記機器人才會回應\n"
                "   • AA分帳：@AI智慧記帳助理 AA 晚餐1200 3人\n"
                "   • 查看分帳面板：@AI智慧記帳助理 查看面板")
            return {"status": "ok"}

        # 圖片 → VLM 收據辨識
        if message_type == "image" and message_id:
            image_bytes = get_line_image(message_id)
            parsed = parse_receipt_image(image_bytes)
            if parsed:
                status = parsed.get("status", "success")
                if status == "cancelled":
                    reply_text = "⚠️ 偵測到取消付款，不記入帳目。"
                else:
                    amount = float(parsed.get("amount", 0))
                    if amount > 0:
                        amount = -amount
                    # 儲存收據圖片
                    img_filename = f"{message_id}.jpg"
                    img_full_path = os.path.join(IMAGES_DIR, img_filename)
                    with open(img_full_path, "wb") as f:
                        f.write(image_bytes)
                    add_record(user_id, amount, parsed.get("category", "其他"),
                               parsed.get("note", ""), parsed.get("date"), img_filename)
                    source = "LINE Pay" if "pay" in parsed.get("note", "").lower() else "收據"
                    reply_text = (
                        f"✅ {source}辨識成功！\n"
                        f"💰 金額：{abs(amount)} 元\n"
                        f"📂 類別：{parsed.get('category', '其他')}\n"
                        f"📝 備註：{parsed.get('note', '')}\n"
                        f"📅 日期：{parsed.get('date', '今天')}\n"
                        f"📷 可在儀表板消費明細點擊查看收據"
                    )
            else:
                reply_text = "抱歉，無法辨識圖片內容，請確認是收據、發票或 LINE Pay 截圖。"
            reply_to_line(reply_token, reply_text)
            return {"status": "ok"}

        if not user_message:
            return {"status": "skipped"}

        # 文字訊息 → 意圖判斷
        intent = classify_intent(user_message)

        if intent == "add_record":
            parsed = parse_record(user_message)
            if parsed:
                amount = float(parsed.get("amount", 0))
                if amount > 0:
                    amount = -amount  # 預設支出
                add_record(user_id, amount, parsed.get("category", "其他"),
                           parsed.get("note", user_message), parsed.get("date"))
                reply_text = (
                    f"✅ 已記帳！\n"
                    f"💰 金額：{abs(amount)} 元\n"
                    f"📂 類別：{parsed.get('category', '其他')}\n"
                    f"📝 備註：{parsed.get('note', '')}"
                )
            else:
                reply_text = "抱歉，無法解析金額，請試試：「早餐花了80元」"

        elif intent == "query":
            reply_text = rag_answer(user_id, user_message, rebuild_index=True)

        elif intent == "aa":
            reply_text = calculate_aa(user_message, user_id, group_id, extra_names)

        else:
            res = client.models.generate_content(
                model=MODEL,
                contents=f"你是AI記帳助理，請用繁體中文簡短回覆：{user_message}"
            )
            reply_text = res.text.strip()

        reply_to_line(reply_token, reply_text)
        return {"status": "ok"}

    except Exception as e:
        print(f"[錯誤] {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def push_to_line(user_id: str, text: str):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}]
    }
    res = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=body
    )
    print(f"[LINE Push] status={res.status_code}, body={res.text}")


@app.post("/weekly-report")
async def weekly_report(request: Request):
    try:
        data = await request.json()
        user_id = data.get("userId", "").lstrip("=")
        if not user_id:
            return {"status": "error", "message": "missing userId"}

        summary_7 = get_summary(user_id, days=7)
        summary_30 = get_summary(user_id, days=30)

        breakdown_lines = "\n".join(
            f"  • {b['category']}：{abs(b['total']):.0f} 元"
            for b in summary_7["breakdown"]
        ) or "  （本週無支出記錄）"

        report = (
            f"📊 每週消費報告\n"
            f"{'─' * 20}\n"
            f"📅 本週支出：{abs(summary_7['total']):.0f} 元\n"
            f"{breakdown_lines}\n\n"
            f"📅 本月累計：{abs(summary_30['total']):.0f} 元\n"
            f"{'─' * 20}\n"
            f"💡 傳送收據圖片或文字即可記帳\n"
            f"🔍 可問我「本週花最多的是什麼？」"
        )

        push_to_line(user_id, report)
        return {"status": "ok"}

    except Exception as e:
        print(f"[週報錯誤] {e}")
        return {"status": "error", "message": str(e)}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(html_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/dashboard-data")
async def api_dashboard_data(user_id: str, group_id: str = None):
    """一次返回所有面板需要的資料，避免多個並行請求被 localtunnel 丟棄"""
    if group_id:
        return {
            "member_debts": get_group_member_debts(group_id),
            "aa_history": get_aa_history(group_id),
        }
    records = get_records(user_id, 90)
    return {
        "summary_1":  get_summary(user_id, 1),
        "summary_7":  get_summary(user_id, 7),
        "summary_30": get_summary(user_id, 30),
        "daily":      get_daily(user_id, 14),
        "records":    records[:25],
        "aa_history": get_aa_history(user_id),
    }


@app.get("/api/summary")
async def api_summary(user_id: str, days: int = 30):
    return get_summary(user_id, days)


@app.get("/api/daily")
async def api_daily(user_id: str, days: int = 14):
    return get_daily(user_id, days)


@app.get("/api/records")
async def api_records(user_id: str, limit: int = 25):
    records = get_records(user_id, 90)
    return records[:limit]


@app.get("/api/group-debts")
async def api_group_debts(user_id: str, group_id: str = None):
    owner = group_id or user_id
    return get_group_debts(owner)


@app.get("/api/group-members")
async def api_group_members(group_id: str):
    return get_group_members(group_id)


@app.get("/api/aa-history")
async def api_aa_history(user_id: str):
    return get_aa_history(user_id)


@app.post("/api/settle")
async def api_settle(request: Request):
    data = await request.json()
    settle_debt(data.get("user_id"), data.get("debtor_name"))
    return {"status": "ok"}


@app.get("/api/image/{record_id}")
async def api_image(record_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT image_path FROM records WHERE id = ?", (record_id,)).fetchone()
    if not row or not row["image_path"]:
        raise HTTPException(status_code=404, detail="此筆記錄沒有收據圖片")
    full_path = os.path.join(IMAGES_DIR, row["image_path"])
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="圖片檔案不存在")
    return FileResponse(full_path, media_type="image/jpeg")


@app.delete("/api/record/{record_id}")
async def api_delete_record(record_id: int):
    delete_record(record_id)
    return {"status": "ok"}


@app.delete("/api/aa-event")
async def api_delete_aa_event(request: Request):
    data = await request.json()
    delete_group_aa_event(data["owner"], data["description"], data["created_at"])
    return {"status": "ok"}


@app.get("/api/group-member-debts")
async def api_group_member_debts(group_id: str):
    return get_group_member_debts(group_id)


@app.get("/api/member-debt-detail")
async def api_member_debt_detail(group_id: str, debtor_name: str):
    return get_member_debt_detail(group_id, debtor_name)


@app.get("/api/aa-event-detail")
async def api_aa_event_detail(owner: str, description: str, created_at: str):
    return get_aa_event_detail(owner, description, created_at)


@app.get("/")
async def root():
    return {"status": "AI記帳助理運行中 ✅"}
