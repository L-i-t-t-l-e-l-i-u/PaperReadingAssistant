import os
from fastapi import HTTPException
from openai import OpenAI, OpenAIError

# 1. 配置阿里云百炼的相关参数
# 强烈建议将真实 API_KEY 配置在 .env 文件中，这里作为兜底或直接替换为 "sk-xxx"
API_KEY = "sk-41a44741404c4e74af5a024f1bb76be9"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
EMBED_MODEL = "text-embedding-v4"

# 2. 全局初始化客户端（推荐做法：复用连接，提升性能）
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


def get_text_embeddings(texts: list[str]) -> list[list[float]]:
    """
    调用阿里云百炼 API (OpenAI兼容模式) 将文本列表转换为向量。
    带有自动分批机制，以适应阿里云 batch_size <= 10 的限制。
    """
    if not texts:
        return []

    try:
        all_embeddings = []
        batch_size = 10  # 阿里云的硬性限制

        # 核心逻辑：对长长的 texts 列表进行切片，每次最多取 10 个
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i: i + batch_size]

            # 发起分批请求
            response = client.embeddings.create(
                model=EMBED_MODEL,
                input=batch_texts
            )

            # 将这一批的向量结果提取出来，追加到总列表中
            all_embeddings.extend([item.embedding for item in response.data])

        return all_embeddings

    except OpenAIError as e:
        print(f"Embedding API Error: {e}")
        raise HTTPException(status_code=500, detail="向量化服务暂时不可用")