import xml.etree.ElementTree as ET
import json
import re
import os

def extract_provinces(svg_file):
    """Extract provinces from SVG file, handling both groups and individual paths"""
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # SVG namespace
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    provinces = []
    province_counter = 1
    processed_paths = set()  # Track paths we've already processed
    
    # First, look for groups (provinces with multiple paths)
    for group in root.findall('.//{http://www.w3.org/2000/svg}g'):
        group_id = group.get('id', f'province_{province_counter}')
        
        # Find all paths within this group
        paths = []
        for path in group.findall('.//{http://www.w3.org/2000/svg}path'):
            path_data = path.get('d', '')
            if path_data:
                paths.append(path_data)
                # Remember we processed this path
                processed_paths.add(id(path))
        
        if paths:  # Only add if it has paths
            province = {
                'id': group_id,
                'name': group_id.replace('_', ' ').title(),
                'owner': 'neutral',
                'color': '#CCCCCC',
                'paths': paths,
                'type': 'group'
            }
            provinces.append(province)
            province_counter += 1
    
    # Then, look for individual paths not in groups
    # We need to find all paths in the document
    for elem in root.iter():
        if elem.tag.endswith('}path') and id(elem) not in processed_paths:
            path_data = elem.get('d', '')
            if path_data:
                province = {
                    'id': elem.get('id', f'province_{province_counter}'),
                    'name': elem.get('id', f'Province {province_counter}').replace('_', ' ').title(),
                    'owner': 'neutral',
                    'color': '#CCCCCC',
                    'paths': [path_data],
                    'type': 'single'
                }
                provinces.append(province)
                province_counter += 1
    
    return provinces

def calculate_bounding_box(paths):
    """Calculate bounding box for all paths in a province"""
    all_coords = []
    for path in paths:
        # Extract coordinates from path data
        numbers = re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', path)
        for i in range(0, len(numbers), 2):
            if i+1 < len(numbers):
                try:
                    x = float(numbers[i])
                    y = float(numbers[i+1])
                    all_coords.append((x, y))
                except ValueError:
                    continue
    
    if all_coords:
        xs = [c[0] for c in all_coords]
        ys = [c[1] for c in all_coords]
        return {
            'min_x': min(xs),
            'min_y': min(ys),
            'max_x': max(xs),
            'max_y': max(ys),
            'center_x': (min(xs) + max(xs)) / 2,
            'center_y': (min(ys) + max(ys)) / 2
        }
    return None

def main():
    # === PUT YOUR SVG FILE PATH HERE ===
    svg_file_path = "EuropeSPD.svg"  # Should be in same folder
    
    # Check if file exists
    if not os.path.exists(svg_file_path):
        print(f"❌ Error: File '{svg_file_path}' not found!")
        print("Current directory files:")
        for file in os.listdir('.'):
            print(f"  - {file}")
        return
    
    print(f"📁 Processing: {svg_file_path}")
    
    # Process SVG and create JSON
    provinces = extract_provinces(svg_file_path)
    
    print(f"✅ Found {len(provinces)} provinces")
    
    # Add bounding boxes for each province
    for province in provinces:
        bbox = calculate_bounding_box(province['paths'])
        if bbox:
            province['bounding_box'] = bbox
    
    # Create the JSON structure
    output = {
        'metadata': {
            'type': 'map_data',
            'source_svg': os.path.basename(svg_file_path),
            'coordinate_system': 'SVG',
            'provinces_count': len(provinces),
            'version': '1.0'
        },
        'provinces': provinces
    }
    
    # Generate output filename
    base_name = os.path.splitext(svg_file_path)[0]
    output_file = f"{base_name}_data.json"
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved to: {output_file}")
    print("\n📋 Next steps:")
    print("1. Open the JSON file to see your province data")
    print("2. Update 'owner' and 'color' fields for each province as needed")
    
    # Show a sample
    if provinces:
        print(f"\n📄 Sample province (first of {len(provinces)}):")
        sample = provinces[0].copy()
        if 'paths' in sample and len(sample['paths']) > 0:
            sample['paths'] = [sample['paths'][0][:50] + "..."]
        print(json.dumps(sample, indent=2))

if __name__ == '__main__':
    main()
