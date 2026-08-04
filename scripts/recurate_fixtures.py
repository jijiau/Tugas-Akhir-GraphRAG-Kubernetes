#!/usr/bin/env python3
"""
scripts/recurate_fixtures.py  — Fase 2 Audit E2E

Re-kurasi ground-truth fixture, MENGGANTI scripts/expand_relevant_nodes.py
(yang menyamakan key_nodes dengan seluruh subgraf = bug F2 pada faithfulness).

PILOT (Langkah 2b) membuktikan: mengecilkan `relevant_nodes` menghancurkan RetQ
(F1 0,77→0,20) karena retriever mengembalikan SELURUH neighborhood depth-bounded.
Keputusan user (D6): **PISAHKAN PERAN** dua kelompok GT —

  • relevant_nodes / expected_path  → mendorong RetQ (COVERAGE neighborhood skema).
        = neighborhood depth-bounded dari resource yang ditanya (edge asli, depth per-intent),
          regenerasi bersih dari KG. TETAP besar → RetQ tinggi & diskriminatif vs baseline.
  • key_nodes                       → mendorong faithfulness/AnsQ (ANSWER-BEARING).
        = node yang disebut di `context` + `answer` (diverifikasi KG). DIKECILKAN
          dari = relevant_nodes (lama) menjadi himpunan answer-bearing → faithfulness naik sah.

Tambahan: `gt_depth` (int, per-intent) + `n_roots` (multi-entity) untuk F3 di Fase 1.
Framing T1: GT = subgraf skema objektif dari swagger; GraphRAG meng-cover-nya, vector tidak.

Metode SEMI-DETERMINISTIK (pencocokan answer-mention heuristik) → WAJIB lewat gerbang
rubrik manual per-kategori. Lihat docs/AUDIT_E2E/phases/FASE_2.md.

Usage:
    python scripts/recurate_fixtures.py --pilot relationship/pvc_storageclass ...
    python scripts/recurate_fixtures.py --dry-run                      # tulis fix_log per kategori
    python scripts/recurate_fixtures.py --apply --category relationship
"""
import sys
import re
import json
import math
import argparse
import logging
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from src.graph.neo4j_client import Neo4jClient
from src.graph.queries import _ALL_EDGE_TYPES, PATH_EDGES_QUERY

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR     = Path(__file__).parent.parent
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
DOCS_DIR     = ROOT_DIR / "docs" / "AUDIT_E2E"

DEPTH_BY_TYPE = {
    "conceptual": 2, "followup": 2,
    "yaml_gen": 3, "relationship": 3, "planning": 3,
    "command": 3, "troubleshooting": 3, "realworld": 3,
}
DEFAULT_DEPTH = 3
MULTI_ENTITY_TYPES = {"planning", "yaml_gen"}
CATEGORIES = ["command", "conceptual", "followup", "planning",
              "realworld", "relationship", "troubleshooting", "yaml_gen"]

_FQN_RE  = re.compile(r"io\.k8s\.[\w.]+")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9]+")


# ── KG vocabulary ────────────────────────────────────────────────────────────
class KGVocab:
    def __init__(self, db: Neo4jClient):
        rows = db.execute_query(
            "MATCH (d:Definition) RETURN d.name AS name, d.fullName AS fullName, d.kind AS kind", {})
        self.name2fqn, self.fqn2name = {}, {}
        self.names, self.fqns, self.resource_names = set(), set(), set()
        for r in rows:
            nm, fqn, kind = r["name"], r["fullName"], r.get("kind")
            if nm:
                self.names.add(nm)
                if fqn:
                    self.name2fqn.setdefault(nm, fqn)
                if kind:
                    self.resource_names.add(nm)
            if fqn:
                self.fqns.add(fqn)
                if nm:
                    self.fqn2name[fqn] = nm

    def short(self, ref: str):
        if not ref:
            return None
        if ref in self.names:
            return ref
        if ref in self.fqn2name:
            return self.fqn2name[ref]
        tail = ref.split(".")[-1]
        return tail if tail in self.names else None

    def fqn(self, short: str):
        return self.name2fqn.get(short)


