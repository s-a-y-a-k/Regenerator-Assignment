import random
import math

# Define 3-core network with adjacency (1-2 and 2-3 adjacent)
CORES = 3
SLOTS = 15
adjacent_cores = {
    0: [1],
    1: [0, 2],
    2: [1]
}

# Sample graph
graph = [
    [0, 1000, 1200, 0, 0, 0],    
    [1000, 0, 600, 800, 1000, 0],    
    [1200, 600, 0, 0, 800, 0],    
    [0, 800, 0, 0, 600, 1000],      
    [0, 1000, 800, 600, 0, 1200],    
    [0, 0, 0, 1000, 1200, 0]      
]

nodes = []
for i in range(len(graph)):
    label = i + 1
    label_str = str(label)
    nodes.append(label_str)

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if graph[i][j] != 0:
            edges.append((nodes[i], nodes[j]))
print("The edges are: ", edges)

# Each link now has slots per core
rsa = {}
for i, j in edges:
    link = frozenset([i, j])
    rsa[link] = [[0] * SLOTS for _ in range(CORES)]

# Core selection counters
core_counters = [0] * CORES

mod_formats = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 4000},
    {'name': 'QPSK', 'capacity': 25, 'efficiency': 2, 'reach': 2000},
    {'name': '8-QAM', 'capacity': 37.5, 'efficiency': 3, 'reach': 1000},
    {'name': '16-QAM', 'capacity': 50, 'efficiency': 4, 'reach': 500}
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

def check_crosstalk(path, core, start_slot, slots_needed):
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        link = frozenset([u, v])
        for adj_core in adjacent_cores[core]:
            overlapping = any(
                rsa[link][adj_core][s] == 1
                for s in range(start_slot, start_slot + slots_needed)
                if s < SLOTS
            )
            if overlapping:
                return True
    return False

def allocate_path(path, slots_needed):
    print("\nChecking for path: ", path)
    total_slots = slots_needed + 1

    selected_core = core_counters.index(max(core_counters))
    print("Trying to allocate on core " + str(selected_core+1) + " with counter " + str(core_counters[selected_core]))

    for start_slot in range(SLOTS - total_slots + 1):
        if check_crosstalk(path, selected_core, start_slot, slots_needed):
            continue

        available = True
        for i in range(len(path)-1):
            u, v = path[i], path[i+1]
            link = frozenset([u, v])
            if any(rsa[link][selected_core][s] != 0 for s in range(start_slot, start_slot + total_slots)):
                available = False
                break

        if available:
            print("  Allocating on core " + str(selected_core+1) + ", slots " + str(start_slot) + "-" + str(start_slot + total_slots - 1))
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                link = frozenset([u, v])
                for s in range(start_slot, start_slot + slots_needed):
                    rsa[link][selected_core][s] = 1
                rsa[link][selected_core][start_slot + slots_needed] = 'G'
            core_counters[selected_core] = 0
            for i in range(CORES):
                if i != selected_core:
                    core_counters[i] += 1
            return True

    print("  Allocation FAILED: No contiguous slots available without crosstalk.")
    for i in range(CORES):
        if i != selected_core:
            core_counters[i] += 1
    return False

def request():
    n = len(graph)
    source = random.randint(0, n - 1)
    destination = random.randint(0, n - 1)
    while destination == source:
        destination = random.randint(0, n - 1)

    path, sp_length = dijkstra(source, destination)

    if path:
        bandwidth = random.randint(100, 151)

        valid_mods = [m for m in mod_formats if m['reach'] >= sp_length]
        if not valid_mods:
            print("No suitable modulation format found for SP length:", sp_length)
            return

        best_mod = max(valid_mods, key=lambda m: m['efficiency'])
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

for _ in range(10):
    request()
    show_slots()

print("\nRequest Log:")
count = 1
for req in request_log:
    print("Request", count, ": Source=", req['source'], ", Destination=", req['destination'], ", Path=", ' -> '.join(req['path']), ", SP Length=", req['sp_length'], " km, Bandwidth=", req['bandwidth'], " Gbps, Modulation=", req['modulation'], ", Slots Needed=", req['slots_needed'], ", Success=", req['success'])
    count += 1
