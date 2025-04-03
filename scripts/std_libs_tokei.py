import os
import subprocess
import argparse
import pathlib
import datetime

CURR_DIR = os.getcwd()
LOG_DIR = None
SRC_DIR = None


def helper(crate):
    log_filename = os.path.join(LOG_DIR, f"{crate}_summary_tokei_log.log")
    try:
        # Construct the command. Assuming the crate is in the current directory or a path that can be understood by tokei
        command = ["tokei", os.path.join(SRC_DIR, f"{crate}")] #adjust if needed based on directory structure.

        with open(log_filename, "w") as log_file:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            log_file.write(f"Timestamp: {datetime.datetime.now()}\n")
            log_file.write(f"Command: {' '.join(command)}\n\n")

            if stdout:
                log_file.write(stdout)

            if stderr:
                log_file.write("\n--- Standard Error ---\n")
                log_file.write(stderr)

            log_file.write(f"\nReturn Code: {process.returncode}\n")
        print(f"Tokei run for {crate} completed. Summary log Log saved to {log_filename}")
        
    except FileNotFoundError:
        print(f"Error: Tokei not found. Ensure it's installed and in your PATH.")
    except Exception as e:
        print(f"An error occurred while running tokei for {crate}: {e}")

    
def process_module(crate, root):
    log_filename = os.path.join(LOG_DIR, f"{crate}_tokei_log.log")
    with open(log_filename, "w") as log_file:
        log_file.write(f"Timestamp: {datetime.datetime.now()}\n")
        for directory_path, module, files in os.walk(root):
            relative_path = os.path.relpath(directory_path, root) 
            module_path_str = os.path.join(crate, relative_path)
            if relative_path == ".":
                module_path_str = crate 
            
            log_file.write(f"\n***************************          \n")
            log_file.write(f"\nModule {module_path_str}: \n")
            for file in files:
                log_file.write(f"\nFile {file}:\n")
                file_path = os.path.join(directory_path, file)                    
                try:
                    command = ["tokei", file_path]
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate()

                    if stdout:
                        log_file.write(stdout)

                    if stderr:
                        log_file.write("\n--- Standard Error ---\n")
                        log_file.write(stderr)

                    print(f"Tokei run for {file_path} completed. Log saved to {log_filename}")

                except FileNotFoundError:
                    print(f"Error: Tokei not found. Ensure it's installed and in your PATH.")
                except Exception as e:
                    print(f"An error occurred while running Tokei for {file_path}: {e}")
    
    # Generating the summary.
    helper(crate)    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Get the path to the log dir.")
    parser.add_argument("--log-dir", type = pathlib.Path, required = True, help = "log directory path")
    parser.add_argument("--src-dir", type = pathlib.Path, required = True, help = "path for rusts sources")
    args = parser.parse_args()
    LOG_DIR = args.log_dir
    os.makedirs(LOG_DIR)
    SRC_DIR = args.src_dir #This has to path_to_rust/library
    print(f"Source directory is {SRC_DIR}")
    crates = ['core','alloc','proc_macro','std']
    for crate in crates:
        crate_path = os.path.join(SRC_DIR, crate)
        process_module(crate, crate_path)

                      
