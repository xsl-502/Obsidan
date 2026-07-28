#!/usr/bin/env python3
"""Clean the initial regression panel and create analysis-ready samples."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import openpyxl


IN = Path("02_数据集/回归面板数据_流动性风险_2014-2023_初版.csv")
OUT_CLEAN_CSV = Path("02_数据集/回归面板数据_流动性风险_2014-2023_清洗版.csv")
OUT_BASELINE_CSV = Path("02_数据集/基准回归样本_流动性风险_2014-2023.csv")
OUT_CLEAN_XLSX = Path("02_数据集/回归面板数据_流动性风险_2014-2023_清洗版.xlsx")
OUT_BASELINE_XLSX = Path("02_数据集/基准回归样本_流动性风险_2014-2023.xlsx")


def as_float(v: str) -> float | None:
    if v is None:
        return None
    v = str(v).strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def fmt(v: float | int | str | None) -> str | float | int | None:
    if isinstance(v, float):
        return round(v, 6)
    return v


def valid_range(field: str, value: float | None) -> float | None:
    if value is None:
        return None
    ranges = {
        "liquidity_ratio": (20, 120),
        "liquidity_risk": (-120, -20),
        "dfi_index": (0, 600),
        "dfi_breadth": (0, 600),
        "dfi_depth": (0, 600),
        "dfi_digitization": (0, 600),
        "total_assets": (100000, 50000000),
        "roa": (0.1, 3.0),
        "roe": (0.1, 30.0),
        "capital_adequacy_ratio": (5, 30),
        "core_tier1_capital_ratio": (3, 25),
        "npl_ratio": (0, 10),
        "cost_income_ratio": (10, 60),
        "provision_coverage": (20, 1000),
    }
    low, high = ranges.get(field, (-float("inf"), float("inf")))
    return value if low <= value <= high else None


def save_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_xlsx(path: Path, rows: list[dict], fields: list[str], sheet_name: str) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(fields)
    for row in rows:
        ws.append([row.get(field) for field in fields])
    for col in ws.columns:
        max_len = min(max(len(str(cell.value)) if cell.value is not None else 0 for cell in col) + 2, 42)
        ws.column_dimensions[col[0].column_letter].width = max_len
    wb.save(path)


def main() -> int:
    rows = list(csv.DictReader(IN.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys()) + ["data_quality_note"]
    numeric_fields = [
        "liquidity_ratio",
        "liquidity_risk",
        "dfi_index",
        "dfi_breadth",
        "dfi_depth",
        "dfi_digitization",
        "dfi_payment",
        "dfi_credit",
        "dfi_investment",
        "dfi_insurance",
        "total_assets",
        "ln_total_assets",
        "roa",
        "roe",
        "capital_adequacy_ratio",
        "core_tier1_capital_ratio",
        "npl_ratio",
        "cost_income_ratio",
        "provision_coverage",
    ]
    cleaned = []
    for row in rows:
        note = []
        out = dict(row)
        for field in numeric_fields:
            if field == "ln_total_assets":
                continue
            old = as_float(row.get(field))
            new = valid_range(field, old)
            if old is not None and new is None:
                note.append(f"{field} abnormal set missing: {old}")
            out[field] = fmt(new)
        total_assets = as_float(out.get("total_assets"))
        out["ln_total_assets"] = fmt(math.log(total_assets)) if total_assets and total_assets > 0 else ""
        out["data_quality_note"] = "; ".join(note)
        cleaned.append(out)

    baseline_needed = [
        "liquidity_risk",
        "dfi_index",
        "capital_adequacy_ratio",
        "npl_ratio",
        "cost_income_ratio",
    ]
    baseline = [row for row in cleaned if all(str(row.get(f) or "").strip() for f in baseline_needed)]

    save_csv(OUT_CLEAN_CSV, cleaned, fields)
    save_csv(OUT_BASELINE_CSV, baseline, fields)
    save_xlsx(OUT_CLEAN_XLSX, cleaned, fields, "clean_panel")
    save_xlsx(OUT_BASELINE_XLSX, baseline, fields, "baseline_sample")

    print("Clean rows:", len(cleaned))
    print("Baseline rows:", len(baseline))
    by_bank = {}
    for row in baseline:
        by_bank[row["bank_name"]] = by_bank.get(row["bank_name"], 0) + 1
    print("Baseline by bank:", by_bank)
    print("Saved:", OUT_CLEAN_CSV)
    print("Saved:", OUT_BASELINE_CSV)
    print("Saved:", OUT_CLEAN_XLSX)
    print("Saved:", OUT_BASELINE_XLSX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
