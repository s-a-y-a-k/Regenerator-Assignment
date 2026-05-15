import random
import math

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
    [0, 1100, 600, 1000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],     # A
    [1100, 0, 600, 0, 0, 0, 0, 2800, 0, 0, 0, 0, 0, 0],     # B
    [600, 600, 0, 0, 0, 2000, 0, 0, 0, 0, 0, 0, 0, 0],      # C
    [1000, 0, 0, 0, 600, 0, 0, 0, 0, 0, 2400, 0, 0, 0],     # D
    [0, 0, 0, 600, 0, 1100, 800, 0, 0, 0, 0, 0, 0, 0],      # E
    [0, 0, 2000, 0, 1100, 0, 0, 0, 0, 1200, 0, 0, 0, 2000], # F
    [0, 0, 0, 0, 800, 0, 0, 700, 0, 1300, 0, 0, 0, 0],      # G
    [0, 2800, 0, 0, 0, 0, 700, 0, 700, 0, 0, 0, 0, 0],      # H
    [0, 0, 0, 0, 0, 0, 0, 700, 0, 900, 0, 500, 500, 0],     # I
    [0, 0, 0, 0, 0, 1200, 1300, 0, 900, 0, 0, 0, 0, 0],     # J
    [0, 0, 0, 2400, 0, 0, 0, 0, 0, 0, 0, 800, 1000, 0],     # K
    [0, 0, 0, 0, 0, 0, 0, 0, 500, 0, 800, 0, 0, 500],       # L
    [0, 0, 0, 0, 0, 0, 0, 0, 500, 0, 1000, 0, 0, 300],      # M
    [0, 0, 0, 0, 0, 2000, 0, 0, 0, 0, 0, 500, 300, 0]       # N
]

nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if graph[i][j] != 0:
            edges.append((nodes[i], nodes[j]))
print("The edges are: ", edges)

rsa = {}
for i, j in edges:
    link = frozenset([i, j])
    rsa[link] = [[0] * SLOTS for _ in range(CORES)]

mod_formats = [
    {'name': 'BPSK', 'capacity': 12.5, 'efficiency': 1, 'reach': 8000},
    {'name': 'QPSK', 'capacity': 25, 'efficiency': 2, 'reach': 4000},
    {'name': '8-QAM', 'capacity': 37.5, 'efficiency': 3, 'reach': 2000},
    {'name': '16-QAM', 'capacity': 50, 'efficiency': 4, 'reach': 1000},
    {'name': '32-QAM', 'capacity': 62.5, 'efficiency': 5, 'reach': 500},
    {'name': '64-QAM', 'capacity': 75, 'efficiency': 6, 'reach': 250}
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
        if len(overlapping_cores) > 1:
            return True
    return False

def find_best_core(path, slots_needed):
    best_core = -1
    best_start_slot = -1
    max_free_slots = -1

    for core in range(CORES):
        for start_slot in range(SLOTS - slots_needed + 1):  # fixed off-by-one
            if causes_strong_crosstalk(core, start_slot, slots_needed, path):
                continue

            valid = True
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                link = frozenset([u, v])
                for s in range(start_slot, start_slot + slots_needed):
                    if rsa[link][core][s] != 0:
                        valid = False
                        break
                if not valid:
                    break

            if valid:
                total_free = 0
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    link = frozenset([u, v])
                    segment = rsa[link][core][start_slot:SLOTS]
                    total_free += segment.count(0)

                if total_free > max_free_slots:
                    max_free_slots = total_free
                    best_core = core
                    best_start_slot = start_slot

    return best_core, best_start_slot

def allocate_path(path, slots_needed):
    print("\nChecking for path: ", path)
    total_slots = slots_needed + 1  # including guard slot

    selected_core, selected_start = find_best_core(path, slots_needed)
    if selected_core == -1:
        print("  Allocation FAILED: No contiguous slots available without strong crosstalk.")
        return False

    print(f"  Allocating on core {selected_core+1}, slots {selected_start}-{selected_start + total_slots - 1}")
    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        link = frozenset([u, v])
        for s in range(selected_start, selected_start + slots_needed):
            rsa[link][selected_core][s] = 1
        if selected_start + slots_needed < SLOTS:  # guard slot within bounds
            rsa[link][selected_core][selected_start + slots_needed] = 'G'
    return True

def request(source, destination):
    path, sp_length = dijkstra(source, destination)

    if path:
        bandwidth = random.randint(100, 201)

        valid_mods = [m for m in mod_formats if m['reach'] >= sp_length]

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

for i in range(len(graph)):
    for j in range(len(graph)):
        if i != j:
            request(i, j)

show_slots()

print("\nRequest Log:")
count = 1
fail_count = 0
for req in request_log:
    print(f"Request {count}: Source={req['source']}, Destination={req['destination']}, Path={' -> '.join(req['path'])}, SP Length={req['sp_length']} km, Bandwidth={req['bandwidth']} Gbps, Modulation={req['modulation']}, Slots Needed={req['slots_needed']}, Success={req['success']}")
    count += 1
    if not req['success']:
        fail_count += 1
print("The fail probability is:", float(fail_count/len(request_log)))
print("The no. of failed requests are: ", fail_count)
