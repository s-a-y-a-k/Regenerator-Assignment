import time
import random
import math
import copy

start_time = time.perf_counter()

# --- Core Network and RSA Setup (Unchanged) ---
SLOTS = 100
graph = [
    [0, 1000, 1200, 9999, 9999, 9999],
    [1000, 0, 600, 800, 1000, 9999],
    [1200, 600, 0, 9999, 800, 9999],
    [9999, 800, 9999, 0, 600, 1000],
    [9999, 1000, 800, 600, 0, 1200],
    [9999, 9999, 9999, 1000, 1200, 0]
]

nodes = [str(i + 1) for i in range(len(graph))]
regenerators = nodes  # All nodes can act as regenerators

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if 0 < graph[i][j] < 9999:
            edges.append((nodes[i], nodes[j]))
print("The edges are: ", edges)

rsa = {frozenset([i, j]): [0] * SLOTS for i, j in edges}

mod_formats = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 8000},
    {'name': 'QPSK', 'capacity': 12.5, 'efficiency': 2, 'reach': 4000},
    {'name': '8-QAM', 'capacity': 12.5, 'efficiency': 3, 'reach': 2000},
    {'name': '16-QAM', 'capacity': 12.5, 'efficiency': 4, 'reach': 1000},
    {'name': '32-QAM', 'capacity': 12.5, 'efficiency': 5, 'reach': 500},
    {'name': '64-QAM', 'capacity': 12.5, 'efficiency': 6, 'reach': 250}
]
MAX_REACH = max(m['reach'] for m in mod_formats)

request_log = []

def show_slots():
    print("\nCurrent Slot Usage:")
    for links, slots in rsa.items():
        node_a, node_b = list(links)
        print(f"{node_a} - {node_b} : {slots}")

# --- Pathfinding and Modulation (Unchanged) ---

def find_shortest_path(source, destination, current_graph):
    """Dijkstra's algorithm on a given graph matrix."""
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
                min_distance = distance[i]
                u = i
        
        if u == -1:
            break

        visited[u] = True
        for v in range(n):
            if current_graph[u][v] > 0 and not visited[v]:
                new_dist = distance[u] + current_graph[u][v]
                if new_dist < distance[v]:
                    distance[v] = new_dist
                    previous[v] = u

    path = []
    curr = destination
    if distance[curr] < 9999:
        while curr is not None:
            path.insert(0, curr)
            curr = previous[curr]
        return [nodes[i] for i in path], distance[destination]
    return None, None

def get_disjoint_path(primary_path, source, destination):
    """Finds a link-disjoint path by temporarily modifying the graph."""
    temp_graph = copy.deepcopy(graph)
    for i in range(len(primary_path) - 1):
        u_idx, v_idx = nodes.index(primary_path[i]), nodes.index(primary_path[i+1])
        temp_graph[u_idx][v_idx] = 9999
        temp_graph[v_idx][u_idx] = 9999
    
    return find_shortest_path(source, destination, temp_graph)

def get_best_mod(distance):
    """Selects the most spectrally efficient modulation for a given distance."""
    valid_mods = [m for m in mod_formats if m['reach'] >= distance]
    return max(valid_mods, key=lambda m: m['efficiency']) if valid_mods else None

# --- NEW: First Narrowest Reach (FNR) Regenerator Placement ---

def place_fnr_regenerators(path, bandwidth):
    """
    Implements the First Narrowest Reach (FNR) regenerator placement strategy.
    Places a regenerator when the path requires a step-down in modulation efficiency.
    """
    if not path:
        return None
        
    segments = []
    current_node_idx = 0

    while current_node_idx < len(path) - 1:
        start_of_segment_idx = current_node_idx
        end_of_segment_idx = -1
        last_valid_mod = None

        # Find the point where modulation efficiency drops
        for next_node_idx in range(start_of_segment_idx + 1, len(path)):
            sub_path = path[start_of_segment_idx : next_node_idx + 1]
            dist = sum(graph[nodes.index(sub_path[i])][nodes.index(sub_path[i+1])] for i in range(len(sub_path)-1))
            
            current_best_mod = get_best_mod(dist)

            if current_best_mod is None:
                end_of_segment_idx = next_node_idx - 1
                break

            if last_valid_mod and current_best_mod['efficiency'] < last_valid_mod['efficiency']:
                end_of_segment_idx = next_node_idx - 1
                break
            
            last_valid_mod = current_best_mod
        
        # If we reached the end of the path without a mod change
        if end_of_segment_idx == -1:
            end_of_segment_idx = len(path) - 1
        
        # Create the segment
        final_segment_path = path[start_of_segment_idx : end_of_segment_idx + 1]
        segment_dist = sum(graph[nodes.index(final_segment_path[i])][nodes.index(final_segment_path[i+1])] for i in range(len(final_segment_path)-1))
        
        mod = get_best_mod(segment_dist)
        if not mod:
            print(f"  FNR FAILED: Cannot find modulation for segment {' -> '.join(final_segment_path)}.")
            return None
            
        slots_needed = math.ceil(bandwidth / (mod['capacity'] * mod['efficiency']))
        
        segments.append({
            'path': final_segment_path,
            'dist': segment_dist,
            'mod': mod['name'],
            'slots': slots_needed
        })
        
        current_node_idx = end_of_segment_idx

    return segments

# --- Unified Slot Allocation (Unchanged) ---

