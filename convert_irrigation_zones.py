#!/usr/bin/env python3
"""
Convert Irrigation Zones Flow from Legacy UI to Dashboard 2.0

This script:
1. Reads the original irrigation flow (420-irrigation-zones-ORIGINAL.json)
2. Converts ONLY UI nodes to Dashboard 2.0
3. Adds boolean conversion nodes for switches
4. Adds state tracking to global context
5. Preserves ALL automation nodes (zone-timer, zone in, run-gate, etc.)
6. Outputs converted flow (420-irrigation-zones-controls.json)
"""

import json
import sys
from pathlib import Path

def generate_id():
    """Generate a unique node ID"""
    import random
    import string
    return ''.join(random.choices(string.hexdigits.lower(), k=16))

def convert_ui_switch_to_dashboard2(node, group_id="ui_group_irrigation_zones"):
    """
    Convert ui_switch (legacy) to ui-switch (Dashboard 2.0)
    Returns: [ui-switch node, convert_to_bool node, convert_to_str node, store_state node]
    """
    zone_num = None
    if "switch" in node.get("label", "").lower():
        # Extract zone number from label like "switch 1"
        import re
        match = re.search(r'\d+', node.get("label", ""))
        if match:
            zone_num = match.group()
    elif "power" in node.get("label", "").lower():
        zone_num = "power"
    
    # Create convert to boolean node (MQTT → Dashboard)
    convert_to_bool_id = generate_id()
    convert_to_bool = {
        "id": convert_to_bool_id,
        "type": "change",
        "z": node["z"],
        "name": "ON/OFF to Boolean",
        "rules": [
            {
                "t": "change",
                "p": "payload",
                "pt": "msg",
                "from": "OFF",
                "fromt": "str",
                "to": "false",
                "tot": "bool"
            },
            {
                "t": "change",
                "p": "payload",
                "pt": "msg",
                "from": "ON",
                "fromt": "str",
                "to": "true",
                "tot": "bool"
            }
        ],
        "action": "",
        "property": "",
        "from": "",
        "to": "",
        "reg": False,
        "x": node["x"] + 200,
        "y": node["y"],
        "wires": [[node["id"]]]
    }
    
    # Create convert to string node (Dashboard → MQTT)
    convert_to_str_id = generate_id()
    convert_to_str = {
        "id": convert_to_str_id,
        "type": "change",
        "z": node["z"],
        "name": "Boolean to ON/OFF",
        "rules": [
            {
                "t": "change",
                "p": "payload",
                "pt": "msg",
                "from": "false",
                "fromt": "bool",
                "to": "OFF",
                "tot": "str"
            },
            {
                "t": "change",
                "p": "payload",
                "pt": "msg",
                "from": "true",
                "fromt": "bool",
                "to": "ON",
                "tot": "str"
            }
        ],
        "action": "",
        "property": "",
        "from": "",
        "to": "",
        "reg": False,
        "x": node["x"] + 200,
        "y": node["y"] + 60,
        "wires": [node["wires"][0] if node.get("wires") else [[]]]
    }
    
    # Create state tracking node
    store_state_id = generate_id()
    state_var = f"zone_{zone_num}" if zone_num and zone_num != "power" else "power_24v"
    store_state = {
        "id": store_state_id,
        "type": "function",
        "z": node["z"],
        "name": f"Store {state_var} State",
        "func": f"let state = global.get('irrigation_zones_state') || {{}};\nstate.{state_var} = msg.payload;\nglobal.set('irrigation_zones_state', state);\nreturn null;",
        "outputs": 0,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": node["x"] + 200,
        "y": node["y"] - 60,
        "wires": []
    }
    
    # Convert the ui_switch node to ui-switch
    ui_switch_node = node.copy()
    ui_switch_node["type"] = "ui-switch"
    ui_switch_node["group"] = group_id
    ui_switch_node["passthru"] = False
    ui_switch_node["decouple"] = True
    ui_switch_node["onvalue"] = "true"
    ui_switch_node["onvalueType"] = "bool"
    ui_switch_node["offvalue"] = "false"
    ui_switch_node["offvalueType"] = "bool"
    ui_switch_node["wires"] = [[convert_to_str_id]]
    # Remove old ui_switch properties
    ui_switch_node.pop("animate", None)
    
    return ui_switch_node, convert_to_bool, convert_to_str, store_state, convert_to_bool_id, store_state_id

def convert_ui_button_to_dashboard2(node, group_id="ui_group_irrigation_automation"):
    """Convert ui_button (legacy) to ui-button (Dashboard 2.0)"""
    ui_button_node = node.copy()
    ui_button_node["type"] = "ui-button"
    ui_button_node["group"] = group_id
    return ui_button_node

