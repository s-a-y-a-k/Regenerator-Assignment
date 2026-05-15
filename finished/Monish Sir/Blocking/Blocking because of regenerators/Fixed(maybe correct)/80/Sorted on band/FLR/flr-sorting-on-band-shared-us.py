import time
import random
import math
import copy
random.seed(42)
start_time = time.perf_counter()

# --- Core Network and RSA Setup ---
SLOTS = 760
graph = [
    [    0,  800, 99999, 99999, 99999, 1000, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [  800,    0, 1100, 99999, 99999,  950, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 1100,    0,  250,  800, 99999, 1000, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999,  250,    0,  800, 99999,  850, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999,  800,  800,    0, 99999, 99999, 1200, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [1000,  950, 99999, 99999, 99999,    0, 1000, 99999, 1200, 99999, 1900, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 1000,  850, 99999, 1000,    0, 1150, 1000, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 1200, 99999, 1150,    0, 99999,  900, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 1200, 1000, 99999,    0, 1000, 1400, 1000, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999,  900, 1000,    0, 99999, 99999,  950,  850, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 1900, 99999, 99999, 1400, 99999,    0,  900, 99999, 99999, 1300, 99999, 99999, 99999, 2600, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1000, 99999,  900,    0,  900, 99999, 99999, 1000, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999,  950, 99999,  900,    0,  650, 99999, 99999, 1100, 99999, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999,  850, 99999, 99999,  650,    0, 99999, 99999, 99999, 1200, 99999, 99999, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1300, 99999, 99999, 99999,    0,  600, 99999, 99999, 99999, 1300, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1000, 99999, 99999,  600,    0, 1000, 99999, 99999, 99999, 1000,  800, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1100, 99999, 99999, 1000,    0,  800, 99999, 99999, 99999,  850, 1000, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1200, 99999, 99999,  800,    0, 99999, 99999, 99999, 99999, 99999,  900],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 2600, 99999, 99999, 99999, 99999, 99999, 99999, 99999,    0, 1200, 99999, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1300, 99999, 99999, 99999, 1200,    0,  700, 99999, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1000, 99999, 99999, 99999,  700,    0,  300, 99999, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999,  800,  850, 99999, 99999, 99999,  300,    0,  600, 99999],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 1000, 99999, 99999, 99999, 99999,  600,    0,  900],
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999,  900, 99999, 99999, 99999, 99999,  900,    0]
]
nodes = [str(i + 1) for i in range(len(graph))]

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if 0 < graph[i][j] < 9999:
            edges.append((nodes[i], nodes[j]))

rsa = {frozenset(link): [{'status': 'free', 'request_id': []} for _ in range(SLOTS)] for link in edges}

mod_formats = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 4000},
    {'name': 'QPSK', 'capacity': 12.5, 'efficiency': 2, 'reach': 2000},
    {'name': '8-QAM', 'capacity': 12.5, 'efficiency': 3, 'reach': 1000},
    {'name': '16-QAM', 'capacity': 12.5, 'efficiency': 4, 'reach': 500},
    {'name': '32-QAM', 'capacity': 12.5, 'efficiency': 5, 'reach': 250}
]

# We need the max reach for the FLR algorithm
MAX_REACH = max(m['reach'] for m in mod_formats)


request_log = []
request_id_counter = 0
active_connections = {}
# NEW: Dictionary to track regenerator usage per node
regenerator_usage = {node: 0 for node in nodes}
# --- NEW: Regenerator limit ---
max_regenerators_at_a_node = 30
# --- NEW: Counters for Bandwidth Blocking Ratio ---
total_slots_requested_all_links = 0
total_slots_failed_all_links = 0

# --- Pathfinding and Modulation (Unchanged) ---
def find_shortest_path(source, destination, current_graph):
    n = len(current_graph)
    visited = [False] * n
    distance = [9999] * n
    previous = [None] * n
    distance[source] = 0
    for _ in range(n):
        min_distance = 9999
        u = -1
        for i in range(n):
            if not visited[i] and distance[i] < min_distance:
                min_distance, u = distance[i], i
        if u == -1: break
        visited[u] = True
        for v in range(n):
            if current_graph[u][v] > 0 and not visited[v]:
                new_dist = distance[u] + current_graph[u][v]
                if new_dist < distance[v]:
                    distance[v], previous[v] = new_dist, u
    path = []
    curr = destination
    if distance[curr] < 9999:
        while curr is not None:
            path.insert(0, curr)
            curr = previous[curr]
        return [nodes[i] for i in path], distance[destination]
    return None, None

