"""
Analisis #4: Impact of smart_truncate_description.
Justifikasi: Quantify token savings untuk LLM cost optimization.
"""
from typing import Any, Dict

import numpy as np
import matplotlib.pyplot as plt
from src.analysis.eda_base import EDABase
from src.utils.text_utils import safe_truncate_description
import re
from collections import Counter
from src.analysis.eda_base import EDABase

class TruncationEfficiencyAnalysis(EDABase):
    """Measure character/token reduction from smart truncation."""
    
    def extract(self) -> Dict[str, Any]:
        """
        Compare original vs truncated description lengths.
        Focus on outlier reduction (long descriptions).
        """
        original_lengths = []
        truncated_lengths = []
        
        for schema in self.definitions.values():
            desc = schema.get('description', '')
            if desc:  # Skip empty descriptions
                original_lengths.append(len(desc))
                truncated = safe_truncate_description(desc, hard_limit=4000)
                truncated_lengths.append(len(truncated))
        
        # Calculate savings
        savings = [o - t for o, t in zip(original_lengths, truncated_lengths)]
        
        return {
            'original': {
                'mean': np.mean(original_lengths),
                'median': np.median(original_lengths),
                'max': np.max(original_lengths),
                'std': np.std(original_lengths),
                'data': original_lengths
            },
            'truncated': {
                'mean': np.mean(truncated_lengths),
                'median': np.median(truncated_lengths),
                'max': np.max(truncated_lengths),
                'std': np.std(truncated_lengths),
                'data': truncated_lengths
            },
            'savings': {
                'mean_chars_saved': np.mean(savings),
                'total_chars_saved': sum(savings),
                'estimated_token_savings': sum(savings) // 4,  # ~4 chars/token
                'outliers_reduced': sum(1 for o in original_lengths if o > 4000)
            }
        }
    
    def visualize(self, output_path: str = "output/eda/TruncationEfficiencyAnalysis") -> None:
        """Overlapping histogram + boxplot: academic standard for distribution comparison."""
        import seaborn as sns
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Left: Overlapping histograms
        ax1.hist(
            [self.results['original']['data'], self.results['truncated']['data']],
            bins=50, label=['Original', 'Truncated'],
            color=['#A23B72', '#2E86AB'], alpha=0.7, density=True
        )
        ax1.set_xlabel('Description Length (characters)')
        ax1.set_ylabel('Density')
        ax1.set_title('Distribution Shift After Truncation')
        ax1.legend()
        ax1.axvline(x=4000, color='red', linestyle='--', label='Hard Limit')
        
        # Right: Boxplot comparison
        box_data = [
            self.results['original']['data'],
            self.results['truncated']['data']
        ]
        ax2.boxplot(box_data, labels=['Original', 'Truncated'], patch_artist=True,
                   boxprops=dict(facecolor='#2E86AB', color='black'),
                   medianprops=dict(color='white', linewidth=2))
        ax2.set_ylabel('Length (characters)')
        ax2.set_title('Outlier Reduction (Boxplot)')
        ax2.grid(axis='y', alpha=0.3)
        
        # Add annotation for token savings
        savings = self.results['savings']
        ax2.text(0.5, -0.15, 
                f"Mean saved: {savings['mean_chars_saved']:.0f} chars\n"
                f"Est. tokens saved: {savings['estimated_token_savings']:,}",
                ha='center', transform=ax2.transAxes,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(f"{output_path}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved: {output_path}.png")

"""
Analisis #5: Frequency of operational constraint keywords.
Justifikasi: Validasi bahwa truncation harus preserve semantic logic.
"""

class CriticalKeywordAnalysis(EDABase):
    """Count constraint keywords that must survive truncation."""
    
    CRITICAL_KEYWORDS = [
        'deprecated', 'immutable', 'must match', 'required', 
        'cannot be updated', 'defaults to', 'if unspecified'
    ]
    
    def extract(self) -> Dict[str, Any]:
        """
        Case-insensitive regex search across all descriptions.
        Track both frequency and which resources contain them.
        """
        keyword_counts = Counter()
        keyword_resources = {kw: [] for kw in self.CRITICAL_KEYWORDS}
        
        for full_name, schema in self.definitions.items():
            desc = schema.get('description', '').lower()
            short_name = full_name.split('.')[-1]
            
            for keyword in self.CRITICAL_KEYWORDS:
                # Use word boundaries for accurate matching
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = len(re.findall(pattern, desc))
                if matches > 0:
                    keyword_counts[keyword] += matches
                    keyword_resources[keyword].append(short_name)
        
        return {
            'keyword_frequencies': dict(keyword_counts),
            'keyword_resources': keyword_resources,
            'total_descriptions_with_constraints': sum(
                1 for kw in keyword_resources.values() if len(kw) > 0
            )
        }
    
    def visualize(self, output_path: str = "output/eda/CriticalKeywordAnalysis") -> None:
        """Simple table-style visualization: clarity over complexity."""
        import matplotlib.pyplot as plt
        import pandas as pd
        
        # Create DataFrame for clean display
        data = []
        for kw in self.CRITICAL_KEYWORDS:
            count = self.results['keyword_frequencies'].get(kw, 0)
            sample_resources = self.results['keyword_resources'][kw][:3]  # Top 3 examples
            data.append({
                'Keyword': f'"{kw}"',
                'Frequency': count,
                'Example Resources': ', '.join(sample_resources) if sample_resources else '-'
            })
        
        df = pd.DataFrame(data)
        
        # Create table visualization
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axis('tight')
        ax.axis('off')
        
        # Style table
        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='left',
            loc='center',
            colColours=['#2E86AB']*3,
            colWidths=[0.3, 0.2, 0.5]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Header styling
        for (i, j), cell in table.get_celld().items():
            if i == 0:  # Header row
                cell.set_text_props(weight='bold', color='white')
        
        ax.set_title(
            'Critical Constraint Keywords in Kubernetes Documentation\n'
            '(Must be preserved during text truncation)',
            fontsize=12, pad=20, weight='bold'
        )
        
        plt.tight_layout()
        plt.savefig(f"{output_path}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved: {output_path}.png")
        
        # Also export to CSV for thesis appendix
        df.to_csv(f"{output_path}.csv", index=False)