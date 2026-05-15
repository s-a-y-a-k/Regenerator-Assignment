import time
import random
import math
import copy
random.seed(42)

# --- Core Network and RSA Setup ---
SLOTS = 100
GRAPH_DEFINITION = [
    [0, 1000, 1200, 9999, 9999, 9999], [1000, 0, 600, 800, 1000, 9999],
    [1200, 600, 0, 9999, 800, 9999], [9999, 800, 9999, 0, 600, 1000],
    [9999, 1000, 800, 600, 0, 1200], [9999, 9999, 9999, 1000, 1200, 0]
]
NODES = [str(i + 1) for i in range(len(GRAPH_DEFINITION))]
EDGES = []
for i in range(len(GRAPH_DEFINITION)):
    for j in range(i + 1, len(GRAPH_DEFINITION)):
        if 0 < GRAPH_DEFINITION[i][j] < 9999:
            EDGES.append((NODES[i], NODES[j]))

MOD_FORMATS = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 8000},
    {'name': 'QPSK', 'capacity': 12.5, 'efficiency': 2, 'reach': 4000},
    {'name': '8-QAM', 'capacity': 12.5, 'efficiency': 3, 'reach': 2000},
    {'name': '16-QAM', 'capacity': 12.5, 'efficiency': 4, 'reach': 1000},
    {'name': '32-QAM', 'capacity': 12.5, 'efficiency': 5, 'reach': 500},
    {'name': '64-QAM', 'capacity': 12.5, 'efficiency': 6, 'reach': 250}
]
MAX_REACH = max(m['reach'] for m in MOD_FORMATS)

# --- Global State Variables (managed by reset_network_state) ---
graph = None
rsa = None
request_log = None
request_id_counter = None
active_connections = None

def reset_network_state():
    """Resets all network state variables for a fresh simulation run."""
    global graph, rsa, request_log, request_id_counter, active_connections
    graph = copy.deepcopy(GRAPH_DEFINITION)
    rsa = {frozenset(link): [{'status': 'free', 'request_id': None} for _ in range(SLOTS)] for link in EDGES}
    request_log = []
    request_id_counter = 0
    active_connections = {}
    print("\nNetwork state has been reset for the new simulation.")

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
        return [NODES[i] for i in path], distance[destination]
    return None, None

def get_disjoint_path(primary_path, source, destination):
    temp_graph = copy.deepcopy(graph)
    for i in range(len(primary_path) - 1):
        u_idx, v_idx = NODES.index(primary_path[i]), NODES.index(primary_path[i+1])
        temp_graph[u_idx][v_idx] = 9999
        temp_graph[v_idx][u_idx] = 9999
    return find_shortest_path(source, destination, temp_graph)

def get_best_mod(distance):
    valid_mods = [m for m in MOD_FORMATS if m['reach'] >= distance]
    return max(valid_mods, key=lambda m: m['efficiency']) if valid_mods else None

# --- Regenerator Placement Strategy Functions ---

def show_slots():
    """Prints a visual representation of the current slot usage on all links."""
    print("\nCurrent Slot Usage:")
    sorted_links = sorted(rsa.items(), key=lambda item: (min(int(n) for n in list(item[0])), max(int(n) for n in list(item[0]))))
    
    for link, slots in sorted_links:
        node_a, node_b = list(link)
        slot_display = []
        for slot_info in slots:
            if slot_info['status'] == 'free':
                slot_display.append('_')
            elif slot_info['status'] == 'primary':
                slot_display.append(f"P{slot_info['request_id']}")
            elif slot_info['status'] == 'backup':
                slot_display.append(f"B{slot_info['request_id']}")
        print(f"{node_a} - {node_b} : {' '.join(slot_display)}")

def place_flr_regenerators(path, bandwidth):
    if not path or len(path) < 2: return None
    segments, current_node_idx = [], 0
    while current_node_idx < len(path) - 1:
        farthest_reach_idx = -1
        for next_node_idx in range(current_node_idx + 1, len(path)):
            sub_path = path[current_node_idx : next_node_idx + 1]
            dist = sum(graph[NODES.index(sub_path[i])][NODES.index(sub_path[i+1])] for i in range(len(sub_path)-1))
            if dist <= MAX_REACH: farthest_reach_idx = next_node_idx
            else: break
        if farthest_reach_idx == -1: return None
        final_path = path[current_node_idx : farthest_reach_idx + 1]
        dist = sum(graph[NODES.index(final_path[i])][NODES.index(final_path[i+1])] for i in range(len(final_path)-1))
        mod = get_best_mod(dist)
        if not mod: return None
        slots = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
        segments.append({'path': final_path, 'dist': dist, 'mod': mod['name'], 'slots': slots})
        current_node_idx = farthest_reach_idx
    return segments

