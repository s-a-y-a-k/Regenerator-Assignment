import time
start_time = time.perf_counter()

import random
import math
SLOTS = 300
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

regenerators = nodes

edges = []
for i in range(len(graph)):
    for j in range(i + 1, len(graph)):
        if graph[i][j] > 0 and graph[i][j] < 99999:
            edges.append((nodes[i], nodes[j]))
print("The edges are: ", edges)

rsa = {}
for i, j in edges:
    link = frozenset([i, j])
    rsa[link] = [0] * SLOTS 

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
    for links, slots in rsa.items():
        node_a = list(links)[0]
        node_b = list(links)[1]
        print(node_a, " - ", node_b, " : ", slots)

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

def get_best_mod(sp_length):
    valid_mods = [m for m in mod_formats if m['reach'] >= sp_length]
    if not valid_mods:
        return None

    return max(valid_mods, key=lambda m: m['efficiency'])

def find_best_regenerator(path, bandwidth):
    min_total_slots = float('inf')
    best_regen_choice = None
    
    intermediate_nodes = [node for node in path[1:-1] if node in regenerators]

    for regen_node in intermediate_nodes:
        regen_index = path.index(regen_node)
        path1 = path[:regen_index + 1]
        path2 = path[regen_index:]
        
        dist1 = sum(graph[nodes.index(path1[i])][nodes.index(path1[i+1])] for i in range(len(path1)-1))
        dist2 = sum(graph[nodes.index(path2[i])][nodes.index(path2[i+1])] for i in range(len(path2)-1))

        mod1 = get_best_mod(dist1)
        mod2 = get_best_mod(dist2)
        
        if not mod1 or not mod2:
            continue

        slots1 = math.ceil(bandwidth / (mod1['capacity'] * mod1['efficiency']))
        slots2 = math.ceil(bandwidth / (mod2['capacity'] * mod2['efficiency']))
        total_slots = slots1 + slots2
        
        if total_slots < min_total_slots:
            min_total_slots = total_slots
            best_regen_choice = {
                'node': regen_node,
                'path1': path1, 'mod1': mod1, 'slots1': slots1,
                'path2': path2, 'mod2': mod2, 'slots2': slots2
            }
            
    return best_regen_choice

def allocate_path(path, slots_needed):
    print("\nChecking for path: ", path)
    total_slots = slots_needed + 1 
    for start_slot in range(SLOTS - total_slots + 1):
        #print("Checking for slot: ", start_slot , " to ", (start_slot + total_slots - 1))
        check = True
        for i in range(len(path)-1):
            first_node = path[i]
            second_node = path[i+1]
            subpath = frozenset([first_node, second_node])
            segment = rsa[subpath][start_slot:start_slot + total_slots]
            if 1 in segment or 'G' in segment:
                #print("  This set of slots is already occupied on link:", first_node, "-", second_node)
                check = False
                break
        if check:
            #print("  Found free slots. Allocating now...")
            for i in range(len(path)-1):
                u = path[i]
                v = path[i+1]
                sub = frozenset([u,v])
                for s in range(start_slot, start_slot + slots_needed):
                    rsa[sub][s] = 1
                rsa[sub][start_slot + slots_needed] = 'G' 
            print("  SUCCESS: Allocated slots", start_slot, "to", start_slot + total_slots - 1, "(including guard bit) for path", path)
            return start_slot
    print("  Allocation FAILED: No contiguous slots available.")
    return None

def deallocate_path(path, start_slot, slots_needed):
    if start_slot is None:
        return
    total_slots_with_guard = slots_needed + 1
    for i in range(len(path) - 1):
        link = frozenset([path[i], path[i+1]])
        for s in range(start_slot, start_slot + total_slots_with_guard):
            rsa[link][s] = 0

