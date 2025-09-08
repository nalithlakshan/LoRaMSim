import matplotlib.pyplot as plt
import os

# Enter Node IDs
nodes = [8, 14, 15, 16]

# Create figure and subplots (share x-axis)
fig, axes = plt.subplots(len(nodes), 1, figsize=(12, 8), sharex=True)

# File paths
files = ["./tx status data/dump_node_" + str(id) + ".txt" for id in nodes]

for i in range(len(files)):
    file_name = files[i]

    intervals = []
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    start = float(parts[0])
                    end = float(parts[1])
                    intervals.append((start, end))
    else:
        print(f"Warning: {file_name} not found!")
        continue

    # Prepare time and state lists
    times = []
    states = []

    for start, end in intervals:
        times.append(start)
        states.append(1)
        times.append(end)
        states.append(0)

    # Plot into corresponding axis
    ax = axes[i]
    ax.step(times, states, where='post')
    ax.set_ylabel(f'Node {nodes[i]}')
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Rx/CAD", "Tx"])
    ax.grid(True)

# Common labels
plt.xlabel('Time (s)')
fig.suptitle('Transmission State vs Time', fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()
