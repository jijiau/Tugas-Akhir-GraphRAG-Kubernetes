"""
Exploratory Data Analysis: Kubernetes Swagger Specification
============================================================
Analyzes the structure and content of kubernetes_swagger.json
to understand the data before graph ingestion.

Purpose:
    - Thesis methodology documentation (Bab 3)
    - Data quality assessment (Bab 4)
    - Ingestion planning & optimization

Usage:
    python scripts/eda_swagger_analysis.py

Output:
    - Console summary tables
    - logs/eda_swagger_report.json (thesis appendix)
    - logs/eda_root_resources.csv (for manual review)
"""

import json
import os
import sys
import csv
import statistics
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


# ============================================
# CONFIGURATION
# ============================================
SWAGGER_PATH = "data/kubernetes_swagger.json"
OUTPUT_DIR = "logs"

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
def load_swagger(swagger_path: str) -> Dict[str, Any]:
    """Loads and parses the Kubernetes Swagger file."""
    print(f"📂 Loading Swagger file: {swagger_path}")
    
    with open(swagger_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   ✓ File size: {os.path.getsize(swagger_path) / (1024*1024):.2f} MB")
    return data


def analyze_definitions(definitions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comprehensive analysis of Kubernetes definitions.
    """
    print(f"\n🔍 Analyzing {len(definitions)} definitions...")
    
    results = {
        "total_definitions": len(definitions),
        "ignored_definitions": 0,
        "root_resources": [],
        "sub_resources": [],
        "kind_distribution": Counter(),
        "api_group_distribution": Counter(),
        "field_statistics_per_def": {},  # ✅ FIX: Separate per-definition stats
        "ref_statistics": {},
        "description_statistics": {},
        "gvk_analysis": {},
    }
    
    for full_name, schema in definitions.items():
        # Skip ignored definitions
        if full_name in IGNORE_LIST:
            results["ignored_definitions"] += 1
            continue
        
        # Extract basic info
        short_name = full_name.split(".")[-1]
        description = schema.get('description', '')
        properties = schema.get('properties', {})
        gvk_list = schema.get('x-kubernetes-group-version-kind', [])
        
        # === ROOT vs SUB-RESOURCE CLASSIFICATION ===
        is_root = len(gvk_list) > 0
        
        if is_root:
            first_gvk = gvk_list[0] if isinstance(gvk_list, list) and gvk_list else {}
            kind = first_gvk.get('kind', short_name) if isinstance(first_gvk, dict) else short_name
            group = first_gvk.get('group', 'core') if isinstance(first_gvk, dict) else 'core'
            version = first_gvk.get('version', 'v1') if isinstance(first_gvk, dict) else 'v1'
            
            results["root_resources"].append({
                "full_name": full_name,
                "short_name": short_name,
                "kind": kind,
                "api_group": group,
                "api_version": version,
                "description_length": len(description),
                "property_count": len(properties),
            })
            results["kind_distribution"][kind] += 1
            results["api_group_distribution"][group] += 1
        else:
            results["sub_resources"].append({
                "full_name": full_name,
                "short_name": short_name,
                "description_length": len(description),
                "property_count": len(properties),
            })
        
        # === FIELD STATISTICS ===
        field_types = Counter()
        ref_count = 0
        primitive_count = 0
        
        for field_name, field_schema in properties.items():
            field_type = field_schema.get('type')
            has_ref = '$ref' in field_schema
            
            if has_ref:
                ref_count += 1
                field_types['$ref'] += 1
            elif field_type:
                primitive_count += 1
                field_types[field_type] += 1
            
            # Handle array items
            if field_type == 'array' and 'items' in field_schema:
                items = field_schema['items']
                if isinstance(items, dict):
                    if '$ref' in items:
                        field_types['array<$ref>'] += 1
                    elif items.get('type'):
                        field_types[f"array<{items['type']}>"] += 1
        
        # ✅ FIX: Store per-definition stats in separate dict
        results["field_statistics_per_def"][full_name] = {
            "total_fields": len(properties),
            "ref_fields": ref_count,
            "primitive_fields": primitive_count,
            "field_type_distribution": dict(field_types),
        }
        
        # === DESCRIPTION STATISTICS ===
        desc_length = len(description)
        if "lengths" not in results["description_statistics"]:
            results["description_statistics"]["lengths"] = []
        results["description_statistics"]["lengths"].append(desc_length)
        
        # Check for critical keywords
        critical_keywords = ["WARNING", "DEPRECATED", "REQUIRED", "IMMUTABLE", "BASE64"]
        found_keywords = [kw for kw in critical_keywords if kw in description.upper()]
        if found_keywords:
            if "with_critical_keywords" not in results["description_statistics"]:
                results["description_statistics"]["with_critical_keywords"] = []
            results["description_statistics"]["with_critical_keywords"].append({
                "full_name": full_name,
                "keywords": found_keywords,
            })
        
        # === GVK ANALYSIS ===
        if gvk_list and isinstance(gvk_list, list):
            if "structure" not in results["gvk_analysis"]:
                results["gvk_analysis"]["structure"] = []
            results["gvk_analysis"]["structure"].append({
                "full_name": full_name,
                "gvk_count": len(gvk_list),
                "first_gvk_type": type(gvk_list[0]).__name__ if gvk_list else None,
            })
    
    # === AGGREGATE STATISTICS ===
    
    # Root vs Sub-resource counts
    results["root_count"] = len(results["root_resources"])
    results["sub_resource_count"] = len(results["sub_resources"])
    results["root_percentage"] = round(results["root_count"] / results["total_definitions"] * 100, 2)
    
    # Description length stats
    if results["description_statistics"]["lengths"]:
        lengths = results["description_statistics"]["lengths"]
        results["description_statistics"]["summary"] = {
            "min": min(lengths),
            "max": max(lengths),
            "mean": round(statistics.mean(lengths), 2),
            "median": statistics.median(lengths),
            "stdev": round(statistics.stdev(lengths), 2) if len(lengths) > 1 else 0,
        }
    
    # ✅ FIX: Field statistics aggregate (from per_def dict)
    all_field_counts = [s["total_fields"] for s in results["field_statistics_per_def"].values()]
    if all_field_counts:
        results["field_statistics"] = {  # ✅ Now separate from per_def
            "summary": {
                "avg_fields_per_definition": round(statistics.mean(all_field_counts), 2),
                "max_fields": max(all_field_counts),
                "min_fields": min(all_field_counts),
            }
        }
    
    # ✅ FIX: Ref statistics (from per_def dict)
    ref_counts = [s["ref_fields"] for s in results["field_statistics_per_def"].values()]
    if ref_counts:
        results["ref_statistics"]["summary"] = {
            "avg_refs_per_definition": round(statistics.mean(ref_counts), 2),
            "definitions_with_refs": sum(1 for c in ref_counts if c > 0),
        }
    
    return results

def print_summary(analysis: Dict[str, Any]):
    """Prints formatted EDA summary for console."""
    print("\n" + "="*80)
    print("📊 KUBERNETES SWAGGER EDA SUMMARY")
    print("="*80)
    
    print(f"\n🔧 Basic Statistics:")
    print(f"   • Total Definitions: {analysis['total_definitions']:,}")
    print(f"   • Ignored (noise): {analysis['ignored_definitions']}")
    print(f"   • Analyzed: {analysis['total_definitions'] - analysis['ignored_definitions']:,}")
    
    print(f"\n🎯 Root vs Sub-Resource Classification:")
    print(f"   • Root Resources (with GVK): {analysis['root_count']:,} ({analysis['root_percentage']}%)")
    print(f"   • Sub-Resources (schema types): {analysis['sub_resource_count']:,} ({100-analysis['root_percentage']:.2f}%)")
    
    print(f"\n📋 Top 10 Resource Kinds:")
    for kind, count in analysis['kind_distribution'].most_common(10):
        print(f"   • {kind}: {count}")
    
    print(f"\n🌐 Top 10 API Groups:")
    for group, count in analysis['api_group_distribution'].most_common(10):
        label = "core/v1" if group == "core" else f"{group}/*"
        print(f"   • {label}: {count}")
    
    print(f"\n📏 Description Length Statistics:")
    desc_stats = analysis['description_statistics'].get('summary', {})
    if desc_stats:
        print(f"   • Min: {desc_stats['min']:,} chars")
        print(f"   • Max: {desc_stats['max']:,} chars")
        print(f"   • Mean: {desc_stats['mean']:.1f} chars")
        print(f"   • Median: {desc_stats['median']:,} chars")
    
    print(f"\n🔗 Field Statistics:")
    # ✅ FIX: Access field_statistics.summary
    field_stats = analysis.get('field_statistics', {}).get('summary', {})
    if field_stats:
        print(f"   • Avg fields per definition: {field_stats['avg_fields_per_definition']}")
        print(f"   • Max fields: {field_stats['max_fields']}")
        print(f"   • Min fields: {field_stats['min_fields']}")
    
    # ✅ FIX: Access ref_statistics.summary
    ref_stats = analysis.get('ref_statistics', {}).get('summary', {})
    if ref_stats:
        print(f"   • Avg $ref per definition: {ref_stats['avg_refs_per_definition']}")
        print(f"   • Definitions with $ref: {ref_stats['definitions_with_refs']:,}")
    
    print(f"\n⚠️  Descriptions with Critical Keywords:")
    critical = analysis['description_statistics'].get('with_critical_keywords', [])
    if critical:
        keyword_counts = Counter()
        for item in critical:
            for kw in item['keywords']:
                keyword_counts[kw] += 1
        for kw, count in keyword_counts.most_common(5):
            print(f"   • {kw}: {count} definitions")
    else:
        print(f"   • None found")
    
    print(f"\n🔍 GVK Structure Analysis:")
    gvk_struct = analysis['gvk_analysis'].get('structure', [])
    if gvk_struct:
        type_counts = Counter(item['first_gvk_type'] for item in gvk_struct)
        for gvk_type, count in type_counts.most_common(5):
            print(f"   • {gvk_type}: {count} definitions")

def save_root_resources_csv(root_resources: List[Dict], output_path: str):
    """Saves root resources to CSV for manual review."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not root_resources:
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=root_resources[0].keys())
        writer.writeheader()
        writer.writerows(root_resources)
    
    print(f"\n💾 Root resources saved to: {output_path}")


def save_full_report(analysis: Dict[str, Any], output_path: str):
    """Saves complete EDA report to JSON for thesis appendix."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "swagger_path": SWAGGER_PATH,
        "basic_statistics": {
            "total_definitions": analysis["total_definitions"],
            "ignored_definitions": analysis["ignored_definitions"],
            "root_count": analysis["root_count"],
            "sub_resource_count": analysis["sub_resource_count"],
            "root_percentage": analysis["root_percentage"],
        },
        "kind_distribution": dict(analysis["kind_distribution"].most_common(20)),
        "api_group_distribution": dict(analysis["api_group_distribution"].most_common(20)),
        "description_statistics": {
            "summary": analysis["description_statistics"].get("summary", {}),
            "critical_keywords_count": len(analysis["description_statistics"].get("with_critical_keywords", [])),
        },
        # ✅ FIX: Access field_statistics.summary
        "field_statistics": analysis.get("field_statistics", {}).get("summary", {}),
        "ref_statistics": analysis.get("ref_statistics", {}).get("summary", {}),
        "thesis_insights": {
            "expected_graph_nodes": analysis["root_count"] + analysis["sub_resource_count"],
            "expected_root_resource_labels": len(analysis["kind_distribution"]),
            "complexity_indicator": f"{analysis.get('field_statistics', {}).get('summary', {}).get('avg_fields_per_definition', 0):.1f} fields/definition",
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Full EDA report saved to: {output_path}")

def print_thesis_narrative(analysis: Dict[str, Any]):
    """Prints thesis-ready narrative for Bab 3/4."""
    print(f"\n📝 Thesis Narrative (Bab 3 - Methodology):")
    print(f"   Berdasarkan EDA terhadap {analysis['total_definitions']:,} definisi dalam")
    print(f"   Kubernetes OpenAPI Specification, ditemukan:")
    print(f"   • {analysis['root_count']} resource Kubernetes yang dapat di-deploy mandiri (memiliki GVK)")
    print(f"   • {analysis['sub_resource_count']} tipe schema pendukung (tanpa GVK)")
    print(f"   • Rata-rata {analysis['field_statistics'].get('summary', {}).get('avg_fields_per_definition', 0):.1f} field per definisi")
    print(f"   • {len(analysis['kind_distribution'])} jenis resource kind yang unik")
    print()
    print(f"   Data ini menjadi dasar untuk desain graph schema dengan {analysis['root_count'] + analysis['sub_resource_count']} node")
    print(f"   dan estimasi {(analysis['field_statistics'].get('summary', {}).get('avg_fields_per_definition', 0) * (analysis['root_count'] + analysis['sub_resource_count']))/2:.0f} edge.")


# ============================================
# MAIN
# ============================================
def main():
    print("🚀 Kubernetes Swagger Exploratory Data Analysis")
    print("="*80)
    
    # Step 1: Load swagger
    try:
        data = load_swagger(SWAGGER_PATH)
    except FileNotFoundError:
        print(f"❌ ERROR: Swagger file not found at {SWAGGER_PATH}")
        print("   Download: https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON: {e}")
        sys.exit(1)
    
    # Step 2: Analyze definitions
    definitions = data.get('definitions', {})
    analysis = analyze_definitions(definitions)
    
    # Step 3: Print summary
    print_summary(analysis)
    
    # Step 4: Save outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save root resources CSV
    csv_path = os.path.join(OUTPUT_DIR, "eda_root_resources.csv")
    save_root_resources_csv(analysis["root_resources"], csv_path)
    
    # Save full JSON report
    json_path = os.path.join(OUTPUT_DIR, "eda_swagger_report.json")
    save_full_report(analysis, json_path)
    
    # Step 5: Print thesis narrative
    print_thesis_narrative(analysis)
    
    print("\n" + "="*80)
    print("✅ EDA Complete! Use these insights for:")
    print("   • Bab 3: Graph schema design justification")
    print("   • Bab 4: Data quality assessment")
    print("   • Ingestion: Expected node/edge counts")
    print("="*80)


if __name__ == "__main__":
    main()