"""
Debug Script: Analyze Cross-References and IGNORE_LIST
========================================================
Shows:
1. Which $ref targets are NOT in definitions (cross-references)
2. Which definitions are skipped by IGNORE_LIST
3. Statistics about missing references
"""

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

SWAGGER_PATH = "data/kubernetes_swagger.json"

# Same IGNORE_LIST as parser.py
IGNORE_LIST = {
    "io.k8s.apimachinery.pkg.apis.meta.v1.ManagedFieldsEntry",
    "io.k8s.apimachinery.pkg.apis.meta.v1.ObjectMeta",
    "io.k8s.apimachinery.pkg.apis.meta.v1.StatusDetails",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Time",
    "io.k8s.apimachinery.pkg.apis.meta.v1.MicroTime",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Duration",
    "io.k8s.apimachinery.pkg.apis.meta.v1.RawExtension",
    "io.k8s.apimachinery.pkg.apis.meta.v1.FieldsV1",
    "io.k8s.apimachinery.pkg.apis.meta.v1.OwnerReference",
    "io.k8s.apimachinery.pkg.apis.meta.v1.Patch",
    "io.k8s.apimachinery.pkg.apis.meta.v1.StatusCause",
    "io.k8s.apimachinery.pkg.version.Info",
}

def main():
    print("="*80)
    print("🔍 DEBUG: Cross-References & IGNORE_LIST Analysis")
    print("="*80)
    
    # Load swagger
    print(f"\n📂 Loading Swagger file: {SWAGGER_PATH}")
    with open(SWAGGER_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    definitions = data.get('definitions', {})
    print(f"   ✓ Total definitions in swagger: {len(definitions)}")
    
    # ==================== 1. IGNORE_LIST ANALYSIS ====================
    print("\n" + "="*80)
    print("📋 IGNORE_LIST ANALYSIS")
    print("="*80)
    
    ignored_in_swagger = []
    for ignored in IGNORE_LIST:
        if ignored in definitions:
            ignored_in_swagger.append(ignored)
        else:
            print(f"   ⚠️  {ignored} - NOT in swagger (can be removed from IGNORE_LIST)")
    
    print(f"\n   ✓ Definitions skipped by IGNORE_LIST: {len(ignored_in_swagger)}")
    print(f"   📝 Skipped (10 ignored):")
    for i, ignored in enumerate(ignored_in_swagger[:10], 1):
        print(f"      {i:2}. {ignored}")
    if len(ignored_in_swagger) > 10:
        print(f"      ... and {len(ignored_in_swagger) - 10} more")
    
    # ==================== 2. CROSS-REFERENCE ANALYSIS ====================
    print("\n" + "="*80)
    print("🔗 CROSS-REFERENCE ANALYSIS")
    print("="*80)
    
    all_refs = set()
    refs_from_definitions = set()
    refs_from_ignored = set()
    
    # Collect all $ref targets
    for full_name, schema in definitions.items():
        is_ignored = full_name in IGNORE_LIST
        
        # Check properties
        properties = schema.get('properties', {})
        for field_name, field_schema in properties.items():
            # Direct $ref
            ref = field_schema.get('$ref')
            if ref:
                target = ref.split('/')[-1]
                all_refs.add(target)
                if is_ignored:
                    refs_from_ignored.add(target)
                else:
                    refs_from_definitions.add(target)
            
            # Array items $ref
            if field_schema.get('type') == 'array' and 'items' in field_schema:
                items = field_schema['items']
                if isinstance(items, dict) and '$ref' in items:
                    target = items['$ref'].split('/')[-1]
                    all_refs.add(target)
                    if is_ignored:
                        refs_from_ignored.add(target)
                    else:
                        refs_from_definitions.add(target)
            
            # additionalProperties $ref
            if field_schema.get('type') == 'object' and 'additionalProperties' in field_schema:
                add_props = field_schema['additionalProperties']
                if isinstance(add_props, dict) and '$ref' in add_props:
                    target = add_props['$ref'].split('/')[-1]
                    all_refs.add(target)
                    if is_ignored:
                        refs_from_ignored.add(target)
                    else:
                        refs_from_definitions.add(target)
        
        # Check allOf, oneOf, anyOf
        for key in ['allOf', 'oneOf', 'anyOf']:
            items = schema.get(key, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and '$ref' in item:
                        target = item['$ref'].split('/')[-1]
                        all_refs.add(target)
                        if is_ignored:
                            refs_from_ignored.add(target)
                        else:
                            refs_from_definitions.add(target)
    
    # Find missing references
    missing_refs = all_refs - set(definitions.keys())
    
    print(f"\n   📊 Reference Statistics:")
    print(f"      • Total unique $ref targets: {len(all_refs)}")
    print(f"      • Referenced from non-ignored definitions: {len(refs_from_definitions)}")
    print(f"      • Referenced from ignored definitions: {len(refs_from_ignored)}")
    print(f"      • Missing from definitions (cross-references): {len(missing_refs)}")
    
    # Categorize missing refs
    k8s_missing = []
    other_missing = []
    
    for ref in sorted(missing_refs):
        if ref.startswith('io.k8s.'):
            k8s_missing.append(ref)
        else:
            other_missing.append(ref)
    
    if k8s_missing:
        print(f"\n   ⚠️  MISSING K8s DEFINITIONS ({len(k8s_missing)}):")
        for i, ref in enumerate(k8s_missing[:20], 1):
            print(f"      {i:2}. {ref}")
        if len(k8s_missing) > 20:
            print(f"      ... and {len(k8s_missing) - 20} more")
    
    if other_missing:
        print(f"\n   ⚠️  MISSING NON-K8s DEFINITIONS ({len(other_missing)}):")
        for i, ref in enumerate(other_missing[:20], 1):
            print(f"      {i:2}. {ref}")
        if len(other_missing) > 20:
            print(f"      ... and {len(other_missing) - 20} more")
    
    # ==================== 3. WHICH DEFINITIONS REFERENCE MISSING REFS ====================
    print("\n" + "="*80)
    print("📍 DEFINITIONS THAT REFERENCE MISSING CROSS-REFERENCES")
    print("="*80)
    
    ref_to_definitions = {}
    for full_name, schema in definitions.items():
        if full_name in IGNORE_LIST:
            continue
        
        properties = schema.get('properties', {})
        for field_name, field_schema in properties.items():
            ref = field_schema.get('$ref')
            if ref:
                target = ref.split('/')[-1]
                if target in missing_refs:
                    if target not in ref_to_definitions:
                        ref_to_definitions[target] = []
                    ref_to_definitions[target].append(full_name)
            
            # Array items
            if field_schema.get('type') == 'array' and 'items' in field_schema:
                items = field_schema['items']
                if isinstance(items, dict) and '$ref' in items:
                    target = items['$ref'].split('/')[-1]
                    if target in missing_refs:
                        if target not in ref_to_definitions:
                            ref_to_definitions[target] = []
                        ref_to_definitions[target].append(full_name)
    
    print(f"\n   Found {len(ref_to_definitions)} missing refs that are referenced by definitions:\n")
    
    for i, (missing_ref, referencing_defs) in enumerate(sorted(ref_to_definitions.items())[:15], 1):
        print(f"   {i:2}. Missing: {missing_ref}")
        print(f"       Referenced by {len(referencing_defs)} definition(s):")
        for ref_def in referencing_defs[:5]:
            print(f"          • {ref_def}")
        if len(referencing_defs) > 5:
            print(f"          • ... and {len(referencing_defs) - 5} more")
        print()
    
    if len(ref_to_definitions) > 15:
        print(f"   ... and {len(ref_to_definitions) - 15} more missing refs")
    
    # ==================== 4. SUMMARY ====================
    print("\n" + "="*80)
    print("📝 SUMMARY")
    print("="*80)
    print(f"""
   • Total definitions in swagger: {len(definitions)}
   • Definitions in IGNORE_LIST: {len(ignored_in_swagger)}
   • Definitions that will be ingested: {len(definitions) - len(ignored_in_swagger)}
   
   • Total unique $ref targets: {len(all_refs)}
   • Missing cross-references: {len(missing_refs)}
   • Missing refs that are referenced: {len(ref_to_definitions)}
   
   • Parser will create placeholder nodes for: {len(ref_to_definitions)} cross-references
     (These will have source='k8s_swagger_cross_ref' and is_cross_reference=true)
    """)
    
    print("="*80)
    print("✅ Debug Complete!")
    print("="*80)

if __name__ == "__main__":
    main()