def request(source, destination):
    n = len(graph)  
    path, sp_length = dijkstra(source, destination)
    print("\nSource:", nodes[source])
    print("Destination:", nodes[destination])
    print("Path:", ' -> '.join(path))
    print("SP Length (km):", sp_length)
    if path:
        bandwidth = random.randint(100, 401)
        print("Bandwidth (Gbps):", bandwidth) 
        intermediate_path = path[1:-1]
        print("Intermediate nodes:", intermediate_path)
        if any(regen in regenerators for regen in intermediate_path):
            print("Path contains regenerator node. Checking for best regen choice...")
            best_regen_choice = find_best_regenerator(path, bandwidth)
            print("Best regen choice: ", best_regen_choice)
            start_slot1 = allocate_path(best_regen_choice['path1'], best_regen_choice['slots1'])
            start_slot2 = allocate_path(best_regen_choice['path2'], best_regen_choice['slots2'])
            if start_slot1 is not None:
                print("Allocated slots for path1")
                if start_slot2 is not None:
                    print("Allocated slots for path2")
                    print("SUCCESS: Request from", source+1, "to", destination+1, "allocated")
                    request_log.append({
                        'source': nodes[source],
                        'destination': nodes[destination],
                        'path': path,
                        'sp_length': sp_length,
                        'bandwidth': bandwidth,
                        'modulation': [best_regen_choice['mod1']['name'], best_regen_choice['mod2']['name']] ,
                        'slots_needed': best_regen_choice['slots1'] + best_regen_choice['slots2'],
                        'success': True
                    })
                    return True
                else:
                    print("Regen FAILED: Allocation for Segment 2 failed. Note: Segment 1 resources are now occupied. Attempting to deallocate: ")
                    deallocate_path(best_regen_choice['path1'], start_slot1, best_regen_choice['slots1'])
                    request_log.append({
                        'source': nodes[source],
                        'destination': nodes[destination],
                        'path': path,
                        'sp_length': sp_length,
                        'bandwidth': bandwidth,
                        'modulation': [best_regen_choice['mod1']['name'], best_regen_choice['mod2']['name']] ,
                        'slots_needed': best_regen_choice['slots1'] + best_regen_choice['slots2'],
                        'success': False 
                    })
                    
            else:
                print("Regen FAILED: Allocation for Segment 1 failed.")  
                request_log.append({
                    'source': nodes[source],
                    'destination': nodes[destination],
                    'path': path,
                    'sp_length': sp_length,
                    'bandwidth': bandwidth,
                    'modulation': [best_regen_choice['mod1']['name'], best_regen_choice['mod2']['name']] ,
                    'slots_needed': best_regen_choice['slots1'] + best_regen_choice['slots2'],
                    'success': False
                })
        
        else:
            best_mod = get_best_mod(sp_length)
            if best_mod:
                slots_needed = math.ceil(bandwidth / (best_mod['capacity'] * best_mod['efficiency']))
                print(f"Direct attempt: Modulation '{best_mod['name']}', Slots needed: {slots_needed}")
                start_slot3 = allocate_path(path, slots_needed)
                if start_slot3 is not None:
                    print("SUCCESS: Allocated slots for the direct path.")
                    request_log.append({
                        'source': nodes[source],
                        'destination': nodes[destination],
                        'path': path,
                        'sp_length': sp_length,
                        'bandwidth': bandwidth,
                        'modulation': [best_mod['name']],
                        'slots_needed': slots_needed,
                        'success': True
                    })
                    return
                else:
                    print("Direct allocation failed: No suitable contiguous slots available.")
                    request_log.append({
                        'source': nodes[source],
                        'destination': nodes[destination],
                        'path': path,
                        'sp_length': sp_length,
                        'bandwidth': bandwidth,
                        'modulation': [best_mod['name']],
                        'slots_needed': slots_needed,
                        'success': False
                    })
            else:
                print("Direct allocation failed: Path distance exceeds max reach.")
                request_log.append({
                    'source': nodes[source],
                    'destination': nodes[destination],
                    'path': path,
                    'sp_length': sp_length,
                    'bandwidth': bandwidth,
                    'modulation': "N/A", #[best_mod['name']],
                    'slots_needed': "N/A", #slots_needed,
                    'success': False
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

end_time = time.perf_counter()  # End timing right before the program ends
print(f"\nTotal program execution time: {end_time - start_time:} seconds")
