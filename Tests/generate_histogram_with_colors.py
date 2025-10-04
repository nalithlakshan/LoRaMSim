import matplotlib.pyplot as plt
import numpy as np
import os

def generate_histogram_with_colors(file_paths, titles, colors, output_path=None):
    """
    Generates a histogram with four subplots, each with a different color.

    Args:
        file_paths (list): A list of file paths to the data.
        titles (list): A list of titles for each subplot.
        colors (list): A list of colors for each subplot.
        output_path (str, optional): The path to save the figure. Defaults to None.
    """

    if len(file_paths) != 4 or len(titles) != 4 or len(colors) != 4:
        raise ValueError("The number of file paths, titles, and colors must be 4.")

    plt.figure(figsize=(12, 8))

    for i, (file_path, title, color) in enumerate(zip(file_paths, titles, colors)):
        try:
            with open(file_path, 'r') as f:
                data = [float(line.strip()) for line in f]

            plt.hist(data, bins=50, color=color, alpha=0.7, label=title)

        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
        except ValueError:
            print("Error: Could not convert data to float. Check the file format.")
        except Exception as e:
            print(f"An error occurred: {e}")

    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.title('Combined Histogram')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path)
    else:
        plt.show()


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_paths = [
        os.path.join(script_dir, 'histograms', 'PIR_1_dump_node_3.txt'),
        os.path.join(script_dir, 'histograms', 'PIR_1_dump_node_13.txt'),
        os.path.join(script_dir, 'histograms', 'PIR_102_dump_node_3.txt'),
        os.path.join(script_dir, 'histograms', 'PIR_102_dump_node_13.txt')
    ]
    titles = [
        'PIR_1_dump_node_3',
        'PIR_1_dump_node_13',
        'PIR_102_dump_node_3',
        'PIR_102_dump_node_13'
    ]
    colors = ['blue', 'green', 'red', 'purple']

    generate_histogram_with_colors(file_paths, titles, colors)