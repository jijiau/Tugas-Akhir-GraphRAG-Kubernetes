"""
scripts/translate_realworld_gt.py
----------------------------------
One-time script: translate realworld fixture ground_truth.answer from English
to Indonesian so that Token F1 (answer_relevance) can compare apples-to-apples.

Rules:
  - Already Indonesian  → skip (no translation needed)
  - YAML content        → strip HTML only, keep YAML as-is (not translated)
  - English with HTML   → strip HTML tags first, then translate via OpenAI

Usage:
  python scripts/translate_realworld_gt.py [--dry-run]

Writes translated text back into each fixture's ground_truth.answer field
and adds a "answer_lang": "id" marker so the script is idempotent.
"""
import sys
import re
import json
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from src.config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "realworld"
REALWORLD_MIN_SCORE = 2.0

# Common Indonesian words — used to detect if text is already Indonesian
_ID_MARKERS = {
    "adalah", "untuk", "dengan", "yang", "pada", "dari", "dapat",
    "digunakan", "ketika", "dalam", "atau", "dan", "tidak", "jika",
    "sebuah", "akan", "harus", "bisa", "ini", "itu", "anda",
}


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode common HTML entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&quot;", '"').replace("&lt;", "<").replace(
        "&gt;", ">").replace("&amp;", "&").replace("&#39;", "'")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _is_yaml(text: str) -> bool:
    """True if the stripped text looks like a YAML document."""
    stripped = _strip_html(text).strip()
    return stripped.startswith("apiVersion:") or stripped.startswith("kind:")


def _is_indonesian(text: str) -> bool:
    """Heuristic: count Indonesian marker words; if >= 3, treat as Indonesian."""
    words = set(re.sub(r"[^a-zA-Z\s]", " ", text).lower().split())
    return len(words & _ID_MARKERS) >= 3


def _translate(text: str, llm: ChatOpenAI) -> str:
    """
    Translate `text` to Indonesian using OpenAI.
    Returns original text on failure.
    """
    prompt = (
        "Terjemahkan teks teknis berikut dari bahasa Inggris ke bahasa Indonesia. "
        "Pertahankan semua nama teknis Kubernetes (seperti Pod, Deployment, ConfigMap, "
        "kubectl, apiVersion, dll.) apa adanya tanpa diterjemahkan. "
        "Hanya kembalikan terjemahannya saja, tanpa penjelasan tambahan.\n\n"
        f"Teks:\n{text}"
    )
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text


def translate_fixtures(dry_run: bool = False):
    llm = ChatOpenAI(
        model=settings.thinker_model,
        temperature=0.0,
        api_key=settings.openai_api_key,
    )

    all_paths = sorted(FIXTURES_DIR.rglob("*.json"))
    qualified = []
    for p in all_paths:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if ("selection_scores_breakdown" in d
                and d.get("selection_score", 0) >= REALWORLD_MIN_SCORE):
            qualified.append((p, d))

    logger.info(f"Found {len(qualified)} qualified realworld fixtures")

    skipped_id   = 0
    skipped_yaml = 0
    translated   = 0
    already_done = 0

    for path, data in qualified:
        gt = data.get("ground_truth", {})
        answer = gt.get("answer", "")

        # Idempotent: skip if already translated
        if gt.get("answer_lang") == "id":
            already_done += 1
            logger.info(f"  SKIP (already done): {path.stem}")
            continue

        # Case 1: YAML content — strip HTML only
        if _is_yaml(answer):
            clean = _strip_html(answer).strip()
            logger.info(f"  YAML  (strip HTML): {path.stem}")
            if not dry_run:
                data["ground_truth"]["answer"] = clean
                data["ground_truth"]["answer_lang"] = "yaml"
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                encoding="utf-8")
            skipped_yaml += 1
            continue

        # Case 2: Already Indonesian
        clean = _strip_html(answer)
        if _is_indonesian(clean):
            logger.info(f"  SKIP (Indonesian): {path.stem}")
            if not dry_run:
                data["ground_truth"]["answer"] = clean
                data["ground_truth"]["answer_lang"] = "id"
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                                encoding="utf-8")
            skipped_id += 1
            continue

        # Case 3: English — strip HTML then translate
        logger.info(f"  TRANSLATE: {path.stem}")
        translated_text = _translate(clean, llm)
        translated += 1

        if not dry_run:
            data["ground_truth"]["answer"]      = translated_text
            data["ground_truth"]["answer_lang"] = "id"
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                            encoding="utf-8")
        else:
            logger.info(f"    Original : {clean[:100]}...")
            logger.info(f"    Translated: {translated_text[:100]}...")

    print("\n" + "=" * 50)
    print(f"  Total qualified : {len(qualified)}")
    print(f"  Already done    : {already_done}")
    print(f"  Skipped (ID)    : {skipped_id}")
    print(f"  Skipped (YAML)  : {skipped_yaml}")
    print(f"  Translated      : {translated}")
    if dry_run:
        print("  [DRY RUN — no files written]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate realworld GT answers to Indonesian")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview translations without writing files")
    args = parser.parse_args()
    translate_fixtures(dry_run=args.dry_run)
