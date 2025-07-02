import json
import os
from collections import defaultdict

def count_cache_entities():
    """
    Analyze cache.json file to count entities in each section.
    """
    cache_path = os.path.join('backend', 'cache.json')
    
    if not os.path.exists(cache_path):
        print(f"Cache file not found at {cache_path}")
        return
    
    print(f"Reading cache file: {cache_path}")
    try:
        with open(cache_path, 'r', encoding='utf-8') as file:
            cache_data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Initialize counts
    entity_counts = {}
    total_entities = 0
    
    # Count entities in each section
    for section, data in cache_data.items():
        if section == "timestamp":
            # Skip timestamp, it's not an entity collection
            continue
            
        if isinstance(data, list):
            count = len(data)
            entity_counts[section] = count
            total_entities += count
        elif isinstance(data, dict):
            # For nested structures, count items in the dictionary
            count = len(data)
            entity_counts[section] = count
            total_entities += count
    
    # Print results
    print("\n===== Cache Entity Count Report =====\n")
    print(f"{'Section':<15} {'Entity Count':<15}")
    print("-" * 30)
    
    for section, count in sorted(entity_counts.items()):
        print(f"{section:<15} {count:<15}")
    
    print("-" * 30)
    print(f"{'TOTAL':<15} {total_entities:<15}")
    
    # Analyze entity structure for the first entity in each section
    print("\n===== Entity Structure Sample =====\n")
    for section, data in cache_data.items():
        if section == "timestamp":
            continue
            
        if isinstance(data, list) and data:
            print(f"\nSection: {section}")
            first_entity = data[0]
            if isinstance(first_entity, dict):
                print(f"  Sample entity keys: {', '.join(list(first_entity.keys())[:5])}")
                # Try to find an identifier field
                for id_field in ['id', 'name', 'guid', 'entityId', 'entity_id']:
                    if id_field in first_entity:
                        print(f"  Sample identifier ({id_field}): {first_entity[id_field]}")
                        break
            else:
                print(f"  Sample entity (non-dict): {str(first_entity)[:50]}")
        elif isinstance(data, dict) and data:
            print(f"\nSection: {section}")
            print(f"  Sample keys: {', '.join(list(data.keys())[:5])}")

if __name__ == "__main__":
    count_cache_entities()
