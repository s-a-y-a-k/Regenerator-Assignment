import matplotlib.pyplot as plt
import numpy as np

# Import the functions from your refactored scripts
from simulation_flr import run_flr_simulation
from simulation_fns import run_fns_simulation

print("Starting spectrum scarcity experiment...")

# --- Define Your Independent Variable Range ---
slot_counts = [100, 150, 200, 250, 300]

# --- Define Your Fixed Variable ---
FIXED_REGEN_LIMIT = 50 # A mid-range value is good for this test

# --- Store Your Dependent Variables (Results) ---
flr_results = {
    'blocking': [],
    'regenerations': [],
    'fragmentation': []
}
fns_results = {
    'blocking': [],
    'regenerations': [],
    'fragmentation': []
}

# --- Run the Experiment Loop ---
for slots in slot_counts:
    print(f"Running simulations with {slots} slots (Regen Limit: {FIXED_REGEN_LIMIT})...")
    
    # Run FLR
    flr_data = run_flr_simulation(slots_limit=slots, regen_limit=FIXED_REGEN_LIMIT)
    flr_results['blocking'].append(flr_data['bandwidth_blocking_ratio'])
    flr_results['regenerations'].append(flr_data['total_regenerations'])
    flr_results['fragmentation'].append(flr_data['network_fragmentation'])
    
    # Run FNS
    fns_data = run_fns_simulation(slots_limit=slots, regen_limit=FIXED_REGEN_LIMIT)
    fns_results['blocking'].append(fns_data['bandwidth_blocking_ratio'])
    fns_results['regenerations'].append(fns_data['total_regenerations'])
    fns_results['fragmentation'].append(fns_data['network_fragmentation'])

print("Experiment complete. Plotting results...")

# --- Plotting ---

# === Graph 1: Bandwidth Blocking Ratio vs. Number of Slots ===
plt.figure(figsize=(10, 6))
plt.plot(slot_counts, flr_results['blocking'], 'o-', label='FLR-RA')
plt.plot(slot_counts, fns_results['blocking'], 's-', label='FNS-RA')
plt.title(f'Bandwidth Blocking Ratio (BBR) vs. Available Slots (Regens = {FIXED_REGEN_LIMIT})', fontsize = 14)
plt.xlabel('Number of Slots per Link',fontsize = 14)
plt.ylabel('Bandwidth Blocking Ratio', fontsize = 14)
plt.legend()
plt.grid(True)
plt.yscale('log')
plt.savefig('bbr_vs_slots_50.png')

# === Graph 2: Total Regenerations vs. Number of Slots ===
plt.figure(figsize=(10, 6))
plt.plot(slot_counts, flr_results['regenerations'], 'o-', label='FLR-RA')
plt.plot(slot_counts, fns_results['regenerations'], 's-', label='FNS-RA')
plt.title(f'Total Regenerations Used vs. Available Slots (Regens = {FIXED_REGEN_LIMIT})', fontsize = 14)
plt.xlabel('Number of Slots per Link', fontsize = 14)
plt.ylabel('Total Regenerations Used', fontsize = 14)
plt.legend()
plt.grid(True)
plt.savefig('regenerations_vs_slots_50.png')

# === Graph 3: Network Fragmentation vs. Number of Slots ===
plt.figure(figsize=(10, 6))
plt.plot(slot_counts, flr_results['fragmentation'], 'o-', label='FLR-RA')
plt.plot(slot_counts, fns_results['fragmentation'], 's-', label='FNS-RA')
plt.title(f'Network Fragmentation vs. Available Slots (Regens = {FIXED_REGEN_LIMIT})', fontsize = 14)
plt.xlabel('Number of Slots per Link', fontsize = 14)
plt.ylabel('Average Network Fragmentation', fontsize = 14)
plt.legend()
plt.grid(True)
plt.savefig('fragmentation_vs_slots_50.png')

plt.show() # Show all plots