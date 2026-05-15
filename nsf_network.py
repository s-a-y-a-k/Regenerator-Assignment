import random
import math

graph = [
    [0, 1100, 600, 1000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],     # A
    [1100, 0, 600, 0, 0, 0, 0, 2800, 0, 0, 0, 0, 0, 0],     # B
    [600, 600, 0, 0, 0, 2000, 0, 0, 0, 0, 0, 0, 0, 0],      # C
    [1000, 0, 0, 0, 600, 0, 0, 0, 0, 0, 2400, 0, 0, 0],     # D
    [0, 0, 0, 600, 0, 1100, 800, 0, 0, 0, 0, 0, 0, 0],      # E
    [0, 0, 2000, 0, 1100, 0, 0, 0, 0, 1200, 0, 0, 0, 2000], # F
    [0, 0, 0, 0, 800, 0, 0, 700, 0, 1300, 0, 0, 0, 0],      # G
    [0, 2800, 0, 0, 0, 0, 700, 0, 700, 0, 0, 0, 0, 0],      # H
    [0, 0, 0, 0, 0, 0, 0, 700, 0, 900, 0, 500, 500, 0],       # I
    [0, 0, 0, 0, 0, 1200, 1300, 0, 900, 0, 0, 0, 0, 0],     # J
    [0, 0, 0, 2400, 0, 0, 0, 0, 0, 0, 0, 800, 1000, 0],     # K
    [0, 0, 0, 0, 0, 0, 0, 0, 500, 0, 800, 0, 0, 500],       # L
    [0, 0, 0, 0, 0, 0, 0, 0, 500, 0, 1000, 0, 0, 300],      # M
    [0, 0, 0, 0, 0, 2000, 0, 0, 0, 0, 0, 500, 300, 0]       # N
]

nodes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']

# Build edge list
edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if graph[i][j] != 0:
            edges.append((nodes[i], nodes[j]))
print("The edges are: ", edges)

# Initialize RSA table
rsa = {}
for i, j in edges:
    link = frozenset([i, j])
    rsa[link] = [0] * 350 

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
    for links, slots in rsa.items():
        node_a = list(links)[0]
        node_b = list(links)[1]
        print(node_a, " - ", node_b, " : ", slots)

def dijkstra(source, destination):
    """Returns shortest valid path (only direct edges) and distance"""
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

    # Build path
    path = []
    node = destination
    while node is not None:
        path.insert(0, node)
        node = previous[node]

    # Validate path
    for i in range(len(path) - 1):
        if graph[path[i]][path[i+1]] == 0:
            return None, None  # Invalid path

    if distance[destination] < 9999:
        return [nodes[i] for i in path], distance[destination]
    else:
        return None, None

def allocate_path(path, slots_needed):
    print("\nChecking for path: ", path)
    total_slots = slots_needed + 1  # guard bit
    for start_slot in range(350 - total_slots + 1):
        #print("Checking for slot: ", start_slot, "to", (start_slot + total_slots - 1))
        check = True
        for i in range(len(path)-1):
            subpath = frozenset([path[i], path[i+1]])
            if subpath not in rsa:
                print(f"  ERROR: Link {path[i]}-{path[i+1]} not found in topology. Skipping allocation.")
                return False
            segment = rsa[subpath][start_slot:start_slot + total_slots]
            if 1 in segment or 'G' in segment:
                #print("  This set of slots is already occupied on link:", path[i], "-", path[i+1])
                check = False
                break
        if check:
            print("  Found free slots. Allocating now...")
            for i in range(len(path)-1):
                sub = frozenset([path[i], path[i+1]])
                for s in range(start_slot, start_slot + slots_needed):
                    rsa[sub][s] = 1
                rsa[sub][start_slot + slots_needed] = 'G'  # guard bit
            print("  SUCCESS: Allocated slots", start_slot, "to", start_slot + total_slots - 1)
            return True
    print("  Allocation FAILED: No contiguous slots available.")
    return False

def request(source, destination):
    path, sp_length = dijkstra(source, destination)

    if path:
        bandwidth = random.randint(100, 402)  # Gbps

        valid_mods = [m for m in mod_formats if m['reach'] >= sp_length]
        if not valid_mods:
            print("No suitable modulation format for SP length:", sp_length)
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
        print(f"No valid path found between {nodes[source]} and {nodes[destination]}")
        request_log.append({
            'source': nodes[source],
            'destination': nodes[destination],
            'path': "N/A",
            'sp_length': "N/A",
            'bandwidth': "N/A",
            'modulation': "N/A",
            'slots_needed': "N/A",
            'success': False
        })

# Run all requests
for i in range(len(graph)):
    for j in range(len(graph)):
        if i != j:
            request(i, j)

show_slots()

print("\nRequest Log:")
count = 1
fail_count = 0
for req in request_log:
    print(f"Request {count}: Source={req['source']}, Destination={req['destination']}, Path={req['path']}, "
          f"SP Length={req['sp_length']}, Bandwidth={req['bandwidth']}, Modulation={req['modulation']}, "
          f"Slots Needed={req['slots_needed']}, Success={req['success']}")
    count += 1
    if req['success'] == False:
        fail_count += 1
print("The fail probability is:", float(fail_count/len(request_log)))
print("The number of failed requests are: ", fail_count)
