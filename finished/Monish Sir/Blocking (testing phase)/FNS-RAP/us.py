import time
import random
import math
import copy
random.seed(42)
start_time = time.perf_counter()

# --- Core Network and RSA Setup ---
SLOTS = 2000
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
    {'name': 'QPSK', 'capacity': 12.5, 'efficiency': 2, 'reach': 4000},
    {'name': '8-QAM', 'capacity': 12.5, 'efficiency': 3, 'reach': 2000},
    {'name': '16-QAM', 'capacity': 12.5, 'efficiency': 4, 'reach': 1000},
    {'name': '32-QAM', 'capacity': 12.5, 'efficiency': 5, 'reach': 500},
    {'name': '64-QAM', 'capacity': 12.5, 'efficiency': 6, 'reach': 250}
]

# We need the max reach for pathfinding
MAX_REACH = max(m['reach'] for m in mod_formats)

# For FNS-RA, we sort from most spectrally efficient to least
mod_formats.sort(key=lambda x: x['efficiency'], reverse=True)

# <<< NEW: Regenerator Node Limit ---
max_regenerators_at_a_node = 30 # <<<<<<<<<<<<< You can change this value

request_log = []
request_id_counter = 0
active_connections = {}
# Dictionary to track *live* regenerator usage per node
regenerator_usage = {node: 0 for node in nodes}


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
    sorted_links = sorted(rsa.items(), key=lambda item: (min(int(n) for n in list(item[0])), max(int(n) for n in list(item[0]))))
    
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

# --- FNS-RA (First-Fit Network Spectrum and Regenerator Allocation) (Unchanged) ---
def place_fns_ra_regenerators(path, bandwidth):
    """
    Implements the FNS-RA regenerator placement strategy.
    This is called ONLY when the whole path is too long for any single MF.
    """
    if not path or len(path) < 2:
        return None
    
    segments = []
    current_node_idx = 0
    most_efficient_mf = mod_formats[0]

    while current_node_idx < len(path) - 1:
        segment_start_idx = current_node_idx
        
        # PLAN A: Try for the longest segment with the MOST efficient MF
        farthest_reach_idx = -1
        for possible_end_idx in range(segment_start_idx + 1, len(path)):
            current_sub_path = path[segment_start_idx : possible_end_idx + 1]
            current_dist = sum(graph[nodes.index(current_sub_path[i])][nodes.index(current_sub_path[i+1])] for i in range(len(current_sub_path)-1))
            
            if current_dist <= most_efficient_mf['reach']:
                farthest_reach_idx = possible_end_idx
            else:
                break
        
        if farthest_reach_idx != -1:
            # PLAN A SUCCESS
            final_segment_path = path[segment_start_idx : farthest_reach_idx + 1]
            final_dist = sum(graph[nodes.index(final_segment_path[i])][nodes.index(final_segment_path[i+1])] for i in range(len(final_segment_path)-1))
            
            slots_needed = math.ceil(bandwidth / (most_efficient_mf['capacity'] * most_efficient_mf['efficiency']))
            segments.append({
                'path': final_segment_path, 'dist': final_dist,
                'mod': most_efficient_mf['name'], 'slots': slots_needed
            })
            current_node_idx = farthest_reach_idx
            continue

        # PLAN B: If Plan A fails, find the SHORTEST segment with any OTHER MF
        else:
            shortest_segment_path = path[segment_start_idx : segment_start_idx + 2]
            shortest_segment_dist = graph[nodes.index(shortest_segment_path[0])][nodes.index(shortest_segment_path[1])]
            
            fallback_mf = None
            for mf in mod_formats[1:]: # Skip the most efficient one
                if shortest_segment_dist <= mf['reach']:
                    fallback_mf = mf
                    break
            
            if fallback_mf:
                # PLAN B SUCCESS
                slots_needed = math.ceil(bandwidth / (fallback_mf['capacity'] * fallback_mf['efficiency']))
                segments.append({
                    'path': shortest_segment_path, 'dist': shortest_segment_dist,
                    'mod': fallback_mf['name'], 'slots': slots_needed
                })
                current_node_idx = segment_start_idx + 1
            else:
                # COMPLETE FAILURE
                return None
    return segments
    
# <<< NEW: Helper function to get regenerator nodes for a set of segments ---
def get_needed_regenerators(segments):
    """Returns a list of nodes where regenerators are placed."""
    if not segments or len(segments) <= 1:
        return []
    
    regenerator_nodes = []
    # A regenerator is placed at the *end* of each segment, *except* the last one.
    for i in range(len(segments) - 1):
        regenerator_node = segments[i]['path'][-1]
        regenerator_nodes.append(regenerator_node)
    return regenerator_nodes

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
        return place_fns_ra_regenerators(path, bandwidth)

