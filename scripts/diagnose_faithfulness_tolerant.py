"""
diagnose_faithfulness_tolerant.py
==================================
Sensitivity-analysis script (FUTURE WORK, bukan bagian dari metrik resmi Bab VI).

DESAIN 2-TAHAP (revisi setelah gate-check pilot v1 gagal -- lihat catatan di bawah):
  Tahap 1 (SUDAH ADA, tidak diulang): dekomposisi jawaban -> klaim atomik, tersimpan
    persis di data/faithfulness_decomposition_raw.jsonl (hasil run resmi asli).
  Tahap 2 (script ini): muat klaim yang SAMA PERSIS dari file itu, lalu MINTA JUDGE
    MENILAI ULANG SAJA (tanpa dekomposisi ulang) dengan aturan toleran terhadap
    perbedaan modalitas kalimat (deklaratif vs prosedural/imperatif).

Kenapa didesain ulang: versi v1 (satu panggilan yang dekomposisi+menilai sekaligus)
diuji pilot 15 fixture dan GAGAL gate-check -- 4/15 fixture (27%) punya jumlah klaim
yang beda jauh dari baseline (contoh ekstrem: add_liveness_probe 18->1 klaim), karena
instruksi toleransi ikut mengubah CARA LLM memecah jawaban, bukan cuma cara menilai.
Itu mencemari perbandingan berpasangan (membandingkan himpunan klaim berbeda, bukan
menilai ulang klaim yang sama). Desain 2-tahap ini menghilangkan sumber pencemaran
itu: klaim dikunci identik dengan baseline (n_claims dijamin sama secara konstruksi),
jadi delta faithfulness murni berasal dari perbedaan ATURAN PENILAIAN, bukan
perbedaan APA YANG DINILAI.

Terisolasi penuh dari pipeline resmi:
  - TIDAK menimpa data/faithfulness_decomposition*  (hanya DIBACA sebagai sumber klaim).
  - TIDAK menyentuh data/eval_results_*.csv atau data/ragas_results_*.csv.
  - Semua output baru: data/faithfulness_tolerant.csv / _raw.jsonl / _summary.json

Perbandingan yang SAH untuk hasil script ini adalah terhadap faithfulness_micro=0.3154
dari faithfulness_decomposition_summary.json (SAMA judge=gpt-4o, SAMA klaim persis,
hanya aturan penilaian yang beda) -- BUKAN terhadap 0.3055 (itu pipeline RAGAS
gpt-4o-mini yang berbeda pula judge-nya).

Ceiling aritmatik = (258 supported + 81 modality) / 818 = 0.4144.
Hasil di luar rentang [0.3154, 0.4144] wajib diselidiki sebelum dipakai (lihat --help).

Usage:
  python scripts/diagnose_faithfulness_tolerant.py --pilot            # 15 fixture stratifikasi
  python scripts/diagnose_faithfulness_tolerant.py --resume           # lanjutkan/full run aman
  python scripts/diagnose_faithfulness_tolerant.py --limit 5          # dry-run kecil
  python scripts/diagnose_faithfulness_tolerant.py --overwrite        # HANYA jika sengaja mulai ulang

Cost estimate (full run, 102 fixture): ~$1-1.5 (prompt lebih pendek dari v1 karena
tidak perlu mengirim ulang jawaban lengkap), ~17-20 menit (throttle 10s/panggilan
karena kuota akun 30.000 TPM -- lihat rencana untuk detail).
"""
import sys, os, json, csv, argparse, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(str(Path(__file__).parent.parent / ".env"))

# -- Reuse dari script asli (BUKAN menyalin ulang -- demi konsistensi konteks) --
sys.path.insert(0, str(Path(__file__).parent))
from diagnose_faithfulness import (
    _graphrag_ctx_to_texts,
    _ctx_kind,
    load_all_cases,
    SPEAKER_MAX_CONTEXT_CHARS,
)

BASELINE_RAW_PATH = Path(__file__).parent.parent / "data" / "faithfulness_decomposition_raw.jsonl"


