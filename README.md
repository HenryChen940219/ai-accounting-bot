# AI 智慧記帳助理

> 結合 RAG、HyDE、Pseudo Query、LLM/VLM 與 n8n 的 LINE Bot 智慧記帳系統

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com/)

---

## 專案簡介

AI 智慧記帳助理是一個以 **LINE Bot** 為介面的 AI 記帳系統，讓使用者直接在 LINE 上用自然語言記帳、查帳、分帳，無需安裝任何額外 App。

本專案整合六大技術：
- **LLM**（Gemini 2.5 Flash）：意圖分類與記帳資訊解析
- **VLM**（Gemini 2.5 Flash Vision）：收據與發票圖片自動辨識
- **RAG**（Retrieval-Augmented Generation）：個人消費記錄語意檢索
- **HyDE**（Hypothetical Document Embeddings）：提升查詢向量匹配精度
- **Pseudo Query**：多視角查詢擴展，提高召回率
- **n8n**：LINE Webhook 事件清洗與轉發自動化

---

## 主要功能

### 個人記帳
- 自然語言輸入記帳（「早餐花了 80 元」）
- 拍收據 / 發票 / LINE Pay 截圖自動辨識記帳
- 智慧查詢（「上週吃飯花多少？」）
- Web Dashboard 即時查看圓餅圖、長條圖與消費明細

### 群組分帳
- 群組訊息中 @mention 觸發 AA 分帳
- 支援含空格的多字 LINE 顯示名稱
- 自動計算每人應付金額並記錄欠款
- 可查看欠款明細，一鍵標記結清

---

## 技術架構

```
使用者
  │
  ▼
LINE Messaging API
  │
  ▼
n8n Workflow（事件清洗 → 轉發）
  │
  ▼
FastAPI 後端
  ├── Gemini LLM   → 意圖分類 / 記帳解析 / AA 解析
  ├── Gemini VLM   → 收據圖片辨識
  └── RAG + HyDE + Pseudo Query → 智慧查詢
  │
  ▼
SQLite 資料庫
  │
  ├── LINE Bot 回覆訊息
  └── Web Dashboard
```

---

## 技術棧

| 類別 | 技術 |
|------|------|
| 後端框架 | Python FastAPI + Uvicorn |
| 資料庫 | SQLite |
| AI 模型 | Google Gemini 2.5 Flash (LLM + VLM) |
| 向量檢索 | sentence-transformers + FAISS |
| 工作流自動化 | n8n + localtunnel |
| LINE 串接 | LINE Messaging API |
| 前端 Dashboard | HTML / CSS / JavaScript |

---

## 安裝與執行

### 環境需求
- Python 3.10+
- n8n（本地或雲端）
- LINE Bot Channel（LINE Developers Console）
- Google AI Studio API Key（Gemini）

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/HenryChen940219/ai-accounting-bot.git
cd ai-accounting-bot

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定環境變數
cp .env.example .env
# 編輯 .env 填入以下設定：
# LINE_CHANNEL_ACCESS_TOKEN=你的TOKEN
# LINE_CHANNEL_SECRET=你的SECRET
# GEMINI_API_KEY=你的KEY

# 4. 啟動伺服器
uvicorn main:app --reload --port 8000
```

### 公網 Webhook（開發用）

```bash
# 使用 localtunnel 建立公網通道
npx localtunnel --port 8000
# 將產生的 URL 設定到 LINE Developers Console 的 Webhook URL
# 並在 n8n 的 HTTP Request Node 中更新轉發目標
```

---

## 專案結構

```
ai-accounting-bot/
├── main.py              # FastAPI 主程式（路由、LINE Bot 處理）
├── database.py          # SQLite 資料庫操作（records、group_debts、members）
├── rag.py               # RAG + HyDE + Pseudo Query 智慧查詢模組
├── dashboard.html       # Web Dashboard 前端
├── setup_richmenu.py    # LINE Rich Menu 設定腳本
├── requirements.txt     # Python 依賴清單
├── .env.example         # 環境變數範本（不含實際金鑰）
└── receipt_images/      # VLM 辨識用的收據暫存圖片
```

---

## 環境變數說明

請複製 `.env.example` 為 `.env` 並填入實際值：

```env
LINE_CHANNEL_ACCESS_TOKEN=    # LINE Bot Channel Access Token
LINE_CHANNEL_SECRET=          # LINE Bot Channel Secret
GEMINI_API_KEY=               # Google Gemini API Key
```

> **注意：** `.env` 已加入 `.gitignore`，請勿將實際金鑰提交至版本控制。

---

## License

本專案採用 [MIT License](LICENSE) 授權。

Copyright (c) 2026 CHI-YU, CHEN (HenryChen940219)
