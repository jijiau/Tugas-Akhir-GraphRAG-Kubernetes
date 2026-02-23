from src.validation.auditor import GraphAuditor
import json

def main():
    print("Starting Full Graph Audit...")
    auditor = GraphAuditor()
    results = auditor.run_full_audit()
    
    # Save report for Thesis Appendix
    with open("validation_report.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"Audit Complete. Report saved to validation_report.json")
    print(f"Orphans: {results['orphan_resources']}")
    print(f"Node Counts: {results['total_nodes']}")

if __name__ == "__main__":
    main()