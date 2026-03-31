"""
Analyze Cluster-Scope vs Namespace-Scope from Kubernetes OpenAPI Paths
========================================================================
This script analyzes the `paths` section of Kubernetes Swagger to determine
which resources are cluster-scoped vs namespace-scoped.

Purpose:
- Validate CLUSTER_SCOPED_RESOURCES hardcoded list
- Discover missing cluster-scoped resources
- Provide evidence for thesis defense

Usage:
    python scripts/analyze_cluster_scope.py
"""

import json
import re
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the hardcoded list from parser.py for comparison
from src.ingestion.parser import CLUSTER_SCOPED_RESOURCES

SWAGGER_PATH = "data/kubernetes_swagger.json"


def extract_scope_from_paths(paths):
    """
    Extract resource kinds from API paths and determine their scope.
    
    Namespace-scoped paths contain: /namespaces/{namespace}/
    Cluster-scoped paths do NOT contain: /namespaces/{namespace}/
    
    Example:
    - /api/v1/namespaces/{namespace}/pods → Namespace-scoped (Pod)
    - /api/v1/nodes → Cluster-scoped (Node)
    - /apis/apps/v1/namespaces/{namespace}/deployments → Namespace-scoped (Deployment)
    - /apis/apps/v1/deployments → Cluster-scoped (Deployment) [doesn't exist, just example]
    """
    resources = {
        'cluster_scoped': {},
        'namespace_scoped': {}
    }
    
    # Pattern to extract resource kind from path
    # Matches: /api/{version}/{resource} or /apis/{group}/{version}/{resource}
    # With optional /namespaces/{namespace}/ prefix
    namespace_pattern = re.compile(r'/namespaces/\{namespace\}/([a-z]+)(?:/|$)')
    cluster_pattern = re.compile(r'(?:/api|/apis)/[^/]+/[^/]+/([a-z]+)(?:/|$)')
    
    for path, methods in paths.items():
        # Skip non-resource paths (like /healthz, /version, etc.)
        if not (path.startswith('/api/') or path.startswith('/apis/')):
            continue
        
        # Skip subresources (like /status, /scale, /log, etc.)
        if any(sub in path for sub in ['/status', '/scale', '/log', '/exec', '/attach', 
                                        '/proxy', '/portforward', '/binding', '/eviction']):
            continue
        
        # Determine scope from path structure
        namespace_match = namespace_pattern.search(path)
        cluster_match = cluster_pattern.search(path)
        
        if namespace_match:
            # Namespace-scoped resource
            resource = namespace_match.group(1)
            if resource not in resources['namespace_scoped']:
                resources['namespace_scoped'][resource] = []
            if path not in resources['namespace_scoped'][resource]:
                resources['namespace_scoped'][resource].append(path)
        elif cluster_match:
            # Cluster-scoped resource
            resource = cluster_match.group(1)
            if resource not in resources['cluster_scoped']:
                resources['cluster_scoped'][resource] = []
            if path not in resources['cluster_scoped'][resource]:
                resources['cluster_scoped'][resource].append(path)
    
    return resources


