# scripts/run_baseline.py
"""
Baseline comparison script for Bab VI evaluation.
Usage:
  python scripts/run_baseline.py --mode llm      # Vanilla LLM only
  python scripts/run_baseline.py --mode vector   # Vector-RAG only
  python scripts/run_baseline.py --mode graphrag # Full GraphRAG (default)

Outputs a summary table and saves results to data/baseline_{mode}.csv.
"""
import sys
import os
import json
import csv
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
OUTPUT_DIR   = Path(__file__).parent.parent / "data"


def run_llm_baseline(question: str) -> tuple[str, list]:
    """Mode 1: Vanilla LLM — no retrieval, no graph."""
    from src.chatbot.llm_factory import get_speaker_llm
    from langchain_core.messages import HumanMessage
    llm = get_speaker_llm()
    response = llm.invoke([HumanMessage(content=question)])
    return response.content, []


def run_vector_baseline(question: str) -> tuple[str, list]:
    """Mode 2: Vector-RAG — pure dense top-k, no graph traversal.

    Uses SIMPLE_VECTOR_QUERY (k=5), identical to evaluate.py --mode vector.
    GraphRetriever was removed here because it uses SIMPLE_GRAPH_EXPAND_QUERY
    which does a 1-hop OPTIONAL MATCH — making it a partial graph baseline,
    not a pure vector baseline. That would conflate the graph contribution with
    the vector contribution, invalidating the GraphRAG-vs-Vector delta (T1).
    """
    from src.graph.neo4j_client import Neo4jClient
    from src.graph.vector_index import VectorIndexManager
    from src.graph.queries import SIMPLE_VECTOR_QUERY
    from src.chatbot.llm_factory import get_speaker_llm
    from langchain_core.messages import HumanMessage

    db        = Neo4jClient()
    vector_mgr = VectorIndexManager()
    embedding = vector_mgr.generate_embedding(question)
    results   = db.execute_query(SIMPLE_VECTOR_QUERY, {"embedding": embedding, "top_k": 5})

    parts = []
    for r in results:
        fn   = r.get("node.fullName", "")
        desc = r.get("node.description", "")
        parts.append(f"Resource: {fn}\nDescription: {desc}\n")
    context  = "\n---\n".join(parts)
    prompt   = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    llm      = get_speaker_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content, []


def run_graphrag_baseline(question: str) -> tuple[str, list]:
    """Mode 3: Full GraphRAG pipeline."""
    from src.chatbot.graph_agent import create_agent_graph
    agent  = create_agent_graph()
    result = agent.invoke({
        "question": question,
        "session_id": "baseline_graphrag",
        "messages": [],
        "chat_history": "",
        "extracted_intent": {},
        "graph_context": "",
        "reasoning_path": [],
        "error": None,
    })
    answer = result["messages"][-1].content if result.get("messages") else ""
    path   = result.get("reasoning_path") or []
    return answer, path


RUNNERS = {
    "llm":      run_llm_baseline,
    "vector":   run_vector_baseline,
    "graphrag": run_graphrag_baseline,
}


def main(mode: str):
    runner   = RUNNERS[mode]
    fixtures = sorted(FIXTURES_DIR.rglob("*.json"))

    if not fixtures:
        logger.error("No fixtures found.")
        sys.exit(1)

    logger.info(f"Baseline mode: {mode}  |  fixtures: {len(fixtures)}")

    rows = []
    for fpath in fixtures:
        data     = json.loads(fpath.read_text(encoding="utf-8"))
        question = data["question"]
        logger.info(f"  {data['id']}: {question[:60]}...")

        answer, path = runner(question)
        rows.append({
            "id":           data["id"],
            "type":         data["type"],
            "mode":         mode,
            "question":     question,
            "answer":       answer[:300].replace("\n", " "),
            "hops":         len(path),
            "reasoning":    " | ".join(path[:3]),
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"baseline_{mode}.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. {len(rows)} answers saved to {out_file}")
    print("Run scripts/evaluate.py --mode <mode> to score each baseline.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="graphrag", choices=["llm", "vector", "graphrag"])
    args = parser.parse_args()
    main(args.mode)
