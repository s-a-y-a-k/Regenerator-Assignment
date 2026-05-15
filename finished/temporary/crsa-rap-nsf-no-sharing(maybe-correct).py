import time
import random
import math
import copy
import itertools # Imported for finding combinations
random.seed(42)
start_time = time.perf_counter()

# --- Core Network and RSA Setup ---
SLOTS = 1000
graph = [
    [    0,  1100,   600,  1000, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],  # A
    [ 1100,     0,   600, 99999, 99999, 99999, 99999,  2800, 99999, 99999, 99999, 99999, 99999, 99999],  # B
    [  600,   600,     0, 99999, 99999,  2000, 99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999],  # C
    [ 1000, 99999, 99999,     0,   600, 99999, 99999, 99999, 99999, 99999,  2400, 99999, 99999, 99999],  # D
    [99999, 99999, 99999,   600,     0,  1100,   800, 99999, 99999, 99999, 99999, 99999, 99999, 99999],  # E
    [99999, 99999,  2000, 99999,  1100,     0, 99999, 99999, 99999,  1200, 99999, 99999, 99999,  2000],  # F
    [99999, 99999, 99999, 99999,   800, 99999,     0,   700, 99999,  1300, 99999, 99999, 99999, 99999],  # G
    [99999,  2800, 99999, 99999, 99999, 99999,   700,     0,   700, 99999, 99999, 99999, 99999, 99999],  # H
    [99999, 99999, 99999, 99999, 99999, 99999, 99999,   700,     0,   900, 99999,   500,   500, 99999],  # I
    [99999, 99999, 99999, 99999, 99999,  1200,  1300, 99999,   900,     0, 99999, 99999, 99999, 99999],  # J
    [99999, 99999, 99999,  2400, 99999, 99999, 99999, 99999, 99999, 99999,     0,   800,  1000, 99999],  # K
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999,   500, 99999,   800,     0, 99999,   500],  # L
    [99999, 99999, 99999, 99999, 99999, 99999, 99999, 99999,   500, 99999,  1000, 99999,     0,   300],  # M
    [99999, 99999, 99999, 99999, 99999,  2000, 99999, 99999, 99999, 99999, 99999,   500,   300,     0]   # N
]

nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']
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

MAX_REACH = max(m['reach'] for m in mod_formats)


request_log = []
request_id_counter = 0
active_connections = {}
regenerator_usage = {node: 0 for node in nodes}
# --- NEW: Changed counter name for the new algorithm ---
crsa_rap_used_count = 0


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
    # Sort links numerically based on node indices
    sorted_links = sorted(rsa.items(), key=lambda item: (min(nodes.index(n) for n in list(item[0])), max(nodes.index(n) for n in list(item[0]))))

    for link, slots in sorted_links:
        node_a, node_b = list(link)
        slot_display = []
        for slot_info in slots:
            if slot_info['status'] == 'free':
                slot_display.append('_')
            elif slot_info['status'] == 'primary':
                # Show only the first ID
                slot_display.append(f"P{slot_info['request_id'][0]}")
            elif slot_info['status'] == 'backup':
                 # Show only the first ID
                slot_display.append(f"B{slot_info['request_id'][0]}")
            elif slot_info['status'] == 'guard':
                slot_display.append('G')
            # Removed hybrid_backup display logic as it's not generated anymore

        print(f"{node_a} - {node_b} : {' '.join(slot_display)}")


# --- First Longest Reach (FLR) Regenerator Placement (Unchanged) ---
def place_flr_regenerators(path, bandwidth):
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

def calculate_segment_details(segment_path, bandwidth):
    """Calculates distance, modulation, and slots for a given path segment."""
    if len(segment_path) < 2: return None

    dist = sum(graph[nodes.index(segment_path[i])][nodes.index(segment_path[i+1])] for i in range(len(segment_path)-1))
    mod = get_best_mod(dist)
    if not mod: return None

    slots_needed = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
    return {'path': segment_path, 'dist': dist, 'mod': mod['name'], 'slots': slots_needed}

