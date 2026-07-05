"""
批量上传论文脚本
用法: python batch_upload.py
可选参数: --dir 指定论文目录 (默认 D:\Projectfolder\DB\papers)
"""

import os
import sys
import time
import argparse
import requests

# ============ 配置区 ============
BASE_URL = "http://localhost:8000"       # 主后端地址
PAPERS_DIR = r"D:\Projectfolder\DB\papers"  # 论文目录
USERNAME = "24300240126"                 # 用户名
PASSWORD = "123456"                      # 密码
# ================================


def login(username: str, password: str) -> str:
    """登录并返回 JWT token"""
    resp = requests.post(f"{BASE_URL}/token", data={
        "username": username,
        "password": password,
    })
    if resp.status_code != 200:
        print(f"[错误] 登录失败 ({resp.status_code}): {resp.text}")
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"[OK] 登录成功，用户: {username}\n")
    return token


def upload_file(filepath: str, token: str) -> bool:
    """上传单个文件，成功返回 True"""
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers=headers,
            timeout=120,
        )

    if resp.status_code == 200:
        data = resp.json()
        chunks = data.get("chunks_count", "?")
        title = data.get("title", "")
        title_info = f"  标题: {title}" if title else ""
        print(f"  [OK] {filename}  ->  {chunks} 个知识块{title_info}")
        return True
    else:
        print(f"  [FAIL] {filename}  ->  {resp.status_code}: {resp.text[:120]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="批量上传论文到知识库")
    parser.add_argument("--dir", "-d", default=PAPERS_DIR, help="论文目录（可选）")
    args = parser.parse_args()

    # 1. 扫描论文文件
    pdf_files = sorted([
        os.path.join(args.dir, f)
        for f in os.listdir(args.dir)
        if f.lower().endswith((".pdf", ".docx"))
    ])
    if not pdf_files:
        print(f"[错误] 在 {args.dir} 下没有找到 .pdf / .docx 文件")
        sys.exit(1)

    print(f"找到 {len(pdf_files)} 篇论文，准备上传...\n")

    # 2. 登录
    token = login(USERNAME, PASSWORD)

    # 3. 逐个上传
    success = 0
    fail = 0
    start_time = time.time()

    for i, filepath in enumerate(pdf_files, 1):
        filename = os.path.basename(filepath)
        print(f"[{i}/{len(pdf_files)}] 上传中: {filename}")
        if upload_file(filepath, token):
            success += 1
        else:
            fail += 1

    elapsed = time.time() - start_time
    print(f"\n{'='*40}")
    print(f"上传完成！  成功: {success}  失败: {fail}  耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
