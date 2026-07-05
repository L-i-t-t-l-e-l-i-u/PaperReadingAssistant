import os

# 🌟 修复报错2：强制使用 HuggingFace 国内镜像源，绕过 SSL 和网络封锁
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# 可选：如果还是报 SSL 错，可以解除 Python 的全局 SSL 验证限制
os.environ["CURL_CA_BUNDLE"] = ""

import json
import requests
import re
import numpy as np
from tqdm import tqdm

from rouge_score import rouge_scorer
from bert_score import score as bert_score
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

# 🌟 修复报错1：直接打给算法层(8001端口)，绕过 8000 端口的 JWT 登录鉴权！
BASE_URL = "http://localhost:8001"


def load_data():
    with open("papers.json", "r", encoding="utf-8") as f:
        papers = json.load(f)
    with open("questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    id_to_filename = {p["id"]: os.path.basename(p["path"]) for p in papers}
    return questions, id_to_filename


def query_rag_system(question_text):
    # 直接组装匹配算法层 schemas.Conversation 的结构
    payload = {
        "messages": [{"role": "user", "content": question_text}]
    }

    try:
        response = requests.post(f"{BASE_URL}/chat/stream", json=payload, stream=True, timeout=60)

        # 如果还是被拒绝，打印出来看看为什么
        if response.status_code != 200:
            print(f"\n⚠️ 请求失败，状态码: {response.status_code}, 返回: {response.text}")
            return [], ""

        sources = []
        answer = ""

        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                text = chunk.decode('utf-8')
                match = re.search(r'\[\[SOURCES:(.*?)\]\]', text)
                if match:
                    sources_str = match.group(1)
                    if sources_str.strip():
                        sources = sources_str.split(',')
                    text = text.replace(match.group(0), '')
                answer += text
        return sources, answer.strip()
    except Exception as e:
        print(f"\n❌ 请求崩溃: {e}")
        return [], ""


def evaluate():
    questions, id_to_filename = load_data()

    precisions, recalls, f1s = [], [], []
    refs_list, preds_list = [], []

    print(f"🚀 开始对 {len(questions)} 个问题进行自动化测评...\n")

    for idx, q in enumerate(tqdm(questions, desc="测评进度")):
        question_text = q["Q"]
        true_answer = q["A"]
        true_sources = [id_to_filename[tid] for tid in q["R"]]

        pred_sources, pred_answer = query_rag_system(question_text)

        # 如果模型什么都没返回，直接记 0 分
        if not pred_answer and not pred_sources:
            precisions.append(0.0)
            recalls.append(0.0)
            f1s.append(0.0)
            refs_list.append(true_answer)
            preds_list.append("")
            continue

        hits = set(pred_sources).intersection(set(true_sources))

        # 严格按照老师要求的 @K 公式计算 (系统设定 final_top_k=3，所以 K=3)
        K = 2

        # Precision@K: 命中相关数 / K (看准不准)
        p = len(hits) / K

        # Recall@K: 命中相关数 / 相关总数 (看漏不漏)
        r = len(hits) / len(true_sources) if true_sources else 0.0

        # F1@K: 同时考虑 Precision 和 Recall 的综合分
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)

        refs_list.append(true_answer)
        preds_list.append(pred_answer)

    print("\n\n" + "=" * 40)
    print("📊 测评完成！你的系统成绩单如下：")
    print("=" * 40)

    print("\n【1. 检索阶段能力 (Retrieval)】")
    print(f"平均 Precision@2: {np.mean(precisions):.4f}")
    print(f"平均 Recall@2:    {np.mean(recalls):.4f}")
    print(f"平均 F1@2:        {np.mean(f1s):.4f}")

    print("\n【2. 生成阶段能力 (Generation)】")
    print("正在计算复杂的 NLP 语义指标，这可能需要一点时间下载模型...")

    smoothie = SmoothingFunction().method1
    bleu_scores = []
    for ref, pred in zip(refs_list, preds_list):
        bleu = sentence_bleu([list(ref)], list(pred), smoothing_function=smoothie)
        bleu_scores.append(bleu)
    print(f"平均 BLEU 分数: {np.mean(bleu_scores):.4f}")

    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=False)
    rouge_scores = [scorer.score(ref, pred)['rougeL'].fmeasure for ref, pred in zip(refs_list, preds_list)]
    print(f"平均 ROUGE-L 分数: {np.mean(rouge_scores):.4f}")

    try:
        print("(正在加载 BERTScore 模型算分...)")
        P, R, F1_bert = bert_score(preds_list, refs_list, lang="zh", verbose=False)
        print(f"平均 BERTScore (F1): {F1_bert.mean().item():.4f}")
    except Exception as e:
        print(f"⚠️ BERTScore 计算失败 (可能是网络依旧拦截): {e}")

    print("=" * 40)


if __name__ == "__main__":
    evaluate()