import time
start_time = time.perf_counter() 

import random
import math
random.seed(42)
CORES = 7
SLOTS = 100
adjacent_cores = {
    0: [1],
    1: [0, 2],
    2: [1, 3],
    3: [2, 4, 6],
    4: [3],
    5: [6],
    6: [3, 5]
}

graph = [
    [   0, 1100,  600, 1000,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0],   # A
    [1100,    0,  600,    0,    0,    0,    0, 2800,    0,    0,    0,    0,    0,    0],   # B
    [ 600,  600,    0,    0,    0, 2000,    0,    0,    0,    0,    0,    0,    0,    0],   # C
    [1000,    0,    0,    0,  600,    0,    0,    0,    0,    0, 2400,    0,    0,    0],   # D
    [   0,    0,    0,  600,    0, 1100,  800,    0,    0,    0,    0,    0,    0,    0],   # E
    [   0,    0, 2000,    0, 1100,    0,    0,    0,    0, 1200,    0,    0,    0, 2000], # F
    [   0,    0,    0,    0,  800,    0,    0,  700,    0, 1300,    0,    0,    0,    0],   # G
    [   0, 2800,    0,    0,    0,    0,  700,    0,  700,    0,    0,    0,    0,    0],   # H
    [   0,    0,    0,    0,    0,    0,    0,  700,    0,  900,    0,  500,  500,    0],   # I
    [   0,    0,    0,    0,    0, 1200, 1300,    0,  900,    0,    0,    0,    0,    0],   # J
    [   0,    0,    0, 2400,    0,    0,    0,    0,    0,    0,    0,  800, 1000,    0],   # K
    [   0,    0,    0,    0,    0,    0,    0,    0,  500,    0,  800,    0,    0,  500],   # L
    [   0,    0,    0,    0,    0,    0,    0,    0,  500,    0, 1000,    0,    0,  300],   # M
    [   0,    0,    0,    0,    0, 2000,    0,    0,    0,    0,    0,  500,  300,    0]    # N
]

nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if graph[i][j] > 0:
            edges.append((nodes[i], nodes[j]))
# print("The edges are: ", edges)

rsa = {}
for i, j in edges:
    link = frozenset([i, j])
    rsa[link] = [[0] * SLOTS for _ in range(CORES)] 

mod_formats = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 8000},
    {'name': 'QPSK', 'capacity': 12.5, 'efficiency': 2, 'reach': 4000},
    {'name': '8-QAM', 'capacity': 12.5, 'efficiency': 3, 'reach': 2000},
    {'name': '16-QAM', 'capacity': 12.5, 'efficiency': 4, 'reach': 1000},
    {'name': '32-QAM', 'capacity': 12.5, 'efficiency': 5, 'reach': 500},
    {'name': '64-QAM', 'capacity': 12.5, 'efficiency': 6, 'reach': 250}
]

request_log = []

def show_slots():
    print("\nCurrent Slot Usage:")
    for links, slots_per_core in rsa.items():
        print(list(links)[0] + " - " + list(links)[1] + ":")
        for core_index, slots in enumerate(slots_per_core):
            print("  Core " + str(core_index+1) + ": " + str(slots))

def dijkstra(source_idx, destination_idx):
    n = len(graph)
    visited = [False] * n
    distance = [float('inf')] * n
    previous = [None] * n
    distance[source_idx] = 0

    for _ in range(n):
        min_distance = float('inf')
        current_node = -1
        for i in range(n):
            if not visited[i] and distance[i] < min_distance:
                min_distance = distance[i]
                current_node = i

        if current_node == -1:
            break

        visited[current_node] = True
        for neighbor in range(n):
            if graph[current_node][neighbor] > 0 and not visited[neighbor]:
                new_distance = distance[current_node] + graph[current_node][neighbor]
                if new_distance < distance[neighbor]:
                    distance[neighbor] = new_distance
                    previous[neighbor] = current_node

    path = []
    node = destination_idx
    while node is not None:
        path.insert(0, node)
        node = previous[node]

    if distance[destination_idx] != float('inf'):
        return [nodes[i] for i in path], distance[destination_idx]
    else:
        return None, None

def causes_strong_crosstalk(core, start_slot, slots_needed, path):
    for s in range(start_slot, min(start_slot + slots_needed, SLOTS)):
        overlapping_cores = set()
        for i in range(len(path) - 1):
            link_key = frozenset([path[i], path[i+1]])
            if link_key in rsa:
                for c in adjacent_cores[core]:
                    if rsa[link_key][c][s] == 1:
                        overlapping_cores.add(c)
                        for c1 in adjacent_cores[c]:
                            if rsa[link_key][c1][s] == 1:
                                overlapping_cores.add(c1)
        adjacent_overlap = list(overlapping_cores)
        if len(adjacent_overlap) > 1:
            return True
    return False

