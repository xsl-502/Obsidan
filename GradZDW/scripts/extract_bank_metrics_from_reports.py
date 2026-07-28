#!/usr/bin/env python3
"""Extract common bank metrics from downloaded annual-report PDFs.

This is a pragmatic first-pass extractor. Annual reports vary by bank and year,
so use the generated CSV as a working dataset and audit flagged rows manually.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


METRICS = {
    "total_assets": ["资产总额", "资产总计", "总资产"],
    "total_loans": [
        "发放贷款和垫款总额",
        "发放贷款及垫款总额",
        "客户贷款和垫款总额",
        "客户贷款及垫款总额",
        "贷款和垫款总额",
        "贷款及垫款总额",
        "贷款总额",
    ],
    "total_deposits": ["吸收存款", "客户存款总额", "客户存款", "存款总额", "存款总计"],
    "liquidity_ratio": ["流动性比例"],
    "loan_deposit_ratio": ["存贷比", "贷存比"],
    "capital_adequacy_ratio": ["资本充足率"],
    "tier1_capital_ratio": ["一级资本充足率"],
    "core_tier1_capital_ratio": ["核心一级资本充足率"],
    "npl_ratio": ["不良贷款率"],
    "provision_coverage": ["拨备覆盖率"],
    "cost_income_ratio": ["成本收入比"],
    "roa": ["平均总资产收益率", "总资产收益率", "ROA"],
    "roe": ["加权平均净资产收益率", "平均净资产收益率", "ROE"],
}


@dataclass
class ExtractedValue:
    value: str = ""
    page: str = ""
    evidence: str = ""


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def parse_filename(path: Path) -> tuple[str, str, str]:
    match = re.match(r"(?P<code>\d{6})_(?P<name>.+?)_(?P<year>\d{4})_年度报告\.pdf$", path.name)
    if not match:
        return "", "", ""
    return match.group("code"), match.group("name"), match.group("year")


def looks_like_percent_metric(metric: str) -> bool:
    return metric in {
        "liquidity_ratio",
        "loan_deposit_ratio",
        "capital_adequacy_ratio",
        "tier1_capital_ratio",
        "core_tier1_capital_ratio",
        "npl_ratio",
        "provision_coverage",
        "cost_income_ratio",
        "roa",
        "roe",
    }


def normalize_number(raw: str) -> str:
    raw = raw.strip()
    raw = raw.replace(",", "")
    raw = raw.replace("，", "")
    raw = raw.replace("%", "")
    raw = raw.replace("％", "")
    return raw


def candidate_numbers(line: str) -> list[str]:
    pattern = r"[-+]?\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?%?|[-+]?\d+(?:\.\d+)?%?"
    return re.findall(pattern, line)


def line_matches_metric(line: str, metric: str, keywords: list[str]) -> bool:
    if not any(kw in line for kw in keywords):
        return False
    if "指标" in line and "月" in line:
        return False
    if metric == "capital_adequacy_ratio":
        return "资本充足率" in line and "核心一级资本充足率" not in line and "一级资本充足率" not in line
    if metric == "tier1_capital_ratio":
        return "一级资本充足率" in line and "核心一级资本充足率" not in line
    return True


def score_line(line: str, keywords: list[str], metric: str, page_idx: int) -> int:
    score = 0
    for kw in keywords:
        if kw in line:
            score += 10 + len(kw)
    if looks_like_percent_metric(metric) and ("%" in line or "％" in line):
        score += 4
    if "监管指标" in line or "主要财务指标" in line or "财务摘要" in line or "资本充足率指标" in line:
        score += 2
    if page_idx <= 30:
        score += 3
    if any(line.startswith(kw) for kw in keywords):
        score += 8
    if "较上年" in line or "同比" in line or "增加" in line or "减少" in line:
        score -= 2
    return score


def choose_value_from_line(line: str, metric: str, report_year: str, keywords: list[str]) -> str:
    positions = [line.find(kw) for kw in keywords if kw in line]
    scoped_line = line[min(positions) :] if positions else line
    scoped_line = re.sub(r"[≥>=]\s*\d+(?:\.\d+)?%?", " ", scoped_line)
    nums = [normalize_number(x) for x in candidate_numbers(scoped_line)]
    nums = [x for x in nums if x and x != report_year]
    if not nums:
        return ""

    if looks_like_percent_metric(metric):
        plausible = []
        for x in nums:
            try:
                val = float(x)
            except ValueError:
                continue
            if metric in {"provision_coverage"}:
                if 0 <= val <= 1000:
                    plausible.append(x)
            elif 0 <= val <= 200:
                plausible.append(x)
        decimal_plausible = [x for x in plausible if "." in x]
        return decimal_plausible[0] if decimal_plausible else (plausible[0] if plausible else nums[0])

    plausible = []
    for x in nums:
        try:
            val = float(x)
        except ValueError:
            continue
        if val > 10:
            plausible.append(x)
    return plausible[0] if plausible else nums[0]


def extract_from_pdf(path: Path, max_pages: int | None = 80) -> dict[str, ExtractedValue]:
    code, name, year = parse_filename(path)
    results = {metric: ExtractedValue() for metric in METRICS}
    best_scores = {metric: -999 for metric in METRICS}

    reader = PdfReader(str(path))
    pages = reader.pages if max_pages is None else reader.pages[:max_pages]
    for page_idx, page in enumerate(pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            continue
        text = clean_text(text)
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            for metric, keywords in METRICS.items():
                if not line_matches_metric(line, metric, keywords):
                    continue
                value = choose_value_from_line(line, metric, year, keywords)
                if not value:
                    continue
                score = score_line(line, keywords, metric, page_idx)
                if score > best_scores[metric]:
                    best_scores[metric] = score
                    results[metric] = ExtractedValue(
                        value=value,
                        page=str(page_idx),
                        evidence=line[:260],
                    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract metrics from listed bank annual reports.")
    parser.add_argument("--reports-dir", default="02_数据集/上市银行年报PDF")
    parser.add_argument("--out", default="02_数据集/上市银行年报PDF/上市银行年报指标提取_初版.csv")
    parser.add_argument("--max-pages", type=int, default=80, help="Limit pages per PDF. Default: 80.")
    args = parser.parse_args()

    reports = sorted(Path(args.reports_dir).glob("*_年度报告.pdf"))
    if not reports:
        print("No annual report PDFs found.")
        return 2

    out_path = Path(args.out)
    fieldnames = ["code", "bank_name", "year", "pdf_file"]
    for metric in METRICS:
        fieldnames += [metric, f"{metric}_page", f"{metric}_evidence"]
    fieldnames += ["missing_metric_count"]

    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, path in enumerate(reports, start=1):
            code, name, year = parse_filename(path)
            print(f"[{idx}/{len(reports)}] {path.name}", flush=True)
            extracted = extract_from_pdf(path, max_pages=args.max_pages)
            row = {"code": code, "bank_name": name, "year": year, "pdf_file": str(path)}
            missing = 0
            for metric, val in extracted.items():
                row[metric] = val.value
                row[f"{metric}_page"] = val.page
                row[f"{metric}_evidence"] = val.evidence
                if not val.value:
                    missing += 1
            row["missing_metric_count"] = missing
            writer.writerow(row)

    print(f"\nSaved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
