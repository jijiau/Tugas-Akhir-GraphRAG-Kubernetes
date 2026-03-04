"""
Kubernetes Swagger Description Length Analyzer
===============================================
Calculates statistics for description lengths before and after smart truncation.

Purpose:
    - Empirical validation for thesis (Bab 4: Hasil & Pembahasan)
    - Justify truncation threshold (2000 chars)
    - Measure critical info preservation rate

Usage:
    python scripts/analyze_description_length.py

Output:
    - Console summary table
    - logs/description_length_analysis.json (for thesis appendix)
"""

import json
import os
import sys
import statistics
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.text_utils import smart_truncate_description


# ============================================
# CONFIGURATION
# ============================================
SWAGGER_PATH = "data/kubernetes_swagger.json"
MAX_LENGTH = 2000  # Smart truncation threshold

# Critical keywords for preservation tracking
CRITICAL_KEYWORDS = [
        # 1. API Lifecycle & Maturity (Mencegah LLM memakai struktur usang)
        "DEPRECATED", "OBSOLETE", "REMOVED", "ALPHA", "BETA",
        
        # 2. Alerts & Warnings (Peringatan operasional krusial)
        "WARNING", "IMPORTANT", "CAUTION", "SECURITY", "DANGER", "NOTE",
        
        # 3. Mutability & Defaults (Aturan dasar field YAML)
        "IMMUTABLE", "READ-ONLY", "CANNOT BE UPDATED", "REQUIRED", "DEFAULTS TO",
        
        # 4. Structural Logic & Conflicts (BARU: Mencegah error logika YAML)
        "MUTUALLY EXCLUSIVE", # Misal: Tidak boleh pakai hostPath dan emptyDir bersamaan
        "IGNORED IF",         # Misal: Field ini diabaikan kalau field lain diisi
        "MUST MATCH",         # Misal: Label selector harus sama dengan pod template
        "AT LEAST ONE",       # Misal: Harus ada minimal satu container di dalam Pod
        "ONLY ALLOWED",       # Menandakan batasan nilai yang ketat
        
        # 5. Data Formatting (BARU: Mencegah error sintaks/tipe data)
        "BASE64",             # Krusial untuk K8s Secret, LLM harus tahu nilainya butuh base64
        "RFC 1123",           # Standar penamaan resource K8s (tidak boleh pakai spasi/huruf besar)
        "CIDR"                # Format jaringan (untuk NetworkPolicy atau Service)
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


# ============================================
# ANALYSIS FUNCTIONS
# ============================================
def load_swagger_descriptions(swagger_path: str) -> Dict[str, str]:
    """
    Loads all descriptions from Kubernetes Swagger definitions.
    
    Returns:
        Dict[full_name, description]
    """
    print(f"📂 Loading Swagger file: {swagger_path}")
    
    with open(swagger_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    definitions = data.get('definitions', {})
    descriptions = {}
    
    for full_name, schema in definitions.items():
        if full_name in IGNORE_LIST:
            continue
        
        desc = schema.get('description', '')
        if desc:  # Only include non-empty descriptions
            descriptions[full_name] = desc
    
    print(f"   ✓ Loaded {len(descriptions)} descriptions")
    return descriptions


def calculate_length_stats(lengths: List[int]) -> Dict[str, Any]:
    """
    Calculates comprehensive statistics for a list of lengths.
    """
    if not lengths:
        return {}
    
    return {
        "count": len(lengths),
        "min": min(lengths),
        "max": max(lengths),
        "mean": round(statistics.mean(lengths), 2),
        "median": statistics.median(lengths),
        "stdev": round(statistics.stdev(lengths), 2) if len(lengths) > 1 else 0,
        "q1": statistics.quantiles(lengths, n=4)[0] if len(lengths) >= 4 else None,
        "q3": statistics.quantiles(lengths, n=4)[2] if len(lengths) >= 4 else None,
        "p90": sorted(lengths)[int(len(lengths) * 0.9)] if len(lengths) >= 10 else None,
        "p95": sorted(lengths)[int(len(lengths) * 0.95)] if len(lengths) >= 20 else None,
        "p99": sorted(lengths)[int(len(lengths) * 0.99)] if len(lengths) >= 100 else None,
    }


def count_critical_keywords(text: str) -> Dict[str, Any]:
    """
    Counts critical keywords found in text.
    """
    text_upper = text.upper()
    found = [kw for kw in CRITICAL_KEYWORDS if kw in text_upper]
    
    return {
        "count": len(found),
        "keywords": found
    }


def analyze_truncation(descriptions: Dict[str, str], max_length: int) -> Dict[str, Any]:
    """
    Analyzes truncation effectiveness across all descriptions.
    """
    before_lengths = []
    after_lengths = []
    reduction_rates = []
    keyword_preservation = []
    truncated_count = 0
    
    print(f"\n🔍 Analyzing {len(descriptions)} descriptions with max_length={max_length}...")
    
    for full_name, original_desc in descriptions.items():
        original_length = len(original_desc)
        before_lengths.append(original_length)
        
        # Apply smart truncation
        truncated_desc = smart_truncate_description(
            desc=original_desc,
            original_length=original_length,
            max_length=max_length
        )
        after_length = len(truncated_desc)
        after_lengths.append(after_length)
        
        # Calculate reduction rate
        if original_length > 0:
            reduction = (1 - after_length / original_length) * 100
            reduction_rates.append(reduction)
        
        # Track if was truncated
        if after_length < original_length:
            truncated_count += 1
        
        # Check keyword preservation
        before_keywords = count_critical_keywords(original_desc)
        after_keywords = count_critical_keywords(truncated_desc)
        
        if before_keywords["count"] > 0:
            preservation_rate = after_keywords["count"] / before_keywords["count"] * 100
            keyword_preservation.append(preservation_rate)
    
    # Calculate aggregate stats
    results = {
        "before": calculate_length_stats(before_lengths),
        "after": calculate_length_stats(after_lengths),
        "reduction": calculate_length_stats(reduction_rates) if reduction_rates else {},
        "truncated_count": truncated_count,
        "truncated_percentage": round(truncated_count / len(descriptions) * 100, 2),
        "keyword_preservation": {
            "avg_rate": round(statistics.mean(keyword_preservation), 2) if keyword_preservation else 100,
            "min_rate": min(keyword_preservation) if keyword_preservation else 100,
            "descriptions_with_keywords": len(keyword_preservation),
        },
        "config": {
            "max_length": max_length,
            "total_descriptions": len(descriptions),
            "critical_keywords_tracked": len(CRITICAL_KEYWORDS),
        }
    }
    
    return results


def print_summary(analysis: Dict[str, Any]):
    """
    Prints a formatted summary table for console output.
    """
    before = analysis["before"]
    after = analysis["after"]
    reduction = analysis["reduction"]
    config = analysis["config"]
    
    print("\n" + "="*80)
    print("📊 DESCRIPTION LENGTH ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"\n🔧 Configuration:")
    print(f"   • Max Length Threshold: {config['max_length']} chars")
    print(f"   • Total Descriptions Analyzed: {config['total_descriptions']}")
    print(f"   • Critical Keywords Tracked: {config['critical_keywords_tracked']}")
    
    print(f"\n📏 Length Statistics (characters):")
    print(f"   {'Metric':<15} {'Before':>12} {'After':>12} {'Change':>12}")
    print(f"   {'-'*15} {'-'*12} {'-'*12} {'-'*12}")
    print(f"   {'Count':<15} {before['count']:>12,} {after['count']:>12,} {'-':>12}")
    print(f"   {'Min':<15} {before['min']:>12,} {after['min']:>12,} {'-':>12}")
    print(f"   {'Max':<15} {before['max']:>12,} {after['max']:>12,} {'-':>12}")
    print(f"   {'Mean (Avg)':<15} {before['mean']:>12,.1f} {after['mean']:>12,.1f} {-(before['mean']-after['mean']):>+11,.1f}")
    print(f"   {'Median':<15} {before['median']:>12,} {after['median']:>12,} {'-':>12}")
    print(f"   {'Std Dev':<15} {before['stdev']:>12,.1f} {after['stdev']:>12,.1f} {'-':>12}")
    
    if before.get('p90') and after.get('p90'):
        print(f"   {'90th Percentile':<15} {before['p90']:>12,} {after['p90']:>12,} {'-':>12}")
    if before.get('p95') and after.get('p95'):
        print(f"   {'95th Percentile':<15} {before['p95']:>12,} {after['p95']:>12,} {'-':>12}")
    if before.get('p99') and after.get('p99'):
        print(f"   {'99th Percentile':<15} {before['p99']:>12,} {after['p99']:>12,} {'-':>12}")
    
    print(f"\n📉 Reduction Statistics:")
    print(f"   • Descriptions Truncated: {analysis['truncated_count']} ({analysis['truncated_percentage']}%)")
    if reduction:
        print(f"   • Avg Reduction Rate: {reduction['mean']:.1f}%")
        print(f"   • Median Reduction: {reduction['median']:.1f}%")
        print(f"   • Max Reduction: {reduction['max']:.1f}%")
    
    print(f"\n🎯 Critical Keyword Preservation:")
    kp = analysis["keyword_preservation"]
    print(f"   • Descriptions with Keywords: {kp['descriptions_with_keywords']}")
    print(f"   • Avg Preservation Rate: {kp['avg_rate']:.1f}%")
    print(f"   • Min Preservation Rate: {kp['min_rate']:.1f}%")
    
    # Storage estimation
    before_total_bytes = before['mean'] * before['count']
    after_total_bytes = after['mean'] * after['count']
    storage_saved_mb = (before_total_bytes - after_total_bytes) / (1024 * 1024)
    
    print(f"\n💾 Storage Estimation (Neo4j):")
    print(f"   • Before: ~{before_total_bytes / (1024*1024):.1f} MB")
    print(f"   • After:  ~{after_total_bytes / (1024*1024):.1f} MB")
    print(f"   • Saved:  ~{storage_saved_mb:.1f} MB ({(1-after_total_bytes/before_total_bytes)*100:.1f}%)")
    
    # Quality rating
    avg_preservation = kp['avg_rate']
    if avg_preservation >= 95:
        rating = "🏆 EXCELLENT"
    elif avg_preservation >= 85:
        rating = "✅ GOOD"
    elif avg_preservation >= 70:
        rating = "⚠️  ACCEPTABLE"
    else:
        rating = "❌ NEEDS IMPROVEMENT"
    
    print(f"\n🏅 Overall Quality Rating: {rating}")
    print("="*80)


def save_report(analysis: Dict[str, Any], output_path: str):
    """
    Saves full analysis to JSON file for thesis appendix.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis,
        "methodology": {
            "smart_truncation_threshold": analysis["config"]["max_length"],
            "critical_keywords": CRITICAL_KEYWORDS,
            "ignore_list_size": len(IGNORE_LIST),
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full report saved to: {output_path}")


# ============================================
# MAIN
# ============================================
def main():
    print("🚀 Kubernetes Description Length Analyzer")
    print("="*80)
    
    # Step 1: Load descriptions
    try:
        descriptions = load_swagger_descriptions(SWAGGER_PATH)
    except FileNotFoundError:
        print(f"❌ ERROR: Swagger file not found at {SWAGGER_PATH}")
        print("   Download from: https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in swagger file: {e}")
        sys.exit(1)
    
    # Step 2: Analyze truncation
    analysis = analyze_truncation(descriptions, MAX_LENGTH)
    
    # Step 3: Print summary
    print_summary(analysis)
    
    # Step 4: Save report
    report_path = "logs/description_length_analysis.json"
    save_report(analysis, report_path)
    
    # Step 5: Thesis-ready conclusion
    print(f"\n📝 Thesis Conclusion (Bab 4):")
    kp = analysis["keyword_preservation"]
    storage_before = analysis["before"]["mean"] * analysis["before"]["count"] / (1024*1024)
    storage_after = analysis["after"]["mean"] * analysis["after"]["count"] / (1024*1024)
    
    print(f"   • Smart Truncation (2000 char) mengurangi panjang deskripsi rata-rata")
    print(f"     dari {analysis['before']['mean']:.0f} menjadi {analysis['after']['mean']:.0f} karakter.")
    print(f"   • {analysis['truncated_percentage']}% deskripsi memerlukan truncation.")
    print(f"   • {kp['avg_rate']:.1f}% informasi kritis (WARNING, DEPRECATED, dll) berhasil dipertahankan.")
    print(f"   • Estimasi penghematan storage Neo4j: {storage_before - storage_after:.1f} MB.")
    print(f"   • Kesimpulan: Smart Truncation adalah trade-off optimal untuk constraint budget.")


if __name__ == "__main__":
    main()