# --- Helper function to prepare request details (Unchanged) ---
def prepare_request(source, destination):
    global request_id_counter
    request_id_counter += 1
    req_id = request_id_counter
    print(f"\n--- Preparing Request #{req_id}: {nodes[source]} -> {nodes[destination]} ---")
    bandwidth = random.randint(100, 401)
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
        request_log.append(log_entry) # Append the log entry here
        return None, log_entry, None, None, None, None

    backup_temp_graph = copy.deepcopy(filtered_graph)
    for i in range(len(primary_path) - 1):
        u_idx, v_idx = nodes.index(primary_path[i]), nodes.index(primary_path[i+1])
        backup_temp_graph[u_idx][v_idx] = 99999
        backup_temp_graph[v_idx][u_idx] = 99999
    backup_path, backup_dist = find_shortest_path(source, destination, backup_temp_graph)
    
    if not backup_path:
        log_entry['reason'] = "No link-disjoint viable backup path found."
        print(f"FAILED: {log_entry['reason']}")
        return None, log_entry, None, None, None, None
    
    primary_segments = process_path_for_segments(primary_path, primary_dist, bandwidth)
    backup_segments = process_path_for_segments(backup_path, backup_dist, bandwidth)
    
    if not primary_segments or not backup_segments:
        log_entry['reason'] = "Could not place regenerators on a viable path."
        print(f"FAILED: {log_entry['reason']}")
        return None, log_entry, None, None, None, None
    
    return req_id, log_entry, primary_path, backup_path, primary_segments, backup_segments

# --- (REMOVED) update_final_regenerator_counts function is deleted ---
# The 'regenerator_usage' dictionary is now updated live in Phase 3.


# --- Main Execution Loop ---

# --- Phase 1: Allocate all Primary Paths (Unchanged) ---
print("\n" + "="*20 + " Phase 1: Primary Path Allocation " + "="*20)
pending_backup_req_ids = []

for i in range(len(graph)):
    for j in range(len(graph)):
        if i == j: continue

        req_id, log_entry, p_path, b_path, p_segments, b_segments = prepare_request(i, j)
        
        if not req_id:
            request_log.append(log_entry)
            continue

        p_allocations = allocate_segments(p_segments, req_id, 'primary', None)

        if p_allocations:
            print(f"Request #{req_id}: Primary path SUCCESS. Queued for backup.")
            connection_info = {
                'primary_path': p_path, 'primary_details': p_segments, 'primary_allocations': p_allocations,
                'backup_path': b_path, 'backup_details': b_segments, 'backup_allocations': None,
                'success': False # Not fully successful until backup is allocated
            }
            active_connections[req_id] = connection_info
            log_entry.update(connection_info)
            request_log.append(log_entry)
            pending_backup_req_ids.append(req_id)
        else:
            print(f"Request #{req_id}: Primary path FAILED.")
            log_entry['reason'] = "No spectrum available for primary path."
            request_log.append(log_entry)
        #show_slots()

# --- Phase 2: Group Pending Backups into Mutually Exclusive Sets (Unchanged) ---
print("\n" + "="*20 + " Phase 2: Grouping Backup Paths " + "="*20)
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


# --- Phase 3: Allocate Backup Paths from Sets (MODIFIED) ---
print("\n" + "="*20 + " Phase 3: Backup Path Allocation " + "="*20)
mutually_exclusive_sets.sort(key=len, reverse=True)

for i, me_set in enumerate(mutually_exclusive_sets):
    print(f"\n--> Allocating backups for Set #{i} (size: {len(me_set)}): {me_set}")
    for req_id in me_set:
        conn_info = active_connections[req_id]
        
        # 1. Attempt to allocate SPECTRUM for the backup path
        b_allocations = allocate_segments(conn_info['backup_details'], req_id, 'backup', conn_info['primary_path'])

        if b_allocations:
            # 2. SPECTRUM SUCCESS. Now check REGENERATOR availability.
            primary_regen_nodes = get_needed_regenerators(conn_info['primary_details'])
            backup_regen_nodes = get_needed_regenerators(conn_info['backup_details'])
            
            can_allocate_regens = True
            blocking_node = None
            nodes_to_increment = primary_regen_nodes + backup_regen_nodes
            
            # Check if all needed regenerators are within the limit
            # We check the *combined* load of this request against the *current* network load
            for node in set(nodes_to_increment): # Use set to avoid double-checking a node
                needed_count_at_node = nodes_to_increment.count(node)
                if regenerator_usage[node] + needed_count_at_node > max_regenerators_at_a_node:
                    can_allocate_regens = False
                    blocking_node = node
                    break
            
            if can_allocate_regens:
                # 3a. REGENERATOR SUCCESS: Commit the request
                # Increment live usage counts
                for node in nodes_to_increment:
                    regenerator_usage[node] += 1
                    
                # Mark as successful
                print(f"  Request #{req_id}: Backup SUCCESSFUL (Spectrum + Regenerators).")
                conn_info['backup_allocations'] = b_allocations
                conn_info['success'] = True
                for log in request_log:
                    if log['id'] == req_id:
                        log.update(conn_info)
                        break
            else:
                # 3b. REGENERATOR FAILED: Block request, roll back BOTH paths
                print(f"  Request #{req_id}: Backup FAILED. Regenerator limit ({max_regenerators_at_a_node}) exceeded at Node '{blocking_node}'. Rolling back.")
                
                # Roll back the backup spectrum we just allocated
                deallocate_path(conn_info['backup_details'], b_allocations, req_id, 'backup')
                # Roll back the primary spectrum
                deallocate_path(conn_info['primary_details'], conn_info['primary_allocations'], req_id, 'primary')
                
                del active_connections[req_id]
                for log in request_log:
                    if log['id'] == req_id:
                        log['success'] = False
                        log['reason'] = f"Regenerator limit ({max_regenerators_at_a_node}) exceeded at node '{blocking_node}'."
                        break
        else:
            # 1b. SPECTRUM FAILED: Block request, roll back primary path
            print(f"  Request #{req_id}: Backup FAILED (Spectrum). Rolling back primary path.")
            deallocate_path(conn_info['primary_details'], conn_info['primary_allocations'], req_id, 'primary')
            del active_connections[req_id]
            for log in request_log:
                if log['id'] == req_id:
                    log['success'] = False
                    log['reason'] = "No spectrum available for shared backup path."
                    break
        #show_slots()