# ── Seed extraction (answer-bearing → key_nodes) ─────────────────────────────
def seeds_from_fixture(fixture: dict, vocab: KGVocab):
    """Returns (seed_short:set, missing_refs:set, low_confidence:bool)."""
    gt = fixture.get("ground_truth", {})
    context = gt.get("context", []) or []
    answer = gt.get("answer", "") or ""
    resource = fixture.get("resource", "") or ""
    seeds, missing = set(), set()

    def add(ref):
        s = vocab.short(ref)
        if s:
            seeds.add(s)
        elif ref and ref.startswith("io.k8s"):
            missing.add(ref)

    add(resource)
    ctx_text = " ".join(context) if isinstance(context, list) else str(context)
    for fqn in _FQN_RE.findall(ctx_text):
        add(fqn)
    low_conf = not context
    for w in set(_WORD_RE.findall(answer)):
        if len(w) > 3 and w in vocab.names:
            seeds.add(w)
    return seeds, missing, low_conf


# ── Neighborhood (coverage → relevant_nodes / expected_path) ─────────────────
def _neighborhood(db, root_short: str, depth: int):
    """All (parent,rel,child) short-name edges + node short-names reachable within depth."""
    if not root_short:
        return set(), set()
    q = (
        "MATCH p = (root:Definition {name:$root})-[:" + _ALL_EDGE_TYPES + "*1.." + str(int(depth)) + "]->(c:Definition) "
        "WITH p LIMIT 3000 "
        "UNWIND range(0, size(relationships(p))-1) AS i "
        "RETURN DISTINCT nodes(p)[i].name AS pn, type(relationships(p)[i]) AS rel, nodes(p)[i+1].name AS cn"
    )
    rows = db.execute_query(q, {"root": root_short})
    nodes, edges = {root_short}, set()
    for r in rows:
        nodes.add(r["pn"]); nodes.add(r["cn"])
        edges.add(f"{r['pn']} -[{r['rel']}]-> {r['cn']}")
    return nodes, edges


def roots_for(fixture, vocab, seeds):
    """Root resource(s) whose neighborhood forms relevant_nodes/expected_path.

    Uses the PRIMARY resource only. Pilot showed that unioning every resource-kind
    seed (planning: 9 roots → 99 nodes) inflates relevant_nodes far beyond what the
    retriever returns (root + ≤2 merged), cratering RetQ recall. The queried-resource
    neighborhood is the defensible coverage gold standard; multi-entity benefit is
    captured by key_nodes (faithfulness), not by inflating coverage GT.
    """
    primary = vocab.short(fixture.get("resource", ""))
    return [primary] if primary else []


def recurate_one(db, vocab, fixture: dict):
    """Compute new GT for one fixture. Returns dict(new fields) + diagnostics."""
    ftype = fixture.get("type", "")
    depth = DEPTH_BY_TYPE.get(ftype, DEFAULT_DEPTH)
    seeds, missing, low_conf = seeds_from_fixture(fixture, vocab)
    roots = roots_for(fixture, vocab, seeds)

    nbr_nodes, nbr_edges = set(), set()
    for r in roots:
        n, e = _neighborhood(db, r, depth)
        nbr_nodes |= n
        nbr_edges |= e

    # key_nodes = answer-bearing seeds (verified in KG)
    key_short = {s for s in seeds if s in vocab.names}
    # relevant_nodes = neighborhood ∪ key (guarantee key ⊆ relevant)
    relevant_short = nbr_nodes | key_short

    relevant_fqn = sorted({vocab.fqn(n) or n for n in relevant_short})
    key_fqn      = sorted({vocab.fqn(n) or n for n in key_short})
    expected_path = sorted(nbr_edges)

    return {
        "relevant_nodes": relevant_fqn,
        "expected_path": expected_path,
        "key_nodes": key_fqn,
        "gt_depth": depth,
        "n_roots": len(roots),
        "_diag": {
            "roots": roots, "missing": sorted(missing), "low_conf": low_conf,
            "n_neighborhood": len(nbr_nodes), "n_seeds": len(key_short),
        },
    }