# --- Helper function to add/remove regenerator costs (Unchanged) ---
def update_regenerator_cost(segments, action='add'):
    """
    Updates the global 'regenerator_usage' dictionary.
    'action' can be 'add' or 'subtract'.
    """
    if not segments or len(segments) <= 1:
        return # No regenerators to update

    for seg in segments[:-1]: # Loop through all segments except the last one
        regen_node = seg['path'][-1]
        if action == 'add':
            regenerator_usage[regen_node] += 1
        elif action == 'subtract':
            if regenerator_usage[regen_node] > 0:
                regenerator_usage[regen_node] -= 1

# --- MODIFIED: CRSA-RAP Algorithm ---
def run_crsa_rap(path, bandwidth, flr_segments):
    """
    Implements Cost at Regeneration Site Aware Regenerator Assignment with Protection (CRSA-RAP).
    Finds a regenerator placement that minimizes usage of busy regenerator nodes,
    using total link-slots as a secondary metric.
    """
    num_regenerators_flr = len(flr_segments) - 1
    intermediate_nodes = path[1:-1]

    if num_regenerators_flr < 1 or len(intermediate_nodes) < num_regenerators_flr:
        return None

    print(f"     - Running CRSA-RAP with {num_regenerators_flr} regenerator(s) to find a cost-aware placement...")

    possible_placements = itertools.combinations(intermediate_nodes, num_regenerators_flr)

    valid_placements = []

    for placement_combo in possible_placements:
        sorted_regen_nodes = sorted(list(placement_combo), key=path.index)

        current_segments_temp = []
        is_valid_placement = True
        start_node_of_segment = path[0]

        for regen_node in sorted_regen_nodes:
            start_idx = path.index(start_node_of_segment)
            end_idx = path.index(regen_node)
            segment_path = path[start_idx : end_idx + 1]

            seg_details = calculate_segment_details(segment_path, bandwidth)
            if not seg_details:
                is_valid_placement = False
                break
            current_segments_temp.append(seg_details)
            start_node_of_segment = regen_node

        if not is_valid_placement:
            continue

        last_regen_node = sorted_regen_nodes[-1]
        start_idx = path.index(last_regen_node)
        final_segment_path = path[start_idx:]

        final_seg_details = calculate_segment_details(final_segment_path, bandwidth)
        if not final_seg_details:
            continue
        current_segments_temp.append(final_seg_details)

        # --- NEW: Calculate total link-slot usage for this placement ---
        current_total_link_slots = 0
        for seg in current_segments_temp:
            num_links_in_segment = len(seg['path']) - 1
            current_total_link_slots += seg['slots'] * num_links_in_segment
        # --- End NEW Calculation ---

        total_usage_cost = sum(regenerator_usage[node] for node in sorted_regen_nodes)

        valid_placements.append({
            'placement': sorted_regen_nodes,
            'segments': current_segments_temp,
            'total_link_slots': current_total_link_slots, # Store link-slots
            'usage_cost': total_usage_cost
        })

    if not valid_placements:
        return None

    # Sort primarily by usage_cost, secondarily by total_link_slots
    best_placement = sorted(valid_placements, key=lambda p: (p['usage_cost'], p['total_link_slots']))[0]

    # Return the dictionary containing best placement details, including total_link_slots
    return best_placement


