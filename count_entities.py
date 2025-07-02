import json
import os
import sys
from collections import Counter
from datetime import datetime

def load_cache():
    """Load the cache file and return the data."""
    cache_path = os.path.join("backend", "cache.json")
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Cache file not found at {cache_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Cache file at {cache_path} is not valid JSON")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading cache: {str(e)}")
        sys.exit(1)

def count_entities(cache_data):
    """Count the entities in the cache by category."""
    entity_counts = {}
    total_entities = 0
    
    # Count entities by category
    for category, entities in cache_data.items():
        if isinstance(entities, list):
            entity_counts[category] = len(entities)
            total_entities += len(entities)
        elif isinstance(entities, dict):
            # For nested structures
            entity_counts[category] = count_nested_entities(entities)
            total_entities += entity_counts[category]
    
    return entity_counts, total_entities

def count_nested_entities(data):
    """Count entities in nested structures."""
    if isinstance(data, list):
        return len(data)
    elif isinstance(data, dict):
        if "entities" in data and isinstance(data["entities"], list):
            return len(data["entities"])
        count = 0
        for key, value in data.items():
            if isinstance(value, list):
                count += len(value)
        return count
    return 0

def analyze_entity_fields(cache_data):
    """Analyze the fields present in entities and their completeness."""
    field_analysis = {}
    field_presence = Counter()
    entities_analyzed = 0
    
    for category, entities in cache_data.items():
        if isinstance(entities, list):
            for entity in entities:
                entities_analyzed += 1
                for field in entity.keys():
                    field_presence[field] += 1
        elif isinstance(entities, dict) and "entities" in entities:
            for entity in entities["entities"]:
                entities_analyzed += 1
                for field in entity.keys():
                    field_presence[field] += 1
    
    if entities_analyzed > 0:
        for field, count in field_presence.items():
            field_analysis[field] = {
                "count": count,
                "percentage": (count / entities_analyzed) * 100
            }
    
    return field_analysis, entities_analyzed

def generate_report(entity_counts, total_entities, field_analysis, entities_analyzed):
    """Generate a detailed report of the cache analysis."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_entities": total_entities,
        "entities_by_category": entity_counts,
        "field_analysis": {
            "entities_analyzed": entities_analyzed,
            "fields": field_analysis
        }
    }
    
    # Save report to file
    report_path = "cache_entity_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    return report, report_path

def print_report(report):
    """Print a human-readable report to the console."""
    print("\n===== CACHE ENTITY ANALYSIS REPORT =====")
    print(f"Timestamp: {report['timestamp']}")
    print(f"\nTotal Entities: {report['total_entities']}")
    
    print("\nEntities by Category:")
    for category, count in report["entities_by_category"].items():
        print(f"  - {category}: {count} entities")
    
    print(f"\nFields Analysis (based on {report['field_analysis']['entities_analyzed']} analyzed entities):")
    sorted_fields = sorted(report['field_analysis']['fields'].items(), 
                         key=lambda x: x[1]['percentage'], 
                         reverse=True)
    
    for field, stats in sorted_fields[:15]:  # Show top 15 most common fields
        print(f"  - {field}: {stats['count']} entities ({stats['percentage']:.1f}%)")
    
    if len(sorted_fields) > 15:
        print(f"  ... and {len(sorted_fields) - 15} more fields")

def main():
    print("Loading cache file...")
    cache_data = load_cache()
    
    print("Counting entities...")
    entity_counts, total_entities = count_entities(cache_data)
    
    print("Analyzing entity fields...")
    field_analysis, entities_analyzed = analyze_entity_fields(cache_data)
    
    print("Generating report...")
    report, report_path = generate_report(entity_counts, total_entities, field_analysis, entities_analyzed)
    
    print_report(report)
    print(f"\nDetailed report saved to: {report_path}")

if __name__ == "__main__":
    main()