def load_baseline_claims() -> dict:
    """Muat klaim yang SUDAH terdekomposisi dari run resmi asli (read-only).
    Mengembalikan {fixture_id: [claim_text, ...]} dengan urutan asli dipertahankan."""
    claims_by_id = {}
    with open(BASELINE_RAW_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            fid = obj.get("id")
            claims = [c.get("claim", "") for c in obj.get("claims", [])]
            if fid:
                claims_by_id[fid] = claims
    return claims_by_id

DATA_DIR = Path(__file__).parent.parent / "data"

# --- Output paths: SEMUA BARU, tidak pernah menimpa file resmi ---
RAW_CACHE_PATH = DATA_DIR / "faithfulness_tolerant_raw.jsonl"
CSV_PATH       = DATA_DIR / "faithfulness_tolerant.csv"
SUMMARY_PATH   = DATA_DIR / "faithfulness_tolerant_summary.json"

KNOWN_CLASSES = {"supported", "modality_equivalent", "partial", "absent"}

# Fixture pilot stratifikasi (dipilih dari faithfulness_decomposition.csv,
# 10 fixture dengan modality>0 + 5 kontrol modality=0, lihat scratchpad
# faithfulness_pilot_ids.json untuk daftar sumber)
PILOT_MODALITY_GROUP = [
    "pod_disruption_budget_concept",
    "precodespec_containers_image_nginx_imagepul",
    "limitrange_yaml",
    "deployment_pod_relation",
    "service_nodeport",
    "add_pvc_to_statefulset",
    "add_resource_limits",
    "plan_redis_persistent",
    "pod_init_container_yaml",
    "limit_range_concept",
]
PILOT_CONTROL_GROUP = [
    "add_readiness_probe",
    "add_liveness_probe",
    "service_types",
    "scale_existing_deployment",
    "update_image_version",
]
PILOT_IDS = PILOT_MODALITY_GROUP + PILOT_CONTROL_GROUP

CSV_FIELDNAMES = [
    "id", "type", "ctx_kind", "multi_hop",
    "n_claims", "supported", "modality_equivalent", "partial", "absent", "other",
    "faithfulness_tolerant", "faithfulness_strict_equiv",
    "pilot_group",
]


# -- Judge prompt: RECLASSIFY-ONLY, klaim sudah tetap (bukan dekomposisi ulang) --
#
# v3 (revisi setelah v2 pilot menunjukkan 50% klaim kategori "modality" baseline
# malah dinilai LEBIH KETAT jadi "absent" -- root cause diduga: v2 menghapus teks
# ANSWER lengkap dari prompt, sehingga klaim lepas tanpa konteks jawaban di
# sekitarnya jadi ambigu dan judge default ke opsi paling ketat sesuai guardrail
# "when in doubt, classify stricter". v3 mengembalikan ANSWER sebagai konteks
# TAMBAHAN -- klaim tetap dikunci sama seperti v2 (tidak didekomposisi ulang),
# cuma judge sekarang bisa melihat kalimat aslinya muncul di jawaban mana.
#
# Beda vs v1 (dihapus setelah gagal gate-check dekomposisi): tidak ada langkah
# "decompose the answer" -- klaim diberikan sebagai daftar tetap bernomor, dan
# judge DIPERINTAHKAN EKSPLISIT untuk tidak memecah/menggabung/menambah/mengurangi.
RECLASSIFY_PROMPT = """You are auditing a RAG system's faithfulness. You are given a QUESTION, \
the system's full ANSWER (for context only), the RETRIEVED CONTEXT (Kubernetes schema node \
descriptions), and a FIXED LIST of {n} pre-extracted atomic claims from that ANSWER.

Your ONLY task is to classify each claim as-is. Do NOT decompose, split, merge, add, or \
remove claims. Return EXACTLY {n} classifications, in the SAME order as the input list. \
The ANSWER is provided only so you can see the original phrasing/context each claim came \
from -- do not classify the ANSWER itself, only the {n} listed claims.

For each claim, decide if it can be inferred from the RETRIEVED CONTEXT, using a
MODALITY-TOLERANT reading: if the context declaratively describes an entity/field/relation
(e.g. "X is a description of Y") and the claim restates the SAME fact as a procedure, step,
instruction, or imperative (e.g. "specify X under Y", "you need to set X"), treat this as
SUPPORTED -- the claim and the context assert the same underlying fact, just in a different
grammatical mood (declarative vs. procedural/imperative). Do NOT require verbatim wording.

IMPORTANT GUARDRAIL -- this tolerance applies ONLY to sentence form, never to substance:
  - If the claim mentions an entity, field, default value, or relationship that is
    genuinely absent from the context (regardless of phrasing), it is still UNSUPPORTED.
  - Do not extend tolerance to claims that add NEW factual content not present in the
    context, even if related in topic.
  - When in doubt whether a mismatch is "just phrasing" vs "an added fact", classify it
    as the stricter option (absent/partial), not modality_equivalent.

Classify each claim into exactly one of:
  - "supported": claim is directly and literally supported by the context (same content,
    same grammatical mood, or a trivial restatement).
  - "modality_equivalent": claim asserts the SAME fact as the context, but the context
    is declarative while the claim is procedural/imperative (or vice versa) -- content
    matches, only sentence mood differs.
  - "partial": claim is partially supported -- some sub-parts trace to the context, other
    sub-parts add facts not present in the context.
  - "absent": the entity/fact in the claim is genuinely NOT present anywhere in the
    context, under any phrasing.

Return STRICT JSON with EXACTLY {n} entries, SAME order as input, each claim text copied
verbatim from the input list:
{{"claims": [{{"claim": "...", "reason_class": "supported"|"modality_equivalent"|"partial"|"absent"}}]}}

QUESTION:
{question}

FULL ANSWER (context only -- do not classify this, only the {n} claims below):
{answer}

RETRIEVED CONTEXT:
{context}

CLAIMS TO CLASSIFY (exactly {n}, in this order -- do not add/remove/split/merge):
{numbered_claims}
"""


def _call_with_retry_throttled(client, prompt, delay_s, max_retries=4, backoff=8.0):
    """Sama seperti _call_with_retry asli, tapi dengan backoff lebih panjang
    (kuota akun 30k TPM jauh lebih kecil dari asumsi script asli)."""
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content), None
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate" in msg.lower():
                wait = backoff * (2 ** attempt)
                print(f"    [rate-limit] menunggu {wait:.0f}s...")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                print(f"    [retry {attempt+1}/{max_retries}] {e}")
                time.sleep(3)
            else:
                return None, str(e)
    return None, "max_retries_exceeded"


