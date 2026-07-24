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
        ('g17_setup1_with_1ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '10000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_1ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '20000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_1ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '30000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_1ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '40000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_1ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '50000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_1ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '60000', '-total_sim_packets', '1000']),

        ('g17_setup1_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '10000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '20000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '30000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '40000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '50000', '-total_sim_packets', '1000']),
        ('g17_setup1_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '60000', '-total_sim_packets', '1000']),

        ('g17_setup2_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '10000', '-total_sim_packets', '1000']),
        ('g17_setup2_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '20000', '-total_sim_packets', '1000']),
        ('g17_setup2_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '30000', '-total_sim_packets', '1000']),
        ('g17_setup2_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '40000', '-total_sim_packets', '1000']),
        ('g17_setup2_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '50000', '-total_sim_packets', '1000']),
        ('g17_setup2_with_3ed.py',[ '-repeater_delay_multiplier', '3', '-avg_send_time', '60000', '-total_sim_packets', '1000']),
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
