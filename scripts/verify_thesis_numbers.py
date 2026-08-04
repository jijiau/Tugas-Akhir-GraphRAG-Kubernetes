"""
Fase 8 (Audit E2E) — cross-check numbers reported in the thesis text against
the source CSVs in data/. Not part of the production pipeline; ad hoc
verification script for docs/AUDIT_E2E/phases/FASE_8.md.

Conventions replicated here (see docs/AUDIT_E2E/CHARTER.md and STATUS.md):
- schema_compliance is computed over all fixtures with a non-null
  ansq_schema_compliance value (yaml_gen + realworld YAML-producing
  fixtures), then RBAC fixture 'serviceaccount_pod_binding' is excluded
  (out of KG scope) per tabel31 footnote.
- Faithfulness thesis value is frozen at 0.3055 (n=95), computed when
  ragas_results_graphrag.csv had 95 non-null rows before fixture
  'kubectl_force_delete_pod' (faith=0) was appended later. This script
  reports both the frozen value (recomputed by dropping that one id) and
  the current full-CSV value, and flags them as EXPECTED_DIFFERENT rather
  than MISMATCH.
"""
import pandas as pd
import numpy as np

DATA = "data"

def load(name):
    return pd.read_csv(f"{DATA}/{name}.csv")

RBAC_EXCLUDE = "serviceaccount_pod_binding"
FAITH_FREEZE_EXCLUDE = "kubectl_force_delete_pod"

results = []

def check(label, thesis_val, computed_val, tol=0.0005, note=""):
    if computed_val is None:
        status = "N/A"
        diff = None
    else:
        diff = round(computed_val - thesis_val, 4)
        status = "MATCH" if abs(diff) <= tol else "MISMATCH"
    results.append({
        "label": label, "thesis": thesis_val, "computed": computed_val,
        "diff": diff, "status": status, "note": note
    })

# ---------------------------------------------------------------------------
# Headline: AnsQ / RetQ / Faithfulness / Hop Accuracy per system
# ---------------------------------------------------------------------------
gr = load("eval_results_graphrag_final")
vec = load("eval_results_vector_final")
llm = load("eval_results_llm_final")

check("GraphRAG AnsQ", 0.8031, round(gr['ansq_ansq_score'].mean(), 4))
check("Vector AnsQ", 0.7984, round(vec['ansq_ansq_score'].mean(), 4))
check("LLM AnsQ", 0.7469, round(llm['ansq_ansq_score'].mean(), 4))

check("GraphRAG AnsQ answer_relevance", 0.7698, round(gr['ansq_answer_relevance'].mean(), 4))
check("Vector AnsQ answer_relevance", 0.7503, round(vec['ansq_answer_relevance'].mean(), 4))
check("LLM AnsQ answer_relevance", 0.7175, round(llm['ansq_answer_relevance'].mean(), 4))

check("GraphRAG RetQ Precision", 0.8405, round(gr['retq_precision'].mean(), 4))
check("GraphRAG RetQ Recall", 0.7258, round(gr['retq_recall'].mean(), 4))
check("GraphRAG RetQ F1", 0.7089, round(gr['retq_f1'].mean(), 4))
check("Vector RetQ F1", 0.2437, round(vec['retq_f1'].mean(), 4))
check("LLM RetQ F1", 0.0000, round(llm['retq_f1'].mean(), 4))

# Syntactic validity — yaml_gen only (n=28 total in CSV incl non-yaml_gen rows
# per prior audit; thesis reports yaml_gen-only n=28/30/30 for syntactic)
def syntactic_stats(df):
    s = df['ansq_syntactic_validity'].dropna()
    return round(s.mean(), 4), len(s)
gr_syn, gr_syn_n = syntactic_stats(gr)
vec_syn, vec_syn_n = syntactic_stats(vec)
llm_syn, llm_syn_n = syntactic_stats(llm)
check(f"GraphRAG syntactic_validity (n={gr_syn_n})", 1.0000, gr_syn)
check(f"Vector syntactic_validity (n={vec_syn_n})", 0.9333, vec_syn)
check(f"LLM syntactic_validity (n={llm_syn_n})", 0.8333, llm_syn)

# Schema compliance — all non-null rows MINUS RBAC exclusion
def schema_stats(df, exclude_rbac=True):
    d = df[df['id'] != RBAC_EXCLUDE] if exclude_rbac else df
    s = d['ansq_schema_compliance'].dropna()
    return round(s.mean(), 4), len(s)
gr_sc, gr_sc_n = schema_stats(gr)
vec_sc, vec_sc_n = schema_stats(vec)
llm_sc, llm_sc_n = schema_stats(llm)
check(f"GraphRAG schema_compliance excl-RBAC (n={gr_sc_n})", 0.9259, gr_sc)
check(f"Vector schema_compliance excl-RBAC (n={vec_sc_n})", 0.9655, vec_sc)
check(f"LLM schema_compliance excl-RBAC (n={llm_sc_n})", 0.7931, llm_sc)

