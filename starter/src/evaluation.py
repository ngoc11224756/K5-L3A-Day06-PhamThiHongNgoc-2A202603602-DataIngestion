"""Evaluate retrieved evidence and preserve per-query traces."""
import re
import unicodedata
from typing import Any


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def _gold_candidates(question: dict[str, Any]) -> list[dict[str, Any]]:
    """Gom các bộ (source, page, evidence) hợp lệ: gold chính + alt_golds nếu có."""
    candidates = [
        {
            "source_id": question.get("gold_source_id"),
            "page": question.get("gold_page"),
            "quote_norm": _normalize(question.get("evidence_quote", "")),
        }
    ]
    for alt in question.get("alt_golds", []):
        candidates.append(
            {
                "source_id": alt.get("gold_source_id"),
                "page": alt.get("gold_page"),
                "quote_norm": _normalize(alt.get("evidence_quote", "")),
            }
        )
    return candidates


def _is_hit(hit: dict[str, Any], candidates: list[dict[str, Any]]) -> bool:
    hit_content_norm = _normalize(hit.get("content", ""))
    for cand in candidates:
        if hit.get("document_id") != cand["source_id"]:
            continue
        if hit.get("page") != cand["page"]:
            continue
        if cand["quote_norm"] and cand["quote_norm"] not in hit_content_norm:
            continue
        return True
    return False


def evaluate_query(
    question: dict[str, Any],
    hits: list[dict[str, Any]],
    filter_used: bool = False,
) -> dict[str, Any]:
    """Chấm tự động Hit@1 / Evidence Hit@3 bằng khớp source + page + evidence_quote.

    Chỉ dùng cho tiêu chí 1 (độ chính xác truy xuất). KHÔNG suy ra nhãn
    coherence hay grounding từ đây: hai tiêu chí đó chấm thủ công thang 0-2.
    """
    candidates = _gold_candidates(question)

    hits_trace: list[dict[str, Any]] = []
    hit_rank: int | None = None
    matched_chunk_id: str | None = None

    for rank, hit in enumerate(hits, start=1):
        is_match = _is_hit(hit, candidates)
        distance = hit.get("distance")
        hits_trace.append(
            {
                "rank": rank,
                "chunk_id": hit.get("chunk_id"),
                "document_id": hit.get("document_id"),
                "source": hit.get("source"),
                "page": hit.get("page"),
                "chuong": hit.get("chuong"),
                "metadata": hit.get("metadata"),
                "distance": distance,
                "score": None if distance is None else 1 - distance,
                "content": hit.get("content"),
                "is_match": is_match,
            }
        )
        if is_match and hit_rank is None:
            hit_rank = rank
            matched_chunk_id = hit.get("chunk_id")

    # Tuân thủ filter: chỉ tính khi câu có filter VÀ cấu hình này đã áp filter.
    # None = không áp dụng (N/A), không mặc định đúng.
    flt = question.get("filter")
    filter_ok: bool | None = None
    if flt and filter_used:
        filter_ok = bool(hits) and all(
            all(h.get(k) == v for k, v in flt.items()) for h in hits
        )

    return {
        "id": question.get("id"),
        "split": question.get("split"),
        "question": question.get("question"),
        "filter": flt,
        "filter_used": filter_used,
        "filter_ok": filter_ok,
        "hit_rank": hit_rank,
        "hit_at_1": hit_rank == 1,
        "hit_at_3": hit_rank is not None and hit_rank <= 3,
        "matched_chunk_id": matched_chunk_id,
        "hits": hits_trace,
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Tổng hợp Hit@1/Hit@3 và tuân thủ filter theo strategy và split.

    Mỗi trace phải có khóa "strategy" do bên gọi gán trước khi đưa vào đây.
    """
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for trace in traces:
        key = (trace.get("strategy"), trace.get("split"))
        grouped.setdefault(key, []).append(trace)

    summary: dict[str, Any] = {}
    for (strategy, split), group in grouped.items():
        n = len(group)
        hit1 = sum(1 for t in group if t.get("hit_at_1"))
        hit3 = sum(1 for t in group if t.get("hit_at_3"))
        fl = [t for t in group if t.get("filter_ok") is not None]
        summary.setdefault(strategy, {})[split] = {
            "n": n,
            "hit_at_1": hit1,
            "hit_at_1_rate": (hit1 / n) if n else None,
            "hit_at_3": hit3,
            "hit_at_3_rate": (hit3 / n) if n else None,
            "filter_n": len(fl),  # 0 -> báo N/A
            "filter_ok": sum(1 for t in fl if t["filter_ok"]),
        }
    return summary