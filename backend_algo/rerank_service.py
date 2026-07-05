# backend_algo/rerank_service.py
import os
import traceback
from openai import OpenAI

# 1. 独立配置重排序客户端 (注意 base_url 和 embedding 接口略有不同，按照官方规范来)
ALIYUN_API_KEY = "sk-41a44741404c4e74af5a024f1bb76be9"

rerank_client = OpenAI(
    api_key=ALIYUN_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-api/v1"
)


def rerank_documents(query: str, documents: list[str], metadatas: list[dict], top_n: int = 2):
    """
    升级版：重排序时，带着 metadatas 一起排序，防止丢失文件名
    """
    if not documents:
        return [], []

    try:
        results = rerank_client.post(
            "/reranks",
            body={
                "model": "qwen3-rerank",
                "query": query,
                "documents": documents,
                "top_n": top_n
            },
            cast_to=object
        )

        rerank_results = results.get("results", [])

        final_top_docs = []
        final_top_metas = []  # 新增：用来存排好序的元数据

        # 按照返回的 index 重新排列原文和元数据
        for item in rerank_results:
            original_index = item["index"]
            final_top_docs.append(documents[original_index])
            final_top_metas.append(metadatas[original_index])

        return final_top_docs, final_top_metas

    except Exception as e:
        print(f"调用 Qwen3-Rerank 失败，退回原始顺序兜底: {e}")
        traceback.print_exc()
        return documents[:top_n], metadatas[:top_n]