# --- MODIFIED: Logic to decide on regeneration strategy using CRSA-RAP ---
def process_path_for_segments(path, path_dist, bandwidth):
    """
    Decides the best segmentation strategy by comparing FLR and CRSA-RAP,
    prioritizing usage_cost then total_link_slots.
    """
    global crsa_rap_used_count

    # Case 1: No regeneration needed
    best_mod_for_whole_path = get_best_mod(path_dist)
    if best_mod_for_whole_path:
        print(f"   Path can be established in a single segment with {best_mod_for_whole_path['name']}.")
        slots_needed = math.ceil(bandwidth / (best_mod_for_whole_path['capacity'] * best_mod_for_whole_path['efficiency']))
        # Calculate link-slots for printing
        num_links = len(path) - 1
        total_link_slots = slots_needed * num_links
        print(f"     - Total Link-Slots: {total_link_slots}.") # Modified print
        return [{'path': path, 'dist': path_dist, 'mod': best_mod_for_whole_path['name'], 'slots': slots_needed}]

    # Case 2: Regeneration needed, run FLR first
    print("   Path is too long. Running FLR to find baseline regenerator placement.")
    flr_segments = place_flr_regenerators(path, bandwidth)

    if not flr_segments:
        return None

    # Calculate FLR metrics
    # --- NEW: Calculate total link-slot usage for FLR ---
    flr_total_link_slots = 0
    for seg in flr_segments:
        num_links_in_segment = len(seg['path']) - 1
        flr_total_link_slots += seg['slots'] * num_links_in_segment
    # --- End NEW Calculation ---
    flr_regen_nodes = [seg['path'][-1] for seg in flr_segments[:-1]]
    flr_usage_cost = sum(regenerator_usage[node] for node in flr_regen_nodes)
    print(f"     - FLR Result: {len(flr_segments) - 1} regenerator(s) at {flr_regen_nodes}. Usage Cost: {flr_usage_cost}, Total Link-Slots: {flr_total_link_slots}.") # Modified print

    # Case 3: Try CRSA-RAP
    crsa_rap_best_placement = run_crsa_rap(path, bandwidth, flr_segments)

    if crsa_rap_best_placement:
        crsa_segments = crsa_rap_best_placement['segments']
        crsa_total_link_slots = crsa_rap_best_placement['total_link_slots'] # Get link-slots
        crsa_usage_cost = crsa_rap_best_placement['usage_cost']
        crsa_regen_nodes = crsa_rap_best_placement['placement']

        print(f"     - CRSA-RAP Best Find: Regenerator(s) at {crsa_regen_nodes}. Usage Cost: {crsa_usage_cost}, Total Link-Slots: {crsa_total_link_slots}.") # Modified print

        # --- MODIFIED: Comparison logic ---
        # Prioritize lower usage_cost, then lower total_link_slots
        if crsa_usage_cost < flr_usage_cost or \
           (crsa_usage_cost == flr_usage_cost and crsa_total_link_slots < flr_total_link_slots):

            # Check if the placement is actually different (avoid counting identical solutions as CRSA-RAP wins)
            if set(crsa_regen_nodes) != set(flr_regen_nodes) or crsa_total_link_slots < flr_total_link_slots:
                 print("   >> CRSA-RAP found a better solution. Using CRSA-RAP segmentation.")
                 crsa_rap_used_count += 1
                 return crsa_segments
            else:
                 print("   >> CRSA-RAP solution is identical or no better than FLR. Using FLR segmentation.")
                 return flr_segments
        else:
            print("   >> FLR solution is better or equal. Using FLR segmentation.")
            return flr_segments
        # --- End MODIFIED Comparison ---
    else:
        print("   >> CRSA-RAP not applicable or no better alternatives found. Using FLR segmentation.")
        return flr_segments


# --- Allocation Logic (Unchanged, uses the no-sharing version) ---
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

# --- MODIFIED: Helper function to prepare request details (structure unchanged, calls modified funcs) ---
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

    # --- Planning and Cost Update ---
    primary_segments = process_path_for_segments(primary_path, primary_dist, bandwidth)
    if not primary_segments:
        log_entry['reason'] = "Could not place regenerators on primary path."
        print(f"FAILED: {log_entry['reason']}")
        return None, log_entry, None, None, None, None

    # Tentatively add primary regenerator costs
    update_regenerator_cost(primary_segments, 'add')

    backup_segments = process_path_for_segments(backup_path, backup_dist, bandwidth)

    if not backup_segments:
        log_entry['reason'] = "Could not place regenerators on backup path."
        print(f"FAILED: {log_entry['reason']}")
        # Roll back the primary cost because the request failed
        update_regenerator_cost(primary_segments, 'subtract')
        return None, log_entry, None, None, None, None

    # Tentatively add backup regenerator costs
    update_regenerator_cost(backup_segments, 'add')

    return req_id, log_entry, primary_path, backup_path, primary_segments, backup_segments