# --- (REMOVED) Call to update_final_regenerator_counts() deleted ---


# --- Final Statistics Calculation and Reporting (MODIFIED) ---
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

    # e) % of Fragmentation
    total_fragmentation_metric = 0
    for link_slots in rsa.values():
        largest_free_block = 0
        current_free_block = 0
        total_free_slots = 0
        for slot_info in link_slots:
            if slot_info['status'] == 'free':
                current_free_block += 1
                total_free_slots += 1
            else:
                largest_free_block = max(largest_free_block, current_free_block)
                current_free_block = 0
        largest_free_block = max(largest_free_block, current_free_block)
        
        if total_free_slots > 0:
            link_fragmentation = 1 - (largest_free_block / total_free_slots)
            total_fragmentation_metric += link_fragmentation
            
    average_fragmentation = (total_fragmentation_metric / len(edges)) if edges else 0
    print(f"e) Network Fragmentation: {average_fragmentation:.2%}")

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
    # This number should also equal sum(regenerator_usage.values())
    print(f"f) Total Number of Regenerations: {total_regenerations}")
    
    # g) Regenerator Node Usage
    # This now uses the live 'regenerator_usage' dictionary
    print(f"g) Regenerator Node Usage (Limit per node: {max_regenerators_at_a_node}):") # <<< MODIFIED
    used_regenerators = {node: count for node, count in regenerator_usage.items() if count > 0}
    if not used_regenerators:
        print("   None")
    else:
        sorted_regenerators = sorted(used_regenerators.items(), key=lambda item: int(item[0]))
        for node, count in sorted_regenerators:
            print(f"   Node '{node}': {count} times")

    # h) Execution Time
    end_time = time.perf_counter()
    print(f"h) Total Execution Time: {end_time - start_time:.4f} seconds")

    # --- NEW BANDWIDTH BLOCKING STATISTICS ---
    
    # i) Total Requested Bandwidth
    total_requested_bandwidth = sum(req['bandwidth'] for req in request_log)
    print(f"i) Total Requested Bandwidth: {total_requested_bandwidth} Gbps")

    # j) Total Blocked Bandwidth
    total_blocked_bandwidth = sum(req['bandwidth'] for req in request_log if not req['success'])
    print(f"j) Total Blocked Bandwidth: {total_blocked_bandwidth} Gbps")
    
    # k) Total Successful Regenerated Bandwidth
    # (Bandwidth of successful requests that used >= 1 regenerator)
    total_successful_regenerated_bandwidth = 0
    for req in request_log:
        if req['success']:
            p_segments = req.get('primary_details', [])
            b_segments = req.get('backup_details', [])
            if (p_segments and len(p_segments) > 1) or \
               (b_segments and len(b_segments) > 1):
                total_successful_regenerated_bandwidth += req['bandwidth']
    print(f"k) Total Successful Regenerated Bandwidth: {total_successful_regenerated_bandwidth} Gbps")

    # l) Bandwidth Blocking Probability (BBP)
    bbp = (total_blocked_bandwidth / total_requested_bandwidth) if total_requested_bandwidth > 0 else 0
    print(f"l) Bandwidth Blocking Probability (BBP): {bbp:.2%} (Blocked BW / Total Requested BW)")

    # m) Bandwidth Blocking Ratio (BBR) - User's Formula
    # Avoid division by zero if no regenerated requests were successful
    if total_successful_regenerated_bandwidth > 0:
        bbr_user_formula = total_blocked_bandwidth / total_successful_regenerated_bandwidth
        print(f"m) Bandwidth Blocking Ratio (BBR): {bbr_user_formula:.2f} (Blocked BW / Successful Regenerated BW)")
    else:
        print("m) Bandwidth Blocking Ratio (BBR): N/A (No successful regenerated bandwidth)")


# --- Detailed Request Log (Unchanged) ---
print("\n" + "="*25 + " Request Log Summary " + "="*25)
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

# --- Print Final Statistics ---
calculate_and_print_statistics()