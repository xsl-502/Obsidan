#!/usr/bin/env python3
"""Create a conservatively filled liquidity-ratio dataset."""

from __future__ import annotations

import csv
import re
from pathlib import Path


BASE = Path("02_数据集/上市银行年报PDF/上市银行年报指标提取_v3_liquidity_filled.csv")
CAND = Path("02_数据集/上市银行年报PDF/流动性指标全文扫描候选.csv")
OUT = Path("02_数据集/上市银行年报PDF/上市银行年报指标提取_v4_保守补流动性比例.csv")
TODO = Path("02_数据集/上市银行年报PDF/liquidity_ratio_最终仍缺失.csv")


def nums_after_liquidity(evidence: str) -> list[str]:
    if "流动性比例" not in evidence:
        return []
    text = evidence[evidence.find("流动性比例") :]
    text = re.sub(r"[≥>=]\s*\d+(?:\.\d+)?%?", " ", text)
    found = re.findall(r"[-+]?\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?%?|[-+]?\d+(?:\.\d+)?%?", text)
    out = []
    for x in found:
        x = x.replace(",", "").replace("，", "").replace("%", "").replace("％", "")
        try:
            v = float(x)
        except ValueError:
            continue
        if 20 <= v <= 120:
            out.append(x)
    return out


def main() -> int:
    rows = list(csv.DictReader(BASE.open(encoding="utf-8-sig")))
    cands = {(r["code"], r["year"]): r for r in csv.DictReader(CAND.open(encoding="utf-8-sig"))}
    fields = list(rows[0].keys())
    fills = []
    for row in rows:
        if row["liquidity_ratio"]:
            continue
        cand = cands.get((row["code"], row["year"]))
        if not cand:
            continue
        evidence = cand.get("liquidity_ratio_evidence", "")
        if "流动性比例" not in evidence:
            continue
        values = nums_after_liquidity(evidence)
        if not values:
            continue
        value = values[0]
        row["liquidity_ratio"] = value
        row["liquidity_ratio_page"] = cand.get("liquidity_ratio_page", "")
        row["liquidity_ratio_evidence"] = evidence
        fills.append((row["code"], row["bank_name"], row["year"], value))

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    missing = [r for r in rows if not r["liquidity_ratio"]]
    with TODO.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "bank_name", "year", "pdf_file"])
        writer.writeheader()
        for r in missing:
            writer.writerow({k: r[k] for k in ["code", "bank_name", "year", "pdf_file"]})

    print("Reliable fills:", len(fills))
    for item in fills:
        print(*item)
    print("Still missing:", len(missing))
    print("Saved:", OUT)
    print("Todo:", TODO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
