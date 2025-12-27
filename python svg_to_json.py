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
    
    # First, look for groups (provinces with multiple paths)
    for group in root.findall('.//svg:g', ns):
        group_id = group.get('id', f'province_{province_counter}')
        
        # Find all paths within this group
        paths = []
        for path in group.findall('.//svg:path', ns):
            path_data = path.get('d', '')
            if path_data:
                paths.append(path_data)
        
        if paths:  # Only add if it has paths
            province = {
                'id': group_id,
                'name': group_id.replace('_', ' ').title(),
                'owner': 'neutral',  # Default owner
                'color': '#CCCCCC',  # Default color
                'paths': paths,  # Multiple paths for complex shapes
                'type': 'group'
            }
            provinces.append(province)
            province_counter += 1
    
    # Then, look for individual paths not in groups
    for path in root.findall('.//svg:path', ns):
        # Skip if this path is already in a group we processed
        skip = False
        parent = path
        while parent is not None:
            parent = parent.getparent()
            if parent is not None and parent.tag.endswith('g'):
                # Check if this group's paths were already processed
                group_id = parent.get('id', '')
                if any(group_id == p['id'] for p in provinces):
                    skip = True
                    break
        
        if not skip:
            path_data = path.get('d', '')
            if path_data:
                province = {
                    'id': path.get('id', f'province_{province_counter}'),
                    'name': path.get('id', f'Province {province_counter}').replace('_', ' ').title(),
                    'owner': 'neutral',
                    'color': '#CCCCCC',
                    'paths': [path_data],  # Single path array
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
        # This is simplified - for production use a proper SVG parser
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
    svg_file_path = "EuropeSPD.svg"  # Change this to your actual file path
    
    # Check if file exists
    if not os.path.exists(svg_file_path):
        print(f"❌ Error: File '{svg_file_path}' not found!")
        print("Please place your SVG file in the same directory as this script,")
        print(f"or update the 'svg_file_path' variable to the correct location.")
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
    
    # Generate output filename based on input filename
    base_name = os.path.splitext(svg_file_path)[0]
    output_file = f"{base_name}_data.json"
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved to: {output_file}")
    print("\n📋 Next steps:")
    print("1. Open the JSON file to see your province data")
    print("2. Update 'owner' and 'color' fields for each province as needed")
    print("3. Use this JSON file in your application")
    
    # Show a sample of the data
    if provinces:
        print(f"\n📄 Sample province (first of {len(provinces)}):")
        sample = provinces[0].copy()
        # Truncate long path data for display
        if 'paths' in sample and len(sample['paths']) > 0:
            sample['paths'] = [sample['paths'][0][:50] + "..."] + [f"... and {len(sample['paths'])-1} more paths" if len(sample['paths']) > 1 else ""]
        print(json.dumps(sample, indent=2))

if __name__ == '__main__':
    main()
