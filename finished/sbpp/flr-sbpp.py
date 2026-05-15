import time
import random
import math
import copy

start_time = time.perf_counter()

# --- Core Network and RSA Setup ---
SLOTS = 100
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

# MODIFICATION: New RSA structure to support sharing
rsa = {frozenset(link): [{'status': 'free', 'request_id': None} for _ in range(SLOTS)] for link in edges}

mod_formats = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 8000},
    {'name': 'QPSK', 'capacity': 12.5, 'efficiency': 2, 'reach': 4000},
    {'name': '8-QAM', 'capacity': 12.5, 'efficiency': 3, 'reach': 2000},
    {'name': '16-QAM', 'capacity': 12.5, 'efficiency': 4, 'reach': 1000},
    {'name': '32-QAM', 'capacity': 12.5, 'efficiency': 5, 'reach': 500},
    {'name': '64-QAM', 'capacity': 12.5, 'efficiency': 6, 'reach': 250}
]

# MODIFICATION: Globals to track requests for sharing logic
request_log = []
request_id_counter = 0
active_connections = {}

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
    # Sort links for a consistent, readable output order
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

# --- NEW: First Longest Reach (FLR) Regenerator Placement ---
def place_flr_regenerators(path, bandwidth):
    """
    Implements the First Longest Reach (FLR) regenerator placement strategy.
    """
    if not path or len(path) < 2:
        return None
        
    segments = []
    current_node_idx = 0
    max_reach = max(m['reach'] for m in mod_formats)

    while current_node_idx < len(path) - 1:
        farthest_reach_idx = -1
        
        # Find the farthest node we can reach from the current node
        for next_node_idx in range(current_node_idx + 1, len(path)):
            sub_path = path[current_node_idx : next_node_idx + 1]
            dist = sum(graph[nodes.index(sub_path[i])][nodes.index(sub_path[i+1])] for i in range(len(sub_path)-1))
            
            if dist <= max_reach:
                farthest_reach_idx = next_node_idx
            else:
                break # Path becomes too long

        if farthest_reach_idx == -1:
            # This happens if the very next hop is unreachable, meaning the path is invalid.
            return None
        
        # Create the segment
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
        
        # Move to the start of the next segment
        current_node_idx = farthest_reach_idx

    return segments

# --- NEW: Shared Backup Path Protection (SBPP) Allocation Logic ---

def are_paths_disjoint(path1, path2):
    """Checks if two paths are link-disjoint."""
    links1 = {frozenset([path1[i], path1[i+1]]) for i in range(len(path1)-1)}
    for i in range(len(path2)-1):
        if frozenset([path2[i], path2[i+1]]) in links1:
            return False
    return True

def allocate_primary_path(segments, request_id):
    """Allocates resources for a primary path. Slots must be entirely free."""
    max_slots_needed = max(s['slots'] for s in segments)
    total_slots_with_guard = max_slots_needed + 1
    
    for start_slot in range(SLOTS - total_slots_with_guard + 1):
        is_block_free = True
        for seg in segments:
            for i in range(len(seg['path']) - 1):
                link = frozenset([seg['path'][i], seg['path'][i+1]])
                for s in range(start_slot, start_slot + total_slots_with_guard):
                    if rsa[link][s]['status'] != 'free':
                        is_block_free = False
                        break
                if not is_block_free: break
            if not is_block_free: break
        
        if is_block_free:
            # Allocate the block
            for seg in segments:
                 for i in range(len(seg['path']) - 1):
                    link = frozenset([seg['path'][i], seg['path'][i+1]])
                    for s in range(start_slot, start_slot + max_slots_needed):
                        rsa[link][s] = {'status': 'primary', 'request_id': request_id}
                    rsa[link][start_slot + max_slots_needed] = {'status': 'primary', 'request_id': request_id} # Guard
            return start_slot, max_slots_needed
    return None, None

