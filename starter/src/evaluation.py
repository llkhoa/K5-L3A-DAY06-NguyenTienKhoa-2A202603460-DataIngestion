"""Evaluate retrieved evidence and preserve per-query traces."""
from typing import Any

def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and enough gold evidence; keep hit@1 and hit@3 trace."""

    gold_source = question.get("gold_source_id")
    gold_page = question.get("gold_page")
    evidence_quote = question.get("evidence_quote", "").lower()

    hit_1 = False
    hit_3 = False
    evaluated_hits = []

    for idx, hit in enumerate(hits):
        # 1. Check if source matches
        source_match = (hit["document_id"] == gold_source)

        # 2. Check if page matches (if gold_page is specified)
        page_match = True
        if gold_page is not None:
            page_match = (hit["page"] == gold_page)

        # 3. Check if evidence is present in the text
        evidence_match = True
        if evidence_quote:
            # Xóa sạch khoảng trắng dư thừa/xuống dòng để so sánh chuẩn xác
            clean_quote = " ".join(evidence_quote.lower().split())
            clean_text = " ".join(hit["text"].lower().split())
            evidence_match = (clean_quote in clean_text)

        is_hit = source_match and page_match and evidence_match

        if is_hit:
            hit_3 = True
            if idx == 0:
                hit_1 = True

        hit_trace = hit.copy()
        hit_trace["is_hit"] = is_hit
        evaluated_hits.append(hit_trace)

    return {
        "question_id": question.get("id"),
        "split": question.get("split", "dev"),
        "hit_1": hit_1,
        "hit_3": hit_3,
        "traces": evaluated_hits
    }

def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by split."""
    summary = {}

    for trace in traces:
        split = trace["split"]
        if split not in summary:
            summary[split] = {"total": 0, "hit_1": 0, "hit_3": 0}

        summary[split]["total"] += 1
        if trace["hit_1"]:
            summary[split]["hit_1"] += 1
        if trace["hit_3"]:
            summary[split]["hit_3"] += 1

    # Calculate percentages
    for split, stats in summary.items():
        total = stats["total"]
        if total > 0:
            stats["hit_1_rate"] = round((stats["hit_1"] / total) * 100, 2)
            stats["hit_3_rate"] = round((stats["hit_3"] / total) * 100, 2)

    return summary