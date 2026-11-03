#!/usr/bin/env python3
"""Offline ranked search for the PPT icon library."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def root_dir() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent if (here.parent.parent / "INDEX").exists() else here.parents[1] / "PPT_ICON_LIBRARY_500_v1.0"


def ngrams(text: str) -> set[str]:
    text = re.sub(r"\s+", "", text.lower())
    if len(text) < 2:
        return {text} if text else set()
    return {text[i:i + 2] for i in range(len(text) - 1)}


def score_record(record: dict, query: str, variants: list[str]) -> tuple[float, list[str]]:
    name = record["name_zh"].lower()
    category = record["category"][3:].lower()
    zh_terms = [x.lower() for x in record["keywords_zh"] + record.get("aliases_zh", [])]
    en_terms = [x.lower() for x in record["keywords_en"] + [record["name_en"]]]
    score = 0.0
    reasons = []
    normalized_query = re.sub(r"[与和及的\s]", "", query.lower())
    normalized_category = re.sub(r"[与和及的\s]", "", category)
    if normalized_query == normalized_category:
        score += 95; reasons.append("类别归一精确")
    concepts = ["设备", "维护", "安全", "风险", "物流", "配送", "仓储", "人员", "培训", "质量", "制造", "工厂", "数据", "数字化", "管理", "计划", "流程", "成本", "财务", "经营", "效率", "改善", "精益", "能源", "环保", "科研", "教育", "技术"]
    corpus_all = "".join([name, category, *zh_terms])
    concept_hits = [concept for concept in concepts if concept in query and concept in corpus_all]
    if concept_hits:
        score += 32 * len(concept_hits); reasons.append("复合语义")
    for variant in variants:
        v = variant.lower().strip()
        if not v:
            continue
        if v == name:
            score += 120; reasons.append("中文名精确")
        if v in zh_terms:
            score += 100; reasons.append("中文关键词精确")
        if v == category:
            score += 70; reasons.append("类别精确")
        if v in name and v != name:
            score += 65; reasons.append("中文名包含")
        matches = sum(1 for term in zh_terms if v in term or term in v)
        if matches:
            score += min(60, matches * 18); reasons.append("中文语义")
        if v in category or category in v:
            score += 30; reasons.append("类别相关")
        if re.fullmatch(r"[a-z0-9 _-]+", v):
            if v in en_terms:
                score += 85; reasons.append("英文关键词精确")
            elif any(v in term for term in en_terms):
                score += 40; reasons.append("英文关键词包含")
    qgrams = ngrams(query)
    corpus = corpus_all
    if qgrams:
        score += 24 * len(qgrams & ngrams(corpus)) / len(qgrams)
    score += {"P1": 10, "P2": 5, "P3": 1}[record["priority"]]
    score += record.get("selection_score_total", 0) / 50
    return score, list(dict.fromkeys(reasons))


def search(query: str, limit: int) -> list[dict]:
    root = root_dir()
    manifest = json.loads((root / "INDEX" / "icon_manifest.json").read_text(encoding="utf-8"))
    aliases = json.loads((root / "INDEX" / "aliases_zh.json").read_text(encoding="utf-8"))
    variants = [query]
    for alias, canonical in aliases.items():
        if alias.lower() in query.lower():
            variants.extend([canonical, query.replace(alias, canonical)])
    ranked = []
    for record in manifest:
        value, reasons = score_record(record, query, list(dict.fromkeys(variants)))
        if value > 10:
            ranked.append({
                "icon_id": record["id"], "name_zh": record["name_zh"], "name_en": record["name_en"],
                "category": record["category"], "path": record["relative_path"],
                "priority": record["priority"], "match_score": round(value, 2), "match_reasons": reasons,
            })
    ranked.sort(key=lambda x: (-x["match_score"], x["priority"], x["icon_id"]))
    return ranked[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="离线检索 PPT_ICON_LIBRARY_500_v1.0")
    parser.add_argument("query", help="中文自然语言或英文关键词")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = search(args.query, max(1, args.limit))
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print(f"{'icon_id':<10} {'中文名':<14} {'英文名':<28} {'分类':<22} {'分数':>7}  路径")
    print("-" * 120)
    for item in results:
        print(f"{item['icon_id']:<10} {item['name_zh']:<14} {item['name_en']:<28} {item['category']:<22} {item['match_score']:>7.2f}  {item['path']}")


if __name__ == "__main__":
    main()
