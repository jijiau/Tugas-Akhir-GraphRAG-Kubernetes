"""
Analyze raw_context length distribution from evaluate.py log output.

Usage:
    python scripts/evaluate.py 2>&1 | python scripts/analyze_context_lengths.py

Or from a saved log file:
    python scripts/analyze_context_lengths.py eval_run.log
"""

import sys
import re
import statistics

def parse_lengths(lines: list[str]) -> list[int]:
    pattern = re.compile(r"CONTEXT_LEN_AUDIT raw_context_len=(\d+)")
    return [int(m.group(1)) for line in lines if (m := pattern.search(line))]


def percentile(data: list[int], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * p / 100
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


def recommend_cap(p95: float, p99: float, current_cap: int) -> str:
    if p99 < current_cap * 0.7:
        return f"P99 ({p99:.0f}) << cap ({current_cap}) — cap is too conservative, could lower to ~{int(p99 * 1.2):,} safely."
    if p95 < current_cap:
        return f"P95 ({p95:.0f}) < cap ({current_cap}) — cap is fine. Only extreme outliers get truncated."
    if p95 < current_cap * 1.5:
        return f"P95 ({p95:.0f}) > cap ({current_cap}) — consider raising to {int(p95 * 1.1):,}–{int(p95 * 1.3):,}."
    return f"P95 ({p95:.0f}) >> cap ({current_cap}) — heavy truncation. Consider raising to {int(p95 * 1.1):,} or fixing retriever over-fetching."


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()

    lengths = parse_lengths(lines)
    if not lengths:
        print("No CONTEXT_LEN_AUDIT lines found. Make sure logging level is INFO.")
        sys.exit(1)

    cap = 12_000
    truncated = sum(1 for l in lengths if l > cap)
    pct_truncated = truncated / len(lengths) * 100

    p50  = percentile(lengths, 50)
    p75  = percentile(lengths, 75)
    p95  = percentile(lengths, 95)
    p99  = percentile(lengths, 99)
    mean = statistics.mean(lengths)
    stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0

    print(f"\n{'='*55}")
    print(f"  Context Length Distribution  (n={len(lengths)} queries)")
    print(f"{'='*55}")
    print(f"  Min     : {min(lengths):>8,}")
    print(f"  Mean    : {mean:>8,.0f}  (±{stdev:,.0f})")
    print(f"  P50     : {p50:>8,.0f}")
    print(f"  P75     : {p75:>8,.0f}")
    print(f"  P95     : {p95:>8,.0f}  ← key signal")
    print(f"  P99     : {p99:>8,.0f}")
    print(f"  Max     : {max(lengths):>8,}")
    print(f"{'='*55}")
    print(f"  Current cap   : {cap:>8,} chars")
    print(f"  Truncated     : {truncated:>8} / {len(lengths)}  ({pct_truncated:.1f}%)")
    print(f"{'='*55}")
    print(f"\n  Recommendation:\n  {recommend_cap(p95, p99, cap)}\n")


if __name__ == "__main__":
    main()
