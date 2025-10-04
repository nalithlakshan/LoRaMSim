import matplotlib.pyplot as plt
import numpy as np
import os

def get_power_level(mode):
    """Convert mode string to power level value"""
    power_levels = {
        "CAD": 1,
        "CAD_Scan_rise": 50,
        "CAD_Scan_fall": 1,
        "RX": 50,
        "TX_preamble": 500,
        "TX_frame": 500
    }
    return power_levels.get(mode, 0)

def read_state_file(filepath):
    """Read state diagram data file and return time and power level arrays"""
    times = []
    modes = []
    power_levels = []
    tx_preamble_regions = []  # To store (start_time, end_time) for TX_preamble regions
    
    with open(filepath, 'r') as file:
        for line in file:
            time, mode = line.strip().split()
            time = float(time)
            times.append(time)
            modes.append(mode)
            power_levels.append(get_power_level(mode))
            
            # Track TX_preamble regions
            if mode == "TX_preamble":
                tx_preamble_regions.append((time, None))  # Start of preamble
            elif mode == "TX_frame" and tx_preamble_regions and tx_preamble_regions[-1][1] is None:
                tx_preamble_regions[-1] = (tx_preamble_regions[-1][0], time)  # End of preamble
    
    return np.array(times), np.array(power_levels), tx_preamble_regions

def plot_state_diagrams(file_list):
    """Create subplots for each node's state diagram"""
    num_plots = len(file_list)
    fig, axes = plt.subplots(num_plots, 1, figsize=(12, 3*num_plots), sharex=True)
    if num_plots == 1:
        axes = [axes]
    
    # Set up common style
    plt.style.use('bmh')  # Using 'bmh' style for a clean, professional look
    
    # Set figure background to white
    fig.patch.set_facecolor('white')
    for ax in axes:
        ax.set_facecolor('white')
    
    for idx, filename in enumerate(file_list):
        filepath = os.path.join("state diagram data", filename)
        times, power_levels, tx_preamble_regions = read_state_file(filepath)
        
        ax = axes[idx]
        
        # Plot the main power level line
        ax.step(times, power_levels, where='post', label='Power Level', color='blue')
        
        # Highlight TX_preamble regions with yellow background
        for start, end in tx_preamble_regions:
            if end is not None:  # Only plot complete regions
                ax.axvspan(start, end, alpha=0.3, color='yellow', label='TX_preamble' if start == tx_preamble_regions[0][0] else "")
        
        # Customize the plot
        node_id = filename.split('_')[2].split('.')[0]  # Extract node ID from filename
        ax.set_ylabel(f'Node {node_id}')
        
        # Set y-axis ticks and labels
        y_ticks = [1, 50, 500]
        y_labels = ['CAD (11uA)', 'RX (50mA)', 'TX (500mA)']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        # Only show x-label for the bottom subplot
        # if idx == num_plots - 1:
        ax.set_xlabel('Time (ms)')
        
        # Add legend for the first subplot only
        if idx == 0:
            ax.legend()

    # Adjust layout to prevent overlap
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('state_diagrams.png', dpi=300, bbox_inches='tight')
    plt.show()

# Example usage
file_list = ["dump_node_0.txt", "dump_node_1.txt", "dump_node_2.txt", "dump_node_3.txt", "dump_node_4.txt", "dump_node_5.txt", "dump_node_11.txt", "dump_node_12.txt"]
plot_state_diagrams(file_list)