def get_disjoint_path(primary_path, source, destination):
    temp_graph = copy.deepcopy(graph)
    for i in range(len(primary_path) - 1):
        u_idx, v_idx = nodes.index(primary_path[i]), nodes.index(primary_path[i+1])
        temp_graph[u_idx][v_idx] = 9999
        temp_graph[v_idx][u_idx] = 9999
    return find_shortest_path(source, destination, temp_graph)

def get_best_mod(distance):
    valid_mods = [m for m in mod_formats if m['reach'] >= distance]
    return max(valid_mods, key=lambda m: m['efficiency']) if valid_mods else None

def show_slots():
    """Prints a visual representation of the current slot usage on all links."""
    print("\nCurrent Slot Usage:")
    sorted_links = sorted(rsa.items(), key=lambda item: (min(nodes.index(n) for n in list(item[0])), max(nodes.index(n) for n in list(item[0]))))
    
    for link, slots in rsa.items():
        node_a, node_b = list(link)
        slot_display = []
        for slot_info in slots:
            if slot_info['status'] == 'free':
                slot_display.append('_')
            elif slot_info['status'] == 'primary':
                slot_display.append(f"P{slot_info['request_id']}")
            elif slot_info['status'] == 'backup':
                slot_display.append(f"B{slot_info['request_id']}")
            elif slot_info['status'] == 'guard':
                slot_display.append('G')
            elif slot_info['status'] == 'hybrid_backup':
                display_parts = []
                for x in slot_info['request_id']:
                    if x == 'G': 
                        display_parts.append('G')
                    else:
                        display_parts.append(f"B{x}")
                
                display_str = f"[{','.join(display_parts)}]"
                slot_display.append(display_str)
        print(f"{node_a} - {node_b} : {' '.join(slot_display)}")

# --- First Longest Reach (FLR) Regenerator Placement (Unchanged) ---
def place_flr_regenerators(path, bandwidth):
    """
    Implements the First Longest Reach (FLR) strategy for paths requiring regeneration.
    """
    if not path or len(path) < 2:
        return None
    
    segments = []
    current_node_idx = 0
    while current_node_idx < len(path) - 1:
        start_node_of_segment = path[current_node_idx]
        farthest_reach_idx = -1
        
        for next_node_idx in range(current_node_idx + 1, len(path)):
            sub_path = path[current_node_idx : next_node_idx + 1]
            dist = sum(graph[nodes.index(sub_path[i])][nodes.index(sub_path[i+1])] for i in range(len(sub_path)-1))
            
            if dist <= MAX_REACH:
                farthest_reach_idx = next_node_idx
            else:
                break 

        if farthest_reach_idx == -1:
            print(f"   FLR FAILED: Cannot reach from {path[current_node_idx]} to {path[current_node_idx+1]}.")
            return None
        
        final_segment_path = path[current_node_idx : farthest_reach_idx + 1]
        segment_dist = sum(graph[nodes.index(final_segment_path[i])][nodes.index(final_segment_path[i+1])] for i in range(len(final_segment_path)-1))
        
        mod = get_best_mod(segment_dist)
        if not mod: return None 
            
        slots_needed = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
        
        segments.append({
            'path': final_segment_path,
            'dist': segment_dist,
            'mod': mod['name'],
            'slots': slots_needed
        })
        
        current_node_idx = farthest_reach_idx

    return segments

# --- NEW: Helper function to calculate total link-slots ---
def calculate_total_link_slots(segments):
    """Calculates the total link-slots for a list of segments."""
    if not segments: return 0
    total_link_slots = 0
    for seg in segments:
        num_links_in_segment = len(seg['path']) - 1
        total_link_slots += seg['slots'] * num_links_in_segment
    return total_link_slots

# --- MODIFIED: Helper function to add/remove regenerator costs with limit ---
def update_regenerator_cost(segments, action='add'):
    """
    Updates the global 'regenerator_usage' dictionary.
    Checks against 'max_regenerators_at_a_node'.
    'action' can be 'add' or 'subtract'.
    Returns True on success, False on failure (only for 'add' action).
    """
    if not segments or len(segments) <= 1:
        return True # No regenerators to update, so it's a success

    regen_nodes_to_update = [seg['path'][-1] for seg in segments[:-1]]

    if action == 'add':
        # --- NEW: Check limits first ---
        for regen_node in regen_nodes_to_update:
            if regenerator_usage[regen_node] + 1 > max_regenerators_at_a_node:
                print(f"   FAILED: Regenerator limit ({max_regenerators_at_a_node}) exceeded at node {regen_node}.")
                return False # Failed to add
        
        # --- If check passes, add them ---
        for regen_node in regen_nodes_to_update:
             regenerator_usage[regen_node] += 1
        return True # Successfully added
    
    elif action == 'subtract':
        for regen_node in regen_nodes_to_update:
            if regenerator_usage[regen_node] > 0:
                regenerator_usage[regen_node] -= 1
        return True # Subtract always succeeds

