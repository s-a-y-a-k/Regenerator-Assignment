import time
import random
import math
import copy
random.seed(42)
start_time = time.perf_counter()

# --- Core Network and RSA Setup ---
SLOTS = 300
graph = [
    [    0,  1310,   760,   390, 99999, 99999,   740, 99999, 99999, 99999, 99999],
    [ 1310,     0,   550, 99999,   390, 99999, 99999,   450, 99999, 99999, 99999],
    [  760,   550,     0,   660,   210,   390, 99999, 99999, 99999, 99999, 99999],
    [  390, 99999,   660,     0, 99999, 99999,   340,  1090, 99999,   660, 99999],
    [99999,   390,   210, 99999,     0,   220, 99999,   300, 99999, 99999,   930],
    [99999, 99999,   390, 99999,   220,     0,   730,   400,   350, 99999, 99999],
    [  740, 99999, 99999,   340, 99999,   730,     0, 99999,   565,   320, 99999],
    [99999,   450, 99999,  1090,   300,   400, 99999,     0,   600, 99999,   820],
    [99999, 99999, 99999, 99999, 99999,   350,   565,   600,     0,   730,   320],
    [99999, 99999, 99999,   660, 99999, 99999,   320, 99999,   730,     0,   820],
    [99999, 99999, 99999, 99999,   930, 99999, 99999,   820,   320,   820,     0]
]
nodes = [str(i + 1) for i in range(len(graph))]

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if 0 < graph[i][j] < 9999:
            edges.append((nodes[i], nodes[j]))

rsa = {frozenset(link): [{'status': 'free', 'request_id': []} for _ in range(SLOTS)] for link in edges}

