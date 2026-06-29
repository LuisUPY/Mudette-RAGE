"""Build FAISS knowledge base from demo_pack kb_src markdown files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import faiss
import numpy as np

from mtguard.embedder import EMBED_DIM, Embedder


def chunk_markdown(text: str, source: str, chunk_size: int = 400) -> list[dict]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[dict] = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) > chunk_size and buffer:
            chunks.append({"text": buffer.strip(), "source": source})
            buffer = para
        else:
            buffer = f"{buffer}\n\n{para}".strip() if buffer else para
    if buffer.strip():
        chunks.append({"text": buffer.strip(), "source": source})
    return chunks


def build_kb(pack_dir: Path) -> None:
    kb_src = pack_dir / "kb_src"
    kb_dir = pack_dir / "kb"
    kb_dir.mkdir(parents=True, exist_ok=True)

    all_chunks: list[dict] = []
    source_files: list[str] = []
    for md_path in sorted(kb_src.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        source_files.append(md_path.name)
        all_chunks.extend(chunk_markdown(text, md_path.name))

    dim = EMBED_DIM
    embedder = Embedder(n_features=dim)
    if all_chunks:
        texts = [c["text"] for c in all_chunks]
        matrix = embedder.embed_many(texts)
        index = faiss.IndexFlatIP(dim)
        index.add(matrix)
        faiss.write_index(index, str(kb_dir / "index.faiss"))
    else:
        index = faiss.IndexFlatIP(dim)
        faiss.write_index(index, str(kb_dir / "index.faiss"))

    (kb_dir / "chunks.json").write_text(json.dumps(all_chunks, indent=2), encoding="utf-8")
    manifest = {
        "pack_id": pack_dir.name,
        "chunk_count": len(all_chunks),
        "embedding_dim": dim,
        "source_files": source_files,
    }
    (kb_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Built KB: {len(all_chunks)} chunks → {kb_dir}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    pack = root / "demo_pack" / "nexa_copilot"
    if len(sys.argv) > 1:
        pack = Path(sys.argv[1])
    build_kb(pack)


if __name__ == "__main__":
    main()
