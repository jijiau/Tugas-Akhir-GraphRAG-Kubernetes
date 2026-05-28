"""Generate Lampiran-C.tex from eval_results_v12.csv"""
import csv
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE, "data", "eval_results_v12.csv")
OUT_PATH = os.path.join(BASE, "docs", "TA-STI-template-1.0", "Lampiran-C.tex")


def fmt(v, d=4):
    if v == "" or v is None:
        return "---"
    try:
        f = float(v)
        if math.isnan(f):
            return "---"
        return f"{f:.{d}f}"
    except Exception:
        return "---"


TYPE_SHORT = {
    "command": "cmd",
    "conceptual": "cncpt",
    "followup": "fllwp",
    "planning": "plan",
    "realworld": "rlwld",
    "relationship": "rel",
    "troubleshooting": "trbl",
    "yaml_gen": "yaml",
}

rows = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

rows.sort(key=lambda r: (r["type"], r["id"]))


def tex_id(s):
    """Truncate and escape for \texttt{}."""
    if len(s) > 30:
        s = s[:28] + ".."
    # underscores are already fine inside \texttt{}
    return s


def make_header_ansq():
    return (
        r"\textbf{ID Fixture} & \textbf{Tipe} & \textbf{Sint.} & "
        r"\textbf{Skema} & \textbf{Relevansi} & \textbf{Faithf.} & \textbf{AnsQ} \\"
    )


def make_header_retq():
    return (
        r"\textbf{ID Fixture} & \textbf{Tipe} & \textbf{P@k} & "
        r"\textbf{R@k} & \textbf{NDCG@k} & \textbf{EdgeCov} & \textbf{RetQ} \\"
    )


def make_header_reaq():
    return (
        r"\textbf{ID Fixture} & \textbf{Tipe} & \textbf{HopAcc} & "
        r"\textbf{Multi-Hop} & \textbf{Scope} & \textbf{Grounding} & \textbf{ReaQ} \\"
    )


def longtable_env(caption, label, header_line, data_lines):
    parts = []
    parts.append(r"\begin{footnotesize}")
    parts.append(r"\begin{longtable}{|p{3.4cm}|c|c|c|c|c|c|}")
    parts.append(r"\caption{" + caption + r"}")
    parts.append(r"\label{" + label + r"} \\")
    parts.append(r"\hline")
    parts.append(header_line)
    parts.append(r"\hline")
    parts.append(r"\endfirsthead")
    parts.append(r"\hline")
    parts.append(header_line)
    parts.append(r"\hline")
    parts.append(r"\endhead")
    parts.append(r"\hline")
    parts.append(r"\endfoot")
    parts.append(r"\hline")
    parts.append(r"\endlastfoot")
    parts.extend(data_lines)
    parts.append(r"\end{longtable}")
    parts.append(r"\end{footnotesize}")
    return parts


# ── Build AnsQ rows ──────────────────────────────────────────────────────
ansq_data = []
for r in rows:
    tid = tex_id(r["id"])
    t = TYPE_SHORT.get(r["type"], r["type"])
    syn = fmt(r["ansq_syntactic_validity"], 2)
    sch = fmt(r["ansq_schema_compliance"], 2)
    rel = fmt(r["ansq_answer_relevance"], 4)
    fai = fmt(r["ansq_faithfulness"], 4)
    ansq = fmt(r["ansq_ansq_score"], 4)
    line = (
        r"\texttt{" + tid + "} & " + t + " & " + syn + " & " + sch
        + " & " + rel + " & " + fai + " & " + r"\textbf{" + ansq + r"} \\"
    )
    ansq_data.append(line)
    ansq_data.append(r"\hline")

# ── Build RetQ rows ──────────────────────────────────────────────────────
retq_data = []
for r in rows:
    tid = tex_id(r["id"])
    t = TYPE_SHORT.get(r["type"], r["type"])
    prec = fmt(r["retq_precision_at_k"], 4)
    rec = fmt(r["retq_recall_at_k"], 4)
    ndcg = fmt(r["retq_ndcg_at_k"], 4)
    ecov = fmt(r["retq_edge_coverage"], 4)
    retq = fmt(r["retq_retq_score"], 4)
    line = (
        r"\texttt{" + tid + "} & " + t + " & " + prec + " & " + rec
        + " & " + ndcg + " & " + ecov + " & " + r"\textbf{" + retq + r"} \\"
    )
    retq_data.append(line)
    retq_data.append(r"\hline")

