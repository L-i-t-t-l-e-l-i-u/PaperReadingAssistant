# backend_algo/knowledge_service.py
import os
import shutil
import chromadb
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 导入你的工具函数
from utils.parser import parse_docx, parse_pdf, table_to_markdown, extract_title
from embed import get_text_embeddings

# --- 1. 初始化持久化组件（模块加载时执行一次） ---
chroma_client = chromadb.HttpClient(host="localhost", port=8002)
collection = chroma_client.get_or_create_collection(name="my_knowledge_base")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", "；", "，", " "]
)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_and_ingest_document(file: UploadFile) -> dict:
    # 2. 现在的路径是永久保存的路径，去掉 temp 前缀
    permanent_file_path = os.path.join(UPLOAD_DIR, file.filename)

    # 3. 永久保存文件到 uploads 目录下
    with open(permanent_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        all_chunks = []

        # 解析提取
        if file.filename.endswith(".docx"):
            paragraphs, tables = parse_docx(permanent_file_path)
            all_chunks.extend(text_splitter.split_text("\n".join(paragraphs)))
            for tb in tables:
                all_chunks.append(table_to_markdown(tb))

        elif file.filename.endswith(".pdf"):
            texts, tables = parse_pdf(permanent_file_path)
            all_chunks.extend(text_splitter.split_text("\n".join(texts)))
            for tb in tables:
                all_chunks.append(table_to_markdown(tb))
        else:
            raise ValueError(f"不支持的文件格式: {file.filename}，仅支持 .docx 或 .pdf")

        if not all_chunks:
            raise ValueError("文件中没有提取到有效文本")

        # 向量化
            # --- 新增：超长文本块终极防御阀 ---
        safe_chunks = []
        for chunk in all_chunks:
            # 阿里云硬限制 8192，我们设 7500 留点余量
            if len(chunk) > 7500:
                print(f"⚠️ 发现超长文本块 (长度: {len(chunk)})，正在进行强制二次切分...")
                # 强行把这个超长的块（比如巨型表格）再切碎
                safe_chunks.extend(text_splitter.split_text(chunk))
            else:
                safe_chunks.append(chunk)
        all_chunks = safe_chunks
        # ----------------------------------

        # 向量化
        print(f"正在将 {len(all_chunks)} 个文本块转换为向量...")
        embeddings = get_text_embeddings(all_chunks)

        # 存入 ChromaDB
        ids = [f"{file.filename}_chunk_{i}" for i in range(len(all_chunks))]
        metadatas = [{"source": file.filename} for _ in range(len(all_chunks))]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=all_chunks,
            metadatas=metadatas
        )

        return {
            "message": "文件处理并入库成功！",
            "filename": file.filename,
            "title": extract_title(permanent_file_path, file.filename),
            "chunks_count": len(all_chunks)
        }

    except Exception as e:
        # 4. 只有在解析或入库彻底失败（崩溃）时，才删掉这个“坏”文件，保持文件夹干净
        if os.path.exists(permanent_file_path):
            os.remove(permanent_file_path)
        raise e


def clear_all_knowledge() -> dict:
    """
    业务逻辑：清空 Chroma 向量数据和本地物理文件
    """
    try:
        # 1. 清空 Chroma 集合里的所有数据
        all_data = collection.get()
        if all_data and all_data['ids']:
            collection.delete(ids=all_data['ids'])
            print(f"🗑️ 已从 ChromaDB 成功删除 {len(all_data['ids'])} 条向量数据")

        # 2. 清空 uploads 目录下的所有物理文件
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print("🗑️ 已彻底清空 uploads 文件夹中的文档")

        return {"message": "知识库和本地文件已全部清空！"}

    except Exception as e:
        print(f"清空知识库时发生错误: {e}")
        raise ValueError(f"清空失败: {e}")


def delete_paper_by_filename(filename: str) -> dict:
    """
    按文件名删除：
    1. 从 ChromaDB 中删除所有 source == filename 的向量
    2. 删除 uploads 目录下的物理文件
    """
    try:
        # 1. 删除 ChromaDB 中该论文的所有向量
        results = collection.get(where={"source": filename})
        deleted_count = 0
        if results and results['ids']:
            collection.delete(ids=results['ids'])
            deleted_count = len(results['ids'])
            print(f"🗑️ 已从 ChromaDB 删除论文《{filename}》的 {deleted_count} 条向量")

        # 2. 删除本地物理文件
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ 已删除本地文件: {file_path}")

        return {
            "message": f"论文《{filename}》已删除",
            "filename": filename,
            "deleted_chunks": deleted_count,
        }

    except Exception as e:
        print(f"删除论文《{filename}》时发生错误: {e}")
        raise ValueError(f"删除论文失败: {e}")