def reclassify_tolerant(case: dict, claim_texts: list, client, delay_s: float):
    """Nilai ulang daftar klaim TETAP (tidak dekomposisi ulang). Mengembalikan
    (result, err). err='claim_count_mismatch' kalau judge tidak patuh instruksi
    jumlah/urutan klaim -- ini divalidasi ketat, bukan diterima diam-diam."""
    if not claim_texts:
        return {"claims": []}, None

    contexts = _graphrag_ctx_to_texts(case.get("graph_context", ""))
    context_str = "\n\n".join(contexts)
    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(claim_texts))
    prompt = RECLASSIFY_PROMPT.format(
        n=len(claim_texts),
        question=case["question"],
        answer=case.get("answer_full", ""),
        context=context_str[:SPEAKER_MAX_CONTEXT_CHARS],
        numbered_claims=numbered,
    )
    result, err = _call_with_retry_throttled(client, prompt, delay_s)
    if err is not None:
        return None, err

    returned = result.get("claims", [])
    if len(returned) != len(claim_texts):
        return None, f"claim_count_mismatch: diminta {len(claim_texts)}, diterima {len(returned)}"

    return result, None


def build_row_tolerant(case: dict, result: dict, pilot_group: str = "") -> dict:
    """Berbeda dari build_row() asli: TIDAK menimpa reason_class dengan
    'supported=true' flag (script asli tidak punya flag terpisah lagi di sini --
    kita hitung murni dari reason_class supaya modality_equivalent tetap
    kelihatan sebagai kategori sendiri, bukan menyamar jadi 'supported')."""
    claims = result.get("claims", []) if result else []
    counts = {"supported": 0, "modality_equivalent": 0, "partial": 0, "absent": 0, "other": 0}
    for c in claims:
        rc = c.get("reason_class", "supported")
        if rc not in KNOWN_CLASSES:
            rc = "other"
        counts[rc] += 1

    n = len(claims) or 1
    faithfulness_tolerant = round((counts["supported"] + counts["modality_equivalent"]) / n, 4)
    faithfulness_strict_equiv = round(counts["supported"] / n, 4)

    ctx_str = case.get("graph_context", "")
    return {
        "id": case["id"],
        "type": case.get("type", ""),
        "ctx_kind": _ctx_kind(ctx_str),
        "multi_hop": case.get("multi_hop", False),
        "n_claims": len(claims),
        "supported": counts["supported"],
        "modality_equivalent": counts["modality_equivalent"],
        "partial": counts["partial"],
        "absent": counts["absent"],
        "other": counts["other"],
        "faithfulness_tolerant": faithfulness_tolerant,
        "faithfulness_strict_equiv": faithfulness_strict_equiv,
        "pilot_group": pilot_group,
    }


