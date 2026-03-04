"""
Truncation Strategy Comparison for Kubernetes Descriptions
===========================================================
Empirical comparison of three approaches:
  1. FULL: No truncation (preserve everything)
  2. SOFT_CAP: Simple safety cap at 2000 chars
  3. SMART: Intelligent truncation at 2000 chars with keyword preservation

Purpose:
  - Data-driven decision for thesis methodology
  - Quantify trade-offs: storage vs. accuracy vs. complexity
  - Generate thesis-ready tables and charts data

Usage:
  python scripts/compare_truncation_strategies.py

Output:
  - Console comparison table
  - logs/truncation_strategy_comparison.json (for thesis appendix)
"""

import json
import os
import sys
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import pure function (no .env dependency)
from src.utils.text_utils import smart_truncate_description


# ============================================
# CONFIGURATION
# ============================================
SWAGGER_PATH = "data/kubernetes_swagger.json"

# Critical keywords for preservation tracking
CRITICAL_KEYWORDS = [
    "DEPRECATED", "OBSOLETE", "REMOVED", "ALPHA", "BETA",
    "WARNING", "IMPORTANT", "CAUTION", "SECURITY", "DANGER", "NOTE",
    "IMMUTABLE", "READ-ONLY", "CANNOT BE UPDATED", "REQUIRED", "DEFAULTS TO",
    "MUTUALLY EXCLUSIVE", "IGNORED IF", "MUST MATCH", "AT LEAST ONE", "ONLY ALLOWED",
    "BASE64", "RFC 1123", "CIDR"
]

# Ignore list (same as parser.py)
IGNORE_LIST = {
    "io.k8s.apimachinery.pkg.apis.meta.v1.ManagedFieldsEntry",
    "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta",
    "io.k8s.apimachinery.pkg.apis.meta.v1.StatusDetails",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Time",
    "io.k8s.apimachinery.pkg.apis.meta.v1.MicroTime",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Duration",
    "io.k8s.apimachinery.pkg.apis.meta.v1.RawExtension",
}

# Strategies to compare
STRATEGIES = {
    "FULL": {
        "name": "Full (No Truncation)",
        "func": lambda desc, orig_len: desc,  # No truncation
        "threshold": None,
        "complexity": "⭐⭐⭐⭐⭐ (Simplest)",
    },
    "SOFT_CAP": {
        "name": "Soft Cap (2000 chars)",
        "func": lambda desc, orig_len: safe_truncate_description(desc, hard_limit=2000),
        "threshold": 2000,
        "complexity": "⭐⭐⭐⭐⭐ (Simple)",
    },
    "SMART": {
        "name": "Smart Truncation (2000 chars)",
        "func": lambda desc, orig_len: smart_truncate_description(desc, orig_len, max_length=2000),
        "threshold": 2000,
        "complexity": "⭐⭐⭐ (Complex)",
    },
}


# ============================================
# TRUNCATION FUNCTIONS
# ============================================
def safe_truncate_description(desc: str, hard_limit: int = 2000) -> str:
    """
    Simple safety cap for descriptions.
    
    Only truncates if exceeding hard_limit (defensive programming).
    Preserves 100% of normal data while protecting against edge cases.
    """
    if not desc:
        return 'No description provided.'
    
    if len(desc) > hard_limit:
        truncated = desc[:hard_limit]
        last_period = truncated.rfind('.')
        if last_period > hard_limit - 200:
            return truncated[:last_period + 1] + "..."
        return truncated + "..."
    
    return desc


