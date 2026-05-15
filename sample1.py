nodes = ['n1', 'n2', 'n3', 'n4']
edges = [('n1','n2'),('n1','n3'),('n2','n3'),('n2','n4'),('n3','n4')]
rsa = {}
for i,j in edges:
    link = frozenset([i,j])
    rsa[link] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
def show_slots():
    for links, slots in rsa.items():
        node_a = list(links)[0]
        node_b = list(links)[1]
        print(node_a, " - ", node_b, " : ", slots)
show_slots()
def allocate_path(path, slots_needed):
    print("Checking for path: ", path)
    for start_slot in range(15-slots_needed+1):
        print("Checking for slot: ", start_slot , " to ", (start_slot + slots_needed-1))
        check = True
        for i in range(len(path)-1):
            first_node = path[i]
            second_node = path[i+1]
            subpath = frozenset([first_node,second_node])
            segment = rsa[subpath][start_slot:start_slot+slots_needed]
            if 1 in segment:
                print("This set of slots cannot be used for allocation")
                check = False
                break
        if check==True:
            print("  Found free slots. Allocating now...")
            for i in range(len(path)-1):
                u = path[i]
                v = path[i+1]
                sub = frozenset([u,v])
                for s in range(start_slot, start_slot + slots_needed):
                    rsa[sub][s] = 1
            print("  SUCCESS: Allocated slots", start_slot, "to", start_slot + slots_needed - 1, "for path", path)
            return True
    print("Allocation not possible as no contiguous or continuous slots found")
    return False
allocate_path(['n1', 'n2', 'n3'], 3)
show_slots()
allocate_path(['n1', 'n3'], 2)
show_slots()
allocate_path(['n1', 'n2'], 4)
show_slots()
              
        
