import time
import random
import math
import copy
random.seed(42)
start_time = time.perf_counter()

# --- Core Network and RSA Setup ---
SLOTS = 250
graph = [
    [0, 1000, 1200, 9999, 9999, 9999], [1000, 0, 600, 800, 1000, 9999],
    [1200, 600, 0, 9999, 800, 9999], [9999, 800, 9999, 0, 600, 1000],
    [9999, 1000, 800, 600, 0, 1200], [9999, 9999, 9999, 1000, 1200, 0]
]
nodes = [str(i + 1) for i in range(len(graph))]
edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if 0 < graph[i][j] < 9999:
            edges.append((nodes[i], nodes[j]))

rsa = {frozenset(link): [{'status': 'free', 'request_id': []} for _ in range(SLOTS)] for link in edges}

mod_formats = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 2000},
    {'name': 'QPSK', 'capacity': 12.5, 'efficiency': 2, 'reach': 1000},
    {'name': '8-QAM', 'capacity': 12.5, 'efficiency': 3, 'reach': 500},
    {'name': '16-QAM', 'capacity': 12.5, 'efficiency': 4, 'reach': 250}
]

# We need the max reach for the FLR algorithm
MAX_REACH = max(m['reach'] for m in mod_formats)


request_log = []
request_id_counter = 0
active_connections = {}
# NEW: Dictionary to track regenerator usage per node
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
                # **NEW**: Format the list of request IDs as [B1,B2,...]
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
        
        # Find the farthest node we can reach from the current node
        for next_node_idx in range(current_node_idx + 1, len(path)):
            sub_path = path[current_node_idx : next_node_idx + 1]
            dist = sum(graph[nodes.index(sub_path[i])][nodes.index(sub_path[i+1])] for i in range(len(sub_path)-1))
            
            if dist <= MAX_REACH:
                farthest_reach_idx = next_node_idx
            else:
                break # Path becomes too long

        if farthest_reach_idx == -1:
            # This case means even the very next hop is unreachable, path is impossible
            print(f"   FLR FAILED: Cannot reach from {path[current_node_idx]} to {path[current_node_idx+1]}.")
            return None
        
        # Create the segment based on the farthest reachable point
        final_segment_path = path[current_node_idx : farthest_reach_idx + 1]
        segment_dist = sum(graph[nodes.index(final_segment_path[i])][nodes.index(final_segment_path[i+1])] for i in range(len(final_segment_path)-1))
        
        mod = get_best_mod(segment_dist)
        if not mod: return None # Safeguard
            
        slots_needed = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
        
        segments.append({
            'path': final_segment_path,
            'dist': segment_dist,
            'mod': mod['name'],
            'slots': slots_needed
        })
        
        # Move to the start of the next segment
        current_node_idx = farthest_reach_idx

    return segments

# --- Allocation Logic with Spectrum Conversion (Unchanged) ---
def are_paths_disjoint(path1, path2):
    links1 = {frozenset([path1[i], path1[i+1]]) for i in range(len(path1)-1)}
    for i in range(len(path2)-1):
        if frozenset([path2[i], path2[i+1]]) in links1:
            return False
    return True

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
                        # For backup, a slot is unavailable if it's primary or a guard band
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
                    # Allocate data slots
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
                    # Allocate guard band slot with 'guard' status
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
            print(f"   Allocation failed for segment {seg_idx+1}. Rolling back.")
            deallocate_path(segments[:seg_idx], all_segment_allocations, request_id, path_type)
            return None
    return all_segment_allocations

def deallocate_path(segments, allocations, request_id, path_type):
    """Robustly deallocates a path by removing its request_id and 'G' marker from slots."""
    if not segments or not allocations: return
    for seg, alloc in zip(segments, allocations):
        start = alloc['start_slot']
        slots_needed = seg['slots']
        end = start + slots_needed + 1 # Total slots including the guard
        
        for i in range(len(seg['path']) - 1):
            link = frozenset([seg['path'][i], seg['path'][i+1]])
            for s in range(start, end):
                if s >= SLOTS: continue # Boundary check
                
                slot_info = rsa[link][s]
                
                # Check if the ID to be removed is in this slot's list
                if request_id in slot_info['request_id']:
                    slot_info['request_id'].remove(request_id)
                
                # If this is the guard slot for the segment, also remove its 'G' marker
                is_guard_slot = (s == start + slots_needed)
                if is_guard_slot and 'G' in slot_info['request_id']:
                    slot_info['request_id'].remove('G')
                
                # Now, update the slot's status based on what's left
                remaining_ids = len(slot_info['request_id'])
                if remaining_ids == 0:
                    slot_info['status'] = 'free'
                elif remaining_ids == 1 and 'G' not in slot_info['request_id']:
                    # If only one request ID is left, it's a simple backup
                    slot_info['status'] = 'backup'
                # If more than one ID or a single 'G' remains, it stays hybrid/guard

