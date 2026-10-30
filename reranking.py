"""Official cross-encoder weights, loaded once per process; no generation API."""
import os
from functools import lru_cache
from pathlib import Path

MODEL_ID = "OpenSciLM/OpenScholar_Reranker"
MODEL_DIR = Path(__file__).resolve().parent / "cache" / "openscholar-reranker"

@lru_cache(maxsize=1)
def load_model():
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    path = os.getenv("RERANKER_MODEL_PATH") or str(MODEL_DIR)
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        path, local_files_only=True, use_safetensors=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    if device == "cuda":
        model.half()
    return tokenizer, model, device

def rerank(question, contexts, top_n=10):
    if not contexts:
        return []
    import torch
    tokenizer, model, device = load_model()
    scores = []
    # One passage per batch bounds memory on laptops.
    with torch.inference_mode():
        for ctx in contexts:
            inputs = tokenizer([[question, ctx.get("title", "") + "\n" + ctx["text"]]],
                               padding=True, truncation=True, max_length=512,
                               return_tensors="pt").to(device)
            score = model(**inputs).logits.float().reshape(-1).item()
            scores.append(score)
    ranked = [dict(ctx, rerank_score=score) for ctx, score in zip(contexts, scores)]
    return sorted(ranked, key=lambda ctx: ctx["rerank_score"], reverse=True)[:top_n]
