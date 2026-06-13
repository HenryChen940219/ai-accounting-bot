"""
RAG module with Pseudo Query + HyDE + FAISS vector search

Flow:
1. Build Index: for each accounting record, generate pseudo queries via LLM,
   embed record + pseudo queries, store in FAISS
2. Query (HyDE): generate a hypothetical answer → embed → search FAISS → retrieve
   relevant records → LLM answers with real context
"""

import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from google import genai
import os
from dotenv import load_dotenv
from database import get_records

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        print("[RAG] 載入 embedding 模型...")
        _embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        print("[RAG] 模型載入完成")
    return _embedder


def record_to_text(r: dict) -> str:
    amount = abs(r["amount"])
    direction = "支出" if r["amount"] < 0 else "收入"
    return f"{r['record_date']} {r['category']} {direction} {amount}元 {r['note'] or ''}"


def generate_pseudo_queries(record_text: str) -> list[str]:
    """Pseudo Query: 為每筆記錄生成 LLM 假設問句"""
    prompt = f"""針對以下記帳記錄，生成3個使用者可能會問的查詢問題，用JSON陣列回傳（不加markdown）：
記錄：{record_text}
範例格式：["問題1", "問題2", "問題3"]"""
    try:
        res = client.models.generate_content(model=MODEL, contents=prompt)
        raw = res.text.strip().strip("```json").strip("```").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[PseudoQuery] 生成失敗: {e}")
        return [record_text]


def generate_hyde_answer(question: str) -> str:
    """HyDE: 先讓 LLM 假設一個答案，用來做語意搜尋"""
    prompt = f"""假設你是一個記帳系統，請根據「{question}」這個問題，
生成一段假設性的記帳摘要回答（2-3句話，包含可能的金額和類別）："""
    res = client.models.generate_content(model=MODEL, contents=prompt)
    return res.text.strip()


class AccountingRAG:
    def __init__(self):
        self.index = None
        self.chunks = []  # list of (record_dict, chunk_text)
        self.embedder = None
        self.user_id = None

    def build_index(self, user_id: str):
        """建立向量索引：每筆記錄 + 其 Pseudo Queries"""
        self.user_id = user_id
        self.embedder = get_embedder()
        records = get_records(user_id, days=90)

        if not records:
            print("[RAG] 無記錄，跳過建索引")
            self.index = None
            self.chunks = []
            return

        self.chunks = []
        texts_to_embed = []

        for r in records:
            record_text = record_to_text(r)

            # 原始記錄文字
            self.chunks.append((r, record_text))
            texts_to_embed.append(record_text)

            # Pseudo Queries：生成假設問句也一起放進索引
            pseudo_qs = generate_pseudo_queries(record_text)
            for pq in pseudo_qs:
                self.chunks.append((r, pq))
                texts_to_embed.append(pq)

        print(f"[RAG] 建立索引：{len(records)} 筆記錄 → {len(texts_to_embed)} 個向量")
        embeddings = self.embedder.encode(texts_to_embed, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # Inner Product (cosine with normalized vectors)
        self.index.add(embeddings)
        print("[RAG] 索引建立完成")

    def search(self, question: str, top_k: int = 5) -> list[dict]:
        """HyDE + FAISS 搜尋：找最相關記錄"""
        if self.index is None or len(self.chunks) == 0:
            return []

        # HyDE：生成假設答案作為查詢向量
        hyde_answer = generate_hyde_answer(question)
        print(f"[HyDE] 假設答案: {hyde_answer[:80]}...")

        query_vec = self.embedder.encode([hyde_answer], normalize_embeddings=True)
        query_vec = np.array(query_vec, dtype=np.float32)

        distances, indices = self.index.search(query_vec, min(top_k * 3, len(self.chunks)))

        # 去重：同一筆記錄只取最高分
        seen_ids = set()
        results = []
        for idx in indices[0]:
            if idx < 0 or idx >= len(self.chunks):
                continue
            record, _ = self.chunks[idx]
            record_id = record["id"]
            if record_id not in seen_ids:
                seen_ids.add(record_id)
                results.append(record)
            if len(results) >= top_k:
                break

        return results

    def answer(self, question: str) -> str:
        """完整 RAG 流程：搜尋 + LLM 生成答案"""
        relevant_records = self.search(question)

        if not relevant_records:
            return "目前還沒有足夠的記帳資料，請先記錄一些消費後再查詢。"

        context_lines = [record_to_text(r) for r in relevant_records]
        context = "\n".join(context_lines)

        prompt = f"""你是一個智慧記帳助理，請根據以下最相關的記帳記錄，用繁體中文回答使用者的問題。

【相關記帳記錄】
{context}

【使用者問題】
{question}

請簡潔回答，若記錄不足以回答就如實說明："""

        res = client.models.generate_content(model=MODEL, contents=prompt)
        return res.text.strip()


# 每個 user 一個 RAG 實例（簡單快取）
_rag_cache: dict[str, AccountingRAG] = {}


def get_rag(user_id: str, rebuild: bool = False) -> AccountingRAG:
    if user_id not in _rag_cache or rebuild:
        rag = AccountingRAG()
        rag.build_index(user_id)
        _rag_cache[user_id] = rag
    return _rag_cache[user_id]


def rag_answer(user_id: str, question: str, rebuild_index: bool = False) -> str:
    rag = get_rag(user_id, rebuild=rebuild_index)
    return rag.answer(question)