# --- Allocation Logic with Spectrum Conversion (Unchanged) ---
def are_paths_disjoint(path1, path2):
    links1 = {frozenset([path1[i], path1[i+1]]) for i in range(len(path1)-1)}
    links2 = {frozenset([path2[i], path2[i+1]]) for i in range(len(path2)-1)}
    return links1.isdisjoint(links2)


def allocate_segments(segments, request_id, path_type, primary_path_of_this_request):
    if not segments: return None
    all_segment_allocations = []
    for seg_idx, seg in enumerate(segments):
        slots_needed = seg['slots']
        total_slots_with_guard = slots_needed + 1
        segment_allocated = False
        for start_slot in range(SLOTS - total_slots_with_guard + 1):
            is_block_available = True
            for i in range(len(seg['path']) - 1):
                link = frozenset([seg['path'][i], seg['path'][i+1]])
                for s in range(start_slot, start_slot + total_slots_with_guard):
                    slot_info = rsa[link][s]
                    if path_type == 'primary' and slot_info['status'] != 'free':
                        is_block_available = False
                        break
                    if path_type == 'backup':
                        if slot_info['status'] == 'primary' or (slot_info['status'] == 'guard' and rsa[link][s-1]['status'] == 'primary'):
                            is_block_available = False
                            break
                        if slot_info['status'] == 'backup' or (slot_info['status'] == 'guard' and rsa[link][s-1]['status'] == 'backup'):
                            other_req_id = slot_info['request_id'][0]
                            if other_req_id in active_connections:
                                other_primary_path = active_connections[other_req_id]['primary_path']
                                if not are_paths_disjoint(primary_path_of_this_request, other_primary_path):
                                    is_block_available = False
                                    break
                        if slot_info['status'] == 'hybrid_backup':
                            other_req_ids = [x for x in slot_info['request_id']]
                            check = True
                            for others in other_req_ids:
                                if others == 'G': continue # Skip guard marker
                                if others in active_connections:
                                    other_primary_path = active_connections[others]['primary_path']
                                    if not are_paths_disjoint(primary_path_of_this_request, other_primary_path):
                                        check = False
                                        is_block_available = False
                                        break
                            if check == False: break
                if not is_block_available: break
            if is_block_available:
                for i in range(len(seg['path']) - 1):
                    link = frozenset([seg['path'][i], seg['path'][i+1]])
                    for s in range(start_slot, start_slot + slots_needed):
                        if path_type == 'primary' and rsa[link][s]['status'] == 'free':
                           rsa[link][s]['status'] = path_type
                           rsa[link][s]['request_id'].append(request_id)
                        elif path_type == 'backup' and rsa[link][s]['status'] == 'free':
                           rsa[link][s]['status'] = path_type
                           rsa[link][s]['request_id'].append(request_id)
                        elif path_type == 'backup' and rsa[link][s]['status'] != 'free':
                            if rsa[link][s]['status'] == 'backup':
                                rsa[link][s]['status'] = 'hybrid_backup'
                                rsa[link][s]['request_id'].append(request_id)
                            elif rsa[link][s]['status'] == 'hybrid_backup':
                                rsa[link][s]['status'] = 'hybrid_backup'
                                rsa[link][s]['request_id'].append(request_id)
                            elif rsa[link][s]['status'] == 'guard':
                                rsa[link][s]['status'] = 'hybrid_backup'
                                rsa[link][s]['request_id'].append(request_id)
                    guard_slot_index = start_slot + slots_needed
                    if path_type == 'primary' and rsa[link][guard_slot_index]['status'] == 'free':
                        rsa[link][guard_slot_index]['status'] = 'guard'
                        rsa[link][guard_slot_index]['request_id'].append('G')
                    elif path_type == 'backup' and rsa[link][guard_slot_index]['status'] == 'free':
                        rsa[link][guard_slot_index]['status'] = 'guard'
                        rsa[link][guard_slot_index]['request_id'].append('G')
                    elif path_type == 'backup' and rsa[link][guard_slot_index]['status'] != 'free':
                        if rsa[link][guard_slot_index]['status'] == 'backup':
                            rsa[link][guard_slot_index]['status'] = 'hybrid_backup'
                            rsa[link][guard_slot_index]['request_id'].append('G')
                        elif rsa[link][guard_slot_index]['status'] == 'hybrid_backup':
                            rsa[link][guard_slot_index]['status'] = 'hybrid_backup'
                            rsa[link][guard_slot_index]['request_id'].append('G')
                        elif rsa[link][guard_slot_index]['status'] == 'guard' and rsa[link][guard_slot_index-1]['status'] != 'primary':
                            rsa[link][guard_slot_index]['status'] = 'hybrid_backup'
                            rsa[link][guard_slot_index]['request_id'].append('G')

                all_segment_allocations.append({'start_slot': start_slot, 'slots_needed': slots_needed})
                segment_allocated = True
                break
        if not segment_allocated:
            deallocate_path(segments[:seg_idx], all_segment_allocations, request_id, path_type)
            return None
    return all_segment_allocations

