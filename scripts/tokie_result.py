import os
import subprocess
import pandas as pd
import argparse
import pathlib
import datetime

CURR_DIR = os.getcwd()
crates_list = pd.read_csv(os.path.join(CURR_DIR, "crates_list.csv"))
LOG_DIR = None
SRC_DIR = None
def helper(crate):
    # Log everything
    log_filename = os.path.join(LOG_DIR, f"{crate}_tokei_log.log")
    
    try:
        # Construct the command. Assuming the crate is in the current directory or a path that can be understood by tokei
        command = ["tokei", os.path.join(SRC_DIR, f"{crate}")] #adjust if needed based on directory structure.

        with open(log_filename, "w") as log_file:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            log_file.write(f"Timestamp: {datetime.datetime.now()}\n")
            log_file.write(f"Command: {' '.join(command)}\n\n")

            if stdout:
                log_file.write("--- Standard Output ---\n")
                log_file.write(stdout)

            if stderr:
                log_file.write("\n--- Standard Error ---\n")
                log_file.write(stderr)

            log_file.write(f"\nReturn Code: {process.returncode}\n")

        print(f"Tokei run for {crate} completed. Log saved to {log_filename}")

    except FileNotFoundError:
        print(f"Error: Tokei not found. Ensure it's installed and in your PATH.")
    except Exception as e:
        print(f"An error occurred while running tokei for {crate}: {e}")
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Get the path to the log dir.")
    parser.add_argument("--log-dir", type = pathlib.Path, required = True, help = "log directory path")
    parser.add_argument("--src-dir", type = pathlib.Path, required = True, help = "path for rusts sources")
    args = parser.parse_args()
    LOG_DIR = args.log_dir
    SRC_DIR = args.src_dir
    print(f"Source directory is {SRC_DIR}")
    
    for idx,row in crates_list.iterrows():
        name = row["name"]
        version = row["version"]
        crate = f"{name}-{version}"
        helper(crate)

                      