def allocate_backup_path(segments, request_id, primary_path_of_this_request):
    """Allocates resources for a backup path, allowing sharing."""
    max_slots_needed = max(s['slots'] for s in segments)
    total_slots_with_guard = max_slots_needed + 1

    for start_slot in range(SLOTS - total_slots_with_guard + 1):
        is_block_shareable = True
        for seg in segments:
            for i in range(len(seg['path']) - 1):
                link = frozenset([seg['path'][i], seg['path'][i+1]])
                for s in range(start_slot, start_slot + total_slots_with_guard):
                    slot_info = rsa[link][s]
                    if slot_info['status'] == 'primary':
                        is_block_shareable = False # CANNOT share with a primary path
                        break
                    if slot_info['status'] == 'backup':
                        # This is the core sharing logic
                        other_req_id = slot_info['request_id']
                        other_primary_path = active_connections[other_req_id]['primary_path']
                        if not are_paths_disjoint(primary_path_of_this_request, other_primary_path):
                            is_block_shareable = False # Can't share if primary paths are NOT disjoint
                            break
                if not is_block_shareable: break
            if not is_block_shareable: break

        if is_block_shareable:
            # Allocate the block
            for seg in segments:
                for i in range(len(seg['path']) - 1):
                    link = frozenset([seg['path'][i], seg['path'][i+1]])
                    for s in range(start_slot, start_slot + max_slots_needed):
                        if rsa[link][s]['status'] == 'free': # Only overwrite free slots
                           rsa[link][s] = {'status': 'backup', 'request_id': request_id}
                    if rsa[link][start_slot + max_slots_needed]['status'] == 'free':
                        rsa[link][start_slot + max_slots_needed] = {'status': 'backup', 'request_id': request_id} # Guard
            return start_slot, max_slots_needed
    return None, None

def deallocate_path(segments, request_id):
    """Frees up resources for a given request ID (used for rollback)."""
    for seg in segments:
        for i in range(len(seg['path']) - 1):
            link = frozenset([seg['path'][i], seg['path'][i+1]])
            for s in range(SLOTS):
                if rsa[link][s]['request_id'] == request_id:
                    rsa[link][s] = {'status': 'free', 'request_id': None}

# --- Main Request Handling Logic (UPDATED for SBPP) ---
def request(source, destination):
    global request_id_counter
    request_id_counter += 1
    req_id = request_id_counter

    print(f"\n--- New Request #{req_id}: {nodes[source]} -> {nodes[destination]} ---")
    bandwidth = random.randint(100, 401)
    
    primary_path, _ = find_shortest_path(source, destination, graph)
    if not primary_path:
        print("Request FAILED: No primary path found.")
        return

    backup_path, _ = get_disjoint_path(primary_path, source, destination)
    if not backup_path:
        print("Request FAILED: No link-disjoint backup path found.")
        return

    primary_segments = place_flr_regenerators(primary_path, bandwidth)
    backup_segments = place_flr_regenerators(backup_path, bandwidth)
    
    if not primary_segments or not backup_segments:
        print("Request FAILED: Could not place regenerators on a path.")
        return

    # 1. Allocate Primary Path
    primary_start_slot, primary_slots = allocate_primary_path(primary_segments, req_id)
    if primary_start_slot is None:
        print("Request FAILED: No spectrum available for primary path.")
        return

    # 2. Allocate Backup Path (with sharing)
    backup_start_slot, backup_slots = allocate_backup_path(backup_segments, req_id, primary_path)
    if backup_start_slot is None:
        print("Request FAILED: No spectrum available for shared backup path. Rolling back primary allocation.")
        deallocate_path(primary_segments, req_id) # Rollback
        return

    # 3. Success: Log and store connection info
    print(f"Request SUCCESS: Primary on slots {primary_start_slot}-{primary_start_slot+primary_slots}, Backup on {backup_start_slot}-{backup_start_slot+backup_slots}")
    connection_info = {
        'primary_path': primary_path, 'primary_details': primary_segments,
        'backup_path': backup_path, 'backup_details': backup_segments, 'success': True
    }
    active_connections[req_id] = connection_info
    request_log.append(connection_info)

# --- Main Execution Loop ---
for i in range(len(graph)):
    for j in range(len(graph)):
        if i != j:
            request(i, j)

# --- Final Reporting ---
print("\n" + "="*25 + " Final Statistics " + "="*25)
success_count = len(active_connections)
total_requests = request_id_counter
blocking_probability = (total_requests - success_count) / total_requests if total_requests else 0
print(f"\nTotal Requests: {total_requests}")
print(f"Successful Requests: {success_count}")
print(f"Failed/Blocked Requests: {total_requests - success_count}")
print(f"Blocking Probability: {blocking_probability:.2%}")