def place_fnr_regenerators(path, bandwidth):
    if not path or len(path) < 2: return None
    segments, current_node_idx = [], 0
    while current_node_idx < len(path) - 1:
        segment_start_idx, end_idx = current_node_idx, current_node_idx
        for possible_end_idx in range(segment_start_idx + 1, len(path)):
            current_sub_path = path[segment_start_idx : possible_end_idx + 1]
            current_dist = sum(graph[NODES.index(p)][NODES.index(current_sub_path[i+1])] for i, p in enumerate(current_sub_path[:-1]))
            current_mod = get_best_mod(current_dist)
            if not current_mod:
                end_idx = possible_end_idx - 1
                break
            if possible_end_idx + 1 < len(path):
                next_sub_path = path[segment_start_idx : possible_end_idx + 2]
                next_dist = sum(graph[NODES.index(p)][NODES.index(next_sub_path[i+1])] for i,p in enumerate(next_sub_path[:-1]))
                next_mod = get_best_mod(next_dist)
                if not next_mod or next_mod['efficiency'] < current_mod['efficiency']:
                    end_idx = possible_end_idx
                    break
            end_idx = possible_end_idx
        final_path = path[segment_start_idx : end_idx + 1]
        final_dist = sum(graph[NODES.index(p)][NODES.index(final_path[i+1])] for i, p in enumerate(final_path[:-1]))
        final_mod = get_best_mod(final_dist)
        if not final_mod: return None
        slots = math.ceil(bandwidth / (final_mod['capacity'] * final_mod['efficiency']))
        segments.append({'path': final_path, 'dist': final_dist, 'mod': final_mod['name'], 'slots': slots})
        current_node_idx = end_idx
    return segments

def place_regenerator_closest_to_start(path, bandwidth):
    if not path or len(path) < 2: return None
    if len(path) == 2:
        dist = graph[NODES.index(path[0])][NODES.index(path[1])]
        mod = get_best_mod(dist)
        if mod:
            slots = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
            return [{'path': path, 'dist': dist, 'mod': mod['name'], 'slots': slots}]
        return None
    for i, regen_node in enumerate(path[1:-1]):
        path1, path2 = path[:i + 2], path[i + 1:]
        dist1 = sum(graph[NODES.index(p1)][NODES.index(path1[j+1])] for j, p1 in enumerate(path1[:-1]))
        dist2 = sum(graph[NODES.index(p2)][NODES.index(path2[j+1])] for j, p2 in enumerate(path2[:-1]))
        mod1, mod2 = get_best_mod(dist1), get_best_mod(dist2)
        if mod1 and mod2:
            slots1 = math.ceil(bandwidth / (mod1['capacity'] * mod1['efficiency']))
            slots2 = math.ceil(bandwidth / (mod2['capacity'] * mod2['efficiency']))
            return [{'path': path1, 'dist': dist1, 'mod': mod1['name'], 'slots': slots1},
                    {'path': path2, 'dist': dist2, 'mod': mod2['name'], 'slots': slots2}]
    return None

def place_forced_regenerator_aware(path, bandwidth):
    if not path or len(path) < 2: return None
    if len(path) == 2:
        dist = graph[NODES.index(path[0])][NODES.index(path[1])]
        mod = get_best_mod(dist)
        if mod:
            slots = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
            return [{'path': path, 'dist': dist, 'mod': mod['name'], 'slots': slots}]
        return None
    best_segmentation, min_slots_needed = None, float('inf')
    for i, regen_node in enumerate(path[1:-1]):
        path1, path2 = path[:i + 2], path[i + 1:]
        dist1 = sum(graph[NODES.index(p1)][NODES.index(path1[j+1])] for j,p1 in enumerate(path1[:-1]))
        dist2 = sum(graph[NODES.index(p2)][NODES.index(path2[j+1])] for j,p2 in enumerate(path2[:-1]))
        mod1, mod2 = get_best_mod(dist1), get_best_mod(dist2)
        if mod1 and mod2:
            slots1 = math.ceil(bandwidth / (mod1['capacity'] * mod1['efficiency']))
            slots2 = math.ceil(bandwidth / (mod2['capacity'] * mod2['efficiency']))
            current_max_slots = max(slots1, slots2)
            if current_max_slots < min_slots_needed:
                min_slots_needed = current_max_slots
                best_segmentation = [{'path': path1, 'dist': dist1, 'mod': mod1['name'], 'slots': slots1},
                                     {'path': path2, 'dist': dist2, 'mod': mod2['name'], 'slots': slots2}]
    return best_segmentation

