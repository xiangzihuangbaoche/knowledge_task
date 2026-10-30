import os
import json
import streamlit as st
from retrieval import search
from engine import synthesize

st.set_page_config(page_title="OpenScholar 文献助手", page_icon="📚", layout="wide")
st.title("OpenScholar 文献助手")
st.caption("基于官方推理代码的 API 试运行版 · Semantic Scholar 摘要检索")
st.info("尚未接入完整 OSDS 和专用重排序器。本版本不等同于论文实验配置。生成内容需核查原文。")
with st.sidebar:
    st.header("运行设置")
    st.write("模型 API：" + ("已配置" if os.getenv("OPENAI_API_KEY") else "未配置"))
    st.write("检索 API：" + ("已配置" if os.getenv("S2_API_KEY") else "公共访问，可能限流"))
    year = st.text_input("发表年份筛选（可选）", placeholder="例如 2024-2026")
    feedback = st.checkbox("启用官方自反馈修订（增加调用量）", value=False)
    attribution = st.checkbox("启用官方引用检查", value=True)
    st.caption("密钥只从后端环境变量读取。请勿把密钥写入仓库。")
question = st.text_area("研究问题", placeholder="例如：不同文献如何评价检索增强生成中的引用可靠性？")
query = st.text_input("英文检索词", placeholder="例如 retrieval augmented generation citation faithfulness")
if st.button("检索文献", type="primary"):
    if not question.strip() or not query.strip():
        st.warning("请填写研究问题和检索词。")
    else:
        st.session_state.pop("result", None)
        st.session_state.pop("evidence", None)
        try:
            with st.spinner("检索摘要…"):
                contexts = search(query, os.getenv("S2_API_KEY", ""), year)
            st.session_state.evidence = {"question": question, "query": query, "year": year, "contexts": contexts}
        except Exception:
            st.error("检索失败：可能被限流或网络不可达。请稍后重试，或配置检索 API。")
evidence = st.session_state.get("evidence")
if evidence:
    contexts = evidence["contexts"]
    st.subheader(f"已获取 {len(contexts)} 篇有摘要的文献")
    if not contexts:
        st.warning("未获得可用摘要，请更换检索词。")
    for i, ctx in enumerate(contexts):
        # Upstream uses zero-based reference IDs.
        with st.expander(f"[{i}] {ctx['title']} · {ctx['year']}"):
            st.write(ctx["text"])
            if ctx["url"].startswith("https://"):
                st.link_button("查看来源", ctx["url"])
    if question != evidence["question"] or query != evidence["query"] or year != evidence["year"]:
        st.warning("问题或筛选条件已修改，请重新检索后生成。")
    elif contexts and st.button("基于这些摘要生成回答（会调用付费模型 API）"):
        try:
            with st.spinner("综合证据并检查引用…"):
                st.session_state.result = synthesize(question, contexts, feedback, attribution)
        except Exception:
            st.error("生成失败。请检查后端模型 API 配置、额度及运行依赖。")
if st.session_state.get("result"):
    result = st.session_state.result
    st.subheader("综合回答")
    st.markdown(result.get("output", "未返回回答"), unsafe_allow_html=False)
    st.download_button("下载回答与证据 JSON", json.dumps(result, ensure_ascii=False, indent=2),
                       file_name="openscholar-result.json", mime="application/json")
