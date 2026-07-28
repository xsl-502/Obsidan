#!/usr/bin/env python3
"""Download A-share listed bank annual reports from CNINFO.

The script uses CNINFO's public announcement query endpoint and downloads
matched annual report PDFs into the thesis data folder.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
PDF_BASE = "https://static.cninfo.com.cn/"


DEFAULT_BANKS = [
    ("600036", "招商银行", "sh", "gssh0600036"),
    ("000001", "平安银行", "sz", "gssz0000001"),
    ("601166", "兴业银行", "sh", "gssh0601166"),
    ("600000", "浦发银行", "sh", "gssh0600000"),
    ("600016", "民生银行", "sh", "gssh0600016"),
    ("601398", "工商银行", "sh", "gssh0601398"),
    ("601288", "农业银行", "sh", "gssh0601288"),
    ("601988", "中国银行", "sh", "gssh0601988"),
    ("601939", "建设银行", "sh", "gssh0601939"),
    ("601328", "交通银行", "sh", "gssh0601328"),
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
    "Origin": "https://www.cninfo.com.cn",
    "Accept": "application/json, text/plain, */*",
}


@dataclass(frozen=True)
class Bank:
    code: str
    name: str
    market: str
    org_id: str = ""


def request_with_retry(req: urllib.request.Request, retries: int = 3, sleep: float = 1.5) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(sleep * attempt)
    raise RuntimeError(f"request failed after {retries} attempts: {last_error}")


def post_form(url: str, payload: dict[str, str]) -> dict:
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    raw = request_with_retry(req)
    return json.loads(raw.decode("utf-8", errors="replace"))


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    raw = request_with_retry(req)
    return json.loads(raw.decode("utf-8", errors="replace"))


def download_file(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={**HEADERS, "Accept": "application/pdf,*/*"})
    raw = request_with_retry(req)
    path.write_bytes(raw)


def clean_title(title: str) -> str:
    title = re.sub(r"<[^>]+>", "", title)
    return re.sub(r"\s+", "", title)


def title_is_target_annual_report(title: str, year: int) -> bool:
    title = clean_title(title)
    if f"{year}年年度报告摘要" in title or f"{year}年度报告摘要" in title:
        return False
    if (
        f"{year}年年度报告（英文版）" in title
        or f"{year}年度报告（英文版）" in title
        or f"{year}AnnualReport" in title
    ):
        return False
    if "社会责任报告" in title or "环境、社会" in title or "ESG" in title.upper():
        return False
    return f"{year}年年度报告" in title or f"{year}年度报告" in title


def fallback_org_id(bank: Bank) -> str:
    prefix = "gssz" if bank.market == "sz" else "gssh"
    return f"{prefix}0{bank.code}"


def load_org_ids() -> dict[str, str]:
    orgs: dict[str, str] = {}
    for column in ("szse", "sse"):
        url = f"https://www.cninfo.com.cn/new/data/{column}_stock.json"
        try:
            data = get_json(url)
        except Exception:
            continue
        for item in data.get("stockList", []):
            code = str(item.get("code") or "").strip()
            org_id = str(item.get("orgId") or "").strip()
            if code and org_id:
                orgs[code] = org_id
    return orgs


def query_announcements(bank: Bank, year: int, page_num: int, debug: bool = False) -> list[dict]:
    stock_param = f"{bank.code},{bank.org_id or fallback_org_id(bank)}"
    payload = {
        "pageNum": str(page_num),
        "pageSize": "30",
        "column": "szse" if bank.market == "sz" else "sse",
        "tabName": "fulltext",
        "plate": bank.market,
        "stock": stock_param,
        "searchkey": "",
        "secid": "",
        "category": "category_ndbg_szsh;",
        "trade": "",
        "seDate": f"{year}-01-01~{year + 1}-12-31",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "false",
    }
    data = post_form(QUERY_URL, payload)
    if debug:
        total = data.get("totalAnnouncement")
        has_more = data.get("hasMore")
        print(f"  [debug] stock={stock_param} page={page_num} total={total} hasMore={has_more}")
        for ann in (data.get("announcements") or [])[:5]:
            print(f"  [debug] title={clean_title(ann.get('announcementTitle') or '')}")
    return data.get("announcements") or []


def find_annual_report(bank: Bank, year: int, debug: bool = False) -> dict | None:
    candidates: list[dict] = []
    for page_num in range(1, 6):
        anns = query_announcements(bank, year, page_num, debug=debug)
        if not anns:
            break
        for ann in anns:
            title = ann.get("announcementTitle") or ""
            adjunct = ann.get("adjunctUrl") or ""
            if adjunct.lower().endswith(".pdf") and title_is_target_annual_report(title, year):
                candidates.append(ann)
        time.sleep(0.35)
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.get("announcementTime") or 0, reverse=True)
    return candidates[0]


def iter_banks(bank_arg: str | None) -> list[Bank]:
    banks = [Bank(*item) for item in DEFAULT_BANKS]
    if not bank_arg:
        return banks
    wanted = {x.strip() for x in bank_arg.split(",") if x.strip()}
    return [bank for bank in banks if bank.code in wanted or bank.name in wanted]


def main() -> int:
    parser = argparse.ArgumentParser(description="Download CNINFO annual reports for listed banks.")
    parser.add_argument("--start-year", type=int, default=2014)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--banks", help="Comma-separated stock codes or bank names. Default: 10 major banks.")
    parser.add_argument(
        "--out",
        default="02_数据集/上市银行年报PDF",
        help="Output directory, relative to current working directory by default.",
    )
    parser.add_argument("--delay", type=float, default=1.2, help="Seconds to sleep between downloads.")
    parser.add_argument("--debug", action="store_true", help="Print query diagnostics and first returned titles.")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    banks = iter_banks(args.banks)
    if not banks:
        print("No matching banks selected.")
        return 2

    org_ids = load_org_ids()
    if org_ids:
        banks = [
            Bank(bank.code, bank.name, bank.market, org_ids.get(bank.code, bank.org_id or fallback_org_id(bank)))
            for bank in banks
        ]

    log_rows: list[str] = ["code,name,year,status,title,url,file"]
    for bank in banks:
        for year in range(args.start_year, args.end_year + 1):
            file_path = out_dir / f"{bank.code}_{bank.name}_{year}_年度报告.pdf"
            if file_path.exists() and file_path.stat().st_size > 50_000:
                print(f"[skip] {file_path.name}")
                log_rows.append(f'{bank.code},{bank.name},{year},exists,,,{file_path}')
                continue

            print(f"[query] {bank.code} {bank.name} {year}")
            try:
                ann = find_annual_report(bank, year, debug=args.debug)
                if not ann:
                    print(f"[miss] {bank.code} {bank.name} {year}")
                    log_rows.append(f"{bank.code},{bank.name},{year},missing,,,")
                    continue
                title = clean_title(ann.get("announcementTitle") or "")
                pdf_url = urllib.parse.urljoin(PDF_BASE, ann["adjunctUrl"])
                print(f"[download] {title} -> {file_path.name}")
                download_file(pdf_url, file_path)
                log_rows.append(f'"{bank.code}","{bank.name}",{year},"downloaded","{title}","{pdf_url}","{file_path}"')
                time.sleep(args.delay)
            except Exception as exc:
                print(f"[error] {bank.code} {bank.name} {year}: {exc}")
                log_rows.append(f'"{bank.code}","{bank.name}",{year},"error","{exc}",,')
                time.sleep(args.delay)

    log_path = out_dir / "download_log.csv"
    log_path.write_text("\n".join(log_rows) + "\n", encoding="utf-8")
    print(f"\nDone. Log saved to: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
