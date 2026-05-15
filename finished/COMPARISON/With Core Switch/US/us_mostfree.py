import time
start_time = time.perf_counter() 

import random
import math
random.seed(42)
CORES = 7
SLOTS = 300
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

nodes = [str(i+1) for i in range(len(graph))]

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if graph[i][j] > 0 and graph[i][j] < 99999:
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

def dijkstra(source, destination):
    n = len(graph)
    visited = [False] * n
    distance = [float('inf')] * n
    previous = [None] * n
    distance[source] = 0

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
            if graph[current_node][neighbor] > 0 and graph[current_node][neighbor] < 99999 and not visited[neighbor]:
                new_distance = distance[current_node] + graph[current_node][neighbor]
                if new_distance < distance[neighbor]:
                    distance[neighbor] = new_distance
                    previous[neighbor] = current_node

    path = []
    node = destination
    while node is not None:
        path.insert(0, node)
        node = previous[node]

    if distance[destination] < float('inf'):
        return [nodes[i] for i in path], distance[destination]
    else:
        return None, None

def causes_strong_crosstalk(core, start_slot, slots_needed, path):
    for s in range(start_slot, min(start_slot + slots_needed, SLOTS)):
        overlapping_cores = set()
        for i in range(len(path) - 1):
            link = frozenset([path[i], path[i + 1]])
            for c in adjacent_cores[core]:
                if rsa[link][c][s] == 1:
                    overlapping_cores.add(c)
                    for c1 in adjacent_cores[c]:
                        if rsa[link][c1][s] == 1:
                            overlapping_cores.add(c1)
        adjacent_overlap = [c for c in overlapping_cores]
        if len(adjacent_overlap) > 1:
            return True
    return False

def find_best_core_for_link(link, slots_needed, path_segment):
    best_core = -1
    best_start_slot = -1
    max_free_slots = -1

    for core in range(CORES):
        for start_slot in range(SLOTS - (slots_needed + 1) + 1):
            if causes_strong_crosstalk(core, start_slot, slots_needed, path_segment):
                continue

            valid = True
            for s in range(start_slot, start_slot + slots_needed + 1):
                if rsa[link][core][s] != 0:
                    valid = False
                    break
            if not valid:
                continue

            total_free = rsa[link][core][start_slot:].count(0)

            if total_free > max_free_slots:
                max_free_slots = total_free
                best_core = core
                best_start_slot = start_slot

    return best_core, best_start_slot

def allocate_path(path, slots_needed):
    #print("\nChecking for path: ", path)
    total_slots = slots_needed + 1
    allocation_plan = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        link = frozenset([u, v])

        best_core, best_start_slot = find_best_core_for_link(link, slots_needed, [u, v])

        if best_core == -1:
            #print(f"  Allocation FAILED at link {u}-{v}")
            return False  
        allocation_plan.append((link, best_core, best_start_slot))

    for link, core, start_slot in allocation_plan:
        for s in range(start_slot, start_slot + slots_needed):
            rsa[link][core][s] = 1
        rsa[link][core][start_slot + slots_needed] = 'G'

    #print("  Allocated per link:", [(list(link), core + 1, start) for link, core, start in allocation_plan])
    return True

def request(source_idx, destination_idx):
    n = len(graph)
    
    source_name = nodes[source_idx]
    destination_name = nodes[destination_idx]

    path, sp_length = dijkstra(source_idx, destination_idx)

    if path:
        bandwidth = random.randint(100, 401) 

        valid_mods = []
        for m in mod_formats:
            if m['reach'] >= sp_length:
                valid_mods.append(m)

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
            'source': source_name,
            'destination': destination_name,
            'path': path,
            'sp_length': sp_length,
            'bandwidth': bandwidth,
            'modulation': best_mod_name,
            'slots_needed': slots_needed,
            'success': success
        })

    else:
        print(f"No path found between {source_name} and {destination_name}")       
        
for i in range(len(graph)):
    for j in range(len(graph)):
        if i!=j:
            request(i, j)
# show_slots()

# print("\nRequest Log:")
# count = 1
fail_count = 0
for req in request_log:
    # print("Request", count, ": Source=", req['source'], ", Destination=", req['destination'], ", Path=", ' -> '.join(req['path']), ", SP Length=", req['sp_length'], " km, Bandwidth=", req['bandwidth'], " Gbps, Modulation=", req['modulation'], ", Slots Needed=", req['slots_needed'], ", Success=", req['success'])
    # count += 1
    if req['success'] == False:
        fail_count += 1

# --- Final Analysis Section ---
# a) Find highest utilized spectrum slots index.
slot_utilization = [0] * SLOTS
for link, cores in rsa.items():
    for core_slots in cores:
        for i in range(SLOTS):
            if core_slots[i] == 1: # Only count data slots for utilization
                slot_utilization[i] += 1
highest_utilized_slot = -1
max_utilization = -1
if any(slot_utilization):
    max_utilization = max(slot_utilization)
    highest_utilized_slot = slot_utilization.index(max_utilization)

# b) Total spectrum utilised slots & d) Total guard band used
total_data_slots_used = 0
total_guard_bands_used = 0
for link, cores in rsa.items():
    for core_slots in cores:
        for slot in core_slots:
            if slot == 1:
                total_data_slots_used += 1
            elif slot == 'G':
                total_guard_bands_used += 1

# c) Number of request blocking (Blocking Probability)
blocking_probability = 0
if len(request_log) > 0:
    blocking_probability = (fail_count / len(request_log)) * 100

# e) % of fragmentation.
total_free_slots = 0
sum_of_largest_free_blocks = 0
for link, cores in rsa.items():
    for core_slots in cores:
        core_total_free = 0
        core_max_contiguous = 0
        current_contiguous = 0
        for slot in core_slots:
            if slot == 0:
                core_total_free += 1
                current_contiguous += 1
            else:
                core_max_contiguous = max(core_max_contiguous, current_contiguous)
                current_contiguous = 0
        core_max_contiguous = max(core_max_contiguous, current_contiguous) # Check after loop ends
        
        total_free_slots += core_total_free
        sum_of_largest_free_blocks += core_max_contiguous

fragmentation_percentage = 0
if total_free_slots > 0:
    fragmentation_percentage = (1 - (sum_of_largest_free_blocks / total_free_slots)) * 100

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