# --- update_final_regenerator_counts (Unchanged) ---
def update_final_regenerator_counts():
    global regenerator_usage
    regenerator_usage = {node: 0 for node in nodes}
    for req_id, conn_info in active_connections.items():
        if conn_info['success']:
            primary_segments = conn_info.get('primary_details', [])
            if len(primary_segments) > 1:
                for i in range(len(primary_segments) - 1):
                    regenerator_node = primary_segments[i]['path'][-1]
                    regenerator_usage[regenerator_node] += 1

            backup_segments = conn_info.get('backup_details', [])
            if len(backup_segments) > 1:
                for i in range(len(backup_segments) - 1):
                    regenerator_node = backup_segments[i]['path'][-1]
                    regenerator_usage[regenerator_node] += 1

# --- Main Execution Loop (Structure Unchanged) ---

# --- Phase 1: Allocate all Primary Paths ---
print("\n" + "="*20 + " Phase 1: Primary Path Allocation " + "="*20)
pending_backup_req_ids = []

for i in range(len(graph)):
    for j in range(len(graph)):
        if i == j: continue

        req_id, log_entry, p_path, b_path, p_segments, b_segments = prepare_request(i, j)

        if not req_id:
            # Check if log entry already exists before appending
            found = False
            for entry in request_log:
                if entry['id'] == log_entry['id']:
                    found = True
                    break
            if not found:
                 request_log.append(log_entry)
            continue

        p_allocations = allocate_segments(p_segments, req_id, 'primary', None)

        if p_allocations:
            print(f"Request #{req_id}: Primary path SUCCESS. Queued for backup.")
            connection_info = {
                'primary_path': p_path, 'primary_details': p_segments, 'primary_allocations': p_allocations,
                'backup_path': b_path, 'backup_details': b_segments, 'backup_allocations': None,
                'success': False
            }
            active_connections[req_id] = connection_info
            log_entry.update(connection_info)
            request_log.append(log_entry)
            pending_backup_req_ids.append(req_id)

        else:
            print(f"Request #{req_id}: Primary path FAILED.")
            log_entry['reason'] = "No spectrum available for primary path."
            request_log.append(log_entry)

            # Roll back both planned costs
            update_regenerator_cost(p_segments, 'subtract')
            update_regenerator_cost(b_segments, 'subtract')

# --- Phase 2: Group Pending Backups (Structure Unchanged) ---
print("\n" + "="*20 + " Phase 2: Grouping Backup Paths " + "="*20)
mutually_exclusive_sets = []

# Filter pending_backup_req_ids to ensure they are still active before grouping
active_pending_ids = [req_id for req_id in pending_backup_req_ids if req_id in active_connections]


for req_id_to_place in active_pending_ids: # Use filtered list
    # Check again just in case (shouldn't be necessary with filtering above)
    if req_id_to_place not in active_connections: continue

    p_new = active_connections[req_id_to_place]['primary_path']
    b_new_path = active_connections[req_id_to_place]['backup_path']
    b_new_links = {frozenset([b_new_path[i], b_new_path[i+1]]) for i in range(len(b_new_path)-1)}

    candidate_sets = []

    for set_idx, current_set in enumerate(mutually_exclusive_sets):
        is_primary_disjoint_with_all = True
        is_backup_sharing_link = False # Check potential to share for grouping heuristic

        for existing_req_id in current_set:
            if existing_req_id not in active_connections: continue # Skip if already failed
            p_existing = active_connections[existing_req_id]['primary_path']
            if not are_paths_disjoint(p_new, p_existing):
                is_primary_disjoint_with_all = False
                break
        if not is_primary_disjoint_with_all:
            continue

        for existing_req_id in current_set:
            if existing_req_id not in active_connections: continue
            b_existing_path = active_connections[existing_req_id]['backup_path']
            b_existing_links = {frozenset([b_existing_path[i], b_existing_path[i+1]]) for i in range(len(b_existing_path)-1)}
            if not b_new_links.isdisjoint(b_existing_links):
                is_backup_sharing_link = True
                break

        if is_primary_disjoint_with_all and is_backup_sharing_link:
            total_shared_links = 0
            for existing_req_id in current_set:
                if existing_req_id not in active_connections: continue
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