def find_last_fit_for_link(link, slots_needed, path_segment):
    """
    Finds the first available core and starting slot using a "Last-Fit" strategy,
    searching from the highest slot index downwards.
    """
    total_slots_required = slots_needed + 1
    for core in range(CORES):
        # Use reversed() to search from the highest slot index to the lowest
        for start_slot in reversed(range(SLOTS - total_slots_required + 1)):
            if causes_strong_crosstalk(core, start_slot, slots_needed, path_segment):
                continue
            
            is_block_free = True
            for s in range(start_slot, start_slot + total_slots_required):
                if rsa[link][core][s] != 0:
                    is_block_free = False
                    break
            
            if is_block_free:
                return core, start_slot
    return -1, -1

def allocate_path(path, slots_needed):
    allocation_plan = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        link = frozenset([u, v])
        core, start_slot = find_last_fit_for_link(link, slots_needed, [u, v])
        if core == -1:
            return False
        allocation_plan.append({'link': link, 'core': core, 'start_slot': start_slot})

    for plan in allocation_plan:
        link = plan['link']
        core = plan['core']
        start_slot = plan['start_slot']
        for s in range(start_slot, start_slot + slots_needed):
            rsa[link][core][s] = 1
        rsa[link][core][start_slot + slots_needed] = 'G'
    return True

def request(source_name, destination_name):
    source_idx = nodes.index(source_name)
    destination_idx = nodes.index(destination_name)
    
    path, sp_length = dijkstra(source_idx, destination_idx)

    if path:
        bandwidth = random.randint(100, 401)
        valid_mods = [m for m in mod_formats if m['reach'] >= sp_length]

        if not valid_mods:
            success = False
            best_mod_name = "N/A"
            slots_needed = "N/A"
        else:
            best_mod = max(valid_mods, key=lambda m: m['efficiency'])
            best_mod_name = best_mod['name']
            slots_needed = math.ceil(bandwidth / (best_mod['capacity'] * best_mod['efficiency']))
            success = allocate_path(path, slots_needed)

        request_log.append({
            'source': source_name, 'destination': destination_name, 'path': path,
            'sp_length': sp_length, 'bandwidth': bandwidth, 'modulation': best_mod_name,
            'slots_needed': slots_needed, 'success': success
        })
    else:
        print(f"No path found between {source_name} and {destination_name}")

for i_node in nodes:
    for j_node in nodes:
        if i_node != j_node:
            request(i_node, j_node)

# --- Final Analysis Section ---
fail_count = sum(1 for req in request_log if not req['success'])

# a) Find highest utilized spectrum slots index.
slot_utilization = [0] * SLOTS
for link_data in rsa.values():
    for core_slots in link_data:
        for i in range(SLOTS):
            if core_slots[i] == 1:
                slot_utilization[i] += 1
highest_utilized_slot = -1
max_utilization = -1
if any(slot_utilization):
    max_utilization = max(slot_utilization)
    highest_utilized_slot = slot_utilization.index(max_utilization)

# b) Total spectrum utilised slots & d) Total guard band used
total_data_slots_used = 0
total_guard_bands_used = 0
for link_data in rsa.values():
    for core_slots in link_data:
        total_data_slots_used += core_slots.count(1)
        total_guard_bands_used += core_slots.count('G')

# c) Number of request blocking (Blocking Probability)
blocking_probability = (fail_count / len(request_log)) * 100 if request_log else 0

# e) % of fragmentation.
total_free_slots = 0
sum_of_largest_free_blocks = 0
for link_data in rsa.values():
    for core_slots in link_data:
        core_total_free = 0
        max_contiguous = 0
        current_contiguous = 0
        for slot in core_slots:
            if slot == 0:
                core_total_free += 1
                current_contiguous += 1
            else:
                max_contiguous = max(max_contiguous, current_contiguous)
                current_contiguous = 0
        max_contiguous = max(max_contiguous, current_contiguous)
        total_free_slots += core_total_free
        sum_of_largest_free_blocks += max_contiguous

fragmentation_percentage = (1 - (sum_of_largest_free_blocks / total_free_slots)) * 100 if total_free_slots > 0 else 0

end_time = time.perf_counter()
execution_time = end_time - start_time

# --- Final Results ---
print("\n" + "="*20 + " FINAL SIMULATION RESULTS " + "="*20)
print(f"a) Highest Utilized Slot Index: {highest_utilized_slot} (Used {max_utilization} times)")
print(f"b) Total Spectrum Utilised Slots (Data): {total_data_slots_used}")
print(f"c) Request Blocking Probability: {blocking_probability:.2f}% ({fail_count} failed requests)")
print(f"d) Total Guard Band Slots Used: {total_guard_bands_used}")
print(f"e) Network Fragmentation: {fragmentation_percentage:.2f}%")
print(f"f) Total Execution Time: {execution_time:.4f} seconds")
print("="*64 + "\n")

