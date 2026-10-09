"""
Primo (e unico) download dei modelli densi candidati alla revisione fissata in retrieval/config_dense.yaml (voce 107).
Scarica nella cache di Hugging Face dell'utente (MAI in git) solo i file che servono a sentence-transformers su
PyTorch: niente ONNX, OpenVINO, TensorFlow, Flax, Rust e niente `*.bin` se c'e' `model.safetensors`.
Dopo questo passo l'analisi gira offline (HF_HUB_OFFLINE=1).

Uso:
    python retrieval/download_dense_models.py
"""

from __future__ import annotations

from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parent / "config_dense.yaml"
IGNORE = ["onnx/*", "openvino/*", "*.onnx", "*.h5", "*.msgpack", "rust_model.ot", "tf_model*", "flax_model*",
          "coreml/*"]


def main() -> None:
    from huggingface_hub import HfApi, snapshot_download
    api = HfApi()
    for m in yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["modelli"]:
        files = api.list_repo_files(m["nome"], revision=m["revisione"])
        ignore = IGNORE + (["*.bin"] if "model.safetensors" in files else [])
        path = snapshot_download(m["nome"], revision=m["revisione"], ignore_patterns=ignore)
        size = sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file())
        assert Path(path).name == m["revisione"], (path, m["revisione"])
        print(f"{m['nome']} @ {m['revisione'][:12]}: {size / 1e6:.0f} MB in {path}")


if __name__ == "__main__":
    main()