def deallocate_path(segments, allocations, request_id, path_type):
    """Robustly deallocates a path by removing its request_id and 'G' marker from slots."""
    if not segments or not allocations: return
    for seg, alloc in zip(segments, allocations):
        start = alloc['start_slot']
        slots_needed = seg['slots']
        end = start + slots_needed + 1 
        
        for i in range(len(seg['path']) - 1):
            link = frozenset([seg['path'][i], seg['path'][i+1]])
            for s in range(start, end):
                if s >= SLOTS: continue 
                
                slot_info = rsa[link][s]
                
                if request_id in slot_info['request_id']:
                    slot_info['request_id'].remove(request_id)
                
                is_guard_slot = (s == start + slots_needed)
                if is_guard_slot and 'G' in slot_info['request_id']:
                    slot_info['request_id'].remove('G')
                
                remaining_ids = len(slot_info['request_id'])
                if remaining_ids == 0:
                    slot_info['status'] = 'free'
                elif remaining_ids == 1 and 'G' not in slot_info['request_id']:
                    slot_info['status'] = 'backup'

# --- Logic to decide on regeneration strategy (Unchanged) ---
def process_path_for_segments(path, path_dist, bandwidth):
    best_mod_for_whole_path = get_best_mod(path_dist)

    if best_mod_for_whole_path:
        slots_needed = math.ceil(bandwidth / (best_mod_for_whole_path['capacity'] * best_mod_for_whole_path['efficiency']))
        return [{
            'path': path,
            'dist': path_dist,
            'mod': best_mod_for_whole_path['name'],
            'slots': slots_needed
        }]
    else:
        return place_flr_regenerators(path, bandwidth)

# --- MODIFIED: Helper function to prepare request details ---
def prepare_request(source, destination):
    global request_id_counter, total_slots_requested_all_links, total_slots_failed_all_links
    request_id_counter += 1
    req_id = request_id_counter
    print(f"\n--- Preparing Request #{req_id}: {nodes[source]} -> {nodes[destination]} ---")
    bandwidth = 80
    log_entry = {'id': req_id, 'source': nodes[source], 'destination': nodes[destination], 'bandwidth': bandwidth, 'success': False, 'reason': ''}

    filtered_graph = copy.deepcopy(graph)
    for i in range(len(graph)):
        for j in range(len(graph)):
            if filtered_graph[i][j] > MAX_REACH:
                filtered_graph[i][j] = 99999

    primary_path, primary_dist = find_shortest_path(source, destination, filtered_graph)
    if not primary_path:
        log_entry['reason'] = "No viable primary path found (all routes have unreachable segments)."
        print(f"FAILED: {log_entry['reason']}")
        # No rollback needed, nothing was added
        return None, log_entry, None, None, None, None, None, None

    backup_temp_graph = copy.deepcopy(filtered_graph)
    for i in range(len(primary_path) - 1):
        u_idx, v_idx = nodes.index(primary_path[i]), nodes.index(primary_path[i+1])
        backup_temp_graph[u_idx][v_idx] = 99999
        backup_temp_graph[v_idx][u_idx] = 99999
    backup_path, backup_dist = find_shortest_path(source, destination, backup_temp_graph)
    
    if not backup_path:
        log_entry['reason'] = "No link-disjoint viable backup path found."
        print(f"FAILED: {log_entry['reason']}")
        # No rollback needed, nothing was added
        return None, log_entry, None, None, None, None, None, None
    
    # --- Planning and Cost Update ---
    primary_segments = process_path_for_segments(primary_path, primary_dist, bandwidth)
    if not primary_segments:
        log_entry['reason'] = "Could not place regenerators on primary path."
        print(f"FAILED: {log_entry['reason']}")
        return None, log_entry, None, None, None, None, None, None
    
    backup_segments = process_path_for_segments(backup_path, backup_dist, bandwidth)
    
    if not backup_segments:
        log_entry['reason'] = "Could not place regenerators on backup path."
        print(f"FAILED: {log_entry['reason']}")
        # No rollback needed, nothing was added
        return None, log_entry, None, None, None, None, None, None
    
    # --- NEW: Calculate link-slots and update total requests ---
    p_link_slots = calculate_total_link_slots(primary_segments)
    b_link_slots = calculate_total_link_slots(backup_segments)
    total_slots_requested_all_links += (p_link_slots + b_link_slots)

    # --- NEW: Tentatively add primary regenerator costs and check limit ---
    if not update_regenerator_cost(primary_segments, 'add'):
        log_entry['reason'] = "Regenerator limit exceeded on primary path."
        # Print is now inside update_regenerator_cost
        total_slots_failed_all_links += (p_link_slots + b_link_slots) # Add to failed
        return None, log_entry, None, None, None, None, None, None
    
    # --- NEW: Tentatively add backup regenerator costs and check limit ---
    if not update_regenerator_cost(backup_segments, 'add'):
        log_entry['reason'] = "Regenerator limit exceeded on backup path."
        # Print is now inside update_regenerator_cost
        total_slots_failed_all_links += (p_link_slots + b_link_slots) # Add to failed
        # NEW: Roll back the primary cost because the request failed
        update_regenerator_cost(primary_segments, 'subtract') 
        return None, log_entry, None, None, None, None, None, None
    
    # MODIFIED: Return all data instead of logging
    return req_id, log_entry, primary_path, backup_path, primary_segments, backup_segments, p_link_slots, b_link_slots

