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

def find_tightest_fit_for_link(link, slots_needed, path_segment):
    """
    Finds the core and starting slot using a "Tightest Fit" strategy.
    It searches for the free block that leaves the minimum number of unused slots.
    """
    required_size = slots_needed + 1
    best_fit_core = -1
    best_fit_start_slot = -1
    min_waste = float('inf')

    for core in range(CORES):
        current_slot = 0
        while current_slot <= SLOTS - required_size:
            # Check if this slot is a potential start of a free block
            if rsa[link][core][current_slot] == 0:
                # Measure the size of this contiguous free block
                block_size = 0
                temp_slot = current_slot
                while temp_slot < SLOTS and rsa[link][core][temp_slot] == 0:
                    block_size += 1
                    temp_slot += 1
                
                # Now we have a free block of 'block_size' starting at 'current_slot'
                if block_size >= required_size:
                    waste = block_size - required_size
                    
                    # If this is the tightest fit so far, check it
                    if waste < min_waste:
                        # Check all possible start positions within this block
                        for start_pos in range(current_slot, current_slot + waste + 1):
                            if not causes_strong_crosstalk(core, start_pos, slots_needed, path_segment):
                                min_waste = waste
                                best_fit_core = core
                                best_fit_start_slot = start_pos
                                # We can break here because we only care about the tightest block,
                                # and will place at the first valid position within it.
                                break 
                
                # Move the pointer past the entire block we just analyzed
                current_slot += block_size
            else:
                current_slot += 1
                
    return best_fit_core, best_fit_start_slot

def allocate_path(path, slots_needed):
    #print("\nChecking for path: ", path)
    total_slots = slots_needed + 1
    allocation_plan = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        link = frozenset([u, v])

        best_core, best_start_slot = find_tightest_fit_for_link(link, slots_needed, [u, v])

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
