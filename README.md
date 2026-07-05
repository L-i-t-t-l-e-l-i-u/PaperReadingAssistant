# FastAPI + Vue 示例项目

- 启动流程：
由于项目跨度极长，虽然已经随写随增，但本人无法保证后端由conda管理的包环境已经尽数写入各个文件夹中的requirements中，如有遗漏还请多多包涵，根据报错手动安装。
即便如此，根据本人在本机环境的测试，在环境齐备的情况下，只凭借Submit中的文件，即可正确启动项目。启动流程如下：
- backend:终端进入backend文件夹，
使用conda创建python3.12的新环境并pip install -r requirements.txt ，配置好环境后，启动

```shell 
uvicorn main:app --port 8000
```

- chroma: 终端进入backend_algo文件夹，同上配置好环境后，启动

```shell
chroma run --path ./data_vector_db --host localhost --port 8002
```

- backend_algo: 终端进入backend_algo文件夹，同上配置好环境后，启动

```shell
uvicorn main:app --port 8001
```

- frontend: 终端进入frontend文件夹,先启动

```sh
npm install
```

然后再启动运行

```sh
npm run dev
```

全部启动成功后，根据前端地址在浏览器打开即可。具体细节也可以参考用户手册。

- 可以使用batch_upload.py批量上传本地pdf文件，需要在调用时指定参数-dir到本地目录或在py文件中调整，用户名和密码也需要在py文件中调整以通过鉴权。

- 关于my_evaluate:
这是一个自动化评估脚本，如果采用我采用的50篇论文作为数据集，它可以基于questions.json中的问题对Precision@K Recall@K和回复质量等指标进行自动化打分
但是使用时需要pip install rouge_score,bert_score,nltk
它的运行条件需要论文成功上传，对环境也比较严苛，不保证能在远端运行。
这里给出本地的测评结果：具体分析详见算法文档。
```txt
 开始对 50 个问题进行自动化测评...

测评进度: 100%|██████████| 50/50 [04:44<00:00,  5.69s/it]


========================================
📊 测评完成！你的系统成绩单如下：
========================================

【1. 检索阶段能力 (Retrieval)】
平均 Precision@5: 0.1480
平均 Recall@5:    0.7400
平均 F1@5:        0.2467

【2. 生成阶段能力 (Generation)】
正在计算复杂的 NLP 语义指标，这可能需要一点时间下载模型...
平均 BLEU 分数: 0.0004
平均 ROUGE-L 分数: 0.0011
(正在加载 BERTScore 模型算分...)
平均 BERTScore (F1): 0.4532
```



提交的项目结构：
Submit/
├── README.md（本文档）
├── papers.zip(收录50篇论文，数据集)
├── batch_upload.py（批上传小工具）
(以下为源码)
├── .gitignore
├── _documents         >> (**项目文档所在地，迅速了解项目首选**) <<
│   ├── 24300240126_刘念_实验报告_搜索助手.pdf（项目文档）
│   ├── 设计开发文档（项目概况）
│   ├── 算法方案文档（项目做的核心算法优化）
│   └── 用户手册（使用说明书）
├── backend/           (FastAPI 业务层)
│   ├── main.py, crud.py, database.py, models.py
│   ├── schemas.py, security.py, curl.bash
│   ├── requirements.txt, README.md, .gitignore
├── backend_algo/      (FastAPI 算法层)
│   ├── main.py, knowledge_service.py, retrieval_service.py
│   ├── rerank_service.py, embed.py, schemas.py
│   ├── my_evaluate.py, papers.json,questions.json
│   ├── requirements.txt, README.md, .gitignore
│   └── utils/parser.py
└── frontend/          (Vue 3 前端)
    ├── src/ (components/, pages/, request/, router/, store/, types/, assets/)
    ├── public/favicon.ico
    ├── index.html, package.json, package-lock.json
    ├── vite.config.ts, tsconfig*.json, env.d.ts
    └── README.md, .gitignore

其余详情请见实验报告