# --- Helper function to update regenerator counts (Unchanged) ---
def update_final_regenerator_counts():
    for req_id, conn_info in active_connections.items():
        if conn_info['success']:
            # Primary path regenerators
            primary_segments = conn_info.get('primary_details', [])
            if len(primary_segments) > 1:
                for i in range(len(primary_segments) - 1): # Exclude the final destination
                    regenerator_node = primary_segments[i]['path'][-1]
                    regenerator_usage[regenerator_node] += 1
            
            # Backup path regenerators
            backup_segments = conn_info.get('backup_details', [])
            if len(backup_segments) > 1:
                for i in range(len(backup_segments) - 1): # Exclude the final destination
                    regenerator_node = backup_segments[i]['path'][-1]
                    regenerator_usage[regenerator_node] += 1

# --- Main Execution Loop (MODIFIED) ---

# --- Phase 1: Request Generation and Sorting ---
print("\n" + "="*20 + " Phase 1: Request Generation and Sorting " + "="*20)
all_requests_data = []

for i in range(len(graph)):
    for j in range(len(graph)):
        if i == j: continue

        # --- MODIFIED: Unpack new link-slot values ---
        req_id, log_entry, p_path, b_path, p_segments, b_segments, p_link_slots, b_link_slots = prepare_request(i, j)
        
        if not req_id:
            # This request failed pathfinding or regenerator limits. Log it.
            # Failure counters were already updated in prepare_request.
            request_log.append(log_entry)
            continue
        
        # Store data for sorting. Costs were already added in prepare_request.
        p_path_len = len(p_path) 
        b_path_len = len(b_path)
        bandwidth = log_entry['bandwidth'] # <-- Store bandwidth
        
        all_requests_data.append({
            'req_id': req_id,
            'log_entry': log_entry,
            'p_path': p_path,
            'b_path': b_path,
            'p_segments': p_segments,
            'b_segments': b_segments,
            'p_path_len': p_path_len,
            'b_path_len': b_path_len,
            'bandwidth': bandwidth, # <-- Add bandwidth to dictionary
            'p_link_slots': p_link_slots, # <-- NEW
            'b_link_slots': b_link_slots  # <-- NEW
        })

# Now, perform the sort based on user criteria:
# 1. Bandwidth (descending)
# 2. Primary path length (descending)
# 3. Backup path length (descending)
# 4. Request ID (ascending - for "first come first serve")
all_requests_data.sort(key=lambda x: (-x['bandwidth'], -x['p_path_len'], -x['b_path_len'], x['req_id'])) # <-- MODIFIED SORT KEY

print(f"Generated and sorted {len(all_requests_data)} viable requests.")


# --- Phase 2: Primary Path Allocation (from sorted list) ---
print("\n" + "="*20 + " Phase 2: Primary Path Allocation " + "="*20)
pending_backup_req_ids = []

