"""Download only official weights/tokenizer files into the project cache."""
import argparse
import hashlib
from reranking import MODEL_DIR, MODEL_ID

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct", action="store_true", help="Use HTTPS streaming when Hub download stalls")
    args = parser.parse_args()
    revision = "f371d9d9a5c47d5b89dfa130d8d6fa303f27126e"
    if args.direct:
        import requests
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        for name in ["config.json", "model.safetensors", "tokenizer_config.json",
                     "special_tokens_map.json", "sentencepiece.bpe.model"]:
            path = MODEL_DIR / name
            digest = hashlib.sha256()
            temporary = path.with_suffix(path.suffix + ".part")
            with requests.get(f"https://huggingface.co/{MODEL_ID}/resolve/{revision}/{name}",
                              stream=True, timeout=(20, 90)) as response:
                response.raise_for_status()
                count = 0
                with temporary.open("wb") as output:
                    for chunk in response.iter_content(4 * 1024 * 1024):
                        output.write(chunk)
                        digest.update(chunk)
                        count += len(chunk)
                if name == "model.safetensors":
                    if digest.hexdigest() != "a094204493283b1a87cf2d59674fe0db1f04891f0667b6d84368042a51c07e90":
                        raise ValueError("Official model SHA256 mismatch")
                temporary.replace(path)
                print("Downloaded", name, count, flush=True)
    else:
        from huggingface_hub import snapshot_download
        snapshot_download(MODEL_ID, revision=revision, local_dir=str(MODEL_DIR),
                          allow_patterns=["config.json", "model.safetensors", "tokenizer*",
                                          "special_tokens_map.json", "sentencepiece*", "*.model"])
    print("Model saved to", MODEL_DIR)