# --- Logic to decide on regeneration strategy (Unchanged) ---
def process_path_for_segments(path, path_dist, bandwidth):
    """
    Decides whether to use regenerators or treat the path as a single segment.
    - If the total path distance is within reach of a modulation format,
      it creates a single segment for the entire path.
    - Otherwise, it uses the FLR strategy to place regenerators.
    """
    best_mod_for_whole_path = get_best_mod(path_dist)

    if best_mod_for_whole_path:
        # Path is short enough, no regenerators needed. Treat as one segment.
        print(f"   Path can be established in a single segment with {best_mod_for_whole_path['name']}.")
        slots_needed = math.ceil(bandwidth / (best_mod_for_whole_path['capacity'] * best_mod_for_whole_path['efficiency']))
        return [{
            'path': path,
            'dist': path_dist,
            'mod': best_mod_for_whole_path['name'],
            'slots': slots_needed
        }]
    else:
        # Path is too long, FLR regenerator placement is required.
        print("   Path is too long for any single modulation format. Using FLR.")
        return place_flr_regenerators(path, bandwidth)

# --- Main Request Handling Logic (UPDATED) ---
def request(source, destination):
    global request_id_counter
    request_id_counter += 1
    req_id = request_id_counter
    print(f"\n--- New Request #{req_id}: {nodes[source]} -> {nodes[destination]} ---")
    bandwidth = random.randint(100, 401)
    log_entry = {'id': req_id, 'source': nodes[source], 'destination': nodes[destination], 'bandwidth': bandwidth, 'success': False, 'reason': ''}

    primary_path, primary_dist = find_shortest_path(source, destination, graph)
    if not primary_path:
        log_entry['reason'] = "No primary path found."
        print(f"Request FAILED: {log_entry['reason']}")
        request_log.append(log_entry)
        return

    backup_path, backup_dist = get_disjoint_path(primary_path, source, destination)
    if not backup_path:
        log_entry['reason'] = "No link-disjoint backup path found."
        print(f"Request FAILED: {log_entry['reason']}")
        request_log.append(log_entry)
        return
    
    # Decide on regeneration strategy based on path length
    print("FOR PRIMARY PATH: ")
    primary_segments = process_path_for_segments(primary_path, primary_dist, bandwidth)
    print(primary_segments)
    print("FOR BACKUP PATH: ")
    backup_segments = process_path_for_segments(backup_path, backup_dist, bandwidth)
    print(backup_segments)
    
    if not primary_segments or not backup_segments:
        log_entry['reason'] = "Could not place regenerators on a path."
        print(f"Request FAILED: {log_entry['reason']}")
        request_log.append(log_entry)
        return

    primary_allocations = allocate_segments(primary_segments, req_id, 'primary', None)
    if not primary_allocations:
        log_entry['reason'] = "No spectrum available for primary path."
        print(f"Request FAILED: {log_entry['reason']}")
        request_log.append(log_entry)
        return

    backup_allocations = allocate_segments(backup_segments, req_id, 'backup', primary_path)
    if not backup_allocations:
        log_entry['reason'] = "No spectrum available for shared backup path."
        print(f"Request FAILED: {log_entry['reason']} Rolling back primary allocation.")
        deallocate_path(primary_segments, primary_allocations, req_id, 'backup')
        request_log.append(log_entry)
        return
        
    print(f"Request SUCCESS")
    
    # NEW: Update regenerator counts on successful allocation
    if len(primary_segments) > 1:
        for i in range(len(primary_segments) - 1): # Exclude the final destination
            regenerator_node = primary_segments[i]['path'][-1]
            regenerator_usage[regenerator_node] += 1
    
    if len(backup_segments) > 1:
        for i in range(len(backup_segments) - 1): # Exclude the final destination
            regenerator_node = backup_segments[i]['path'][-1]
            regenerator_usage[regenerator_node] += 1
            
    connection_info = {
        'primary_path': primary_path, 'primary_details': primary_segments, 'primary_allocations': primary_allocations,
        'backup_path': backup_path, 'backup_details': backup_segments, 'backup_allocations': backup_allocations,
        'success': True
    }
    active_connections[req_id] = connection_info
    log_entry.update(connection_info)
    request_log.append(log_entry)

# --- Main Execution Loop ---
for i in range(len(graph)):
    for j in range(len(graph)):
        if i != j:
            request(i, j)
            show_slots() # Uncomment for debugging