# ---------------------------------------------------------------------------
# Faithfulness (frozen n=95 vs current CSV) + Hop Accuracy
# ---------------------------------------------------------------------------
ragas_gr = load("ragas_results_graphrag")
ragas_vec = load("ragas_results_vector")

faith_gr_current = ragas_gr['ragas_faithfulness'].dropna()
faith_gr_frozen = ragas_gr[ragas_gr['id'] != FAITH_FREEZE_EXCLUDE]['ragas_faithfulness'].dropna()
check(f"GraphRAG Faithfulness FROZEN excl-{FAITH_FREEZE_EXCLUDE} (n={len(faith_gr_frozen)})",
      0.3055, round(faith_gr_frozen.mean(), 4), tol=0.005,
      note="ACCEPTED per consistency_trace.md C1 (user decision 2026-06-28): frozen value, diff <0.002 immaterial")
print(f"\n[INFO, not a formal check] GraphRAG Faithfulness on CURRENT full CSV "
      f"(n={len(faith_gr_current)}): {round(faith_gr_current.mean(), 4)} "
      f"— differs from thesis 0.3055 by design (1 fixture appeared after thesis was frozen); "
      f"see consistency_trace.md C1.")

faith_vec = ragas_vec['ragas_faithfulness'].dropna()
check(f"Vector Faithfulness (n={len(faith_vec)})", 0.1675, round(faith_vec.mean(), 4))

hop = gr['reaq_hop_accuracy'].dropna()
check(f"GraphRAG Hop Accuracy all (n={len(hop)})", 0.7562, round(hop.mean(), 4))

# Hop accuracy stratified focused (<=15 edge) / closure (>15 edge).
# NOTE: 'depth_gt' column = len(expected_path) = GT edge count (evaluate.py:372).
# 'gt_depth' is a DIFFERENT column (traversal depth, values 2-3 only) — do not confuse.
hop_df = gr.dropna(subset=['reaq_hop_accuracy'])
focused = hop_df[hop_df['depth_gt'] <= 15]['reaq_hop_accuracy']
closure = hop_df[hop_df['depth_gt'] > 15]['reaq_hop_accuracy']
check(f"GraphRAG Hop Accuracy focused <=15 edge (n={len(focused)})", 0.9086, round(focused.mean(), 4))
check(f"GraphRAG Hop Accuracy closure >15 edge (n={len(closure)})", 0.5791, round(closure.mean(), 4))

# ---------------------------------------------------------------------------
# Depth sensitivity (d=1,3,4,5) — d=2 is the n=102 default baseline itself.
# NOTE (confirmed empirically): ablation/depth sweep CSVs are compared AS-IS
# (n=103, still containing 'pim_trying_to_use_a_container') against the
# pruned n=102 baseline. This asymmetric-N pairing is what actually
# reproduces the thesis numbers (STATUS.md 2026-07-04: "delta/CI tidak
# berubah" after the n=102 pass — i.e. deltas were re-verified stable, not
# recomputed from a re-pruned ablation/depth set). Do NOT prune these CSVs.
# ---------------------------------------------------------------------------
for d, thesis in [(1, dict(retq=0.3666, ansq=0.7815, hop=0.2574)),
                   (4, dict(retq=0.6113, ansq=0.7828, hop=0.9007)),
                   (5, dict(retq=0.5838, ansq=0.7817, hop=0.8760))]:
    df = load(f"eval_results_depth_{d}")
    check(f"Depth d={d} RetQ F1 (n={len(df)})", thesis['retq'], round(df['retq_f1'].mean(), 4))
    check(f"Depth d={d} AnsQ (n={len(df)})", thesis['ansq'], round(df['ansq_ansq_score'].mean(), 4))
    hopd = df['reaq_hop_accuracy'].dropna()
    check(f"Depth d={d} HopAcc (n={len(hopd)})", thesis['hop'], round(hopd.mean(), 4))
# d=3 == ablation A4 (depth fixed at 3)
df3 = load("eval_results_ablation_A4")
check(f"Depth d=3 (A4) RetQ F1 (n={len(df3)})", 0.6593, round(df3['retq_f1'].mean(), 4))
check(f"Depth d=3 (A4) AnsQ (n={len(df3)})", 0.7891, round(df3['ansq_ansq_score'].mean(), 4))
hop3 = df3['reaq_hop_accuracy'].dropna()
check(f"Depth d=3 (A4) HopAcc (n={len(hop3)})", 0.9007, round(hop3.mean(), 4))