mod_formats = [
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

# --- Allocation Logic with Spectrum Conversion (Unchanged) ---
def are_paths_disjoint(path1, path2):
    links1 = {frozenset([path1[i], path1[i+1]]) for i in range(len(path1)-1)}
    links2 = {frozenset([path2[i], path2[i+1]]) for i in range(len(path2)-1)}
    return links1.isdisjoint(links2)


# --- allocate_segments (Uses the fixed, no-sharing version) ---
def allocate_segments(segments, request_id, path_type, primary_path_of_this_request):
    """
    Allocates segments by finding contiguous FREE slots.
    Backup paths are treated just like primary paths and require their own free slots.
    """
    if not segments: return None
    all_segment_allocations = []
    for seg_idx, seg in enumerate(segments):
        slots_needed = seg['slots']
        total_slots_with_guard = slots_needed + 1
        segment_allocated = False
        # Check if the required block size even fits within SLOTS
        if total_slots_with_guard > SLOTS:
             print(f"   Segment {seg_idx+1} requires {total_slots_with_guard} slots, exceeding total SLOTS ({SLOTS}). Cannot allocate.")
             return None

        for start_slot in range(SLOTS - total_slots_with_guard + 1):
            is_block_available = True
            for i in range(len(seg['path']) - 1):
                link = frozenset([seg['path'][i], seg['path'][i+1]])
                # Check if the block is free on this link
                for s in range(start_slot, start_slot + total_slots_with_guard):
                    # Boundary check
                    if s >= SLOTS:
                        is_block_available = False
                        print(f"   Error: Slot index {s} out of bounds during check.")
                        break
                    slot_info = rsa[link][s]
                    if slot_info['status'] != 'free':
                        is_block_available = False
                        break
                if not is_block_available: break

            if is_block_available:
                # Allocate the block on all links of the segment
                for i in range(len(seg['path']) - 1):
                    link = frozenset([seg['path'][i], seg['path'][i+1]])
                    # Allocate data slots
                    for s in range(start_slot, start_slot + slots_needed):
                       if s < SLOTS:
                           rsa[link][s]['status'] = path_type
                           rsa[link][s]['request_id'].append(request_id)
                    # Allocate guard slot
                    guard_slot_index = start_slot + slots_needed
                    if guard_slot_index < SLOTS:
                        rsa[link][guard_slot_index]['status'] = 'guard'
                        rsa[link][guard_slot_index]['request_id'].append('G')

                all_segment_allocations.append({'start_slot': start_slot, 'slots_needed': slots_needed})
                segment_allocated = True
                break # Found a slot block for this segment

        if not segment_allocated:
            print(f"   Segment {seg_idx+1} could not be allocated for Req #{request_id} ({path_type}). Rolling back previous segments.")
            deallocate_path(segments[:seg_idx], all_segment_allocations, request_id, path_type)
            return None # Allocation failed

    return all_segment_allocations

# --- deallocate_path (Uses the simplified, no-sharing version) ---
def deallocate_path(segments, allocations, request_id, path_type):
    """Deallocates a path by removing its request_id and 'G' marker, setting slots to 'free' if empty."""
    if not segments or not allocations: return
    for seg, alloc in zip(segments, allocations):
        start = alloc['start_slot']
        slots_needed = seg['slots']
        end = start + slots_needed + 1 # Deallocate data slots + guard slot

        for i in range(len(seg['path']) - 1):
            link = frozenset([seg['path'][i], seg['path'][i+1]])
            for s in range(start, end):
                if s >= SLOTS: continue

                slot_info = rsa[link][s]
                is_guard_slot = (s == start + slots_needed)

                if request_id in slot_info['request_id']:
                    slot_info['request_id'].remove(request_id)

                if is_guard_slot and 'G' in slot_info['request_id']:
                     slot_info['request_id'].remove('G')

                if not slot_info['request_id']:
                    slot_info['status'] = 'free'

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

# --- Helper function to prepare request details (MODIFIED) ---
def prepare_request(source, destination):
    """
    Prepares a request by finding paths and segments.
    MODIFIED: Removed direct logging to request_log. The caller will handle logging.
    """
    global request_id_counter
    request_id_counter += 1
    req_id = request_id_counter
    print(f"\n--- Preparing Request #{req_id}: {nodes[source]} -> {nodes[destination]} ---")
    x = random.choice([1,2,3,4,5,6])
    bandwidth = 20 * x
    log_entry = {'id': req_id, 'source': nodes[source], 'destination': nodes[destination], 'bandwidth': bandwidth, 'success': False, 'reason': ''}

    # --- Create a filtered graph that removes physically impossible single links ---
    filtered_graph = copy.deepcopy(graph)
    for i in range(len(graph)):
        for j in range(len(graph)):
            if filtered_graph[i][j] > MAX_REACH:
                filtered_graph[i][j] = 99999 # Make this link unusable

    # --- Find the primary path using the new filtered graph ---
    primary_path, primary_dist = find_shortest_path(source, destination, filtered_graph)
    if not primary_path:
        log_entry['reason'] = "No viable primary path found (all routes have unreachable segments)."
        print(f"FAILED: {log_entry['reason']}")
        # MODIFICATION: Do not append to request_log here.
        return None, log_entry, None, None, None, None

    # --- Find the backup path on a similarly filtered graph ---
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
    
    # --- The rest of the function remains the same ---
    primary_segments = process_path_for_segments(primary_path, primary_dist, bandwidth)
    backup_segments = process_path_for_segments(backup_path, backup_dist, bandwidth)
    
    if not primary_segments or not backup_segments:
        log_entry['reason'] = "Could not place regenerators on a viable path."
        print(f"FAILED: {log_entry['reason']}")
        return None, log_entry, None, None, None, None
    
    return req_id, log_entry, primary_path, backup_path, primary_segments, backup_segments

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

        req_id, log_entry, p_path, b_path, p_segments, b_segments = prepare_request(i, j)
        
        if not req_id:
            # This request failed pathfinding (primary or backup). Log it now.
            request_log.append(log_entry)
            continue

        # Store data for sorting
        p_path_len = len(p_path) # p_path is guaranteed to exist here
        b_path_len = len(b_path) # b_path is guaranteed to exist here
        
        all_requests_data.append({
            'req_id': req_id,
            'log_entry': log_entry,
            'p_path': p_path,
            'b_path': b_path,
            'p_segments': p_segments,
            'b_segments': b_segments,
            'p_path_len': p_path_len,
            'b_path_len': b_path_len
        })

# Now, perform the sort based on user criteria:
# 1. Primary path length (descending)
# 2. Backup path length (descending)
# 3. Request ID (ascending - for "first come first serve")
all_requests_data.sort(key=lambda x: (-x['p_path_len'], -x['b_path_len'], x['req_id']))

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
    
    p_allocations = allocate_segments(p_segments, req_id, 'primary', None)

    if p_allocations:
        # Add a print to show the sorting is working
        print(f"Request #{req_id}: Primary path SUCCESS (P_len:{req_data['p_path_len']}, B_len:{req_data['b_path_len']}). Queued for backup.")
        connection_info = {
            'primary_path': p_path, 'primary_details': p_segments, 'primary_allocations': p_allocations,
            'backup_path': b_path, 'backup_details': b_segments, 'backup_allocations': None,
            'success': False # Not fully successful until backup is allocated
        }
        active_connections[req_id] = connection_info
        log_entry.update(connection_info)
        request_log.append(log_entry) # Log success/failure *after* allocation attempt
        pending_backup_req_ids.append(req_id)
    else:
        # Add a print to show the sorting is working
        print(f"Request #{req_id}: Primary path FAILED (P_len:{req_data['p_path_len']}, B_len:{req_data['b_path_len']}). No spectrum.")
        log_entry['reason'] = "No spectrum available for primary path."
        request_log.append(log_entry) # Log success/failure *after* allocation attempt
    #show_slots()


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
            # This is a valid candidate. I'm using the strategy of maximizing the number
            # of shared links as a heuristic for maximizing slot sharing.
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
            for log in request_log:
                if log['id'] == req_id:
                    log.update(conn_info)
                    break
        else:
            print(f"  Request #{req_id}: Backup FAILED. Rolling back primary path.")
            deallocate_path(conn_info['primary_details'], conn_info['primary_allocations'], req_id, 'primary')
            del active_connections[req_id]
            for log in request_log:
                if log['id'] == req_id:
                    log['success'] = False
                    log['reason'] = "No spectrum available for shared backup path."
                    break
        #show_slots()

# --- Final Step: Update regenerator counts for all fully successful requests ---
update_final_regenerator_counts()


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