# ── Build ReaQ rows ──────────────────────────────────────────────────────
reaq_data = []
for r in rows:
    tid = tex_id(r["id"])
    t = TYPE_SHORT.get(r["type"], r["type"])
    hacc = fmt(r["reaq_hop_accuracy"], 4)
    mhop = fmt(r["reaq_multi_hop_success"], 4)
    scope = fmt(r["reaq_scope_accuracy"], 4)
    gnd = fmt(r["reaq_grounding_score"], 4)
    reaq = fmt(r["reaq_reaq_score"], 4)
    line = (
        r"\texttt{" + tid + "} & " + t + " & " + hacc + " & " + mhop
        + " & " + scope + " & " + gnd + " & " + r"\textbf{" + reaq + r"} \\"
    )
    reaq_data.append(line)
    reaq_data.append(r"\hline")

# ── Assemble document ────────────────────────────────────────────────────
out = []
out.append(r"\cleardoublepage")
out.append(r"\chapter{HASIL EVALUASI KUANTITATIF}")
out.append("")
out.append(
    r"Lampiran ini menyajikan nilai metrik lengkap untuk seluruh 97 \textit{fixture} "
    r"evaluasi pada sistem \textit{GraphRAG} Kubernetes. "
    r"Tabel~\ref{tbl:ansq-full} menampilkan metrik \textit{Answer Quality} (AnsQ); "
    r"Tabel~\ref{tbl:retq-full} menampilkan metrik \textit{Retrieval Quality} (RetQ); "
    r"dan Tabel~\ref{tbl:reaq-full} menampilkan metrik \textit{Reasoning Quality} (ReaQ). "
    r"Kolom \textbf{Sint.}\ dan \textbf{Skema} pada Tabel~\ref{tbl:ansq-full} "
    r"hanya relevan untuk \textit{fixture} bertipe \texttt{yaml}; "
    r"nilai ``---'' menunjukkan bahwa metrik tersebut tidak diukur untuk tipe \textit{fixture} yang bersangkutan."
)
out.append("")
out.append(
    r"Singkatan tipe \textit{fixture}: "
    r"\textit{cmd} = perintah, "
    r"\textit{cncpt} = konseptual, "
    r"\textit{fllwp} = lanjutan, "
    r"\textit{plan} = perencanaan, "
    r"\textit{rlwld} = skenario nyata, "
    r"\textit{rel} = relasional, "
    r"\textit{trbl} = \textit{troubleshooting}, "
    r"\textit{yaml} = generasi YAML."
)
out.append("")
out.append(r"% ─────────────────────────────────────────────────────────────────────────────")
out.append(r"\section{Metrik \textit{Answer Quality} (AnsQ)}")
out.append(r"% ─────────────────────────────────────────────────────────────────────────────")
out.append("")
out.extend(longtable_env(
    caption="Nilai Metrik AnsQ per Fixture (97 Fixture)",
    label="tbl:ansq-full",
    header_line=make_header_ansq(),
    data_lines=ansq_data,
))
out.append("")
out.append(r"% ─────────────────────────────────────────────────────────────────────────────")
out.append(r"\section{Metrik \textit{Retrieval Quality} (RetQ)}")
out.append(r"% ─────────────────────────────────────────────────────────────────────────────")
out.append("")
out.extend(longtable_env(
    caption="Nilai Metrik RetQ per Fixture (97 Fixture)",
    label="tbl:retq-full",
    header_line=make_header_retq(),
    data_lines=retq_data,
))
out.append("")
out.append(r"% ─────────────────────────────────────────────────────────────────────────────")
out.append(r"\section{Metrik \textit{Reasoning Quality} (ReaQ)}")
out.append(r"% ─────────────────────────────────────────────────────────────────────────────")
out.append("")
out.extend(longtable_env(
    caption="Nilai Metrik ReaQ per Fixture (97 Fixture)",
    label="tbl:reaq-full",
    header_line=make_header_reaq(),
    data_lines=reaq_data,
))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"Written {len(out)} lines to {OUT_PATH}")
