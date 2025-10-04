import matplotlib.pyplot as plt
import numpy as np

def generate_histogram(file_path):
    """
    Generates a histogram from the data in the given file.

    Args:
        file_path (str): The path to the file containing the data.
    """
    try:
        # Read data from the file
        with open(file_path, 'r') as f:
            data = [float(line.strip()) for line in f]

        # Create the histogram
        plt.hist(data, bins=50)  # You can adjust the number of bins as needed
        plt.xlabel('Preamble Length (ms)')
        plt.ylabel('Frequency')
        plt.title('Histogram of Data from {}'.format(file_path))
        plt.grid(True)

        # Show the histogram
        plt.show()

    except FileNotFoundError:
        print("Error: File not found at {}".format(file_path))
    except ValueError:
        print("Error: Could not convert data to float. Check the file format.")
    except Exception as e:
        print("An error occurred: {}".format(e))

if __name__ == "__main__":
    import os
    import matplotlib.pyplot as plt

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_paths = [
        os.path.join(script_dir, 'histograms', 'PIR_1_dump_node_3.txt'),
        os.path.join(script_dir, 'histograms', 'PIR_1_dump_node_13.txt'),
        os.path.join(script_dir, 'histograms', 'PIR_102_dump_node_3.txt'),
        os.path.join(script_dir, 'histograms', 'PIR_102_dump_node_13.txt')
    ]
    titles = [
        'Node 3 at PIR=17',
        'Node 13 at PIR=17',
        'Node 3 at PIR=102',
        'Node 13 at PIR=102'
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    colors = ['blue', 'green', 'blue', 'green']
    for i, (file_path, title) in enumerate(zip(file_paths, titles)):
        try:
            with open(file_path, 'r') as f:
                data = [float(line.strip()) for line in f]
            color = colors[i]

            if len(set(data)) == 1 and data[0] == 1000:
                print("uniform data")
                axes[i].hist(data, bins=[980, 1000], color=color)
                if i > 1:
                    axes[i].set_xlabel('Preamble Length')
                axes[i].set_ylabel('Frequency')
            else:
                axes[i].hist(data, bins=50, color=color)
                if i > 1:
                    axes[i].set_xlabel('Preamble Length')
                axes[i].set_ylabel('Frequency')
            #axes[i].set_title(title)
            axes[i].set_xlim(0, 1000)  # Set x-axis range
            axes[i].grid(True)
            axes[i].legend([title])

        except FileNotFoundError:
            print("Error: File not found at {}".format(file_path))
        except ValueError:
            print("Error: Could not convert data to float. Check the file format.")
        except Exception as e:
            print("An error occurred: {}".format(e))

    plt.tight_layout()
    plt.show()