def load_cached_ids() -> set:
    done = set()
    if not RAW_CACHE_PATH.exists():
        return done
    with open(RAW_CACHE_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                if obj.get("id"):
                    done.add(obj["id"])
            except json.JSONDecodeError:
                pass
    return done


def _agg(rows: list) -> dict:
    totals = {"n_fixtures": 0, "n_claims": 0,
              "supported": 0, "modality_equivalent": 0, "partial": 0, "absent": 0, "other": 0}
    for r in rows:
        totals["n_fixtures"] += 1
        totals["n_claims"] += r["n_claims"]
        for k in ("supported", "modality_equivalent", "partial", "absent", "other"):
            totals[k] += r[k]
    n = totals["n_claims"] or 1
    return {
        **totals,
        "faithfulness_tolerant_micro": round((totals["supported"] + totals["modality_equivalent"]) / n, 4),
        "faithfulness_strict_equiv_micro": round(totals["supported"] / n, 4),
    }


def main():
    parser = argparse.ArgumentParser(description="Sensitivity analysis: modality-tolerant faithfulness judge (FUTURE WORK)")
    parser.add_argument("--pilot", action="store_true", help="Jalankan 15 fixture stratifikasi (10 modality-group + 5 control-group) saja.")
    parser.add_argument("--limit", type=int, default=None, help="Proses N baris pertama saja (dry-run).")
    parser.add_argument("--resume", action="store_true", help="Lewati fixture yang sudah ada di cache (default aman).")
    parser.add_argument("--overwrite", action="store_true", help="Timpa cache dari awal -- HARUS eksplisit, tidak ada default diam-diam.")
    parser.add_argument("--delay", type=float, default=10.0, help="Jeda detik antar panggilan API (default 10, sesuai kuota 30k TPM).")
    parser.add_argument("--allow-partial", action="store_true", help="Izinkan menulis summary walau ada fixture gagal.")
    args = parser.parse_args()

    if not args.overwrite and not args.resume:
        # Default aman: kalau cache sudah ada dan user tidak eksplisit minta overwrite,
        # perlakukan sebagai resume otomatis supaya tidak pernah diam-diam menimpa.
        args.resume = RAW_CACHE_PATH.exists()

    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    baseline_claims = load_baseline_claims()

    if args.pilot:
        all_cases = {c["id"]: c for c in load_all_cases()}
        cases = []
        for fid in PILOT_IDS:
            if fid in all_cases:
                cases.append(all_cases[fid])
            else:
                print(f"  [WARN] pilot id tidak ditemukan di eval_cases_graphrag.jsonl: {fid}")
        group_of = {fid: "modality_group" for fid in PILOT_MODALITY_GROUP}
        group_of.update({fid: "control_group" for fid in PILOT_CONTROL_GROUP})
    else:
        cases = load_all_cases(limit=args.limit)
        group_of = {}

    cached_ids = load_cached_ids() if args.resume else set()
    n_total = len(cases)
    n_skip = sum(1 for c in cases if c["id"] in cached_ids)
    n_run = n_total - n_skip

    mode_tag = "PILOT" if args.pilot else (f"LIMIT={args.limit}" if args.limit else "FULL")
    print(f"\n{'='*70}")
    print(f"  diagnose_faithfulness_tolerant.py  [{mode_tag}]")
    print(f"  fixtures: {n_total}  |  cached/skip: {n_skip}  |  to run: {n_run}  |  delay: {args.delay}s")
    if n_run:
        est_min = n_run * args.delay / 60
        print(f"  Estimasi waktu: ~{est_min:.1f} menit  |  biaya: ~${n_run * 0.02:.2f}")
    print(f"{'='*70}\n")

    raw_f = open(RAW_CACHE_PATH, "a", encoding="utf-8") if args.resume or not args.overwrite else \
            open(RAW_CACHE_PATH, "w", encoding="utf-8")
    if args.overwrite:
        print("  [OVERWRITE] cache ditimpa dari awal (diminta eksplisit via --overwrite)\n")

    all_rows = []
    failed_ids = []

    # Muat ulang baris yang sudah di-cache (untuk resume)
    if cached_ids:
        full_cases = {c["id"]: c for c in load_all_cases()}
        with open(RAW_CACHE_PATH, encoding="utf-8") as cf:
            cached_lines = [json.loads(l) for l in cf if l.strip()]
        for obj in cached_lines:
            fid = obj.get("id")
            case = full_cases.get(fid)
            if case and fid in [c["id"] for c in cases]:
                all_rows.append(build_row_tolerant(case, obj, group_of.get(fid, "")))

    try:
        for i, case in enumerate(cases):
            fid = case["id"]
            if fid in cached_ids:
                print(f"  [{i+1:>3}/{n_total}] SKIP  {fid}")
                continue

            claim_texts = baseline_claims.get(fid)
            if claim_texts is None:
                print(f"  [{i+1:>3}/{n_total}] SKIP  {fid}  -- tidak ada di faithfulness_decomposition_raw.jsonl (baseline)")
                failed_ids.append(fid)
                continue

            print(f"  [{i+1:>3}/{n_total}] reclassify gpt-4o ({len(claim_texts)} klaim tetap) ... {fid}", end="", flush=True)
            result, err = reclassify_tolerant(case, claim_texts, client, args.delay)

            if err is not None or result is None:
                print(f"  [GAGAL] {err}")
                failed_ids.append(fid)
                if i < n_total - 1:
                    time.sleep(args.delay)
                continue

            row = build_row_tolerant(case, result, group_of.get(fid, ""))
            all_rows.append(row)
            print(f"  -> {row['n_claims']} klaim  sup={row['supported']} "
                  f"mod_eq={row['modality_equivalent']} abs={row['absent']} par={row['partial']}"
                  + (f" oth={row['other']}" if row['other'] else "")
                  + f"  faith_tol={row['faithfulness_tolerant']:.3f}")

            cache_entry = {"id": fid, "claims": result.get("claims", [])}
            raw_f.write(json.dumps(cache_entry, ensure_ascii=False) + "\n")
            raw_f.flush()

            if i < n_total - 1:
                time.sleep(args.delay)
    finally:
        raw_f.close()

    print(f"\n{'='*70}")
    if failed_ids:
        print(f"  [PERINGATAN] {len(failed_ids)} fixture GAGAL total: {failed_ids}")
        if not args.allow_partial:
            print("  Summary TIDAK ditulis (perbandingan berpasangan butuh himpunan lengkap).")
            print("  Jalankan ulang dengan --resume untuk mencoba fixture yang gagal,")
            print("  atau --allow-partial untuk tetap menulis summary parsial.")
            print(f"{'='*70}\n")
            return
    else:
        print("  Semua fixture berhasil, tidak ada yang gagal.")

    if not all_rows:
        print("\nTidak ada hasil untuk diagregasi.")
        return

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        for row in all_rows:
            w.writerow({k: row.get(k, "") for k in CSV_FIELDNAMES})
    print(f"  Disimpan CSV per-fixture -> {CSV_PATH.name}  ({len(all_rows)} baris)")

    agg = _agg(all_rows)
    modality_rows = [r for r in all_rows if r["pilot_group"] == "modality_group"]
    control_rows = [r for r in all_rows if r["pilot_group"] == "control_group"]
    summary = {
        "whole": agg,
        "n_failed": len(failed_ids),
        "failed_ids": failed_ids,
    }
    if modality_rows:
        summary["pilot_modality_group"] = _agg(modality_rows)
    if control_rows:
        summary["pilot_control_group"] = _agg(control_rows)

    print(f"\n  AGGREGATE (whole): n_fixtures={agg['n_fixtures']} n_claims={agg['n_claims']}")
    print(f"    faithfulness_tolerant_micro     = {agg['faithfulness_tolerant_micro']}")
    print(f"    faithfulness_strict_equiv_micro = {agg['faithfulness_strict_equiv_micro']}")
    if modality_rows:
        print(f"\n  Pilot MODALITY group (n={len(modality_rows)}): faithfulness_tolerant_micro = {_agg(modality_rows)['faithfulness_tolerant_micro']}")
    if control_rows:
        print(f"  Pilot CONTROL group  (n={len(control_rows)}): faithfulness_tolerant_micro = {_agg(control_rows)['faithfulness_tolerant_micro']}")

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Disimpan summary -> {SUMMARY_PATH.name}")
    print(f"  Cache -> {RAW_CACHE_PATH.name}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
