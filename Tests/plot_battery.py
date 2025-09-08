import matplotlib.pyplot as plt
import csv
import numpy as np

#Enter Node IDs of which you need to plot battery percentage over time
nodes = [8,14,15,16]


#CSV file paths
csv_files = []
for id in nodes:
    csv_file = "./battery status data/dump_node_"+str(id)+".csv"
    csv_files.append(csv_file)

for i in range(len(csv_files)):
    csv_file = csv_files[i]
    # Read the CSV file
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        time = []
        battery_remaining = []
        for row in reader:
            # Skip empty rows or malformed rows
            if len(row) < 4:
                continue
            time.append(float(row[1])/60000)  # Column 2: time (env.now)
            battery_remaining.append(float(row[3]))  # Column 3: batteryRemaining

        # Read the CSV file
        with open(csv_file, 'r') as file:
            lb = "Repeater " +csv_file.strip('.csv').split("_")[-1]
            plt.plot(time, battery_remaining, label=lb)

plt.xlabel('Time (min)')
plt.ylabel('Remaining Battery %')
plt.xlim(0,)
plt.ylim(0,100)
plt.yticks([10*i for i in range(11)])
plt.title('Battery Remaining over Time')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
