import concurrent.futures
import subprocess

def run_script(script_filename, script_args):
    try:
        command = ['python3', script_filename] + script_args
        result = subprocess.run(command, check=True, capture_output=True)
        return f"Output of {script_filename} with arguments {script_args}:\n{result.stdout.decode()}"
    except subprocess.CalledProcessError as e:
        return f"Error executing {script_filename} with arguments {script_args}: {e}"

if __name__ == "__main__":
    # List of tuples: (script filename, script arguments)
    script_args_list = [
        ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '3000', '-total_sim_packets', '1000']),
        ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '3000', '-total_sim_packets', '2000']),
        ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '3000', '-total_sim_packets', '3000']),
        ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '3000', '-total_sim_packets', '4000']),
        ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '3000', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2500', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2500', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2500', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2500', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2500', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2400', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2400', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2400', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2400', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2400', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2300', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2300', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2300', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2300', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2300', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2200', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2200', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2200', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2200', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2200', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2100', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2100', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2100', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2100', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2100', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2000', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2000', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2000', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2000', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '2000', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1900', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1900', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1900', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1900', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1900', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1800', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1800', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1800', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1800', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1800', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1700', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1700', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1700', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1700', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1700', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1600', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1600', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1600', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1600', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1600', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1500', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1500', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1500', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1500', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1500', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1400', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1400', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1400', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1400', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1400', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1300', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1300', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1300', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1300', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1300', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1200', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1200', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1200', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1200', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1200', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1100', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1100', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1100', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1100', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1100', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1000', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1000', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1000', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1000', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '1000', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '900', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '900', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '900', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '900', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '900', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '800', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '800', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '800', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '800', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '800', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '700', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '700', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '700', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '700', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '700', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '600', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '600', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '600', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '600', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '600', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '500', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '500', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '500', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '500', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '500', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '400', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '400', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '400', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '400', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '400', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '300', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '300', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '300', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '300', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '300', '-total_sim_packets', '5000']),

        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '200', '-total_sim_packets', '1000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '200', '-total_sim_packets', '2000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '200', '-total_sim_packets', '3000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '200', '-total_sim_packets', '4000']),
        # ('representative_network.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '200', '-total_sim_packets', '5000']),

    ]

    for script_info in script_args_list:
        result = run_script(*script_info)
        print(result)

    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     # Use executor.map to parallelize the execution of run_script
    #     results = executor.map(lambda x: run_script(*x), script_args_list)

    #     # Print the results
    #     for result in results:
    #         print(result)
