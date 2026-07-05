from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import schemas
import requests

from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel
from embed import get_text_embeddings
from knowledge_service import process_and_ingest_document, clear_all_knowledge, delete_paper_by_filename
from retrieval_service import handle_rag_chat_stream
app = FastAPI()

URL = 'http://10.176.64.152:11434/v1'
MODEL = 'qwen2.5:7b'

os.makedirs("uploads", exist_ok=True)
app.mount("/files", StaticFiles(directory="uploads"), name="files")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],        # 允许所有前端地址访问（开发环境可用 *）
#     allow_credentials=True,
#     allow_methods=["*"],        # 👈 核心所在：允许 DELETE、OPTIONS 等所有方法！
#     allow_headers=["*"],        # 允许所有请求头
# )
@app.post("/chat/stream")
async def chat_stream(conversation: schemas.Conversation):
    """
    流式 RAG 对话。
    接收前端的对话历史，交给 retrieval_service 进行检索和打字机生成。
    """
    try:
        # 完美的甩手掌柜：直接调用、直接返回流式响应
        return await handle_rag_chat_stream(conversation)
    except HTTPException as he:
        # 如果 service 层主动抛出了 HTTP 异常（比如调远端模型失败），直接抛出
        raise he
    except Exception as e:
        print(f"流式对话接口发生未知错误: {e}")
        raise HTTPException(status_code=500, detail="流式对话服务异常")



# @app.post("/chat/")
# async def chat(conversation: schemas.Conversation):
#     # 1. 发起同步请求
#     resp = requests.post(f'{URL}/chat/completions', json={
#         'model': MODEL,
#         'stream': False,
#         'messages': [m.model_dump() for m in conversation.messages],
#     }, timeout=60)
#
#     if resp.status_code != 200:
#         raise HTTPException(status_code=502, detail=f"远端模型服务异常: {resp.text}")
#
#     # 2. 直接把大模型返回的完整标准 JSON 原封不动地扔回给 backend 层
#     return resp.json()








class EmbedRequest(BaseModel):
    texts: list[str]


@app.post("/internal/embed")
async def do_embedding(request: EmbedRequest):
    """
    算法层的内部接口，只负责接收主后端的请求，具体实现在独立的模块中
    """
    if not request.texts:
        return {"embeddings": []}

    try:
        # 直接调用你已经在其他地方实现好的封装函数！
        vectors = get_text_embeddings(request.texts)
        return {"embeddings": vectors}
    except Exception as e:
        print(f"向量生成失败: {e}")
        raise HTTPException(status_code=500, detail="算法层向量化内部错误")


@app.post("/upload")
async def upload_endpoint(file: UploadFile = File(...)):
    """接收上传文件并触发知识库入库流程"""
    try:
        # 直接调用业务逻辑层，main 里没有任何杂活
        result = process_and_ingest_document(file)
        return result

    except ValueError as ve:
        # 捕获业务层抛出的参数/格式错误 (400 Bad Request)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # 捕获其他未知系统错误 (500 Internal Error)
        print(f"入库接口遇到致命错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部处理失败")

@app.delete("/internal/clear")
async def internal_clear_endpoint():
    """
    【内部接口】算法层专门负责干脏活：真正删除 ChromaDB 和本地物理文件。
    该接口不对外暴露，只接受主后端的转发。
    """
    try:
        result = clear_all_knowledge()
        return result
    except ValueError as ve:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"底层清空遇到错误: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="底层算法执行失败")


@app.delete("/internal/papers/{filename}")
async def delete_single_paper(filename: str):
    """
    【内部接口】按文件名删除单篇论文的所有向量和本地文件。
    只接受主后端的转发调用。
    """
    try:
        result = delete_paper_by_filename(filename)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"删除单篇论文失败: {e}")
        raise HTTPException(status_code=500, detail="删除论文失败")