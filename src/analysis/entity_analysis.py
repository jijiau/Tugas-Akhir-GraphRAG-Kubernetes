"""
Analisis #1: Proporsi K8sResource vs SubResource.
Justifikasi: Memvalidasi desain graph dengan label is_root.
"""
from typing import Dict

import matplotlib.pyplot as plt
from torch import Any
from src.analysis.eda_base import EDABase
import re
from collections import Counter
import pandas as pd

class RootEntityAnalysis(EDABase):
    """Menghitung proporsi root resources vs komponen penyusun."""
    
    def extract(self) -> Dict[str, Any]:
        """
        Ekstraksi metrik berdasarkan atribut x-kubernetes-group-version-kind.
        GVK hanya ada pada root resources yang dapat di-deploy langsung.
        """
        total = len(self.definitions)
        root_count = sum(
            1 for schema in self.definitions.values()
            if schema.get('x-kubernetes-group-version-kind')
        )
        sub_count = total - root_count
        
        return {
            'total_definitions': total,
            'k8s_resources': root_count,
            'sub_resources': sub_count,
            'root_percentage': round(root_count / total * 100, 2),
            'sub_percentage': round(sub_count / total * 100, 2)
        }
    
    def visualize(self, output_path: str = "output/eda/RootEntityAnalysis") -> None:
        """Donut chart: kontras visual yang kuat untuk presentasi."""
        import matplotlib.pyplot as plt
        
        labels = ['K8sResource (Root)', 'SubResource (Component)']
        sizes = [self.results['k8s_resources'], self.results['sub_resources']]
        colors = ['#2E86AB', '#A23B72']  # Professional color palette
        
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=colors, startangle=90,
            wedgeprops=dict(width=0.5, edgecolor='white'),
            textprops={'fontsize': 11, 'weight': 'bold'}
        )
        # Styling autotexts untuk readability
        for autotext in autotexts:
            autotext.set_color('white')
        
        ax.set_title(
            f"Kubernetes Schema Composition\n(Total: {self.results['total_definitions']} definitions)",
            fontsize=14, pad=20, weight='bold'
        )
        ax.axis('equal')
        plt.tight_layout()
        plt.savefig(f"{output_path}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved: {output_path}.png")

"""
Analisis #2: Kepadatan relasi $ref.
Justifikasi: Mengapa Neo4j > SQL untuk data highly-interconnected.
"""


class RefDependencyAnalysis(EDABase):
    """Menganalisis tingkat interkoneksi melalui $ref references."""
    
    def extract(self) -> Dict[str, Any]:
        """
        Count semua $ref occurrences dan identifikasi hub nodes.
        $ref muncul di: properties, items (array), additionalProperties (map).
        """
        ref_pattern = r'\$ref\s*:\s*["\']?#/definitions/([^"\'\s}]+)'
        all_refs = []
        target_counter = Counter()
        
        for full_name, schema in self.definitions.items():
            # Recursive search untuk handle nested structures
            refs_in_schema = self._find_all_refs(schema, ref_pattern)
            all_refs.extend(refs_in_schema)
            # Count target nodes (in-degree untuk graph analysis)
            for ref in refs_in_schema:
                target_name = ref.split('/')[-1]
                target_counter[target_name] += 1
        
        total_refs = len(all_refs)
        total_defs = len(self.definitions)
        
        return {
            'total_ref_occurrences': total_refs,
            'avg_refs_per_definition': round(total_refs / total_defs, 2),
            'density_ratio': round(total_refs / total_defs, 2),  # >1 = highly connected
            'top_referenced': target_counter.most_common(10),
            'unique_targets': len(target_counter)
        }
    
    def _find_all_refs(self, obj: Any, pattern: str) -> list:
        """Recursive helper untuk extract $ref dari nested JSON."""
        refs = []
        if isinstance(obj, dict):
            # Direct $ref match
            if '$ref' in obj and isinstance(obj['$ref'], str):
                refs.append(obj['$ref'])
            # Recursive search in all values
            for value in obj.values():
                refs.extend(self._find_all_refs(value, pattern))
        elif isinstance(obj, list):
            for item in obj:
                refs.extend(self._find_all_refs(item, pattern))
        return refs
    
    def visualize(self, output_path: str = "output/eda/RefDependencyAnalysis") -> None:
        """Tabel + metric cards: fokus pada insight, bukan grafik rumit."""
        import matplotlib.pyplot as plt
        
        # Metric cards (text-based visualization)
        metrics = [
            f"Total $ref occurrences: {self.results['total_ref_occurrences']:,}",
            f"Average refs/definition: {self.results['avg_refs_per_definition']}",
            f"Graph density ratio: {self.results['density_ratio']}x",
            f"Unique target nodes: {self.results['unique_targets']}",
        ]
        
        # Top 5 most-referenced nodes (hubs)
        top_5 = self.results['top_referenced'][:5]
        df = pd.DataFrame(top_5, columns=['Node Name', 'In-Degree (References)'])
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Left: Metric cards
        ax1.axis('off')
        ax1.text(0.1, 0.9, "🔗 Reference Density Metrics", 
                fontsize=14, weight='bold', transform=ax1.transAxes)
        for i, metric in enumerate(metrics):
            ax1.text(0.1, 0.8 - i*0.12, f"• {metric}", 
                    fontsize=11, transform=ax1.transAxes,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # Right: Top 5 bar chart
        if top_5:
            names = [name.split('.')[-1] for name, _ in top_5]  # Short names
            counts = [count for _, count in top_5]
            ax2.barh(names, counts, color='#2E86AB')
            ax2.set_xlabel('Number of Incoming References')
            ax2.set_title('Top 5 Most-Referenced Components\n(Graph Hubs)')
            ax2.invert_yaxis()  # Highest on top
        
        plt.tight_layout()
        plt.savefig(f"{output_path}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved: {output_path}.png")
        
        # Also save as CSV for thesis appendix
        df.to_csv(f"{output_path}_top5.csv", index=False)