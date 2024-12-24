import subprocess



def start_process(part_num):
    process = subprocess.Popen(['python', 'building_clean_csv.py', str(part_num)], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
    print(f"Started new process: {process}")
    return process

def run_processes(max_parallel_processes = 10):
    next_part = 1
    max_part_num = 193
    processes = []

    # start the first max parallel processes
    for _ in range(max_parallel_processes):
        processes.append(start_process(next_part))
        next_part += 1

    # run until list is empty
    while processes:
        for process in processes:

            return_code = process.poll()  # None if not finished, 0 if finished successfully.

            if return_code is not None:  # Process is finished

                print(f"{process} has returned with return code {return_code}")

                # restart process if this happens
                if return_code != 0:
                    new_process = subprocess.Popen(process.args, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True)
                    processes.append(new_process)
                    print(f"Restarted process: {new_process}")
                    processes.remove(process)
                    continue

                # if return code is 0, it means successfully ended
                stdout, stderr = process.communicate()  # Capture the output and error
                if stdout:
                    print(f"Output: {stdout.strip()}")
                if stderr:
                    print(f"Error: {stderr.strip()}")

                processes.remove(process)  # Remove the finished process from the list
                if next_part <= max_part_num:
                    processes.append(start_process(next_part))
                    next_part += 1

if __name__ == "__main__":

    run_processes()