# ── Reproduce retriever output (pilot only, no LLM) ──────────────────────────
def retriever_reasoning_path(db, root_short, depth):
    if not root_short:
        return []
    rows = db.execute_query(PATH_EDGES_QUERY.format(max_depth=int(depth), all_edges=_ALL_EDGE_TYPES), {"root_name": root_short})
    seen, path = set(), []
    for r in rows:
        e = f"{r['parent']} -[{r['rel_type']}]-> {r['child']}"
        if e not in seen:
            seen.add(e); path.append(e)
    return path


_RELATION_RE = re.compile(r"-\[([^\]]+)\]->?")


def _node_tokens(step):
    return [t for t in _RELATION_RE.sub(" ", step).split() if t]


def compute_retq(reasoning_path, relevant_nodes, expected_path):
    expected = set(n.split(".")[-1] for n in relevant_nodes)
    retrieved, seen = [], set()
    for step in reasoning_path:
        for tok in _node_tokens(step):
            if tok not in seen:
                seen.add(tok); retrieved.append(tok)
    rset = set(retrieved)
    inter = rset & expected
    p = len(inter)/len(rset) if rset else 0.0
    rc = len(inter)/len(expected) if expected else 1.0
    f1 = 2*p*rc/(p+rc) if (p+rc) > 0 else 0.0
    if expected_path:
        m = sum(1 for ep in expected_path if any(ep in s or ep.split(" -[")[0] in s for s in reasoning_path))
        pcov = m/len(expected_path)
    else:
        pcov = 1.0
    return {"precision": p, "recall": rc, "f1": f1, "path_coverage": pcov,
            "n_relevant": len(expected), "n_retrieved": len(retrieved)}


# ── IO helpers ───────────────────────────────────────────────────────────────
def load_fixture(rel):
    p = FIXTURES_DIR / (rel if rel.endswith(".json") else rel + ".json")
    return p, json.loads(p.read_text(encoding="utf-8"))


def all_fixture_paths(category=None):
    out = []
    for p in sorted(FIXTURES_DIR.rglob("*.json")):
        if category and p.parent.name != category:
            continue
        out.append(p)
    return out


# ── Pilot ────────────────────────────────────────────────────────────────────
def run_pilot(db, vocab, fixture_paths):
    print("\n" + "=" * 92)
    print("  PILOT — RetQ (separasi peran): relevant_nodes = neighborhood (coverage)")
    print("=" * 92)
    for rel in fixture_paths:
        _, fx = load_fixture(rel)
        depth = DEPTH_BY_TYPE.get(fx.get("type", ""), DEFAULT_DEPTH)
        root = vocab.short(fx.get("resource", ""))
        rpath = retriever_reasoning_path(db, root, depth)
        new = recurate_one(db, vocab, fx)
        gt = fx.get("ground_truth", {})
        old_m = compute_retq(rpath, gt.get("relevant_nodes", []), gt.get("expected_path", []))
        new_m = compute_retq(rpath, new["relevant_nodes"], new["expected_path"])
        print(f"\n── {rel} (type={fx.get('type')}, depth={depth}, roots={new['_diag']['roots']})")
        print(f"   relevant: old={len(gt.get('relevant_nodes',[]))} new={len(new['relevant_nodes'])} | "
              f"key: old={len(gt.get('key_nodes',[]))} new={len(new['key_nodes'])} | "
              f"low_conf={new['_diag']['low_conf']} missing={new['_diag']['missing']}")
        print(f"   RetQ OLD: F1={old_m['f1']:.3f} P={old_m['precision']:.3f} R={old_m['recall']:.3f} pcov={old_m['path_coverage']:.3f}")
        print(f"   RetQ NEW: F1={new_m['f1']:.3f} P={new_m['precision']:.3f} R={new_m['recall']:.3f} pcov={new_m['path_coverage']:.3f}")
    print("=" * 92)