def allocate_slots_for_connection(primary_segments, backup_segments):
    """
    Finds and allocates a single slot block that is free across ALL segments
    of both the primary and backup paths.
    """
    all_links = set()
    max_slots_needed = 0

    for segment in primary_segments + backup_segments:
        max_slots_needed = max(max_slots_needed, segment['slots'])
        for i in range(len(segment['path']) - 1):
            link = frozenset([segment['path'][i], segment['path'][i+1]])
            all_links.add(link)
    
    total_slots_with_guard = max_slots_needed + 1

    for start_slot in range(SLOTS - total_slots_with_guard + 1):
        is_block_free = True
        for link in all_links:
            if 1 in rsa[link][start_slot : start_slot + total_slots_with_guard]:
                is_block_free = False
                break
        
        if is_block_free:
            for link in all_links:
                for s in range(start_slot, start_slot + max_slots_needed):
                    rsa[link][s] = 1
                rsa[link][start_slot + max_slots_needed] = 'G'
            print(f"  SUCCESS: Allocated slots {start_slot}-{start_slot + total_slots_with_guard - 1} for the connection.")
            return start_slot, max_slots_needed
            
    print("  Allocation FAILED: No single contiguous slot block available for both paths.")
    return None, None

# --- Main Request Handling Logic (UPDATED for FNR) ---

def request(source, destination):
    print(f"\n--- New Request: {nodes[source]} -> {nodes[destination]} ---")
    bandwidth = random.randint(100, 401)
    print(f"Bandwidth: {bandwidth} Gbps")

    primary_path, primary_len = find_shortest_path(source, destination, graph)
    if not primary_path:
        print("Request FAILED: No primary path found.")
        return

    print(f"Primary Path: {' -> '.join(primary_path)} (Length: {primary_len} km)")

    backup_path, backup_len = get_disjoint_path(primary_path, source, destination)
    if not backup_path:
        print("Request FAILED: No link-disjoint backup path found for survivability.")
        request_log.append({'source': nodes[source], 'destination': nodes[destination], 'bandwidth': bandwidth, 'success': False, 'reason': 'No backup path'})
        return

    print(f"Backup Path:  {' -> '.join(backup_path)} (Length: {backup_len} km)")

    primary_segments = place_fnr_regenerators(primary_path, bandwidth)
    if not primary_segments:
        print("Request FAILED: Could not place regenerators on primary path (FNR).")
        request_log.append({'source': nodes[source], 'destination': nodes[destination], 'bandwidth': bandwidth, 'success': False, 'reason': 'FNR failed on primary'})
        return
        
    backup_segments = place_fnr_regenerators(backup_path, bandwidth)
    if not backup_segments:
        print("Request FAILED: Could not place regenerators on backup path (FNR).")
        request_log.append({'source': nodes[source], 'destination': nodes[destination], 'bandwidth': bandwidth, 'success': False, 'reason': 'FNR failed on backup'})
        return
        
    print("Primary Segments (FNR):")
    for seg in primary_segments:
        print(f"  - Path: {' -> '.join(seg['path'])}, Mod: {seg['mod']}, Slots: {seg['slots']}")
        
    print("Backup Segments (FNR):")
    for seg in backup_segments:
        print(f"  - Path: {' -> '.join(seg['path'])}, Mod: {seg['mod']}, Slots: {seg['slots']}")

    start_slot, slots_allocated = allocate_slots_for_connection(primary_segments, backup_segments)
    
    success = start_slot is not None
    
    log_entry = {
        'source': nodes[source],
        'destination': nodes[destination],
        'bandwidth': bandwidth,
        'primary_details': primary_segments,
        'backup_details': backup_segments,
        'slots_allocated': slots_allocated,
        'start_slot': start_slot,
        'success': success,
        'reason': 'Allocation successful' if success else 'No spectrum available'
    }
    request_log.append(log_entry)

    if success:
        print(f"Request from {nodes[source]} to {nodes[destination]} provisioned successfully.")
    else:
        print(f"Request from {nodes[source]} to {nodes[destination]} FAILED.")


# --- Main Execution Loop ---
for i in range(len(graph)):
    for j in range(len(graph)):
        if i != j:
            request(i, j)

# --- Final Reporting (UPDATED for detailed output) ---
print("\n" + "="*25 + " Request Log Summary " + "="*25)
success_count = 0
for i, req in enumerate(request_log):
    status = "SUCCESS" if req['success'] else f"FAILED ({req['reason']})"
    print(f"\n--- Req {i+1}: {req['source']} -> {req['destination']}, Status: {status} ---")
    print(f"  - Bandwidth: {req['bandwidth']} Gbps")

    if req['success']:
        success_count += 1
        print(f"  - Slots Allocated: {req['slots_allocated']} (Starting at slot {req['start_slot']}) for both paths.")
        
        # Print Primary Path Details
        print("  - Primary Path Details:")
        if req['primary_details']:
            for seg_num, segment in enumerate(req['primary_details']):
                print(f"    * Segment {seg_num+1}: {' -> '.join(segment['path'])}")
                print(f"      Modulation: {segment['mod']}, Slots Needed: {segment['slots']}")
        
        # Print Backup Path Details
        print("  - Backup Path Details:")
        if req['backup_details']:
             for seg_num, segment in enumerate(req['backup_details']):
                print(f"    * Segment {seg_num+1}: {' -> '.join(segment['path'])}")
                print(f"      Modulation: {segment['mod']}, Slots Needed: {segment['slots']}")

print("\n" + "="*25 + " Final Statistics " + "="*25)
blocking_probability = (len(request_log) - success_count) / len(request_log) if request_log else 0
print(f"\nTotal Requests: {len(request_log)}")
print(f"Successful Requests: {success_count}")
print(f"Failed/Blocked Requests: {len(request_log) - success_count}")
print(f"Blocking Probability: {blocking_probability:.2%}")

end_time = time.perf_counter()
print(f"\nTotal program execution time: {end_time - start_time:.4f} seconds")
# print(request_log)
