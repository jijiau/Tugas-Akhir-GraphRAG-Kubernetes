"""
Analisis #3: Distribusi tipe data primitive.
Justifikasi: AI harus handle strict typing untuk valid YAML generation.
"""
from collections import Counter
from typing import Dict
import matplotlib.pyplot as plt
import numpy as np
from torch import Any
from src.analysis.eda_base import EDABase

class DataTypeDistributionAnalysis(EDABase):
    """Frequency analysis of OpenAPI primitive types."""
    
    PRIMITIVE_TYPES = {'string', 'integer', 'number', 'boolean', 'array', 'object'}
    
    def extract(self) -> Dict[str, Any]:
        """
        Traverse all properties dan collect type frequencies.
        Handle nested structures: array items, map additionalProperties.
        """
        type_counter = Counter()
        
        for schema in self.definitions.values():
            properties = schema.get('properties', {})
            for field_schema in properties.values():
                field_type = self._resolve_effective_type(field_schema)
                if field_type:
                    type_counter[field_type] += 1
        
        total = sum(type_counter.values())
        return {
            'type_counts': dict(type_counter),
            'total_properties': total,
            'percentages': {
                t: round(c/total*100, 1) 
                for t, c in type_counter.items()
            }
        }
    
    def _resolve_effective_type(self, field_schema: dict) -> str:
        """
        Resolve actual type considering arrays/maps.
        Example: array of string → 'array_of_string'
        """
        field_type = field_schema.get('type')
        
        # Handle array: check items type
        if field_type == 'array' and 'items' in field_schema:
            items = field_schema['items']
            if isinstance(items, dict):
                item_type = items.get('type', 'object')
                return f'array_of_{item_type}'
        
        # Handle map: check additionalProperties type
        if field_type == 'object' and 'additionalProperties' in field_schema:
            add_props = field_schema['additionalProperties']
            if isinstance(add_props, dict):
                prop_type = add_props.get('type', 'object')
                return f'map_of_{prop_type}'
        
        return field_type if field_type in self.PRIMITIVE_TYPES else None
    
    def visualize(self, output_path: str = "output/eda/DataTypeDistributionAnalysis") -> None:
        """Horizontal bar chart: easy comparison untuk presentasi."""
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Prepare data
        data = sorted(
            self.results['type_counts'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        labels = [f"{t}\n({self.results['percentages'][t]}%)" for t, _ in data]
        values = [v for _, v in data]
        
        # Plot
        plt.figure(figsize=(10, 6))
        sns.barplot(x=values, y=labels, palette='viridis')
        plt.xlabel('Frequency')
        plt.title('Kubernetes Schema: Primitive Type Distribution')
        plt.tight_layout()
        plt.savefig(f"{output_path}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved: {output_path}.png")

"""
Analisis #6: Strictness of required fields per resource.
Justifikasi: Why Pydantic validation is non-negotiable for AI-generated YAML.
"""
class SchemaRestrictionAnalysis(EDABase):
    """Analyze required field density across Kubernetes resources."""
    
    def extract(self) -> Dict[str, Any]:
        """
        Count required fields per definition.
        Focus on root resources (is_root=true) for practical relevance.
        """
        required_counts = {}
        
        for full_name, schema in self.definitions.items():
            required = schema.get('required', [])
            if required:  # Only track resources with constraints
                short_name = full_name.split('.')[-1]
                gvk = schema.get('x-kubernetes-group-version-kind', [])
                is_root = bool(gvk)
                
                required_counts[short_name] = {
                    'count': len(required),
                    'fields': required,
                    'is_root': is_root
                }
        
        # Sort by count descending
        sorted_counts = sorted(
            required_counts.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Calculate aggregate stats
        all_counts = [v['count'] for v in required_counts.values()]
        root_counts = [v['count'] for v in required_counts.values() if v['is_root']]
        
        return {
            'top_10_most_restrictive': sorted_counts[:10],
            'average_required_fields': round(np.mean(all_counts), 2),
            'average_for_root_resources': round(np.mean(root_counts), 2),
            'max_required_fields': max(all_counts),
            'total_resources_with_constraints': len(required_counts)
        }
    
    def visualize(self, output_path: str = "output/eda/SchemaRestrictionAnalysis") -> None:
        """Vertical bar chart: highlight top restrictive resources."""
        import matplotlib.pyplot as plt
        
        top_10 = self.results['top_10_most_restrictive']
        if not top_10:
            print("⚠ No resources with required fields found")
            return
        
        names = [name for name, _ in top_10]
        counts = [data['count'] for _, data in top_10]
        is_root = [data['is_root'] for _, data in top_10]
        
        # Color code: root resources vs sub-resources
        colors = ['#2E86AB' if root else '#A23B7280' for root in is_root]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(names)), counts, color=colors)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    str(count), ha='center', va='bottom', fontsize=9)
        
        plt.xticks(range(len(names)), names, rotation=45, ha='right', fontsize=9)
        plt.ylabel('Number of Required Fields')
        plt.title('Top 10 Most Restrictive Kubernetes Resources\n(Blue = Deployable Root Resource)')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_path}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved: {output_path}.png")
        
        # Print summary stats for thesis text
        print(f"\n📋 Schema Restriction Summary:")
        print(f"   • Average required fields: {self.results['average_required_fields']}")
        print(f"   • Average for root resources: {self.results['average_for_root_resources']}")
        print(f"   • Most restrictive: {top_10[0][0]} ({top_10[0][1]['count']} fields)")