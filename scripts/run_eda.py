#!/usr/bin/env python3
"""
Unified runner untuk semua analisis EDA.
Usage: python scripts/run_eda.py --swagger path/to/swagger.json --output output/eda
"""
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.entity_analysis import RootEntityAnalysis, RefDependencyAnalysis
from src.analysis.schema_analysis import DataTypeDistributionAnalysis, SchemaRestrictionAnalysis
from src.analysis.text_analysis import TruncationEfficiencyAnalysis, CriticalKeywordAnalysis


def main():
    parser = argparse.ArgumentParser(description='Run Kubernetes Swagger EDA')
    parser.add_argument('--swagger', required=True, help='Path to swagger.json')
    parser.add_argument('--output', default='output/eda', help='Output directory')
    parser.add_argument('--analyses', nargs='*', 
                       default=['all'],
                       help='Specific analyses to run: root, ref, datatype, truncation, keyword, restriction')
    
    args = parser.parse_args()
    
    # Map analysis names to classes
    analyses = {
        'root': RootEntityAnalysis,
        'ref': RefDependencyAnalysis,
        'datatype': DataTypeDistributionAnalysis,
        'truncation': TruncationEfficiencyAnalysis,
        'keyword': CriticalKeywordAnalysis,
        'restriction': SchemaRestrictionAnalysis,
    }
    
    # Create output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    # Run selected analyses
    targets = analyses.keys() if 'all' in args.analyses else args.analyses
    
    for name in targets:
        if name not in analyses:
            print(f"⚠ Unknown analysis: {name}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Running: {name.upper()}")
        print('='*60)
        
        try:
            analysis = analyses[name](args.swagger)
            results = analysis.run(output_dir=args.output)
            print(f"✓ Completed: {name}")
        except Exception as e:
            print(f"✗ Failed: {name} - {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 All analyses complete. Outputs in: {args.output}/")


if __name__ == '__main__':
    main()