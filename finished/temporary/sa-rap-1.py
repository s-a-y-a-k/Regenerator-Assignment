import time
import random
import math
import copy
import itertools # <-- NEW: Imported for finding combinations
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

MAX_REACH = max(m['reach'] for m in mod_formats)


request_log = []
request_id_counter = 0
active_connections = {}
regenerator_usage = {node: 0 for node in nodes}
sa_rap_used_count = 0


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

# --- Regenerator Placement Algorithms (MODIFIED) ---

def place_flr_regenerators(path, bandwidth):
    """
    Implements the First Longest Reach (FLR) strategy for paths requiring regeneration.
    """
    if not path or len(path) < 2:
        return None
    
    segments = []
    current_node_idx = 0
    while current_node_idx < len(path) - 1:
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

def calculate_segment_details(segment_path, bandwidth):
    """Calculates distance, modulation, and slots for a given path segment."""
    if len(segment_path) < 2: return None
    
    dist = sum(graph[nodes.index(segment_path[i])][nodes.index(segment_path[i+1])] for i in range(len(segment_path)-1))
    mod = get_best_mod(dist)
    if not mod: return None
    
    slots_needed = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
    return {'path': segment_path, 'dist': dist, 'mod': mod['name'], 'slots': slots_needed}

# --- NEW: SA-RAP Algorithm (Completely Reworked) ---
def run_sa_rap(path, bandwidth, flr_segments):
    """
    Runs SA-RAP by testing all combinations of regenerator placements to find the minimum slot usage.
    It must use the same number of regenerators as determined by FLR.
    """
    num_regenerators_flr = len(flr_segments) - 1
    intermediate_nodes = path[1:-1]

    # SA-RAP is only applicable if FLR needed at least one regenerator and there are
    # enough intermediate nodes to choose from.
    if num_regenerators_flr < 1 or len(intermediate_nodes) < num_regenerators_flr:
        return None 

    print(f"     - Running SA-RAP with {num_regenerators_flr} regenerator(s) to find a more optimal placement...")

    best_segments = None
    min_total_slots = float('inf')

    # Get all combinations of intermediate nodes where we can place the regenerators.
    possible_placements = itertools.combinations(intermediate_nodes, num_regenerators_flr)

    for placement_combo in possible_placements:
        # Sort the chosen nodes by their original position in the path
        sorted_regen_nodes = sorted(list(placement_combo), key=path.index)
        
        # Construct all segments based on this specific placement
        current_segments = []
        is_valid_placement = True
        start_node_of_segment = path[0]

        # Create segments from the start to each regenerator
        for regen_node in sorted_regen_nodes:
            start_idx = path.index(start_node_of_segment)
            end_idx = path.index(regen_node)
            segment_path = path[start_idx : end_idx + 1]
            
            seg_details = calculate_segment_details(segment_path, bandwidth)
            if not seg_details:
                is_valid_placement = False
                break
            current_segments.append(seg_details)
            start_node_of_segment = regen_node
        
        if not is_valid_placement:
            continue # This combination created an unreachable segment, so it's invalid.

        # Create the final segment from the last regenerator to the destination
        last_regen_node = sorted_regen_nodes[-1]
        start_idx = path.index(last_regen_node)
        final_segment_path = path[start_idx:]
        
        final_seg_details = calculate_segment_details(final_segment_path, bandwidth)
        if not final_seg_details:
            continue # The final segment is unreachable.
        current_segments.append(final_seg_details)
        
        # Calculate total slots for this valid combination
        current_total_slots = sum(seg['slots'] for seg in current_segments)

        # If this combination is better than the best one found so far, save it.
        if current_total_slots < min_total_slots:
            min_total_slots = current_total_slots
            best_segments = current_segments

    return best_segments

