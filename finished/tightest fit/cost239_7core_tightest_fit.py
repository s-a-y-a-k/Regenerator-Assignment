import time
start_time = time.perf_counter()

import random
import math
random.seed(42)
CORES = 7
SLOTS = 20
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


nodes = []
for i in range(len(graph)):
    label = i + 1
    label_str = str(label)
    nodes.append(label_str)

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if graph[i][j] > 0 and graph[i][j] < 99999:
            edges.append((nodes[i], nodes[j]))
print("The edges are: ", edges)

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
    distance = [9999] * n
    previous = [None] * n
    distance[source] = 0

    for _ in range(n):
        min_distance = 9999
        current_node = None
        for i in range(n):
            if not visited[i] and distance[i] < min_distance:
                min_distance = distance[i]
                current_node = i

        if current_node is None:
            break

        visited[current_node] = True
        for neighbor in range(n):
            if graph[current_node][neighbor] > 0 and not visited[neighbor]:
                new_distance = distance[current_node] + graph[current_node][neighbor]
                if new_distance < distance[neighbor]:
                    distance[neighbor] = new_distance
                    previous[neighbor] = current_node

    path = []
    node = destination
    while node is not None:
        path.insert(0, node)
        node = previous[node]

    if distance[destination] < 9999:
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

def find_best_core(path, slots_needed):
    """
    Finds the core and starting slot using a "Most-Fitting" (or "Tightest Fit") strategy.
    It searches for the free block that leaves the minimum number of unused slots (waste).
    The request is placed at the beginning of that best-fit block.
    """
    required_size = slots_needed + 1
    best_fit_core = -1
    best_fit_start_slot = -1
    min_waste = float('inf')

    for core in range(CORES):
        current_slot = 0
        while current_slot <= SLOTS - required_size:
            # Check if this slot is free across the entire path to be a potential start
            is_start_free = True
            for i in range(len(path) - 1):
                link = frozenset([path[i], path[i + 1]])
                if rsa[link][core][current_slot] != 0:
                    is_start_free = False
                    break
            
            if not is_start_free:
                current_slot += 1
                continue

            # If the start is free, measure the size of the contiguous free block
            block_size = 0
            temp_slot = current_slot
            while temp_slot < SLOTS:
                is_slot_in_block_free = True
                for i in range(len(path) - 1):
                    link = frozenset([path[i], path[i + 1]])
                    if rsa[link][core][temp_slot] != 0:
                        is_slot_in_block_free = False
                        break
                
                if is_slot_in_block_free:
                    block_size += 1
                    temp_slot += 1
                else:
                    break # The contiguous block has ended
            
            # We now have a free block of 'block_size' starting at 'current_slot'
            if block_size >= required_size:
                waste = block_size - required_size
                
                # If this is the tightest fit so far, check it for crosstalk
                if waste < min_waste:
                    # We place at the beginning of the block, so check crosstalk for that position
                    if not causes_strong_crosstalk(core, current_slot, slots_needed, path):
                        min_waste = waste
                        best_fit_core = core
                        best_fit_start_slot = current_slot
            
            # Move the pointer past the entire block we just analyzed
            current_slot += block_size if block_size > 0 else 1

    return best_fit_core, best_fit_start_slot

def allocate_path(path, slots_needed):
    #print("\nChecking for path: ", path)
    total_slots = slots_needed + 1

    selected_core, selected_start = find_best_core(path, slots_needed)
    if selected_core == -1:
        #print("  Allocation FAILED: No contiguous slots available.")
        return False

    print("  Allocating on core " + str(selected_core+1) + ", slots " + str(selected_start) + "-" + str(selected_start + total_slots - 1))
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        link = frozenset([u, v])
        for s in range(selected_start, selected_start + slots_needed):
            rsa[link][selected_core][s] = 1
        rsa[link][selected_core][selected_start + slots_needed] = 'G'
    return True

def request(source, destination):
    n = len(graph)

    path, sp_length = dijkstra(source, destination)

    if path:
        bandwidth = random.randint(100, 401) 

        valid_mods = []
        for m in mod_formats:
            if m['reach'] >= sp_length:
                valid_mods.append(m)

        if not valid_mods:
            print("No suitable modulation format found for SP length:", sp_length)
            request_log.append({
                'source': nodes[source],
                'destination': nodes[destination],
                'path': path,
                'sp_length': sp_length,
                'bandwidth': bandwidth,
                'modulation': "N/A",
                'slots_needed': "N/A",
                'success': False
            })
            return

        best_mod = valid_mods[0]
        for m in valid_mods:
            if m['efficiency'] > best_mod['efficiency']:
                best_mod = m

        slots_needed = math.ceil(bandwidth / (best_mod['capacity'] * best_mod['efficiency']))

        print("\nSource:", nodes[source])
        print("Destination:", nodes[destination])
        print("Path:", ' -> '.join(path))
        print("SP Length (km):", sp_length)
        print("Bandwidth (Gbps):", bandwidth)
        print("Selected Modulation Format:", best_mod['name'])
        print("FS Capacity:", best_mod['capacity'], "GHz")
        print("Efficiency:", best_mod['efficiency'])
        print("Slots needed (excluding guard bit):", slots_needed)

        success = allocate_path(path, slots_needed)

        request_log.append({
            'source': nodes[source],
            'destination': nodes[destination],
            'path': path,
            'sp_length': sp_length,
            'bandwidth': bandwidth,
            'modulation': best_mod['name'],
            'slots_needed': slots_needed,
            'success': success
        })

    else:
        print("No path found between", nodes[source], "and", nodes[destination])       
        
for i in range(len(graph)):
    for j in range(len(graph)):
        if i!=j:
            request(i, j)
show_slots()

print("\nRequest Log:")
count = 1
fail_count = 0
for req in request_log:
    print("Request", count, ": Source=", req['source'], ", Destination=", req['destination'], ", Path=", ' -> '.join(req['path']), ", SP Length=", req['sp_length'], " km, Bandwidth=", req['bandwidth'], " Gbps, Modulation=", req['modulation'], ", Slots Needed=", req['slots_needed'], ", Success=", req['success'])
    count += 1
    if req['success'] == False:
        fail_count += 1
print("The fail probability is:", float(fail_count/len(request_log)))
print("The no. of failed requests are: ", fail_count)

end_time = time.perf_counter()
print(f"\nTotal program execution time: {end_time - start_time:.4f} seconds")