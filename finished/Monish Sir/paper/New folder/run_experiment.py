import matplotlib.pyplot as plt
import numpy as np

# Import the functions from your refactored scripts
from simulation_flr import run_flr_simulation
from simulation_fns import run_fns_simulation

print("Starting experiment...")

# --- Define Your Independent Variable Range ---
# We will test a range of regenerator limits
regenerator_limits = [1, 2, 3, 4, 5, 6, 7, 8]
FIXED_SLOTS_LIMIT = 500
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
for limit in regenerator_limits:
    print(f"Running simulations with max {limit} regenerators per node...")
    
    # Run FLR
    flr_data = run_flr_simulation(slots_limit = FIXED_SLOTS_LIMIT, regen_limit=limit)
    flr_results['blocking'].append(flr_data['bandwidth_blocking_ratio'])
    flr_results['regenerations'].append(flr_data['total_regenerations'])
    flr_results['fragmentation'].append(flr_data['network_fragmentation'])
    
    # Run FNS
    fns_data = run_fns_simulation(slots_limit = FIXED_SLOTS_LIMIT, regen_limit=limit)
    fns_results['blocking'].append(fns_data['bandwidth_blocking_ratio'])
    fns_results['regenerations'].append(fns_data['total_regenerations'])
    fns_results['fragmentation'].append(fns_data['network_fragmentation'])

print("Experiment complete. Plotting results...")

# --- Plotting ---

# === Graph 1: Bandwidth Blocking Ratio vs. Regenerator Limit ===
plt.figure(figsize=(10, 6))
plt.plot(regenerator_limits, flr_results['blocking'], 'o-', label='FLR-RA')
plt.plot(regenerator_limits, fns_results['blocking'], 's-', label='FNS-RA')
plt.title('Bandwidth Blocking Ratio (BBR) vs. Regenerator Limit', fontsize = 14)
plt.xlabel('Max Regenerators Per Node', fontsize = 14)
plt.ylabel('Bandwidth Blocking Ratio', fontsize = 14)
plt.legend()
plt.grid(True)
plt.yscale('log') # Blocking is often plotted on a log scale
plt.savefig('bbr_vs_regenerators.png')

# === Graph 2: Total Regenerations vs. Regenerator Limit ===
plt.figure(figsize=(10, 6))
plt.plot(regenerator_limits, flr_results['regenerations'], 'o-', label='FLR-RA')
plt.plot(regenerator_limits, fns_results['regenerations'], 's-', label='FNS-RA')
plt.title('Total Regenerations Used vs. Regenerator Limit', fontsize = 14)
plt.xlabel('Max Regenerators Per Node', fontsize = 14)
plt.ylabel('Total Regenerations Used', fontsize = 14)
plt.legend()
plt.grid(True)
plt.savefig('regenerations_vs_regenerators.png')

# === Graph 3: Network Fragmentation vs. Regenerator Limit ===
plt.figure(figsize=(10, 6))
plt.plot(regenerator_limits, flr_results['fragmentation'], 'o-', label='FLR-RA')
plt.plot(regenerator_limits, fns_results['fragmentation'], 's-', label='FNS-RA')
plt.title('Network Fragmentation vs. Regenerator Limit', fontsize = 14)
plt.xlabel('Max Regenerators Per Node', fontsize = 14)
plt.ylabel('Average Network Fragmentation', fontsize = 14)
plt.legend()
plt.grid(True)
plt.savefig('fragmentation_vs_regenerators.png')

plt.show() # Show all plots