for req_data in all_requests_data:
    # Extract data from the sorted item
    req_id = req_data['req_id']
    log_entry = req_data['log_entry']
    p_path = req_data['p_path']
    b_path = req_data['b_path']
    p_segments = req_data['p_segments']
    b_segments = req_data['b_segments']
    p_link_slots = req_data['p_link_slots'] # <-- NEW
    b_link_slots = req_data['b_link_slots'] # <-- NEW
    
    p_allocations = allocate_segments(p_segments, req_id, 'primary', None)

    if p_allocations:
        # Add a print to show the sorting is working
        print(f"Request #{req_id}: Primary path SUCCESS (BW:{req_data['bandwidth']}, P_len:{req_data['p_path_len']}, B_len:{req_data['b_path_len']}). Queued for backup.")
        connection_info = {
            'primary_path': p_path, 'primary_details': p_segments, 'primary_allocations': p_allocations,
            'backup_path': b_path, 'backup_details': b_segments, 'backup_allocations': None,
            'success': False, # Not fully successful until backup is allocated
            'p_link_slots': p_link_slots, # <-- NEW
            'b_link_slots': b_link_slots  # <-- NEW
        }
        active_connections[req_id] = connection_info
        log_entry.update(connection_info)
        request_log.append(log_entry)
        pending_backup_req_ids.append(req_id)
        # Costs are correctly kept
    else:
        # Add a print to show the sorting is working
        print(f"Request #{req_id}: Primary path FAILED (BW:{req_data['bandwidth']}, P_len:{req_data['p_path_len']}, B_len:{req_data['b_path_len']}). No spectrum.")
        log_entry['reason'] = "No spectrum available for primary path."
        request_log.append(log_entry)
        
        # --- NEW: Update failed slots counter ---
        total_slots_failed_all_links += (p_link_slots + b_link_slots)
        
        # --- NEW: Roll back both planned costs ---
        # The request failed spectrum, so we must remove the regenerator costs
        # that were tentatively added during prepare_request.
        update_regenerator_cost(p_segments, 'subtract')
        update_regenerator_cost(b_segments, 'subtract')


# --- Phase 3: Group Pending Backups into Mutually Exclusive Sets ---
# (This was Phase 2 in the original file)
print("\n" + "="*20 + " Phase 3: Grouping Backup Paths " + "="*20)
mutually_exclusive_sets = []

for req_id_to_place in pending_backup_req_ids:
    p_new = active_connections[req_id_to_place]['primary_path']
    b_new_path = active_connections[req_id_to_place]['backup_path']
    b_new_links = {frozenset([b_new_path[i], b_new_path[i+1]]) for i in range(len(b_new_path)-1)}
    
    candidate_sets = []

    for set_idx, current_set in enumerate(mutually_exclusive_sets):
        is_primary_disjoint_with_all = True
        is_backup_sharing_link = False

        for existing_req_id in current_set:
            p_existing = active_connections[existing_req_id]['primary_path']
            if not are_paths_disjoint(p_new, p_existing):
                is_primary_disjoint_with_all = False
                break
        if not is_primary_disjoint_with_all:
            continue
        
        for existing_req_id in current_set:
            b_existing_path = active_connections[existing_req_id]['backup_path']
            b_existing_links = {frozenset([b_existing_path[i], b_existing_path[i+1]]) for i in range(len(b_existing_path)-1)}
            if not b_new_links.isdisjoint(b_existing_links):
                is_backup_sharing_link = True
                break
        
        if is_primary_disjoint_with_all and is_backup_sharing_link:
            total_shared_links = 0
            for existing_req_id in current_set:
                b_existing_path = active_connections[existing_req_id]['backup_path']
                b_existing_links = {frozenset([b_existing_path[i], b_existing_path[i+1]]) for i in range(len(b_existing_path)-1)}
                total_shared_links += len(b_new_links.intersection(b_existing_links))
            candidate_sets.append((set_idx, total_shared_links))

    if candidate_sets:
        best_set_index, _ = max(candidate_sets, key=lambda item: item[1])
        mutually_exclusive_sets[best_set_index].append(req_id_to_place)
        print(f"Request #{req_id_to_place} added to existing backup set {best_set_index}.")
    else:
        mutually_exclusive_sets.append([req_id_to_place])
        print(f"Request #{req_id_to_place} created new backup set {len(mutually_exclusive_sets)-1}.")


# --- Phase 4: Allocate Backup Paths from Sets ---
# (This was Phase 3 in the original file)
print("\n" + "="*20 + " Phase 4: Backup Path Allocation " + "="*20)
mutually_exclusive_sets.sort(key=len, reverse=True)

