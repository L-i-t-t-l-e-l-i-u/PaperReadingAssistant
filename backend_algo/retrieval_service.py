# backend_algo/retrieval_service.py
import os
import traceback
import chromadb
import requests
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI, OpenAIError
import schemas


from rerank_service import rerank_documents
# ==========================================
# 1. 阿里云百炼 Embedding 配置 (负责"算坐标")
# ==========================================
# 强烈建议在生产环境中将 API_KEY 放入 .env 环境变量
ALIYUN_API_KEY = "sk-41a44741404c4e74af5a024f1bb76be9"

embed_client = OpenAI(
    api_key=ALIYUN_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ==========================================
# 2. 向量数据库配置 (负责"存找坐标")
# ==========================================
chroma_client = chromadb.HttpClient(host="localhost", port=8002)
collection = chroma_client.get_or_create_collection(name="my_knowledge_base")

# ==========================================
# 3. 远端对话大模型配置 (负责"聊天回答")
# ==========================================
LLM_URL = 'http://10.176.64.152:11434/v1'
LLM_MODEL = 'qwen2.5:7b'


def get_query_embedding(query_text: str) -> list[float]:
    """
    【检索专用】：按照阿里云官方规范，将用户的单句提问转化为向量。
    """
    try:
        completion = embed_client.embeddings.create(
            model="text-embedding-v4",
            input=query_text
        )
        # 根据 OpenAI SDK 的结构，提取第一条数据的向量数组
        return completion.data[0].embedding

    except OpenAIError as e:
        print(f"调用阿里云 Embedding API 失败: {e}")
        # 如果向量化失败，抛出异常让上层捕获
        raise ValueError("模型向量化服务暂时不可用")

def retrieve_knowledge(query_text: str, final_top_k: int = 2):
    """
    返回元组: (拼接好的参考上下文, 唯一来源文件列表)
    """
    if not query_text.strip():
        return "", []

    try:
        # 1. 粗排
        query_vector = get_query_embedding(query_text)
        rough_results = collection.query(
            query_embeddings=[query_vector],
            n_results=100
        )

        if not rough_results['documents'] or not rough_results['documents'][0]:
            return "", []

        rough_docs = rough_results['documents'][0]
        rough_metas = rough_results['metadatas'][0]  # 获取粗排的元数据

        # 2. 精排 (传入 metadatas)
        final_docs, final_metas = rerank_documents(query_text, rough_docs, rough_metas, top_n=final_top_k)

        # 3. 提取不重复的参考论文文件名
        unique_sources = list(set([meta.get("source", "未知论文.pdf") for meta in final_metas]))

        context = "\n\n---相关片段---\n\n".join(final_docs)
        return context, unique_sources

    except Exception as e:
        print(f"检索知识库时发生意外错误: {e}")
        traceback.print_exc()
        return "", []


async def handle_rag_chat_stream(conversation: schemas.Conversation) -> StreamingResponse:
    user_latest_message = conversation.messages[-1].content

    # 获取上下文 和 论文来源列表
    context, unique_sources = retrieve_knowledge(user_latest_message, final_top_k=5)

    print(f"[RAG] query='{user_latest_message[:50]}...', context_len={len(context)}, sources={unique_sources}")

    if context.strip():
        augmented_prompt = f"""请仔细阅读以下参考资料，并基于这些资料回答我的问题。如果参考资料中没有提到相关信息，请结合你的知识回答，但要说明资料中未提及。

【参考资料开始】
{context}
【参考资料结束】

【我的问题】：{user_latest_message}"""
    else:
        augmented_prompt = user_latest_message

    payload_messages = [m.model_dump() for m in conversation.messages]
    payload_messages[-1]['content'] = augmented_prompt

    resp = requests.post(f'{LLM_URL}/chat/completions', json={
        'model': LLM_MODEL,
        'stream': True,
        'messages': payload_messages,
    }, stream=True, timeout=60)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"远端大模型服务异常: {resp.text}")

    # ==========================================
    # 核心魔法：生成器流式返回
    # ==========================================
    def generator():
        # 第一步：如果有参考论文，在数据流的最开头，偷偷发一个带特殊标记的字符串
        # 格式例如： "[[SOURCES:论文A.pdf,论文B.pdf]]"
        if unique_sources:
            sources_str = ",".join(unique_sources)
            yield f"[[SOURCES:{sources_str}]]".encode('utf-8')

        # 第二步：透传大模型的正常打字机回答
        for chunk in resp.iter_content(chunk_size=None):
            if chunk:
                yield chunk

    return StreamingResponse(
        generator(),
        media_type="text/event-stream"
    )