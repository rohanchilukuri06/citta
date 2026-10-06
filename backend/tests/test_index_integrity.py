"""
Vector index integrity: a changed registry must be detected as stale, never served silently.
"""

import asyncio
import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

import config
from index_integrity import check_index_integrity, compute_registry_hash
from vector_indexer import INDEX_VERSION, REGISTRY_DIR, compute_combined_knowledge_hash


@pytest.fixture
def registry_copy(tmp_path):
    dst = tmp_path / "registry"
    shutil.copytree(REGISTRY_DIR, dst)
    content_js = tmp_path / "content.js"
    content_js.write_text("export const X = 1;", encoding="utf-8")
    meta = {
        "content_hash": compute_combined_knowledge_hash(str(content_js), dst),
        "registry_hash": compute_registry_hash(dst),
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dimension": "768",
        "version": INDEX_VERSION,
    }
    return dst, str(content_js), meta


def test_fresh_index_is_fresh(registry_copy):
    reg, cjs, meta = registry_copy
    assert check_index_integrity(meta, reg, cjs, stored_dimension=768)["fresh"]


def test_registry_change_is_detected(registry_copy):
    reg, cjs, meta = registry_copy
    f = next((reg / "new").glob("solution_*.json"))
    data = json.loads(f.read_text(encoding="utf-8"))
    data["description"] = (data.get("description") or "") + " (edited)"
    f.write_text(json.dumps(data), encoding="utf-8")
    status = check_index_integrity(meta, reg, cjs, stored_dimension=768)
    assert not status["fresh"]
    assert any("registry_hash" in r for r in status["reasons"])


def test_embedding_model_and_dimension_mismatch_detected(registry_copy):
    reg, cjs, meta = registry_copy
    status = check_index_integrity({**meta, "embedding_model": "other/model"}, reg, cjs, stored_dimension=384)
    assert not status["fresh"]
    assert any("embedding model" in r for r in status["reasons"])
    assert any("dimension" in r for r in status["reasons"])


def test_production_blocks_chat_when_stale(monkeypatch):
    import index_integrity
    monkeypatch.setattr(index_integrity, "_STATUS", {"fresh": False, "rebuild_required": True, "reasons": ["test"]})
    from rag_service import RAGService

    class P:
        async def generate_stream(self, *a, **k):
            yield "x"

    rag = RAGService.__new__(RAGService)  # the integrity gate runs before any service state is touched
    rag.provider = P()

    async def run():
        return [c async for c in rag.chat_stream("s", "What is Education OS?", "m")]
    chunks = asyncio.run(run())
    assert chunks[-1]["metrics"]["index_rebuild_required"] is True
    assert "being updated" in chunks[0]["text"]