# ---------------------------------------------------------------------------
# Ablations A1,A2,A3,A5,A6c,A7 — report delta RetQ / HopAcc vs baseline (18-edge, n=102)
# ---------------------------------------------------------------------------
baseline_retq = gr['retq_f1'].mean()
baseline_hop = gr['reaq_hop_accuracy'].dropna().mean()
baseline_ansq = gr['ansq_ansq_score'].mean()

ablation_thesis = {
    "A1": dict(dretq=-0.309, dhop=None, dansq=None),
    "A2": dict(dretq=-0.656, dhop=-0.700, dansq=None),
    "A3": dict(dretq=-0.123, dhop=-0.147, dansq=None),
    "A5": dict(dretq=-0.057, dhop=0.0037, dansq=None),  # FIXED 2026-07-07 Fase 8: was -0,0037 (sign bug), now +0,0037
    "A6c": dict(dretq=-0.011, dhop=-0.007, dansq=None),
    "A7": dict(dretq=-0.152, dhop=-0.232, dansq=None),
}
for name, thesis in ablation_thesis.items():
    df = load(f"eval_results_ablation_{name}")
    aretq = df['retq_f1'].mean()
    ahop = df['reaq_hop_accuracy'].dropna().mean()
    check(f"Ablation {name} delta RetQ (n={len(df)})", thesis['dretq'], round(aretq - baseline_retq, 4))
    if thesis['dhop'] is not None:
        check(f"Ablation {name} delta HopAcc", thesis['dhop'], round(ahop - baseline_hop, 4))

# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------
st = load("statistical_test_results")
print("\n=== statistical_test_results.csv (raw, for manual cross-check) ===")
print(st.to_string())

# ---------------------------------------------------------------------------
# Boundary condition gains by category + Spearman
# ---------------------------------------------------------------------------
bc = load("boundary_condition_gain")
gains_thesis = {
    "followup": 0.664, "yaml_gen": 0.545, "planning": 0.541, "command": 0.461,
    "troubleshooting": 0.422, "realworld": 0.401, "conceptual": 0.387, "relationship": 0.354,
}
for cat, thesis_val in gains_thesis.items():
    sub = bc[bc['type'] == cat]['retq_gain']
    if len(sub):
        check(f"Boundary RetQ-gain {cat} (n={len(sub)})", thesis_val, round(sub.mean(), 4))
    else:
        check(f"Boundary RetQ-gain {cat}", thesis_val, None, note="category not found in CSV")

from scipy.stats import spearmanr
# boundary_condition.py:366 excludes graph_degree==0 (resource not found in Neo4j lookup)
bc_deg = bc[bc['graph_degree'] > 0]
rho_deg, p_deg = spearmanr(bc_deg['graph_degree'], bc_deg['retq_gain'])
rho_hop, p_hop = spearmanr(bc['hops'], bc['retq_gain'])
check(f"Spearman degree rho (n={len(bc_deg)})", 0.245, round(rho_deg, 4), note=f"p={p_deg:.4f}")
check(f"Spearman hops rho (n={len(bc)})", -0.082, round(rho_hop, 4), note=f"p={p_hop:.4f}")

# ---------------------------------------------------------------------------
# Structural counts
# ---------------------------------------------------------------------------
cat_counts_thesis = {"conceptual": 25, "yaml_gen": 25, "relationship": 18, "followup": 12,
                      "realworld": 9, "planning": 5, "troubleshooting": 5, "command": 3}
cat_counts_actual = gr['type'].value_counts().to_dict()
for cat, n in cat_counts_thesis.items():
    check(f"Fixture category count: {cat}", n, cat_counts_actual.get(cat, 0), tol=0)

print(f"\nTotal fixtures (thesis claims 102): {len(gr)}")

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print("\n" + "=" * 100)
print(f"{'LABEL':<55} {'THESIS':>10} {'COMPUTED':>10} {'DIFF':>8}  STATUS")
print("=" * 100)
mismatches = []
for r in results:
    thesis_s = f"{r['thesis']:.4f}" if isinstance(r['thesis'], float) else str(r['thesis'])
    computed_s = f"{r['computed']:.4f}" if isinstance(r['computed'], float) else str(r['computed'])
    diff_s = f"{r['diff']:.4f}" if isinstance(r['diff'], float) else "-"
    print(f"{r['label']:<55} {thesis_s:>10} {computed_s:>10} {diff_s:>8}  {r['status']}  {r['note']}")
    if r['status'] == "MISMATCH":
        mismatches.append(r)

print("\n" + "=" * 100)
print(f"TOTAL CHECKS: {len(results)} | MISMATCH: {len(mismatches)} | N/A: {sum(1 for r in results if r['status']=='N/A')}")
if mismatches:
    print("\nMISMATCHES REQUIRING REVIEW:")
    for r in mismatches:
        print(f"  - {r['label']}: thesis={r['thesis']} vs computed={r['computed']} (diff={r['diff']}) {r['note']}")