# --- Allocation and Main Logic ---
def are_paths_disjoint(path1, path2):
    links1 = {frozenset([path1[i], path1[i+1]]) for i in range(len(path1)-1)}
    for i in range(len(path2)-1):
        if frozenset([path2[i], path2[i+1]]) in links1:
            return False
    return True

def allocate_segments(segments, request_id, path_type, primary_path_of_this_request=None):
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
                        is_block_available = False; break
                    if path_type == 'backup':
                        if slot_info['status'] == 'primary': is_block_available = False; break
                        if slot_info['status'] == 'backup':
                            other_req_id = slot_info['request_id']
                            if other_req_id in active_connections:
                                other_primary_path = active_connections[other_req_id]['primary_path']
                                if not are_paths_disjoint(primary_path_of_this_request, other_primary_path):
                                    is_block_available = False; break
                if not is_block_available: break
            if is_block_available:
                for i in range(len(seg['path']) - 1):
                    link = frozenset([seg['path'][i], seg['path'][i+1]])
                    for s in range(start_slot, start_slot + slots_needed):
                        if path_type == 'primary' or (path_type == 'backup' and rsa[link][s]['status'] == 'free'):
                           rsa[link][s] = {'status': path_type, 'request_id': request_id}
                    if path_type == 'primary' or (path_type == 'backup' and rsa[link][start_slot + slots_needed]['status'] == 'free'):
                        rsa[link][start_slot + slots_needed] = {'status': path_type, 'request_id': request_id}
                all_segment_allocations.append({'start_slot': start_slot, 'slots_needed': slots_needed})
                segment_allocated = True
                break
        if not segment_allocated:
            deallocate_path(segments[:seg_idx], all_segment_allocations, request_id)
            return None
    return all_segment_allocations

def deallocate_path(segments, allocations, request_id):
    if not segments or not allocations: return
    for seg, alloc in zip(segments, allocations):
        start, end = alloc['start_slot'], alloc['start_slot'] + alloc['slots_needed'] + 1
        for i in range(len(seg['path']) - 1):
            link = frozenset([seg['path'][i], seg['path'][i+1]])
            for s in range(start, end):
                if s < SLOTS and rsa[link][s]['request_id'] == request_id:
                    rsa[link][s] = {'status': 'free', 'request_id': None}

def request(source, destination, placement_function):
    global request_id_counter
    request_id_counter += 1
    req_id = request_id_counter
    bandwidth = random.randint(100, 401)
    log_entry = {'id': req_id, 'source': NODES[source], 'destination': NODES[destination], 'bandwidth': bandwidth, 'success': False, 'reason': ''}
    primary_path, _ = find_shortest_path(source, destination, graph)
    if not primary_path:
        log_entry['reason'] = "No primary path"; request_log.append(log_entry); return
    backup_path, _ = get_disjoint_path(primary_path, source, destination)
    if not backup_path:
        log_entry['reason'] = "No disjoint backup path"; request_log.append(log_entry); return
    primary_segments = placement_function(primary_path, bandwidth)
    backup_segments = placement_function(backup_path, bandwidth)
    if not primary_segments or not backup_segments:
        log_entry['reason'] = "Regenerator placement failed"; request_log.append(log_entry); return
    primary_allocations = allocate_segments(primary_segments, req_id, 'primary')
    if not primary_allocations:
        log_entry['reason'] = "Primary allocation failed"; request_log.append(log_entry); return
    backup_allocations = allocate_segments(backup_segments, req_id, 'backup', primary_path)
    if not backup_allocations:
        log_entry['reason'] = "Backup allocation failed"
        deallocate_path(primary_segments, primary_allocations, req_id)
        request_log.append(log_entry); return
    connection_info = {
        'primary_path': primary_path, 'primary_details': primary_segments, 'primary_allocations': primary_allocations,
        'backup_path': backup_path, 'backup_details': backup_segments, 'backup_allocations': backup_allocations,
        'success': True
    }
    active_connections[req_id] = connection_info
    log_entry.update(connection_info)
    request_log.append(log_entry)