# --- Final Statistics Calculation and Reporting ---
def calculate_and_print_statistics():
    """Calculates and prints all the final network performance metrics."""
    print("\n" + "="*25 + " Final Network Statistics " + "="*25)

    # a) Highest Utilized Spectrum Slot Index
    slot_utilization = [0] * SLOTS
    for link_slots in rsa.values():
        for i, slot_info in enumerate(link_slots):
            if slot_info['status'] != 'free':
                slot_utilization[i] += 1
    
    if not any(slot_utilization): # Handle case where no slots are used
        print("a) Highest Utilized Slot Index(es): None (No slots utilized)")
    else:
        max_utilization = max(slot_utilization)
        highest_utilized_indices = [i for i, v in enumerate(slot_utilization) if v == max_utilization]
        print(f"a) Highest Utilized Slot Index(es): {highest_utilized_indices} (used on {max_utilization} links)")

    # b) Total Spectrum Utilized Slots
    total_utilized_slots = sum(slot_utilization)
    print(f"b) Total Spectrum Utilized Slots: {total_utilized_slots}")

    # c) Number of Request Blocking (Blocking Probability)
    success_count = len(active_connections)
    total_requests = request_id_counter
    blocked_requests = total_requests - success_count
    blocking_probability = (blocked_requests / total_requests) if total_requests else 0
    print(f"c) Request Blocking Probability: {blocking_probability:.2%} ({blocked_requests} blocked / {total_requests} total)")

    # +++ Corrected Guard Band Calculation +++

    # d) Total Guard Band Used
    total_guard_bands = 0
    # Iterate through the physical links and slots to get the true count
    for link_slots in rsa.values():
        for slot_info in link_slots:
            # A slot is a guard band if:
            # 1. Its status is 'guard' (for an exclusive primary path).
            if slot_info['status'] == 'guard':
                total_guard_bands += 1
            # 2. Or, its status is 'hybrid_backup' AND it contains a 'G' marker.
            elif slot_info['status'] == 'hybrid_backup' and 'G' in slot_info['request_id']:
                for x in slot_info['request_id']:
                    if x == 'G': total_guard_bands += 1 
                
                
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
            # For each path, # of regenerators = (# of segments - 1)
            primary_segments = req.get('primary_details', [])
            backup_segments = req.get('backup_details', [])
            if len(primary_segments) > 1:
                total_regenerations += len(primary_segments) - 1
            if len(backup_segments) > 1:
                total_regenerations += len(backup_segments) - 1
    print(f"f) Total Number of Regenerations: {total_regenerations}")
    
    # g) Regenerator Node Usage (NEWLY ADDED)
    print("g) Regenerator Node Usage:")
    used_regenerators = {node: count for node, count in regenerator_usage.items() if count > 0}
    if not used_regenerators:
        print("   None")
    else:
        # Sorting for consistent output
        sorted_regenerators = sorted(used_regenerators.items(), key=lambda item: int(item[0]))
        for node, count in sorted_regenerators:
            print(f"   Node '{node}': {count} times")

    # h) Execution Time
    end_time = time.perf_counter()
    print(f"h) Total Execution Time: {end_time - start_time:.4f} seconds")

# --- Detailed Request Log (Optional) ---
# Uncomment the following lines if you want to see the detailed per-request log again

print("\n" + "="*25 + " Request Log Summary " + "="*25)
for req in request_log:
    status = "SUCCESS" if req['success'] else "FAILED"
    print(f"\n--- Req #{req['id']}: {req['source']} -> {req['destination']}, Status: {status} ---")
    print(f"   - Bandwidth: {req['bandwidth']} Gbps")

    if req['success']:
        print("   - Primary Path Details:")
        if req.get('primary_details'):
            for seg_num, (segment, alloc) in enumerate(zip(req['primary_details'], req['primary_allocations'])):
                start = alloc['start_slot']
                end = start + alloc['slots_needed'] -1
                print(f"     * Segment {seg_num+1}: {' -> '.join(segment['path'])} | Slots Used: {start}-{end}")
                print(f"       Modulation: {segment['mod']}, Slots Needed (for each link): {segment['slots']}")
        
        print("   - Backup Path Details:")
        if req.get('backup_details'):
                for seg_num, (segment, alloc) in enumerate(zip(req['backup_details'], req['backup_allocations'])):
                    start = alloc['start_slot']
                    end = start + alloc['slots_needed'] -1
                    print(f"     * Segment {seg_num+1}: {' -> '.join(segment['path'])} | Slots Used: {start}-{end}")
                    print(f"       Modulation: {segment['mod']}, Slots Needed (for each link): {segment['slots']}")
    else:
        print(f"   - Reason for Failure: {req['reason']}")

# --- Print Final Statistics ---
calculate_and_print_statistics()