for i, me_set in enumerate(mutually_exclusive_sets):
    print(f"\n--> Allocating backups for Set #{i} (size: {len(me_set)}): {me_set}")
    for req_id in me_set:
        conn_info = active_connections[req_id]
        b_allocations = allocate_segments(conn_info['backup_details'], req_id, 'backup', conn_info['primary_path'])

        if b_allocations:
            print(f"  Request #{req_id}: Backup SUCCESSFUL.")
            conn_info['backup_allocations'] = b_allocations
            conn_info['success'] = True
            
            # Costs are correctly kept
            for log in request_log:
                if log['id'] == req_id:
                    log.update(conn_info)
                    break
        else:
            print(f"  Request #{req_id}: Backup FAILED. Rolling back primary path.")
            
            # --- NEW: Update failed slots counter ---
            p_link_slots = conn_info['p_link_slots']
            b_link_slots = conn_info['b_link_slots']
            total_slots_failed_all_links += (p_link_slots + b_link_slots)
            
            # --- Roll back costs for BOTH paths ---
            # (This rollback logic is unchanged from the original file,
            # and is correct)
            update_regenerator_cost(conn_info['primary_details'], 'subtract')
            update_regenerator_cost(conn_info['backup_details'], 'subtract')

            deallocate_path(conn_info['primary_details'], conn_info['primary_allocations'], req_id, 'primary')
            del active_connections[req_id]
            for log in request_log:
                if log['id'] == req_id:
                    log['success'] = False
                    log['reason'] = "No spectrum available for shared backup path."
                    break

# --- Final Step: Update regenerator counts for all fully successful requests ---
#update_final_regenerator_counts()


# --- Final Statistics Calculation and Reporting (Unchanged) ---
def calculate_and_print_statistics():
    """Calculates and prints all the final network performance metrics."""
    print("\n" + "="*25 + " Final Network Statistics " + "="*25)

    # a) Highest Utilized Spectrum Slot Index (NEW LOGIC)
    # Finds the absolute highest slot index used on *any* link.
    highest_slot_index_found = -1
    for link_slots in rsa.values():
        # Iterate backwards from the top slot to find the first (highest) used slot
        for i in range(SLOTS - 1, -1, -1):
            if link_slots[i]['status'] != 'free':
                # If this slot's index is higher than the max found so far, update it
                highest_slot_index_found = max(highest_slot_index_found, i)
                # Found highest for this link, break and move to the next link
                break 
    
    if highest_slot_index_found == -1:
        print("a) Highest Utilized Spectrum Slot Index: None (No slots utilized)")
    else:
        print(f"a) Highest Utilized Spectrum Slot Index: {highest_slot_index_found}")

    # b) Total Spectrum Utilized Slots (UPDATED LOGIC)
    # Calculates the sum of all occupied slot-links independently.
    # This logic is equivalent to the old 'sum(slot_utilization)'
    # but no longer depends on the array from statistic 'a'.
    total_utilized_slots = 0
    for link_slots in rsa.values():
        for slot_info in link_slots:
            if slot_info['status'] != 'free':
                total_utilized_slots += 1
    
    print(f"b) Total Spectrum Utilized Slots: {total_utilized_slots}")

    # c) Number of Request Blocking (Blocking Probability)
    success_count = len(active_connections)
    total_requests = request_id_counter
    blocked_requests = total_requests - success_count
    blocking_probability = (blocked_requests / total_requests) if total_requests else 0
    print(f"c) Request Blocking Probability: {blocking_probability:.2%} ({blocked_requests} blocked / {total_requests} total)")
    
    # d) Total Guard Band Used
    total_guard_bands = 0
    for link_slots in rsa.values():
        for slot_info in link_slots:
            if slot_info['status'] == 'guard':
                total_guard_bands += 1
            elif slot_info['status'] == 'hybrid_backup' and 'G' in slot_info['request_id']:
                total_guard_bands += slot_info['request_id'].count('G')
                
    print(f"d) Total Guard Bands Used: {total_guard_bands}")

    # --- MODIFIED FRAGMENTATION LOGIC ---
    # e) % of Fragmentation (within used spectrum)
    total_fragmentation_metric = 0
    average_fragmentation = 0.0

    if highest_slot_index_found == -1 or not edges:
        # No slots were used, or no edges exist, so fragmentation is 0
        print("e) Network Fragmentation: 0.00% (No slots utilized)")
    else:
        # Define the relevant part of the spectrum to check (from 0 to the highest slot used)
        spectrum_range_to_check = highest_slot_index_found + 1
        
        for link_slots in rsa.values():
            largest_free_block = 0
            current_free_block = 0
            total_free_slots = 0
            
            # Only check slots within the relevant, used range
            for slot_info in link_slots[:spectrum_range_to_check]:
                if slot_info['status'] == 'free':
                    current_free_block += 1
                    total_free_slots += 1
                else:
                    largest_free_block = max(largest_free_block, current_free_block)
                    current_free_block = 0
            # Check for a free block at the end of the *checked range*
            largest_free_block = max(largest_free_block, current_free_block)
            
            if total_free_slots > 0:
                link_fragmentation = 1 - (largest_free_block / total_free_slots)
                total_fragmentation_metric += link_fragmentation
                
        average_fragmentation = (total_fragmentation_metric / len(edges))
        print(f"e) Network Fragmentation: {average_fragmentation:.2%}")
    # --- END OF MODIFIED LOGIC ---

    # f) Total Number of Regenerations
    total_regenerations = 0
    for req in request_log:
        if req['success']:
            primary_segments = req.get('primary_details', [])
            backup_segments = req.get('backup_details', [])
            if len(primary_segments) > 1:
                total_regenerations += len(primary_segments) - 1
            if len(backup_segments) > 1:
                total_regenerations += len(backup_segments) - 1
    print(f"f) Total Number of Regenerations: {total_regenerations}")
    
    # g) Regenerator Node Usage
    print("g) Regenerator Node Usage:")
    used_regenerators = {node: count for node, count in regenerator_usage.items() if count > 0}
    if not used_regenerators:
        print("   None")
    else:
        sorted_regenerators = sorted(used_regenerators.items(), key=lambda item: nodes.index(item[0]))
        for node, count in sorted_regenerators:
            print(f"   Node '{node}': {count} times")

    # h) Execution Time
    end_time = time.perf_counter()
    print(f"h) Total Execution Time: {end_time - start_time:.4f} seconds")

    # --- NEW STATISTIC ADDED ---
    # j) Standard Deviation of Regenerator Usage
    usage_counts = list(regenerator_usage.values())
    num_nodes = len(usage_counts)
    if num_nodes > 0:
        mean_usage = sum(usage_counts) / num_nodes
        # Calculate variance for the population
        variance = sum((x - mean_usage) ** 2 for x in usage_counts) / num_nodes
        std_dev_usage = math.sqrt(variance)
        print(f"j) Std. Deviation of Regenerator Usage: {std_dev_usage:.4f}")
    else:
        print("j) Std. Deviation of Regenerator Usage: N/A (no nodes)")
    # --- END OF NEW STATISTIC ---
    
    # --- NEW STATISTIC ADDED ---
    # k) Bandwidth Blocking Ratio
    if total_slots_requested_all_links == 0:
        print("k) Bandwidth Blocking Ratio: N/A (No slots requested)")
    else:
        bbr = total_slots_failed_all_links / total_slots_requested_all_links
        print(f"k) Bandwidth Blocking Ratio: {bbr:.2%} ({total_slots_failed_all_links} failed slots / {total_slots_requested_all_links} total slots)")
    # --- END OF NEW STATISTIC ---