# ── Dry-run report / apply ───────────────────────────────────────────────────
def write_report(db, vocab, category=None):
    by_cat = defaultdict(list)
    for fpath in all_fixture_paths(category):
        fx = json.loads(fpath.read_text(encoding="utf-8"))
        new = recurate_one(db, vocab, fx)
        gt = fx.get("ground_truth", {})
        by_cat[fpath.parent.name].append((fpath.stem, fx, gt, new))

    lines = ["# Fixture Fix Log — Fase 2 (dry-run)", "",
             "> Otomatis dari `recurate_fixtures.py`. relevant_nodes/expected_path = neighborhood (coverage); key_nodes = answer-bearing. Validasi per kategori dgn Rubrik.", ""]
    for cat in CATEGORIES:
        if cat not in by_cat:
            continue
        lines.append(f"\n## {cat} ({len(by_cat[cat])})\n")
        lines.append("| fixture | rel old→new | key old→new | edges old→new | depth | n_roots | flags |")
        lines.append("|---|---|---|---|---|---|---|")
        for fid, fx, gt, new in by_cat[cat]:
            d = new["_diag"]
            flags = []
            if d["low_conf"]:
                flags.append("LOW_CONF(ctx kosong)")
            if d["missing"]:
                flags.append(f"PHANTOM:{','.join(s.split('.')[-1] for s in d['missing'])}")
            if not set(new["key_nodes"]).issubset(set(new["relevant_nodes"])):
                flags.append("KEY⊄REL")
            if len(new["relevant_nodes"]) == 0:
                flags.append("EMPTY_REL")
            lines.append(f"| {fid} | {len(gt.get('relevant_nodes',[]))}→{len(new['relevant_nodes'])} "
                         f"| {len(gt.get('key_nodes',[]))}→{len(new['key_nodes'])} "
                         f"| {len(gt.get('expected_path',[]))}→{len(new['expected_path'])} "
                         f"| {new['gt_depth']} | {new['n_roots']} | {'; '.join(flags) or 'ok'} |")
    out = DOCS_DIR / "fixture_fix_log.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written: {out}  ({sum(len(v) for v in by_cat.values())} fixtures)")


def apply_category(db, vocab, category):
    paths = all_fixture_paths(category)
    if not paths:
        print(f"No fixtures in category '{category}'.")
        return
    n = 0
    for fpath in paths:
        fx = json.loads(fpath.read_text(encoding="utf-8"))
        new = recurate_one(db, vocab, fx)
        gt = fx.setdefault("ground_truth", {})
        gt["relevant_nodes"] = new["relevant_nodes"]
        gt["expected_path"]  = new["expected_path"]
        gt["key_nodes"]      = new["key_nodes"]
        gt["gt_depth"]       = new["gt_depth"]
        gt["n_roots"]        = new["n_roots"]
        fpath.write_text(json.dumps(fx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        n += 1
    print(f"Applied re-curation to {n} fixtures in '{category}'.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", nargs="+", metavar="FIXTURE")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--category", default=None)
    args = ap.parse_args()

    db = Neo4jClient()
    vocab = KGVocab(db)

    if args.pilot:
        run_pilot(db, vocab, args.pilot)
    elif args.dry_run:
        write_report(db, vocab, args.category)
    elif args.apply:
        if not args.category:
            print("Refusing bulk apply without --category (per-category gate). Use --category <type>.")
            return
        apply_category(db, vocab, args.category)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
