# OpenScholar 文献助手复刻尝试

本仓库保留 [AkariAsai/OpenScholar](https://github.com/AkariAsai/OpenScholar) 的核心推理代码，添加中文 Streamlit 界面和摘要检索入口。当前阶段：本机应用已启动并通过真实摘要检索及界面测试；未配置付费模型 API，未进行真实生成或容器构建验证，尚未公开上线。

## 当前支持
- 可选择 Europe PMC（生命科学 / 生物医学）或 Semantic Scholar（跨学科），按年份筛选，展示真实返回的摘要与来源。无密钥 Semantic Scholar 在本机测试时返回 429 限流，Europe PMC 实测可用。
- 使用官方 OpenScholar 推理类，通过 GPT-4o API 综合证据。
- 可选官方自反馈修订、引用检查，下载完整回答和证据 JSON。
- 密钥仅从后端读取，不上传 GitHub、不保存在网页输入中。

## 与论文配置的区别
本版本默认采用摘要检索，可选官方专用重排序器；不含完整 OSDS 索引、专用稠密检索服务或网页全文检索。OSDS 连接适配器已提供，但必须配置真实检索服务地址。
自反馈开启后会使用已有证据修订；补充检索关闭。因此不能声称达到论文评测效果。
未部署官方 8B 权重；API 方案也属于论文支持的一类生成方式，但并非完整实验复现。
引用编号从 0 开始，保持官方格式。引用检查不保证事实完全正确。
年份筛选不保证收录完整或按时间排序；没有摘要的论文会被排除。

## 启动（推荐 Linux 服务器或有 Docker 的电脑）
1. 克隆本仓库，进入目录。
2. 将 .env.example 复制为 .env，配置 OPENAI_API_KEY；可选配置 S2_API_KEY。不要提交 .env。
3. 运行：
```sh
docker compose up --build -d
```
4. 打开 http://localhost:8501 。

默认仅绑定本机。远程服务器可使用 SSH 隧道访问：
```sh
ssh -L 8501:127.0.0.1:8501 user@your-server
```
之后仍在自己电脑打开 http://localhost:8501 。需要公开网站时，应另外配置认证、HTTPS 和请求额度限制。

## 不使用 Docker
建议 Python 3.11，在独立虚拟环境安装，避免改变系统环境：
```sh
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows PowerShell 改为: .venv/Scripts/Activate.ps1
pip install -r requirements.txt
python -m nltk.downloader punkt punkt_tab
# 可将密钥配置为当前终端环境变量，或写入本地 .env；应用自动读取 .env，但不覆盖已有环境变量。
streamlit run app.py --server.address 127.0.0.1
```

## 使用
填写研究问题、英文检索词、可选年份范围，先检索并查看摘要，再点击生成。
检索本身不调用生成模型；生成、反馈和引用检查会产生模型 API 费用。
模型名暂固定为官方代码费用表支持的 gpt-4o；若服务商停供该模型，需要适配代码。
真实密钥应保留在服务器环境或托管服务的 Secrets 中，不要发到聊天、仓库或 issue。

## 检查
```sh
python -m compileall -q app.py engine.py retrieval.py upstream
python -m unittest discover -s tests -v
```
这些检查验证语法和检索适配逻辑，不代表真实服务连通或模型质量验证。
GitHub Actions 运行相同检查，不会自动部署，也不需要真实密钥。

## 已知条件
- 当前电脑检测到 RTX 5060 Laptop 8GB 显存，但未发现 Docker 命令；本次不安装大模型或改动系统环境。
- 完整原版 8B 推理仍需 vLLM、相容 GPU 环境和检索服务；8GB 显存能否运行特定量化配置未验证。
- 依赖使用主版本范围，尚未生成经过完整运行验证的锁文件；构建后仍需端到端测试。
- 无可用摘要时拒绝生成，不使用演示假数据充当真实检索结果。
- GitHub Pages 无法运行这个 Python 后端。仓库保存代码，实际运行仍需要电脑或服务器。

## 上游与许可证
核心代码位于 upstream/，保留 Apache-2.0 许可证。来源与每个原始文件 blob SHA 见 UPSTREAM.json。
上游适配：run.py 和 src/open_scholar.py 的 vllm 导入改为可选；移除 src/open_scholar.py 中未使用的 spaCy 加载和 FlagReranker 导入，API 模式不安装它们。其他核心文件保持原样。
这里没有修改或重写原始模型的提示词和修订算法，也未复制官方演示站的内部基础设施。

## 本机启动与后续配置
Windows 已有 .venv 时，可运行 ./start.ps1，地址为 http://127.0.0.1:8501 。关闭服务后重新执行即可启动。
当前没有模型密钥也能检索摘要，生成按钮禁用。以后在本地 .env 中填写 OPENAI_API_KEY，重启服务，才会启用生成；不需要更改 GitHub 代码。不要把 .env 提交到仓库。
本机已下载 NLTK punkt_tab 数据并验证官方引擎可导入。NLTK 下载器若因代理策略拒绝下载，不要关闭其安全检查；可通过 requests 从官方 nltk_data 仓库下载对应 tokenizer 压缩包，检查解压目标路径后放入 nltk_data/tokenizers。

## 官方专用重排序器
模型为 OpenSciLM/OpenScholar_Reranker，固定下载版本 f371d9d9a5c47d5b89dfa130d8d6fa303f27126e。
用 Transformers 直接读取官方序列分类权重和 tokenizer，计算问题与段落的相关性 logits，与官方交叉编码器用途一致。未应用引用次数加权；不等于论文完整检索设置。

```sh
pip install -r requirements-reranker.txt
python prepare_reranker.py
```

如果 Hugging Face Hub 的下载在代理环境中停滞，可运行 python prepare_reranker.py --direct，使用官方 HTTPS 文件流并核验权重 SHA256。权重约2.24GB，下载需时间。

模型放在 cache/openscholar-reranker，不上传 GitHub。启动界面后，模型文件存在时默认开启重排序；候选检索增加到最多30条，逐段评分，保留前10条。使用英文检索词评分，建议研究问题也提供英文版本。分数不是正确概率。
CPU 与 GPU 均支持；本机为避免大规模 CUDA 依赖下载，使用 CPU 版 PyTorch，batch=1。首次加载和评分需要等待。跨机器迁移时要重新安装依赖并下载模型。Docker 默认镜像不包含可选重排序依赖；需将 Dockerfile 的安装清单改为 requirements-reranker.txt 后重新构建，并预下载或挂载模型缓存。

## OSDS 连接入口（完整数据服务尚未部署）
在后端 .env 中配置 OSDS_SEARCH_URL，例如你自己服务器的 http://127.0.0.1:9000/search；这里的地址只是示例，程序不会自动创建这个服务。
重启应用后，在来源中选择 OSDS。适配器 POST query、domains=pes2o、n_docs，支持：
- 官方响应：results.passages 与 results["pes2o IDs"] 两个等长列表。没有标题元数据时明确显示 CorpusID 和标题待补充，不伪造论文标题或链接。
- 扩展响应：documents 列表，每项包含 text，可选 title、url、year、citation_counts。

当前 OSDS 适配器不支持年份筛选，填写年份时明确报错。OSDS 服务部署需依照上游 retriever/README.md 配置数据、查询编码器和索引。语料与编码器必须匹配，不能用其他模型随意查询现成索引。