# --- Detailed Request Log (Unchanged) ---
print("\n" + "="*25 + " Request Log Summary " + "="*25)
count=1
for req in request_log:
    status = "SUCCESS" if req['success'] else "FAILED"
    print(f"\n--- Req #{req['id']}: {req['source']} -> {req['destination']}, Status: {status} ---")
    print(f"   - Bandwidth: {req['bandwidth']} Gbps")

    if req['success']:
        print("   - Primary Path Details:")
        if req.get('primary_details') and req.get('primary_allocations'):
            for seg_num, (segment, alloc) in enumerate(zip(req['primary_details'], req['primary_allocations'])):
                start = alloc['start_slot']
                end = start + alloc['slots_needed'] -1
                print(f"     * Segment {seg_num+1}: {' -> '.join(segment['path'])} | Slots Used: {start}-{end}")
                print(f"       Modulation: {segment['mod']}, Slots Needed (for each link): {segment['slots']}")
        
        print("   - Backup Path Details:")
        if req.get('backup_details') and req.get('backup_allocations'):
                for seg_num, (segment, alloc) in enumerate(zip(req['backup_details'], req['backup_allocations'])):
                    start = alloc['start_slot']
                    end = start + alloc['slots_needed'] -1
                    print(f"     * Segment {seg_num+1}: {' -> '.join(segment['path'])} | Slots Used: {start}-{end}")
                    print(f"       Modulation: {segment['mod']}, Slots Needed (for each link): {segment['slots']}")
    else:
        print(f"   - Reason for Failure: {req['reason']}")
    print("Count = ", count)
    count+=1

# --- Print Final Statistics ---
calculate_and_print_statistics()