def convert_ui_text_to_dashboard2(node, group_id="ui_group_irrigation_automation"):
    """Convert ui_text (legacy) to ui-text (Dashboard 2.0)"""
    ui_text_node = node.copy()
    ui_text_node["type"] = "ui-text"
    ui_text_node["group"] = group_id
    # Dashboard 2.0 uses different properties
    ui_text_node.pop("style", None)
    ui_text_node.pop("font", None)
    ui_text_node.pop("fontSize", None)
    ui_text_node.pop("color", None)
    return ui_text_node

def update_mqtt_in_wires(node, convert_to_bool_id, store_state_id):
    """Update MQTT in node wires to include conversion and state tracking"""
    if node.get("wires") and len(node["wires"]) > 0:
        # Replace the first wire (to ui_switch) with conversion nodes
        node["wires"][0] = [convert_to_bool_id, store_state_id]
    return node

def convert_irrigation_flow(input_file, output_file):
    """Main conversion function"""
    print(f"Reading original flow from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        original_flow = json.load(f)
    
    print(f"Original flow has {len(original_flow)} nodes")
    
    converted_flow = []
    ui_switch_ids = {}  # Map old ui_switch ids to new conversion node ids
    mqtt_in_nodes_to_update = {}  # Track which MQTT nodes need wire updates
    
    # Add comment node
    converted_flow.append({
        "id": generate_id(),
        "type": "comment",
        "z": "tab_dashboard",
        "name": "═══════════════ IRRIGATION ZONES CONTROLS (Converted to Dashboard 2.0) ═══════════════",
        "info": "## 12-Zone Irrigation System\n\nConverted from legacy UI to Dashboard 2.0\nPreserves node-red-contrib-sprinkler automation\n\nDevice: IrigationSystem (Tasmota)\nZones: 12 (POWER2-5, POWER10-17)\nPower: POWER1 (24V)\nPump: pompaApa/Power1",
        "x": 340,
        "y": 40,
        "wires": []
    })
    
    # First pass: identify ui_switch nodes and create conversions
    for node in original_flow:
        node_type = node.get("type", "")
        
        if node_type == "ui_switch":
            print(f"  Converting ui_switch: {node.get('name', node.get('label', 'unnamed'))}")
            ui_switch, convert_bool, convert_str, store_state, bool_id, state_id = convert_ui_switch_to_dashboard2(node)
            
            # Store mapping
            ui_switch_ids[node["id"]] = {
                "bool_id": bool_id,
                "state_id": state_id,
                "ui_switch": ui_switch
            }
            
            converted_flow.extend([ui_switch, convert_bool, convert_str, store_state])
            
        elif node_type == "ui_button":
            print(f"  Converting ui_button: {node.get('label', 'unnamed')}")
            converted_flow.append(convert_ui_button_to_dashboard2(node))
            
        elif node_type == "ui_text":
            print(f"  Converting ui_text: {node.get('label', 'unnamed')}")
            converted_flow.append(convert_ui_text_to_dashboard2(node))
            
        elif node_type == "mqtt in":
            # Check if this MQTT node feeds a ui_switch
            if node.get("wires") and len(node["wires"]) > 0:
                target_id = node["wires"][0][0] if node["wires"][0] else None
                if target_id in ui_switch_ids:
                    # Mark for wire update
                    mqtt_in_nodes_to_update[node["id"]] = ui_switch_ids[target_id]
                    node["rap"] = True  # Enable retained message replay
            converted_flow.append(node)
            
        else:
            # Keep all other nodes as-is
            converted_flow.append(node)
    
    # Second pass: update MQTT in node wires
    for node in converted_flow:
        if node["id"] in mqtt_in_nodes_to_update:
            mapping = mqtt_in_nodes_to_update[node["id"]]
            node["wires"][0] = [mapping["bool_id"], mapping["state_id"]]
            print(f"  Updated MQTT in wiring for node: {node.get('name', node['id'])}")
    
    print(f"\nConverted flow has {len(converted_flow)} nodes")
    print(f"Writing converted flow to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_flow, f, indent=4)
    
    print("[OK] Conversion complete!")
    print("\nNext steps:")
    print("1. Import 420-irrigation-zones-controls.json into Node-RED")
    print("2. Deploy and test")
    print("3. Verify all 12 zones work correctly")
    print("4. Test automation (Start/Pause/Resume)")
    print("5. Check state tracking in global context")

if __name__ == "__main__":
    input_file = Path("nodered/flows/420-irrigation-zones-ORIGINAL.json")
    output_file = Path("nodered/flows/420-irrigation-zones-controls.json")
    
    if not input_file.exists():
        print(f"[ERROR] File not found: {input_file}")
        print("\nPlease paste your original irrigation flow into:")
        print(f"  {input_file.absolute()}")
        sys.exit(1)
    
    try:
        convert_irrigation_flow(input_file, output_file)
    except Exception as e:
        print(f"[ERROR] Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