# ============================================
# ANALYSIS FUNCTIONS
# ============================================
def load_swagger_descriptions(swagger_path: str) -> Dict[str, str]:
    """Loads all descriptions from Kubernetes Swagger definitions."""
    print(f"📂 Loading Swagger file: {swagger_path}")
    
    with open(swagger_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    definitions = data.get('definitions', {})
    descriptions = {}
    
    for full_name, schema in definitions.items():
        if full_name in IGNORE_LIST:
            continue
        desc = schema.get('description', '')
        if desc:
            descriptions[full_name] = desc
    
    print(f"   ✓ Loaded {len(descriptions)} descriptions")
    return descriptions


def count_critical_keywords(text: str) -> List[str]:
    """Returns list of critical keywords found in text."""
    text_upper = text.upper()
    return [kw for kw in CRITICAL_KEYWORDS if kw in text_upper]


def calculate_stats(values: List[float]) -> Dict[str, Any]:
    """Calculates comprehensive statistics."""
    if not values:
        return {}
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    return {
        "count": n,
        "min": min(values),
        "max": max(values),
        "mean": round(statistics.mean(values), 2),
        "median": statistics.median(values),
        "stdev": round(statistics.stdev(values), 2) if n > 1 else 0,
        "p90": sorted_vals[int(n * 0.9)] if n >= 10 else None,
        "p95": sorted_vals[int(n * 0.95)] if n >= 20 else None,
    }


def analyze_strategy(descriptions: Dict[str, str], strategy_key: str) -> Dict[str, Any]:
    """Analyzes a single truncation strategy."""
    strategy = STRATEGIES[strategy_key]
    truncate_func = strategy["func"]
    
    original_lengths = []
    result_lengths = []
    reduction_rates = []
    keyword_stats = []
    truncated_count = 0
    
    print(f"   🔍 Analyzing {strategy['name']}...")
    
    for full_name, original_desc in descriptions.items():
        original_length = len(original_desc)
        original_lengths.append(original_length)
        
        # Apply truncation
        result_desc = truncate_func(original_desc, original_length)
        result_length = len(result_desc)
        result_lengths.append(result_length)
        
        # Track truncation
        if result_length < original_length:
            truncated_count += 1
            reduction_rates.append((1 - result_length / original_length) * 100)
        
        # Track keyword preservation
        original_keywords = set(count_critical_keywords(original_desc))
        result_keywords = set(count_critical_keywords(result_desc))
        
        if original_keywords:
            preservation = len(result_keywords & original_keywords) / len(original_keywords) * 100
            keyword_stats.append(preservation)
    
    return {
        "strategy": strategy["name"],
        "threshold": strategy["threshold"],
        "complexity": strategy["complexity"],
        "lengths": {
            "original": calculate_stats(original_lengths),
            "result": calculate_stats(result_lengths),
        },
        "reduction": {
            "count": truncated_count,
            "percentage": round(truncated_count / len(descriptions) * 100, 2),
            "rates": calculate_stats(reduction_rates) if reduction_rates else None,
        },
        "keywords": {
            "descriptions_with_keywords": len(keyword_stats),
            "avg_preservation": round(statistics.mean(keyword_stats), 2) if keyword_stats else 100,
            "min_preservation": min(keyword_stats) if keyword_stats else 100,
        },
        "storage": {
            "total_bytes_original": sum(original_lengths),
            "total_bytes_result": sum(result_lengths),
            "saved_bytes": sum(original_lengths) - sum(result_lengths),
            "saved_mb": (sum(original_lengths) - sum(result_lengths)) / (1024 * 1024),
        }
    }


def print_comparison_table(results: Dict[str, Dict]):
    """Prints a formatted comparison table."""
    print("\n" + "="*100)
    print("📊 TRUNCATION STRATEGY COMPARISON")
    print("="*100)
    
    print(f"\n{'Strategy':<30} {'Threshold':<12} {'Truncated':<12} {'Keyword Pres.':<15} {'Storage Saved':<15} {'Complexity':<20}")
    print(f"{'-'*30} {'-'*12} {'-'*12} {'-'*15} {'-'*15} {'-'*20}")
    
    for key in ["FULL", "SOFT_CAP", "SMART"]:
        r = results[key]
        threshold = f"{r['threshold']} chars" if r['threshold'] else "None"
        truncated = f"{r['reduction']['count']} ({r['reduction']['percentage']}%)"
        keyword_pres = f"{r['keywords']['avg_preservation']}%"
        storage_saved = f"{r['storage']['saved_mb']:.2f} MB"
        complexity = r['complexity']
        
        print(f"{r['strategy']:<30} {threshold:<12} {truncated:<12} {keyword_pres:<15} {storage_saved:<15} {complexity:<20}")
    
    print("="*100)


def print_detailed_analysis(results: Dict[str, Dict], total_descriptions: int):
    """Prints detailed analysis for thesis narrative."""
    print(f"\n🔍 DETAILED ANALYSIS (n={total_descriptions} descriptions)")
    print("-"*100)
    
    for key in ["FULL", "SOFT_CAP", "SMART"]:
        r = results[key]
        print(f"\n📋 {r['strategy']}:")
        print(f"   📏 Length Stats:")
        print(f"      • Original Mean: {r['lengths']['original']['mean']:.1f} chars")
        print(f"      • Result Mean:   {r['lengths']['result']['mean']:.1f} chars")
        print(f"      • Max Result:    {r['lengths']['result']['max']:,} chars")
        
        print(f"   🎯 Keyword Preservation:")
        print(f"      • Descriptions with keywords: {r['keywords']['descriptions_with_keywords']}")
        print(f"      • Avg preservation rate: {r['keywords']['avg_preservation']}%")
        print(f"      • Min preservation rate: {r['keywords']['min_preservation']}%")
        
        print(f"   💾 Storage Impact:")
        print(f"      • Total original: {r['storage']['total_bytes_original'] / (1024*1024):.2f} MB")
        print(f"      • Total result:   {r['storage']['total_bytes_result'] / (1024*1024):.2f} MB")
        print(f"      • Saved:          {r['storage']['saved_mb']:.2f} MB ({r['reduction']['percentage']}%)")
        
        if r['reduction']['rates']:
            print(f"   📉 Reduction Stats:")
            print(f"      • Avg reduction: {r['reduction']['rates']['mean']:.1f}%")
            print(f"      • Max reduction: {r['reduction']['rates']['max']:.1f}%")


def calculate_recommendation_score(results: Dict[str, Dict]) -> Dict[str, float]:
    """
    Calculates a weighted recommendation score for each strategy.
    
    Weights based on thesis constraints:
    - Budget (token cost): 30%
    - Storage (Neo4j Free): 25%
    - Accuracy (keyword preservation): 30%
    - Simplicity (maintainability): 15%
    """
    weights = {
        "budget": 0.30,      # Lower token cost = better
        "storage": 0.25,     # Lower storage = better
        "accuracy": 0.30,    # Higher keyword preservation = better
        "simplicity": 0.15,  # Simpler = better
    }
    
    scores = {}
    
    for key in ["FULL", "SOFT_CAP", "SMART"]:
        r = results[key]
        
        # Budget score: based on avg length (shorter = cheaper tokens)
        avg_len = r['lengths']['result']['mean']
        budget_score = max(0, 100 - (avg_len / 40))  # Normalize: 40 chars = 10 points
        
        # Storage score: based on MB saved (more saved = better, but diminishing returns)
        storage_mb = r['storage']['total_bytes_result'] / (1024 * 1024)
        storage_score = max(0, 100 - storage_mb * 0.5)  # Neo4j Free = 500MB
        
        # Accuracy score: keyword preservation
        accuracy_score = r['keywords']['avg_preservation']
        
        # Simplicity score: hardcoded based on strategy
        simplicity_map = {"FULL": 100, "SOFT_CAP": 95, "SMART": 70}
        simplicity_score = simplicity_map.get(key, 50)
        
        # Weighted total
        total = (
            weights["budget"] * budget_score +
            weights["storage"] * storage_score +
            weights["accuracy"] * accuracy_score +
            weights["simplicity"] * simplicity_score
        )
        
        scores[key] = round(total, 2)
    
    return scores


def print_recommendation(results: Dict[str, Dict], scores: Dict[str, float]):
    """Prints thesis-ready recommendation."""
    print("\n" + "="*100)
    print("🏆 RECOMMENDATION FOR THESIS")
    print("="*100)
    
    # Sort by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Rank':<6} {'Strategy':<30} {'Score':<10} {'Verdict':<20}")
    print(f"{'-'*6} {'-'*30} {'-'*10} {'-'*20}")
    
    for rank, (key, score) in enumerate(ranked, 1):
        r = results[key]
        verdict = "✅ RECOMMENDED" if rank == 1 else "⚠️ Alternative"
        print(f"{rank:<6} {r['strategy']:<30} {score:<10.2f} {verdict:<20}")
    
    # Thesis narrative for winner
    winner_key = ranked[0][0]
    winner = results[winner_key]
    
    print(f"\n📝 Thesis Narrative (Bab 3 - Methodology):")
    print(f"   Berdasarkan analisis empiris terhadap {winner['lengths']['original']['count']} definisi")
    print(f"   Kubernetes API, strategi '{winner['strategy']}' direkomendasikan karena:")
    print(f"   • Preservasi informasi kritis: {winner['keywords']['avg_preservation']}%")
    print(f"   • Impact storage Neo4j: {winner['storage']['saved_mb']:.2f} MB")
    print(f"   • Kompleksitas implementasi: {winner['complexity']}")
    print(f"   • Skor rekomendasi (weighted): {scores[winner_key]}/100")
    print()
    print(f"   Kesimpulan: Trade-off optimal untuk constraint budget 1 juta IDR,")
    print(f"   Neo4j AuraDB Free Tier (500MB), dan timeline 3 bulan.")
    
    print("="*100)


def save_report(results: Dict[str, Dict], scores: Dict[str, float], output_path: str):
    """Saves full comparison to JSON for thesis appendix."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_descriptions": results["FULL"]["lengths"]["original"]["count"],
        "strategies_compared": list(STRATEGIES.keys()),
        "critical_keywords_tracked": CRITICAL_KEYWORDS,
        "results": results,
        "recommendation_scores": scores,
        "recommended_strategy": max(scores, key=scores.get),
        "thesis_constraints": {
            "budget_idr": 1000000,
            "neo4j_tier": "AuraDB Free (500MB)",
            "laptop_ram_gb": 16,
            "timeline_months": 3,
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full report saved to: {output_path}")


# ============================================
# MAIN
# ============================================
def main():
    print("🚀 Truncation Strategy Comparison for Kubernetes GraphRAG")
    print("="*100)
    
    # Step 1: Load descriptions
    try:
        descriptions = load_swagger_descriptions(SWAGGER_PATH)
    except FileNotFoundError:
        print(f"❌ ERROR: Swagger file not found at {SWAGGER_PATH}")
        print("   Download: https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json")
        sys.exit(1)
    
    # Step 2: Analyze each strategy
    print(f"\n🔬 Running comparative analysis...")
    results = {}
    for key in STRATEGIES.keys():
        results[key] = analyze_strategy(descriptions, key)
    
    # Step 3: Print comparison table
    print_comparison_table(results)
    
    # Step 4: Print detailed analysis
    print_detailed_analysis(results, len(descriptions))
    
    # Step 5: Calculate and print recommendation
    scores = calculate_recommendation_score(results)
    print_recommendation(results, scores)
    
    # Step 6: Save report
    report_path = "logs/truncation_strategy_comparison.json"
    save_report(results, scores, report_path)
    
    # Step 7: Quick decision helper
    print(f"\n⚡ Quick Decision:")
    winner = max(scores, key=scores.get)
    print(f"   → Use '{results[winner]['strategy']}' for your thesis")
    print(f"   → Update parser.py with this strategy")
    print(f"   → Cite this analysis in Bab 4 (Hasil & Pembahasan)")


if __name__ == "__main__":
    main()