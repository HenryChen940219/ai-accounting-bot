import requests
import os
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
AUTH = {"Authorization": f"Bearer {LINE_TOKEN}"}

# ── 1. 定義選單結構 ────────────────────────────────────────────
rich_menu = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "AI記帳選單",
    "chatBarText": "快捷功能 ▲",
    "areas": [
        {"bounds": {"x": 0,    "y": 0,   "width": 833, "height": 843},
         "action": {"type": "message", "text": "查看報表"}},
        {"bounds": {"x": 833,  "y": 0,   "width": 834, "height": 843},
         "action": {"type": "message", "text": "快速記帳"}},
        {"bounds": {"x": 1667, "y": 0,   "width": 833, "height": 843},
         "action": {"type": "message", "text": "拍收據"}},
        {"bounds": {"x": 0,    "y": 843, "width": 833, "height": 843},
         "action": {"type": "message", "text": "AA分帳"}},
        {"bounds": {"x": 833,  "y": 843, "width": 834, "height": 843},
         "action": {"type": "message", "text": "本週報告"}},
        {"bounds": {"x": 1667, "y": 843, "width": 833, "height": 843},
         "action": {"type": "message", "text": "使用說明"}},
    ]
}

resp = requests.post(
    "https://api.line.me/v2/bot/richmenu",
    headers={**AUTH, "Content-Type": "application/json"},
    json=rich_menu
)
print(f"[建立選單] {resp.status_code}: {resp.text}")
rich_menu_id = resp.json()["richMenuId"]
print(f"Rich Menu ID: {rich_menu_id}")

# ── 2. 生成選單圖片 ────────────────────────────────────────────
W, H = 2500, 1686
img = Image.new("RGB", (W, H), color=(20, 22, 35))
draw = ImageDraw.Draw(img)

CELLS = [
    (0,    0,   833,  843),
    (833,  0,   1667, 843),
    (1667, 0,   2500, 843),
    (0,    843, 833,  1686),
    (833,  843, 1667, 1686),
    (1667, 843, 2500, 1686),
]

BG_COLORS = [
    (31, 97, 141),   # 查看報表 — 深藍
    (30, 132, 73),   # 快速記帳 — 深綠
    (118, 68, 138),  # 拍收據   — 深紫
    (176, 58, 46),   # AA分帳   — 深紅橘
    (23, 113, 115),  # 本週報告 — 深青
    (64, 64, 80),    # 使用說明 — 深灰
]

ICONS  = ["📊", "✏",  "📷", "💰", "📅", "❓"]
LABELS = ["查看報表", "快速記帳", "拍收據", "AA 分帳", "本週報告", "使用說明"]

# 嘗試載入字型
try:
    font_label = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 120)
    font_small = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 65)
except Exception as e:
    print(f"字型載入失敗: {e}，使用預設字型")
    font_label = ImageFont.load_default()
    font_small = font_label

# 畫各格子
for i, (x1, y1, x2, y2) in enumerate(CELLS):
    pad = 8
    draw.rectangle([x1+pad, y1+pad, x2-pad, y2-pad], fill=BG_COLORS[i])
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    # 主標籤
    draw.text((cx, cy), LABELS[i], fill="white", font=font_label, anchor="mm")

# 畫分隔線
SEP = (12, 14, 22)
draw.line([(833, 0), (833, H)], fill=SEP, width=8)
draw.line([(1667, 0), (1667, H)], fill=SEP, width=8)
draw.line([(0, 843), (W, 843)], fill=SEP, width=8)

out_path = os.path.join(os.path.dirname(__file__), "rich_menu.png")
img.save(out_path)
print(f"圖片已儲存：{out_path}")

# ── 3. 上傳圖片 ───────────────────────────────────────────────
with open(out_path, "rb") as f:
    img_resp = requests.post(
        f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
        headers={**AUTH, "Content-Type": "image/png"},
        data=f.read()
    )
print(f"[上傳圖片] {img_resp.status_code}: {img_resp.text}")

# ── 4. 設為預設選單（所有用戶） ───────────────────────────────
default_resp = requests.post(
    f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
    headers=AUTH
)
print(f"[設為預設] {default_resp.status_code}: {default_resp.text}")
print("✅ Rich Menu 設定完成！")