def map_path_resource_to_kind(resource_name, definitions):
    """
    Map path resource name (e.g., 'deployments') to Kubernetes kind (e.g., 'Deployment').
    
    This uses the definitions section to find the correct kind name.
    """
    # Common mappings from path resource to kind
    kind_mappings = {
        'pods': 'Pod',
        'deployments': 'Deployment',
        'replicasets': 'ReplicaSet',
        'daemonsets': 'DaemonSet',
        'statefulsets': 'StatefulSet',
        'services': 'Service',
        'configmaps': 'ConfigMap',
        'secrets': 'Secret',
        'serviceaccounts': 'ServiceAccount',
        'roles': 'Role',
        'rolebindings': 'RoleBinding',
        'clusterroles': 'ClusterRole',
        'clusterrolebindings': 'ClusterRoleBinding',
        'persistentvolumes': 'PersistentVolume',
        'persistentvolumeclaims': 'PersistentVolumeClaim',
        'storageclasses': 'StorageClass',
        'nodes': 'Node',
        'namespaces': 'Namespace',
        'ingresses': 'Ingress',
        'horizontalpodautoscalers': 'HorizontalPodAutoscaler',
        'cronjobs': 'CronJob',
        'jobs': 'Job',
        'validatingwebhookconfigurations': 'ValidatingWebhookConfiguration',
        'mutatingwebhookconfigurations': 'MutatingWebhookConfiguration',
        'customresourcedefinitions': 'CustomResourceDefinition',
        'priorityclasses': 'PriorityClass',
        'csidrivers': 'CSIDriver',
        'csinodes': 'CSINode',
        'volumeattachments': 'VolumeAttachment',
        'runtimeclasses': 'RuntimeClass',
        'apiservices': 'APIService',
        'validatingadmissionpolicies': 'ValidatingAdmissionPolicy',
        'validatingadmissionpolicybindings': 'ValidatingAdmissionPolicyBinding',
        'endpoints': 'Endpoints',
        'componentstatuses': 'ComponentStatus',
        'events': 'Event',
        'limitranges': 'LimitRange',
        'resourcequotas': 'ResourceQuota',
        'podtemplates': 'PodTemplate',
        'replicationcontrollers': 'ReplicationController',
        'controllerrevisions': 'ControllerRevision',
        'networkpolicies': 'NetworkPolicy',
        'podsecuritypolicies': 'PodSecurityPolicy',
        'poddisruptionbudgets': 'PodDisruptionBudget',
        'csistoragecapacities': 'CSIStorageCapacity',
        'volumeattributesclasses': 'VolumeAttributesClass',
        'leases': 'Lease',
        'certificatesigningrequests': 'CertificateSigningRequest',
        'clustertrustbundles': 'ClusterTrustBundle',
        'tokenreviews': 'TokenReview',
        'subjectaccessreviews': 'SubjectAccessReview',
        'selfsubjectaccessreviews': 'SelfSubjectAccessReview',
        'selfsubjectrulesreviews': 'SelfSubjectRulesReview',
        'localsubjectaccessreviews': 'LocalSubjectAccessReview',
        'storageversions': 'StorageVersion',
        'workloads': 'Workload',
    }
    
    # Try direct mapping first
    if resource_name in kind_mappings:
        return kind_mappings[resource_name]
    
    # Try to find in definitions by searching for matching kind
    resource_singular = resource_name.rstrip('s')  # Remove trailing 's'
    for full_name, schema in definitions.items():
        gvk_list = schema.get('x-kubernetes-group-version-kind', [])
        if gvk_list and isinstance(gvk_list, list) and len(gvk_list) > 0:
            first_gvk = gvk_list[0]
            if isinstance(first_gvk, dict):
                kind = first_gvk.get('kind', '')
                # Check if kind matches (case-insensitive)
                if kind.lower() == resource_singular.lower() or kind.lower() == resource_name.lower():
                    return kind
    
    # Return as-is if no mapping found
    return resource_name.capitalize()


def compare_with_hardcoded_list(cluster_scoped_kinds, hardcoded_list):
    """
    Compare discovered cluster-scoped resources with hardcoded list.
    """
    results = {
        'agreed': [],
        'missing_from_hardcoded': [],
        'in_hardcoded_but_not_discovered': [],
    }
    
    # Check discovered cluster-scoped resources
    for kind in cluster_scoped_kinds:
        if kind in hardcoded_list:
            results['agreed'].append(kind)
        else:
            results['missing_from_hardcoded'].append(kind)
    
    # Check hardcoded list for resources not discovered
    for kind in hardcoded_list:
        if kind not in cluster_scoped_kinds:
            results['in_hardcoded_but_not_discovered'].append(kind)
    
    return results


