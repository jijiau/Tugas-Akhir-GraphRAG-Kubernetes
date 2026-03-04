"""
Smart Truncation Quality Test
==============================
Evaluates the effectiveness of smart_truncate_description function.

Metrics:
    1. Critical Info Preservation Rate
    2. Readability Score (sentence boundary)
    3. Length Reduction Efficiency
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.parser import smart_truncate_description

# ============================================
# TEST CASES (Real Kubernetes Descriptions)
# ============================================
TEST_CASES = [
    {
        "name": "PodSpec with WARNING at end",
        "original": """
        PodSpec defines the desired state of a Pod, including containers, 
        volumes, networking, and scheduling constraints. This is the core 
        building block of Kubernetes workloads. Most users will not need 
        to interact with PodSpec directly, instead using higher-level 
        controllers like Deployment or StatefulSet. The PodSpec is passed 
        to the kubelet which creates the actual container runtime.
        
        WARNING: Running containers as root is discouraged for security. 
        Always use securityContext to set runAsNonRoot: true.
        DEPRECATED: hostPID will be removed in v1.25, use hostProcesses instead.
        """,
        "expected_keywords": ["WARNING", "DEPRECATED"],
        "max_length": 300
    },
    {
        "name": "Container with IMMUTABLE field",
        "original": """
        Container represents a single application container that will be 
        created within a Pod. The container configuration includes image, 
        ports, environment variables, and volume mounts. Once a Pod is 
        scheduled, the container configuration cannot be changed.
        
        IMMUTABLE: This field cannot be updated after Pod creation. 
        To change container specs, you must delete and recreate the Pod.
        REQUIRED: At least one container must be specified in PodSpec.
        DEFAULTS TO: If not specified, image pull policy is Always.
        """,
        "expected_keywords": ["IMMUTABLE", "REQUIRED", "DEFAULTS TO"],
        "max_length": 250
    },
    {
        "name": "Service with RFC 1123 naming",
        "original": """
        Service defines a logical set of Pods and a policy to access them. 
        Services enable loose coupling between dependent Pods. The service 
        selector must match the Pod labels for traffic routing to work.
        
        MUST MATCH: The selector field must match labels on target Pods.
        RFC 1123: Service names must follow DNS subdomain naming rules.
        CIDR: ClusterIP must be a valid IP address within service CIDR range.
        """,
        "expected_keywords": ["MUST MATCH", "RFC 1123", "CIDR"],
        "max_length": 200
    },
    {
        "name": "Volume with MUTUALLY EXCLUSIVE options",
        "original": """
        Volume represents a named volume in a Pod that may be accessed by 
        any container in the Pod. Kubernetes supports multiple volume types: 
        emptyDir, hostPath, configMap, secret, persistentVolumeClaim, etc.
        
        MUTUALLY EXCLUSIVE: Only one volume source type may be specified.
        IGNORED IF: emptyDir is ignored when persistentVolumeClaim is set.
        AT LEAST ONE: A Pod must have at least one volume if using PVC.
        """,
        "expected_keywords": ["MUTUALLY EXCLUSIVE", "IGNORED IF", "AT LEAST ONE"],
        "max_length": 250
    },
    {
        "name": "Secret with BASE64 encoding",
        "original": """
        Secret stores sensitive data such as passwords, OAuth tokens, and 
        SSH keys. Secrets are mounted into Pods as files or environment 
        variables. All Secret data must be base64 encoded before storage.
        
        BASE64: All values in the 'data' field must be base64 encoded.
        SECURITY: Secrets are stored unencrypted in etcd by default.
        WARNING: Do not commit Secret manifests to version control.
        """,
        "expected_keywords": ["BASE64", "SECURITY", "WARNING"],
        "max_length": 200
    },
]


# ============================================
# EVALUATION FUNCTIONS
# ============================================
def evaluate_truncation(test_case, result):
    """
    Evaluates truncation quality with multiple metrics.
    """
    original = test_case["original"]
    expected_keywords = test_case["expected_keywords"]
    max_length = test_case["max_length"]
    
    # === Metric 1: Critical Info Preservation ===
    keywords_found = []
    keywords_missing = []
    
    for keyword in expected_keywords:
        if keyword in result:
            keywords_found.append(keyword)
        else:
            keywords_missing.append(keyword)
    
    preservation_rate = len(keywords_found) / len(expected_keywords) * 100
    
    # === Metric 2: Length Efficiency ===
    original_length = len(original)
    result_length = len(result)
    reduction_rate = (1 - result_length / original_length) * 100
    
    # === Metric 3: Readability (ends with sentence boundary) ===
    ends_properly = result.rstrip().endswith('.') or result.rstrip().endswith('...')
    
    # === Metric 4: Ellipsis Added (if truncated) ===
    has_ellipsis = result_length < original_length and result.rstrip().endswith('...')
    
    return {
        "test_name": test_case["name"],
        "original_length": original_length,
        "result_length": result_length,
        "max_length": max_length,
        "reduction_rate": f"{reduction_rate:.1f}%",
        "preservation_rate": f"{preservation_rate:.1f}%",
        "keywords_found": keywords_found,
        "keywords_missing": keywords_missing,
        "ends_properly": ends_properly,
        "has_ellipsis": has_ellipsis,
        "result": result
    }


def print_evaluation(evaluation):
    """
    Prints evaluation results in a readable format.
    """
    print("\n" + "="*70)
    print(f"📋 TEST: {evaluation['test_name']}")
    print("="*70)
    
    print(f"\n📏 Length:")
    print(f"   Original: {evaluation['original_length']} chars")
    print(f"   Result:   {evaluation['result_length']} chars (max: {evaluation['max_length']})")
    print(f"   Reduction: {evaluation['reduction_rate']}")
    
    print(f"\n🎯 Critical Info Preservation: {evaluation['preservation_rate']}")
    if evaluation['keywords_found']:
        print(f"   ✅ Found: {', '.join(evaluation['keywords_found'])}")
    if evaluation['keywords_missing']:
        print(f"   ❌ Missing: {', '.join(evaluation['keywords_missing'])}")
    
    print(f"\n📖 Readability:")
    print(f"   Ends with sentence boundary: {'✅' if evaluation['ends_properly'] else '❌'}")
    print(f"   Has ellipsis (...): {'✅' if evaluation['has_ellipsis'] else '❌'}")
    
    print(f"\n📄 Result Preview (first 200 chars):")
    print(f"   \"{evaluation['result'][:200]}...\"")


def generate_summary(evaluations):
    """
    Generates overall summary statistics.
    """
    total_tests = len(evaluations)
    avg_preservation = sum(
        float(e['preservation_rate'].rstrip('%')) for e in evaluations
    ) / total_tests
    avg_reduction = sum(
        float(e['reduction_rate'].rstrip('%')) for e in evaluations
    ) / total_tests
    tests_with_all_keywords = sum(
        1 for e in evaluations if len(e['keywords_missing']) == 0
    )
    tests_ending_properly = sum(
        1 for e in evaluations if e['ends_properly']
    )
    
    print("\n" + "="*70)
    print("📊 OVERALL SUMMARY")
    print("="*70)
    print(f"   Total Tests: {total_tests}")
    print(f"   Avg Critical Info Preservation: {avg_preservation:.1f}%")
    print(f"   Avg Length Reduction: {avg_reduction:.1f}%")
    print(f"   Tests with ALL Keywords Preserved: {tests_with_all_keywords}/{total_tests}")
    print(f"   Tests Ending Properly: {tests_ending_properly}/{total_tests}")
    print()
    
    # Quality Rating
    if avg_preservation >= 90 and tests_with_all_keywords == total_tests:
        print("   🏆 QUALITY: EXCELLENT (Ready for thesis)")
    elif avg_preservation >= 70:
        print("   ⚠️  QUALITY: GOOD (Minor improvements needed)")
    else:
        print("   ❌ QUALITY: NEEDS IMPROVEMENT (Adjust algorithm)")
    
    print("="*70)


def save_report(evaluations):
    """
    Saves evaluation results to JSON file for thesis appendix.
    """
    os.makedirs("logs", exist_ok=True)
    report_path = "logs/smart_truncation_test_report.json"
    
    report = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "total_tests": len(evaluations),
        "evaluations": evaluations,
        "summary": {
            "avg_preservation_rate": sum(
                float(e['preservation_rate'].rstrip('%')) for e in evaluations
            ) / len(evaluations),
            "tests_with_all_keywords": sum(
                1 for e in evaluations if len(e['keywords_missing']) == 0
            )
        }
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full report saved to: {report_path}")


# ============================================
# MAIN
# ============================================
def main():
    print("🚀 Smart Truncation Quality Test")
    print("="*70)
    
    evaluations = []
    
    for test_case in TEST_CASES:
        # Run truncation
        original_length = len(test_case["original"])
        result = smart_truncate_description(
            desc=test_case["original"],
            original_length=original_length,
            max_length=test_case["max_length"]
        )
        
        # Evaluate
        evaluation = evaluate_truncation(test_case, result)
        evaluations.append(evaluation)
        
        # Print results
        print_evaluation(evaluation)
    
    # Generate summary
    generate_summary(evaluations)
    
    # Save report
    save_report(evaluations)


if __name__ == "__main__":
    main()