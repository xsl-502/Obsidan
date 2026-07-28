#!/usr/bin/env python3
"""Scan annual reports for liquidity-related indicators."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from pypdf import PdfReader


REPORTS_DIR = Path("02_数据集/上市银行年报PDF")
OUT = REPORTS_DIR / "流动性指标全文扫描候选.csv"


def clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\u3000", " "))


def nums(text: str) -> list[str]:
    text = re.sub(r"[≥>=]\s*\d+(?:\.\d+)?%?", " ", text)
    found = re.findall(r"[-+]?\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?%?|[-+]?\d+(?:\.\d+)?%?", text)
    out = []
    for x in found:
        x = x.replace(",", "").replace("，", "").replace("%", "").replace("％", "")
        try:
            v = float(x)
        except ValueError:
            continue
        if 0 < v <= 300:
            out.append(x)
    return out


def first_value_after(line: str, terms: list[str]) -> str:
    compact = "".join(line.split())
    for term in terms:
        compact_term = "".join(term.split())
        pos = compact.find(compact_term)
        if pos >= 0:
            values = nums(compact[pos:])
            decimals = [v for v in values if "." in v]
            return decimals[0] if decimals else (values[0] if values else "")
    return ""


def parse_filename(path: Path) -> tuple[str, str, str]:
    m = re.match(r"(\d{6})_(.+?)_(\d{4})_年度报告\.pdf$", path.name)
    return m.groups() if m else ("", "", "")


def main() -> int:
    rows = []
    terms = {
        "liquidity_ratio": ["人民币流动性比例", "流动性比例"],
        "lcr": ["流动性覆盖率"],
        "nsfr": ["净稳定资金比例"],
    }
    for path in sorted(REPORTS_DIR.glob("*_年度报告.pdf")):
        code, name, year = parse_filename(path)
        print(path.name, flush=True)
        try:
            reader = PdfReader(str(path))
        except Exception:
            continue
        best: dict[str, tuple[str, str, str]] = {k: ("", "", "") for k in terms}
        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                text = clean(page.extract_text() or "")
            except Exception:
                continue
            if not any(term in text for term_list in terms.values() for term in term_list):
                continue
            lines = text.splitlines()
            for i, line in enumerate(lines):
                window = " ".join(lines[i : i + 3])
                for metric, metric_terms in terms.items():
                    if not any(term in window or "".join(term.split()) in "".join(window.split()) for term in metric_terms):
                        continue
                    value = first_value_after(window, metric_terms)
                    if not value:
                        continue
                    old_value, old_page, _ = best[metric]
                    if not old_value or page_idx < int(old_page):
                        best[metric] = (value, str(page_idx), window[:260])
        row = {"code": code, "bank_name": name, "year": year, "pdf_file": str(path)}
        for metric in terms:
            row[metric], row[f"{metric}_page"], row[f"{metric}_evidence"] = best[metric]
        rows.append(row)

    fields = ["code", "bank_name", "year", "pdf_file"]
    for metric in terms:
        fields += [metric, f"{metric}_page", f"{metric}_evidence"]
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