# --- Statistics and Simulation Runner ---
def calculate_and_print_statistics(sim_start_time):
    print("\n" + "="*25 + " Final Network Statistics " + "="*25)
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
    total_utilized_slots = sum(slot_utilization)
    print(f"b) Total Spectrum Utilized Slots: {total_utilized_slots}")
    success_count = len(active_connections)
    total_requests = request_id_counter
    blocked_requests = total_requests - success_count
    blocking_probability = (blocked_requests / total_requests) if total_requests else 0
    print(f"c) Request Blocking Probability: {blocking_probability:.2%} ({blocked_requests} blocked / {total_requests} total)")
    
    # MODIFICATION: Added Total Number of Regenerations calculation
    total_regenerations = 0
    total_guard_bands = 0
    for req in request_log:
        if req['success']:
            num_primary_segments = len(req.get('primary_details', []))
            num_backup_segments = len(req.get('backup_details', []))
            total_guard_bands += num_primary_segments + num_backup_segments
            if num_primary_segments > 1:
                total_regenerations += num_primary_segments - 1
            if num_backup_segments > 1:
                total_regenerations += num_backup_segments - 1
                
    print(f"d) Total Guard Bands Used: {total_guard_bands}")
    print(f"e) Total Number of Regenerations: {total_regenerations}")

    # e) % of Fragmentation
    total_fragmentation_metric = 0
    for link_slots in rsa.values():
        largest_free_block, current_free_block, total_free_slots = 0, 0, 0
        for slot_info in link_slots:
            if slot_info['status'] == 'free':
                current_free_block += 1
                total_free_slots += 1
            else:
                largest_free_block = max(largest_free_block, current_free_block)
                current_free_block = 0
        largest_free_block = max(largest_free_block, current_free_block)
        if total_free_slots > 0:
            total_fragmentation_metric += 1 - (largest_free_block / total_free_slots)
    average_fragmentation = (total_fragmentation_metric / len(EDGES)) if EDGES else 0
    print(f"f) Network Fragmentation: {average_fragmentation:.2%}")
    
    # f) Execution Time
    sim_end_time = time.perf_counter()
    print(f"g) Simulation Execution Time: {sim_end_time - sim_start_time:.4f} seconds")

def run_simulation(placement_strategy_func, strategy_name):
    """Runs a full simulation for a given regenerator placement strategy."""
    reset_network_state()
    sim_start_time = time.perf_counter()
    print(f"\n--- Running Simulation for: {strategy_name} ---")
    for i in range(len(graph)):
        for j in range(len(graph)):
            if i != j:
                request(i, j, placement_strategy_func)
    print("\n--- Simulation Complete ---")
    show_slots()
    calculate_and_print_statistics(sim_start_time)

def main():
    """Main function to display menu and handle user choices."""
    strategy_map = {
        '1': (place_flr_regenerators, "First Longest Reach (FLR)"),
        '2': (place_fnr_regenerators, "First Narrowest Reach (FNR)"),
        '3': (place_regenerator_closest_to_start, "Closest-to-Start"),
        '4': (place_forced_regenerator_aware, "Forced Regenerator-Aware")
    }
    while True:
        print("\n" + "="*10 + " Optical Network Simulation Menu " + "="*10)
        print("Choose a regenerator placement strategy to simulate:")
        print(" 1) First Longest Reach (FLR)")
        print(" 2) First Narrowest Reach (FNR)")
        print(" 3) Closest-to-Start")
        print(" 4) Forced Regenerator-Aware (R-Aware)")
        print(" 5) End Program")
        choice = input("Enter your choice (1-5): ")

        if choice in strategy_map:
            strategy_func, strategy_name = strategy_map[choice]
            run_simulation(strategy_func, strategy_name)
        elif choice == '5':
            print("Ending program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()
