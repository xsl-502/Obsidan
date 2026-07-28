#!/usr/bin/env python3
"""Backfill liquidity_ratio in the extracted annual-report CSV."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from pypdf import PdfReader


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def normalize_number(raw: str) -> str:
    return raw.strip().replace(",", "").replace("，", "").replace("%", "").replace("％", "")


def numbers_after_keyword(line: str, keyword: str = "流动性比例") -> list[str]:
    if keyword not in line:
        return []
    scoped = line[line.find(keyword) :]
    scoped = re.sub(r"[≥>=]\s*\d+(?:\.\d+)?%?", " ", scoped)
    nums = re.findall(r"[-+]?\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?%?|[-+]?\d+(?:\.\d+)?%?", scoped)
    out = []
    for n in nums:
        n = normalize_number(n)
        try:
            v = float(n)
        except ValueError:
            continue
        if 0 < v <= 200:
            out.append(n)
    return out


def extract_liquidity_ratio(pdf_path: Path) -> tuple[str, str, str]:
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return "", "", ""

    candidates: list[tuple[int, float, str, str]] = []
    for page_idx, page in enumerate(reader.pages, start=1):
        try:
            text = clean_text(page.extract_text() or "")
        except Exception:
            continue
        if "流动性比例" not in text:
            continue
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if "流动性比例" not in line:
                continue
            if "不适用" in line or "释义" in line or "定义" in line:
                continue
            nums = numbers_after_keyword(line)
            if not nums:
                continue
            value = nums[0]
            score = 0.0
            if "人民币" in line:
                score += 8
            if "本外币" in line or "折人民币" in line:
                score += 6
            if "监管" in line or "主要" in line:
                score += 4
            if page_idx <= 80:
                score += 2
            if "≥" in line or ">=" in line:
                score += 2
            candidates.append((page_idx, score, value, line[:260]))

    if not candidates:
        return "", "", ""
    candidates.sort(key=lambda x: (x[1], -x[0]), reverse=True)
    page_idx, _score, value, evidence = candidates[0]
    return value, str(page_idx), evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill liquidity_ratio from annual-report PDFs.")
    parser.add_argument("--in-csv", default="02_数据集/上市银行年报PDF/上市银行年报指标提取_v2.csv")
    parser.add_argument("--out-csv", default="02_数据集/上市银行年报PDF/上市银行年报指标提取_v3_liquidity_filled.csv")
    parser.add_argument("--todo", default="02_数据集/上市银行年报PDF/liquidity_ratio_仍需手动补充.csv")
    args = parser.parse_args()

    in_path = Path(args.in_csv)
    rows = list(csv.DictReader(in_path.open(encoding="utf-8-sig")))
    fieldnames = list(rows[0].keys())

    filled = 0
    still_missing = []
    for row in rows:
        if row.get("liquidity_ratio"):
            continue
        pdf_path = Path(row["pdf_file"])
        value, page, evidence = extract_liquidity_ratio(pdf_path)
        if value:
            row["liquidity_ratio"] = value
            row["liquidity_ratio_page"] = page
            row["liquidity_ratio_evidence"] = evidence
            filled += 1
        else:
            still_missing.append(row)

    out_path = Path(args.out_csv)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    todo_path = Path(args.todo)
    todo_fields = ["code", "bank_name", "year", "pdf_file"]
    with todo_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=todo_fields)
        writer.writeheader()
        for row in still_missing:
            writer.writerow({k: row[k] for k in todo_fields})

    print(f"Filled liquidity_ratio: {filled}")
    print(f"Still missing: {len(still_missing)}")
    print(f"Saved: {out_path}")
    print(f"Todo: {todo_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
