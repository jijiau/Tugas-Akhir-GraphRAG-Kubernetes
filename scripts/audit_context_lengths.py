"""
Dry-run: call retriever only (no LLM) on all fixtures to measure raw_context lengths.
Results are appended to context_audit.log, then analyzed by analyze_context_lengths.py.

Usage:
    python scripts/audit_context_lengths.py
    python scripts/analyze_context_lengths.py context_audit.log
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
FIXTURES_DIR = ROOT / "tests" / "fixtures"
AUDIT_LOG = ROOT / "context_audit.log"

sys.path.insert(0, str(ROOT))

from src.chatbot.custom_retriever import StatefulK8sRetriever
from src.chatbot.graph_agent import SPEAKER_MAX_CONTEXT_CHARS

INTENT_MAP = {
    "conceptual":      "explain",
    "command":         "command",
    "yaml_gen":        "yaml_gen",
    "relationship":    "explain",
    "troubleshooting": "explain",
    "planning":        "explain",
    "followup":        "followup",
    "realworld":       "explain",
}


def load_fixtures() -> list[dict]:
    fixtures = []
    for type_dir in sorted(FIXTURES_DIR.iterdir()):
        if not type_dir.is_dir():
            continue
        for fpath in sorted(type_dir.glob("*.json")):
            with open(fpath, encoding="utf-8") as f:
                fixtures.append(json.load(f))
    return fixtures


def main():
    retriever = StatefulK8sRetriever()
    fixtures = load_fixtures()
    print(f"Loaded {len(fixtures)} fixtures. Running retriever dry-run...", flush=True)

    AUDIT_LOG.unlink(missing_ok=True)

    for i, fx in enumerate(fixtures, 1):
        question = fx.get("question", "")
        intent_type = INTENT_MAP.get(fx.get("type", ""), "explain")
        extracted_intent = {
            "resource":  fx.get("resource", ""),
            "action":    fx.get("type", "explain"),
            "question":  question,
        }
        try:
            graph_context, _ = retriever.retrieve_context(
                extracted_intent,
                intent_type=intent_type,
                ablation_mode=None,
            )
            length = len(graph_context)
        except Exception as e:
            print(f"  [{i}/{len(fixtures)}] ERROR {fx.get('id')}: {e}", flush=True)
            length = 0

        truncated = length > SPEAKER_MAX_CONTEXT_CHARS
        with open(AUDIT_LOG, "a", encoding="utf-8") as af:
            af.write(
                f"CONTEXT_LEN_AUDIT raw_context_len={length} "
                f"cap={SPEAKER_MAX_CONTEXT_CHARS} truncated={truncated}\n"
            )

        if i % 10 == 0 or i == len(fixtures):
            print(f"  [{i}/{len(fixtures)}] done (last len={length})", flush=True)

    print(f"\nAudit complete. Results in: {AUDIT_LOG}", flush=True)
    print(f"Run: python scripts/analyze_context_lengths.py context_audit.log", flush=True)


if __name__ == "__main__":
    main()
