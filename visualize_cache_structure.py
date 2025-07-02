import json
import os
import matplotlib.pyplot as plt
from collections import Counter

def visualize_cache_structure():
    """
    Create visualizations of the cache structure and entity distribution.
    """
    cache_path = os.path.join('backend', 'cache.json')
    
    if not os.path.exists(cache_path):
        print(f"Cache file not found at {cache_path}")
        return
    
    print(f"Reading cache file: {cache_path}")
    try:
        with open(cache_path, 'r', encoding='utf-8') as file:
            cache_data = json.load(file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Get entity counts by domain
    domain_counts = {}
    total_entities = 0
    
    for domain, entities in cache_data.items():
        if domain == "timestamp":
            continue
        
        if isinstance(entities, list):
            count = len(entities)
            domain_counts[domain] = count
            total_entities += count
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    
    # Create bar chart
    plt.subplot(1, 2, 1)
    domains = list(domain_counts.keys())
    counts = [domain_counts[domain] for domain in domains]
    
    colors = ['#3498db' if count > 0 else '#95a5a6' for count in counts]
    
    plt.bar(domains, counts, color=colors)
    plt.title('Entity Count by Domain')
    plt.xlabel('Domain')
    plt.ylabel('Number of Entities')
    plt.xticks(rotation=45)
    
    # Add labels on top of bars
    for i, count in enumerate(counts):
        plt.text(i, count + 0.1, str(count), ha='center')
    
    # Create pie chart for domains with entities
    plt.subplot(1, 2, 2)
    non_empty_domains = {domain: count for domain, count in domain_counts.items() if count > 0}
    labels = non_empty_domains.keys()
    sizes = non_empty_domains.values()
    
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#3498db', '#e74c3c', '#2ecc71'])
    plt.axis('equal')
    plt.title('Distribution of Entities')
    
    plt.tight_layout()
    plt.savefig('cache_structure_visualization.png')
    print("Visualization saved as 'cache_structure_visualization.png'")
    
    # Generate a simple text-based visualization
    print("\nCache Structure Visualization:")
    print("=" * 50)
    print(f"Total Entities: {total_entities}")
    print("-" * 50)
    
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        bar_length = min(40, count * 4)  # Scale bar length
        if count > 0:
            bar = "#" * bar_length
        else:
            bar = "-" * 5
            
        print(f"{domain.upper():<12} | {count:>3} | {bar}")

if __name__ == "__main__":
    try:
        visualize_cache_structure()
    except Exception as e:
        print(f"Error during visualization: {e}")
        print("Note: This script requires matplotlib to be installed.")
        print("Install with: pip install matplotlib")