# --- Phase 3: Allocate Backup Paths (Structure Unchanged, calls modified funcs) ---
print("\n" + "="*20 + " Phase 3: Backup Path Allocation " + "="*20)
mutually_exclusive_sets.sort(key=len, reverse=True)

for i, me_set in enumerate(mutually_exclusive_sets):
    print(f"\n--> Allocating backups for Set #{i} (size: {len(me_set)}): {me_set}")
    for req_id in me_set:
        # Check if request still active before processing backup
        if req_id not in active_connections: continue

        conn_info = active_connections[req_id]
        # Calls the modified allocate_segments (no sharing)
        b_allocations = allocate_segments(conn_info['backup_details'], req_id, 'backup', conn_info['primary_path'])

        if b_allocations:
            print(f"  Request #{req_id}: Backup SUCCESSFUL.")
            conn_info['backup_allocations'] = b_allocations
            conn_info['success'] = True
            # Update log entry
            for log in request_log:
                if log['id'] == req_id:
                    log.update(conn_info) # Update existing entry
                    break
        else:
            print(f"  Request #{req_id}: Backup FAILED. Rolling back primary path.")

            # Roll back costs for BOTH paths if backup allocation fails
            update_regenerator_cost(conn_info['primary_details'], 'subtract')
            update_regenerator_cost(conn_info['backup_details'], 'subtract')

            # Calls the modified deallocate_path
            deallocate_path(conn_info['primary_details'], conn_info['primary_allocations'], req_id, 'primary')
            # Remove from active connections ONLY if backup fails
            del active_connections[req_id]
            # Update log entry to reflect backup failure
            for log in request_log:
                if log['id'] == req_id:
                    log['success'] = False
                    log['reason'] = "No spectrum available for backup path (no sharing)." # Updated reason
                    # Remove allocation details from log
                    log.pop('primary_allocations', None)
                    log.pop('backup_allocations', None)
                    break
        # show_slots() # Keep commented out unless debugging


# --- Final Step: Update regenerator counts (Unchanged) ---
# This recalculates based on finally successful connections
update_final_regenerator_counts()


