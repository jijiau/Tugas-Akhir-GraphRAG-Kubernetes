"""Generate Lampiran-C.tex from eval_results_graphrag_final.csv (102 fixture).

Skema tabel diturunkan ke metrik yang benar-benar tersedia untuk dataset
102-fixture final (lihat docs/AUDIT_E2E untuk konteks rekurasi 97->102).
Faithfulness dan Hop-Accuracy (corrected) diambil dari ragas_results_graphrag.csv
via join per-id, konsisten dengan agregat Bab VI (tabel29c).
"""
import csv
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE, "data", "eval_results_graphrag_final.csv")
RAGAS_PATH = os.path.join(BASE, "data", "ragas_results_graphrag.csv")
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
        return str(v) if v else "---"


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

ragas_by_id = {}
with open(RAGAS_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ragas_by_id[row["id"]] = row

for row in rows:
    ragas_row = ragas_by_id.get(row["id"], {})
    row["ragas_faithfulness"] = ragas_row.get("ragas_faithfulness", "")
    row["reaq_hop_accuracy_corrected"] = ragas_row.get("reaq_hop_accuracy_corrected", "")

rows.sort(key=lambda r: (r["type"], r["id"]))

N_FIXTURE = len(rows)


def tex_id(s):
    if len(s) > 30:
        s = s[:28] + ".."
    return s.replace("_", r"\_")


def make_header_ansq():
    return (
        r"\textbf{ID Fixture} & \textbf{Tipe} & \textbf{Sint.} & "
        r"\textbf{Skema} & \textbf{Relevansi} & \textbf{AnsQ} \\"
    )


def make_header_retq():
    return (
        r"\textbf{ID Fixture} & \textbf{Tipe} & \textbf{Precision} & "
        r"\textbf{Recall} & \textbf{F1} & \textbf{RetQ} \\"
    )


def make_header_reaq():
    return (
        r"\textbf{ID Fixture} & \textbf{Tipe} & \textbf{HopAcc} & "
        r"\textbf{Faithfulness} & \textbf{ReaQ} \\"
    )


def longtable_env(caption, label, col_spec, header_line, data_lines):
    parts = []
    parts.append(r"\begin{footnotesize}")
    parts.append(r"\begin{longtable}{" + col_spec + "}")
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
    tid  = tex_id(r["id"])
    t    = TYPE_SHORT.get(r["type"], r["type"])
    syn  = fmt(r.get("ansq_syntactic_validity", ""), 2)
    sch  = fmt(r.get("ansq_schema_compliance", ""), 2)
    rel  = fmt(r.get("ansq_answer_relevance", ""), 4)
    ansq = fmt(r.get("ansq_ansq_score", ""), 4)
    line = (
        r"\textit{" + tid + "} & " + t + " & " + syn + " & " + sch
        + " & " + rel + " & " + r"\textbf{" + ansq + r"} \\"
    )
    ansq_data.append(line)
    ansq_data.append(r"\hline")

# ── Build RetQ rows ──────────────────────────────────────────────────────
retq_data = []
for r in rows:
    tid  = tex_id(r["id"])
    t    = TYPE_SHORT.get(r["type"], r["type"])
    prec = fmt(r.get("retq_precision", ""), 4)
    rec  = fmt(r.get("retq_recall", ""), 4)
    f1   = fmt(r.get("retq_f1", ""), 4)
    retq = fmt(r.get("retq_retq_score", ""), 4)
    line = (
        r"\textit{" + tid + "} & " + t + " & " + prec + " & " + rec
        + " & " + f1 + " & " + r"\textbf{" + retq + r"} \\"
    )
    retq_data.append(line)
    retq_data.append(r"\hline")

# ── Build ReaQ rows ──────────────────────────────────────────────────────
reaq_data = []
for r in rows:
    tid   = tex_id(r["id"])
    t     = TYPE_SHORT.get(r["type"], r["type"])
    hacc  = fmt(r.get("reaq_hop_accuracy_corrected", ""), 4)
    faith = fmt(r.get("ragas_faithfulness", ""), 4)
    reaq  = fmt(r.get("reaq_reaq_score", ""), 4)
    line = (
        r"\textit{" + tid + "} & " + t + " & " + hacc + " & " + faith
        + " & " + r"\textbf{" + reaq + r"} \\"
    )
    reaq_data.append(line)
    reaq_data.append(r"\hline")

# ── Assemble document ────────────────────────────────────────────────────
out = []
out.append(r"\cleardoublepage")
out.append(r"\chapter{HASIL EVALUASI KUANTITATIF PER \textit{FIXTURE}}")
out.append("")
out.append(
    rf"Lampiran ini menyajikan nilai metrik lengkap untuk seluruh {N_FIXTURE} \textit{{fixture}} "
    r"evaluasi pada sistem \textit{GraphRAG} Kubernetes. "
    r"Tabel~\ref{tbl:ansq-full} menampilkan metrik \textit{Answer Quality} (AnsQ); "
    r"Tabel~\ref{tbl:retq-full} menampilkan metrik \textit{Retrieval Quality} (RetQ); "
    r"dan Tabel~\ref{tbl:reaq-full} menampilkan metrik \textit{Reasoning Quality} (ReaQ). "
    r"Kolom \textbf{Sint.}\ dan \textbf{Skema} pada Tabel~\ref{tbl:ansq-full} "
    r"hanya relevan untuk \textit{fixture} bertipe \texttt{yaml}; "
    r"nilai ``---'' menunjukkan bahwa metrik tersebut tidak diukur atau tidak berlaku "
    r"untuk \textit{fixture} yang bersangkutan (mis.\ \textbf{Faithfulness} pada \textit{fixture} "
    r"yang gagal dinilai oleh RAGAS, atau \textbf{HopAcc} pada \textit{fixture} tanpa "
    r"\textit{expected path})."
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
out.append(r"% ─────────────────────────────────────────────────────────────")
out.append(r"\section{Metrik \textit{Answer Quality} (AnsQ)}")
out.append(r"% ─────────────────────────────────────────────────────────────")
out.append("")
out.extend(longtable_env(
    caption=rf"Nilai Metrik AnsQ per \textit{{Fixture}} ({N_FIXTURE} \textit{{Fixture}})",
    label="tbl:ansq-full",
    col_spec=r"|p{3.6cm}|c|c|c|c|c|",
    header_line=make_header_ansq(),
    data_lines=ansq_data,
))
out.append("")
out.append(r"% ─────────────────────────────────────────────────────────────")
out.append(r"\section{Metrik \textit{Retrieval Quality} (RetQ)}")
out.append(r"% ─────────────────────────────────────────────────────────────")
out.append("")
out.extend(longtable_env(
    caption=rf"Nilai Metrik RetQ per \textit{{Fixture}} ({N_FIXTURE} \textit{{Fixture}})",
    label="tbl:retq-full",
    col_spec=r"|p{3.6cm}|c|c|c|c|c|",
    header_line=make_header_retq(),
    data_lines=retq_data,
))
out.append("")
out.append(r"% ─────────────────────────────────────────────────────────────")
out.append(r"\section{Metrik \textit{Reasoning Quality} (ReaQ)}")
out.append(r"% ─────────────────────────────────────────────────────────────")
out.append("")
out.extend(longtable_env(
    caption=rf"Nilai Metrik ReaQ per \textit{{Fixture}} ({N_FIXTURE} \textit{{Fixture}})",
    label="tbl:reaq-full",
    col_spec=r"|p{3.6cm}|c|c|c|c|",
    header_line=make_header_reaq(),
    data_lines=reaq_data,
))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"Written {len(out)} lines to {OUT_PATH} ({N_FIXTURE} fixtures)")
