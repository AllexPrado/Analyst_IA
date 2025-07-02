import json
import os
from collections import defaultdict

def analyze_cache_entities():
    """
    Analyze cache.json file to provide a detailed report on entities.
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
    section_details = {}
    
    # Count entities in each section and gather detailed information
    for section, data in cache_data.items():
        if section == "timestamp":
            # Store the timestamp separately
            timestamp = data
            continue
            
        if isinstance(data, list):
            count = len(data)
            entity_counts[section] = count
            total_entities += count
            
            # Collect details about entities
            if count > 0:
                section_details[section] = {
                    "count": count,
                    "entity_types": set(),
                    "entities": []
                }
                
                # Process each entity to collect names and types
                for entity in data:
                    if isinstance(entity, dict):
                        name = entity.get('name', 'Unknown')
                        guid = entity.get('guid', 'No GUID')
                        
                        # Try to determine entity type
                        entity_type = None
                        if 'type' in entity:
                            entity_type = entity['type']
                        elif 'entityType' in entity:
                            entity_type = entity['entityType']
                        
                        if entity_type:
                            section_details[section]["entity_types"].add(entity_type)
                            
                        section_details[section]["entities"].append({
                            "name": name,
                            "guid": guid,
                            "type": entity_type
                        })
        elif isinstance(data, dict):
            # For nested structures like alertas which might be a dictionary
            count = len(data)
            entity_counts[section] = count
            total_entities += count
            
            if count > 0:
                section_details[section] = {
                    "count": count,
                    "keys": list(data.keys())
                }
    
    # Print basic count report
    print("\n===== Cache Entity Count Report =====\n")
    print(f"Cache timestamp: {cache_data.get('timestamp', 'Not available')}")
    print(f"\n{'Section':<15} {'Entity Count':<15}")
    print("-" * 30)
    
    for section, count in sorted(entity_counts.items()):
        print(f"{section:<15} {count:<15}")
    
    print("-" * 30)
    print(f"{'TOTAL':<15} {total_entities:<15}")
    
    # Print detailed report
    print("\n===== Detailed Cache Entity Report =====\n")
    
    for section in sorted(section_details.keys()):
        details = section_details[section]
        print(f"\nSection: {section.upper()} ({details['count']} entities)")
        print("-" * 50)
        
        if details['count'] > 0:
            if 'entity_types' in details:
                if details['entity_types']:
                    print(f"Entity types: {', '.join(details['entity_types'])}")
                else:
                    print("No specific entity types found")
                    
                # List all entities
                print("\nEntities:")
                for i, entity in enumerate(details['entities'], 1):
                    print(f"{i}. {entity['name']} (GUID: {entity['guid']})")
                    if entity['type']:
                        print(f"   Type: {entity['type']}")
            elif 'keys' in details:
                print(f"Dictionary keys: {', '.join(details['keys'])}")
        else:
            print("No entities found in this section")
    
    # Save report to file
    report_path = 'cache_entity_report.txt'
    with open(report_path, 'w', encoding='utf-8') as report_file:
        report_file.write("===== Cache Entity Count Report =====\n\n")
        report_file.write(f"Cache timestamp: {cache_data.get('timestamp', 'Not available')}\n\n")
        report_file.write(f"{'Section':<15} {'Entity Count':<15}\n")
        report_file.write("-" * 30 + "\n")
        
        for section, count in sorted(entity_counts.items()):
            report_file.write(f"{section:<15} {count:<15}\n")
        
        report_file.write("-" * 30 + "\n")
        report_file.write(f"{'TOTAL':<15} {total_entities:<15}\n\n")
        
        report_file.write("===== Detailed Cache Entity Report =====\n\n")
        
        for section in sorted(section_details.keys()):
            details = section_details[section]
            report_file.write(f"\nSection: {section.upper()} ({details['count']} entities)\n")
            report_file.write("-" * 50 + "\n")
            
            if details['count'] > 0:
                if 'entity_types' in details:
                    if details['entity_types']:
                        report_file.write(f"Entity types: {', '.join(details['entity_types'])}\n")
                    else:
                        report_file.write("No specific entity types found\n")
                        
                    # List all entities
                    report_file.write("\nEntities:\n")
                    for i, entity in enumerate(details['entities'], 1):
                        report_file.write(f"{i}. {entity['name']} (GUID: {entity['guid']})\n")
                        if entity['type']:
                            report_file.write(f"   Type: {entity['type']}\n")
                elif 'keys' in details:
                    report_file.write(f"Dictionary keys: {', '.join(details['keys'])}\n")
            else:
                report_file.write("No entities found in this section\n")
    
    print(f"\nDetailed report saved to {report_path}")

if __name__ == "__main__":
    analyze_cache_entities()