def main():
    print("="*80)
    print("🔍 KUBERNETES CLUSTER-SCOPE ANALYSIS")
    print("="*80)
    print()
    
    # Load swagger
    print(f"📂 Loading Swagger file: {SWAGGER_PATH}")
    with open(SWAGGER_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    paths = data.get('paths', {})
    definitions = data.get('definitions', {})
    
    print(f"   ✓ Loaded {len(paths)} API paths")
    print(f"   ✓ Loaded {len(definitions)} definitions")
    print()
    
    # Extract scope from paths
    print("🔍 Analyzing paths for scope information...")
    scope_resources = extract_scope_from_paths(paths)
    
    cluster_scoped_resources = scope_resources['cluster_scoped']
    namespace_scoped_resources = scope_resources['namespace_scoped']
    
    print(f"   ✓ Found {len(cluster_scoped_resources)} cluster-scoped resource types")
    print(f"   ✓ Found {len(namespace_scoped_resources)} namespace-scoped resource types")
    print()
    
    # Map to kinds
    print("🔄 Mapping path resources to Kubernetes kinds...")
    cluster_scoped_kinds = set()
    for resource, path_list in cluster_scoped_resources.items():
        kind = map_path_resource_to_kind(resource, definitions)
        cluster_scoped_kinds.add(kind)
    
    namespace_scoped_kinds = set()
    for resource, path_list in namespace_scoped_resources.items():
        kind = map_path_resource_to_kind(resource, definitions)
        namespace_scoped_kinds.add(kind)
    
    print(f"   ✓ Mapped to {len(cluster_scoped_kinds)} cluster-scoped kinds")
    print(f"   ✓ Mapped to {len(namespace_scoped_kinds)} namespace-scoped kinds")
    print()
    
    # Compare with hardcoded list
    print("📊 Comparing with CLUSTER_SCOPED_RESOURCES hardcoded list...")
    comparison = compare_with_hardcoded_list(cluster_scoped_kinds, CLUSTER_SCOPED_RESOURCES)
    
    print()
    print("="*80)
    print("📋 ANALYSIS RESULTS")
    print("="*80)
    print()
    
    print(f"✅ AGREED - In both discovered and hardcoded ({len(comparison['agreed'])}):")
    for kind in sorted(comparison['agreed']):
        print(f"   • {kind}")
    print()
    
    print(f"⚠️  MISSING FROM HARDCODED - Discovered but not in list ({len(comparison['missing_from_hardcoded'])}):")
    if comparison['missing_from_hardcoded']:
        for kind in sorted(comparison['missing_from_hardcoded']):
            print(f"   • {kind}")
        print()
        print("   💡 RECOMMENDATION: Add these to CLUSTER_SCOPED_RESOURCES")
    else:
        print("   None! ✅ Hardcoded list is complete!")
    print()
    
    print(f"ℹ️  IN HARDCODED BUT NOT DISCOVERED ({len(comparison['in_hardcoded_but_not_discovered'])}):")
    if comparison['in_hardcoded_but_not_discovered']:
        for kind in sorted(comparison['in_hardcoded_but_not_discovered']):
            print(f"   • {kind}")
        print()
        print("   ℹ️  These may be valid but not exposed via standard API paths")
    else:
        print("   None! ✅ All hardcoded resources were discovered!")
    print()
    
    # Show detailed cluster-scoped resources
    print("="*80)
    print("📝 DETAILED CLUSTER-SCOPED RESOURCES")
    print("="*80)
    print()
    for resource in sorted(cluster_scoped_resources.keys()):
        paths = cluster_scoped_resources[resource]
        kind = map_path_resource_to_kind(resource, definitions)
        in_hardcoded = "✅" if kind in CLUSTER_SCOPED_RESOURCES else "❌"
        print(f"{in_hardcoded} {kind:45} ({resource})")
        for path in paths[:2]:  # Show first 2 paths
            print(f"      └─ {path}")
        if len(paths) > 2:
            print(f"      └─ ... and {len(paths) - 2} more paths")
    print()
    
    # Generate recommended CLUSTER_SCOPED_RESOURCES
    print("="*80)
    print("💡 RECOMMENDED CLUSTER_SCOPED_RESOURCES")
    print("="*80)
    print()
    print("# Copy this to src/ingestion/parser.py")
    print("CLUSTER_SCOPED_RESOURCES = {")
    all_cluster_kinds = sorted(cluster_scoped_kinds)
    for i, kind in enumerate(all_cluster_kinds):
        comma = "," if i < len(all_cluster_kinds) - 1 else ""
        print(f'    "{kind}"{comma}')
    print("}")
    print()
    
    # Summary for thesis
    print("="*80)
    print("📝 THESIS SUMMARY")
    print("="*80)
    print()
    print(f"Total cluster-scoped resources discovered: {len(cluster_scoped_kinds)}")
    print(f"Total namespace-scoped resources discovered: {len(namespace_scoped_kinds)}")
    print(f"Hardcoded list size: {len(CLUSTER_SCOPED_RESOURCES)}")
    print(f"Agreement rate: {len(comparison['agreed']) / len(CLUSTER_SCOPED_RESOURCES) * 100:.1f}%")
    print()
    
    if len(comparison['missing_from_hardcoded']) == 0:
        print("✅ CONCLUSION: CLUSTER_SCOPED_RESOURCES list is ACCURATE and COMPLETE!")
        print("   This can be cited in thesis as validated against OpenAPI paths.")
    else:
        print("⚠️  CONCLUSION: Some cluster-scoped resources are missing from hardcoded list.")
        print("   Update CLUSTER_SCOPED_RESOURCES with the missing kinds above.")
    print()
    
    # Save report
    report_path = "logs/cluster_scope_analysis_report.json"
    os.makedirs("logs", exist_ok=True)
    
    report = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "total_cluster_scoped": len(cluster_scoped_kinds),
        "total_namespace_scoped": len(namespace_scoped_kinds),
        "hardcoded_list_size": len(CLUSTER_SCOPED_RESOURCES),
        "agreed": sorted(comparison['agreed']),
        "missing_from_hardcoded": sorted(comparison['missing_from_hardcoded']),
        "in_hardcoded_but_not_discovered": sorted(comparison['in_hardcoded_but_not_discovered']),
        "recommended_list": all_cluster_kinds,
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Report saved to: {report_path}")
    print("="*80)


if __name__ == "__main__":
    main()