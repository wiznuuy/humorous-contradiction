#!/usr/bin/env python3
"""Regenerate title_options.csv -- the four title options per comic, in English
and in the Korean wording shown to Korean-language participants.

The option text belongs to the YESBUT benchmark, which is released under
CC BY-NC-ND 4.0. A translation is an adaptation, so neither the English options
nor their Korean translations are redistributed with this dataset. This script
rebuilds the table from the upstream annotation file instead.

    English options  : copied verbatim from the upstream `title_mcq` field.
    Reference answer : copied verbatim from the upstream `title_mcq_answer` field.
    Korean options   : regenerated with the API call reproduced below.

Output columns (join key for `title_choice` in both response tables):

    image_id, option_letter, option_en, option_ko, is_reference_answer

Translation settings used in the study, reproduced exactly by this script:

    provider      Anthropic Messages API
    model         claude-haiku-4-5-20251001
    max_tokens    4096
    temperature   not set in the request (provider default)
    batch size    10 images per request
    prompt        see PROMPT below, verbatim and in Korean as it was issued

No manual post-editing was applied to the generated Korean option text: the
strings shown to participants are the model output as returned. Because the
request does not pin a temperature and commercial model aliases change over
time, a rerun will produce similar but not identical Korean wording. Use
--check against a saved copy if you need to confirm how far a rerun has drifted.

Usage:
    # 1. fetch the upstream annotation file (see README > Sources and attribution)
    curl -o Yesbut_data.json https://raw.githubusercontent.com/Tuo-Liang/YESBUT/90186c127419110eb80fdce3f7336738da545303/data/Yesbut_data.json

    # 2. English options only, no API key needed
    python build_title_translations.py --upstream Yesbut_data.json --out title_options.csv --english-only

    # 3. with Korean options
    ANTHROPIC_API_KEY=... python build_title_translations.py --upstream Yesbut_data.json --out title_options.csv
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4096
BATCH_SIZE = 10

PROMPT = """다음은 웹툰/만화 이미지에 대한 영어 제목 4지선다 문제들입니다.
각 항목을 한국어로 번역해주세요.

번역 규칙:
- A. B. C. D. 기호는 그대로 유지하세요
- 의미와 뉘앙스를 최대한 보존하세요
- 자연스러운 한국어로 번역하세요
- 고유명사(브랜드, 제품명 등)는 영어 또는 한국어 표기 중 자연스러운 것으로 하세요
- 각 항목은 [숫자] 형식으로 구분해서 출력하세요
- 번역 외 다른 설명은 출력하지 마세요

{numbered}"""


def split_options(blob):
    """Upstream stores the four options as one newline-joined string."""
    out = {}
    for line in blob.split("\n"):
        m = re.match(r"\s*([A-D])\.\s*(.+?)\s*$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def translate_batch(client, items):
    numbered = "\n\n".join(f"[{i + 1}]\n{it['title_mcq']}" for i, it in enumerate(items))
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": PROMPT.format(numbered=numbered)}],
    )
    raw = resp.content[0].text.strip()

    # Responses are segmented by [1], [2], ... markers on their own line.
    out, current = [], []
    for line in raw.split("\n"):
        s = line.strip()
        if s.startswith("[") and s.endswith("]") and s[1:-1].isdigit():
            if current:
                out.append("\n".join(current).strip())
                current = []
        elif s:
            current.append(s)
    if current:
        out.append("\n".join(current).strip())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", type=Path, required=True,
                    help="upstream YesBut_data.json (commit 90186c1)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--stimuli", type=Path, default=HERE.parent / "stimuli_images.csv",
                    help="restrict output to these images (default: the 270 analyzed)")
    ap.add_argument("--english-only", action="store_true",
                    help="skip the Korean translation and the API call")
    ap.add_argument("--check", type=Path,
                    help="compare the regenerated Korean text against a saved CSV")
    args = ap.parse_args()

    upstream = {d["image_file"]: d for d in json.loads(args.upstream.read_text(encoding="utf-8"))}
    keep = [r["image_id"] + ".jpg" for r in csv.DictReader(args.stimuli.open(encoding="utf-8"))]
    items = [upstream[f] | {"image_file": f} for f in keep if f in upstream]
    if len(items) != len(keep):
        print(f"warning: {len(keep) - len(items)} images not found upstream", file=sys.stderr)

    ko_blobs = {}
    if not args.english_only:
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            sys.exit("set ANTHROPIC_API_KEY, or pass --english-only")
        client = anthropic.Anthropic(api_key=key)
        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i:i + BATCH_SIZE]
            print(f"batch {i // BATCH_SIZE + 1}/{-(-len(items) // BATCH_SIZE)}", flush=True)
            tr = translate_batch(client, batch)
            if len(tr) != len(batch):
                print(f"  count mismatch ({len(tr)} vs {len(batch)}) - batch skipped",
                      file=sys.stderr)
                continue
            for it, ko in zip(batch, tr):
                ko_blobs[it["image_file"]] = ko
            time.sleep(0.5)  # rate limiting

    rows, skipped = [], []
    for it in items:
        f = it["image_file"]
        en = split_options(it["title_mcq"])
        ko = split_options(ko_blobs.get(f, "")) if not args.english_only else {}
        if sorted(en) != list("ABCD") or (not args.english_only and sorted(ko) != list("ABCD")):
            skipped.append(f)
            continue
        for letter in "ABCD":
            rows.append({
                "image_id": f[:-4],
                "option_letter": letter,
                "option_en": en[letter],
                "option_ko": ko.get(letter, ""),
                "is_reference_answer": str(it["title_mcq_answer"] == letter).lower(),
            })

    with args.out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["image_id", "option_letter", "option_en",
                                           "option_ko", "is_reference_answer"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows ({len(rows) // 4} images) to {args.out}")
    if skipped:
        print(f"skipped {len(skipped)} unparseable: {skipped[:5]}", file=sys.stderr)

    if args.check and args.check.exists():
        saved = {(r["image_id"], r["option_letter"]): r["option_ko"]
                 for r in csv.DictReader(args.check.open(encoding="utf-8"))}
        same = sum(1 for r in rows if saved.get((r["image_id"], r["option_letter"])) == r["option_ko"])
        print(f"check: {same}/{len(rows)} Korean options identical to {args.check}")


if __name__ == "__main__":
    main()
