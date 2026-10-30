"""Adapter for the upstream API inference pipeline."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "upstream"))

def synthesize(question, contexts, feedback=False, attribution=True):
    if not contexts:
        raise ValueError("没有找到可用摘要，请调整检索词；不会在无证据时生成综述。")
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("后端尚未配置 OPENAI_API_KEY。")
    # Upstream reads S2_API_KEY at import time, including supplied-context mode.
    os.environ.setdefault("S2_API_KEY", "")
    from openai import OpenAI
    import nltk
    nltk.data.path.insert(0, str(ROOT / "nltk_data"))
    from src.open_scholar import OpenScholar
    client = OpenAI(api_key=key, timeout=90, max_retries=2)
    # Kept within upstream's supported model/cost table.
    scholar = OpenScholar(model=None, tokenizer=None, client=client,
                          api_model_name="gpt-4o", top_n=10,
                          use_contexts=True, ss_retriever=False)
    item = {"input": question, "answer": "", "ctxs": contexts}
    result, _ = scholar.run(item, ranking_ce=False,
                            use_feedback=feedback, posthoc_at=attribution,
                            zero_shot=True, max_tokens=2500)
    return result