# --- Logic to decide on regeneration strategy (MODIFIED) ---
def process_path_for_segments(path, path_dist, bandwidth):
    """
    Decides the best segmentation strategy by comparing FLR and SA-RAP.
    """
    global sa_rap_used_count
    
    best_mod_for_whole_path = get_best_mod(path_dist)
    if best_mod_for_whole_path:
        print(f"   Path can be established in a single segment with {best_mod_for_whole_path['name']}.")
        slots_needed = math.ceil(bandwidth / (best_mod_for_whole_path['capacity'] * best_mod_for_whole_path['efficiency']))
        return [{
            'path': path,
            'dist': path_dist,
            'mod': best_mod_for_whole_path['name'],
            'slots': slots_needed
        }]
    
    print("   Path is too long. Running FLR to find baseline regenerator placement.")
    flr_segments = place_flr_regenerators(path, bandwidth)
    
    if not flr_segments:
        return None

    flr_total_slots = sum(seg['slots'] for seg in flr_segments)
    print(f"     - FLR Result: {len(flr_segments) - 1} regenerator(s). Total slots: {flr_total_slots}.")

    # Now, try to optimize with SA-RAP
    sa_rap_segments = run_sa_rap(path, bandwidth, flr_segments)
    
    if sa_rap_segments:
        sa_rap_total_slots = sum(seg['slots'] for seg in sa_rap_segments)
        print(f"     - SA-RAP Best Find: Total slots: {sa_rap_total_slots}.")

        if sa_rap_total_slots < flr_total_slots:
            print("   >> SA-RAP found a better solution. Using SA-RAP segmentation.")
            sa_rap_used_count += 1
            return sa_rap_segments
        else:
            print("   >> FLR solution is better or equal. Using FLR segmentation.")
            return flr_segments
    else:
        print("   >> SA-RAP not applicable or no alternatives found. Using FLR segmentation.")
        return flr_segments

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
                        if slot_info['status'] == 'primary' or (slot_info['status'] == 'guard' and s > 0 and rsa[link][s-1]['status'] == 'primary'):
                            is_block_available = False
                            break
                        if slot_info['status'] == 'backup' or (slot_info['status'] == 'guard' and s > 0 and rsa[link][s-1]['status'] == 'backup'):
                            other_req_id = slot_info['request_id'][0] if slot_info['request_id'] else None
                            if other_req_id and other_req_id in active_connections:
                                other_primary_path = active_connections[other_req_id]['primary_path']
                                if not are_paths_disjoint(primary_path_of_this_request, other_primary_path):
                                    is_block_available = False
                                    break
                        if slot_info['status'] == 'hybrid_backup':
                            other_req_ids = [x for x in slot_info['request_id'] if x != 'G']
                            for others in other_req_ids:
                                if others in active_connections:
                                    other_primary_path = active_connections[others]['primary_path']
                                    if not are_paths_disjoint(primary_path_of_this_request, other_primary_path):
                                        is_block_available = False
                                        break
                            if not is_block_available: break
                if not is_block_available: break
            if is_block_available:
                for i in range(len(seg['path']) - 1):
                    link = frozenset([seg['path'][i], seg['path'][i+1]])
                    for s in range(start_slot, start_slot + slots_needed):
                        if path_type == 'primary' and rsa[link][s]['status'] == 'free':
                           rsa[link][s]['status'] = path_type
                           rsa[link][s]['request_id'] = [request_id]
                        elif path_type == 'backup':
                            if rsa[link][s]['status'] == 'free':
                                rsa[link][s]['status'] = 'backup'
                                rsa[link][s]['request_id'].append(request_id)
                            elif rsa[link][s]['status'] in ['backup', 'guard', 'hybrid_backup']:
                                rsa[link][s]['status'] = 'hybrid_backup'
                                if request_id not in rsa[link][s]['request_id']:
                                    rsa[link][s]['request_id'].append(request_id)
                    guard_slot_index = start_slot + slots_needed
                    if rsa[link][guard_slot_index]['status'] == 'free':
                        rsa[link][guard_slot_index]['status'] = 'guard'
                        if path_type == 'primary':
                           rsa[link][guard_slot_index]['request_id'] = ['G']
                        else:
                           rsa[link][guard_slot_index]['request_id'].append('G')
                    elif path_type == 'backup':
                        rsa[link][guard_slot_index]['status'] = 'hybrid_backup'
                        if 'G' not in rsa[link][guard_slot_index]['request_id']:
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
                
                remaining_ids = [rid for rid in slot_info['request_id'] if rid != 'G']
                if not slot_info['request_id']:
                    slot_info['status'] = 'free'
                elif not remaining_ids and 'G' in slot_info['request_id']:
                    slot_info['status'] = 'guard' # It's just a guard for another backup
                elif len(remaining_ids) == 1 and not 'G' in slot_info['request_id']:
                    slot_info['status'] = 'backup'
                # Otherwise, it remains hybrid or guard

# --- Main Request Handling Logic (Unchanged) ---
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
    
    print("FOR PRIMARY PATH:")
    primary_segments = process_path_for_segments(primary_path, primary_dist, bandwidth)
    print("FOR BACKUP PATH:")
    backup_segments = process_path_for_segments(backup_path, backup_dist, bandwidth)
    
    if not primary_segments or not backup_segments:
        log_entry['reason'] = "Could not determine segmentation for a path."
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
        deallocate_path(primary_segments, primary_allocations, req_id, 'primary')
        request_log.append(log_entry)
        return
        
    print(f"Request SUCCESS")
    
    if len(primary_segments) > 1:
        for i in range(len(primary_segments) - 1):
            regenerator_node = primary_segments[i]['path'][-1]
            regenerator_usage[regenerator_node] += 1
    
    if len(backup_segments) > 1:
        for i in range(len(backup_segments) - 1):
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

# --- Final Statistics Calculation and Reporting (Unchanged) ---
def calculate_and_print_statistics():
    """Calculates and prints all the final network performance metrics."""
    print("\n" + "="*25 + " Final Network Statistics " + "="*25)

    # a) Highest Utilized Spectrum Slot Index
    slot_utilization = [0] * SLOTS
    for link_slots in rsa.values():
        for i, slot_info in enumerate(link_slots):
            if slot_info['status'] != 'free':
                slot_utilization[i] += 1
    
    if not any(slot_utilization):
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
    print(f"f) Total Number of Regenerations: {total_regenerations}")
    
    # g) Regenerator Node Usage
    print("g) Regenerator Node Usage:")
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
    
    # i) SA-RAP Algorithm Usage Report
    print("i) SA-RAP Algorithm Usage:")
    if sa_rap_used_count == 0:
        print("   - SA-RAP was not used. For this network topology and traffic, the standard FLR algorithm was always better or equal.")
    else:
        print(f"   - SA-RAP found a more spectrum-efficient solution {sa_rap_used_count} time(s).")


# --- Detailed Request Log ---
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