# --- MODIFIED: Final Statistics Calculation (Uses correct regenerator counts, updated fragmentation, updated CRSA-RAP print) ---
def calculate_and_print_statistics():
    """Calculates and prints all the final network performance metrics."""
    print("\n" + "="*25 + " Final Network Statistics " + "="*25)

    # a) Highest Utilized Spectrum Slot Index
    slot_utilization = [0] * SLOTS
    for link_slots in rsa.values():
        for i, slot_info in enumerate(link_slots):
            if slot_info['status'] != 'free':
                 if i < SLOTS: # Boundary check
                    slot_utilization[i] += 1

    if not any(slot_utilization):
        print("a) Highest Utilized Slot Index(es): None (No slots utilized)")
    else:
        max_utilization = max(slot_utilization)
        highest_utilized_indices = [i for i, v in enumerate(slot_utilization) if v == max_utilization]
        print(f"a) Highest Utilized Slot Index(es): {highest_utilized_indices} (used on {max_utilization} links)")

    # b) Total Spectrum Utilized Slots
    total_utilized_slots = sum(util for util in slot_utilization)
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
            # Removed hybrid_backup check

    print(f"d) Total Guard Bands Used: {total_guard_bands}")

    # e) % of Fragmentation
    total_fragmentation_metric = 0
    num_links_with_free_slots = 0 # Count links that have free slots to average over
    for link_slots in rsa.values():
        largest_free_block = 0
        current_free_block = 0
        total_free_slots = 0
        has_free_slots = False
        for slot_info in link_slots:
            if slot_info['status'] == 'free':
                current_free_block += 1
                total_free_slots += 1
                has_free_slots = True
            else:
                largest_free_block = max(largest_free_block, current_free_block)
                current_free_block = 0
        largest_free_block = max(largest_free_block, current_free_block) # Check block at the end

        if total_free_slots > 0:
            link_fragmentation = 1.0 - (largest_free_block / float(total_free_slots)) # Use float division
            total_fragmentation_metric += link_fragmentation
            num_links_with_free_slots += 1 # Increment counter

    # Average fragmentation only over links that had free slots
    average_fragmentation = (total_fragmentation_metric / num_links_with_free_slots) if num_links_with_free_slots > 0 else 0
    print(f"e) Network Fragmentation: {average_fragmentation:.2%}")

    # f) Total Number of Regenerations (Uses final counts)
    total_regenerations = sum(regenerator_usage.values())
    print(f"f) Total Number of Regenerations: {total_regenerations}")

    # g) Regenerator Node Usage (Uses final counts)
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

    # i) CRSA-RAP Algorithm Usage Report
    print("i) CRSA-RAP Algorithm Usage:")
    if crsa_rap_used_count == 0:
        print("   - CRSA-RAP was not used. For this topology, FLR was always better or equal.")
    else:
        print(f"   - CRSA-RAP found a more cost-aware or link-slot-efficient solution {crsa_rap_used_count} time(s).") # Modified print


# --- Detailed Request Log (Structure Unchanged) ---
print("\n" + "="*25 + " Request Log Summary " + "="*25)
# Sort log by request ID for consistent output
request_log.sort(key=lambda x: x['id'])
count=1
for req in request_log:
    status = "SUCCESS" if req.get('success', False) else "FAILED" # Use .get for safety
    print(f"\n--- Req #{req['id']}: {req['source']} -> {req['destination']}, Status: {status} ---")
    print(f"   - Bandwidth: {req['bandwidth']} Gbps")

    if req.get('success', False): # Check success status safely
        print("   - Primary Path Details:")
        if req.get('primary_details') and req.get('primary_allocations'):
            for seg_num, (segment, alloc) in enumerate(zip(req['primary_details'], req['primary_allocations'])):
                start = alloc.get('start_slot', -1) # Use .get for safety
                slots_needed = alloc.get('slots_needed', segment.get('slots', 0))
                if start != -1 and slots_needed > 0:
                   end = start + slots_needed - 1
                   print(f"     * Segment {seg_num+1}: {' -> '.join(segment.get('path',[]))} | Slots Used: {start}-{end}")
                   print(f"       Modulation: {segment.get('mod', 'N/A')}, Slots Needed (for each link): {segment.get('slots', 'N/A')}")
                else:
                    print(f"     * Segment {seg_num+1}: {' -> '.join(segment.get('path',[]))} | Allocation data missing.")


        print("   - Backup Path Details:")
        if req.get('backup_details') and req.get('backup_allocations'):
                for seg_num, (segment, alloc) in enumerate(zip(req['backup_details'], req['backup_allocations'])):
                    start = alloc.get('start_slot', -1)
                    slots_needed = alloc.get('slots_needed', segment.get('slots', 0))
                    if start != -1 and slots_needed > 0:
                        end = start + slots_needed - 1
                        print(f"     * Segment {seg_num+1}: {' -> '.join(segment.get('path',[]))} | Slots Used: {start}-{end}")
                        print(f"       Modulation: {segment.get('mod', 'N/A')}, Slots Needed (for each link): {segment.get('slots', 'N/A')}")
                    else:
                         print(f"     * Segment {seg_num+1}: {' -> '.join(segment.get('path',[]))} | Allocation data missing.")

    else:
        # Provide reason, default if not set
        print(f"   - Reason for Failure: {req.get('reason', 'Unknown')}")
    print("Count = ", count)
    count+=1


# --- Print Final Statistics ---
calculate_and_print_statistics()