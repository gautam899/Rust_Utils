"""
vendor.py   - vendor selected rust crates.
This is script that will generate all the vendored sources in the src/  directory

This script essentially vendors the crates listed in the crates_list.csv

Prequisite:
Python version >= 3.8 is required to run the script.
The script assumes that the run_vendor.py and crates_list.csv are present at the same path.

Usage:
Run the following command in the terminal.
python3 vendor.py

This will create a directory 'vendored_project'.
Inside 'vendored_project' directory there are two more directories created 'source' and  'src' respectively.
The 'source' directory contains all the source repositories and the 'src' directory contains all the vendored dependencies respectively.
"""

import pandas as pd
import os
import subprocess
import re



# The directory in which the script is present.
SCRIPT_DIR = os.getcwd()
vendored_project = os.path.join(SCRIPT_DIR, "vendored_project")
os.mkdir(vendored_project)

# Crates specified in the requirements
crates_list = pd.read_csv(os.path.join(SCRIPT_DIR, "crates_list.csv"))
 
# Directory where all the crate sources from crates.io gets downloaded.
sources = os.path.join(vendored_project, "sources")
os.mkdir(sources)

# Directory where all the vendored dependencies get stored.
src = os.path.join(SCRIPT_DIR,vendored_project,"src")
os.mkdir(src)

# Create the vendor_logs file
vendor_logs_path = os.path.join(vendored_project, "vendor_logs.txt")
vendor_logs = open(vendor_logs_path, "a")

def get_url(name, version):
    return f"https://crates.io/api/v1/crates/{name}/{version}/download"

# Download the tar file and untar the sources. This will create a directory {name}-{version}. This is because when a crate is published it is published in the format {name}-{version}
def download_and_untar(url):
    try:
        command = f"curl -LJO {url}"
        subprocess.check_output(f"{command}", shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(f"tar -xf download && rm download", shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
       vendor_logs.write(f"Error occured : {e}")

# Parse the crate_list.csv file row wise and read the name,version and git url respectively.
for idx, row in crates_list.iterrows():
    name = row["name"]
    version = row["version"]
    url = get_url(name,version)
        
    # Change current directory to the sources directory.
    os.chdir(sources)

    crate_dir = f"{name}-{version}"

    # Download and untar the sources for the specific version from crates.io
    download_and_untar(url)

    # Run Cargo vendor and store the vendored dependencies inside the src directory. 
    try:
        vendor_logs.write(f"Running cargo vendor command for {name}\n")
        command = f"cd {crate_dir} && cargo vendor --no-delete --versioned-dirs {src}"
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output

    # Append the vendor logs to the vendor_log.txt
    vendor_logs.write(f"Vendor logs for {name}\n")
    vendor_logs.write(output)
    vendor_logs.write("\n")

# Now vendor the crates themselves. We do this by creating a new cargo project and dumping
# the list in Cargo.toml's [dependencies] section.
crate_dir = os.path.join(sources, "tmp")
os.mkdir(crate_dir)
try:
   vendor_logs.write(f"Running cargo vendor command for tmp\n")

   # This initializes the folder and generates the Cargo.toml for us.
   command = f"cd {crate_dir} && cargo init ."
   output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
   output = e.output

with open(os.path.join(sources, "tmp", "Cargo.toml"), "a+") as f:
   for idx, row in crates_list.iterrows():
      name = row["name"]
      version = row["version"]

      # Create a dependency entry in the format : name = "=version".
      # The = before version is important so that cargo does not ignore the patch part of semver (MAJOR.MINOR.PATCH).
      dep = name + " = " +  "\"=" + version + "\"\n"
      f.write(dep)

try:
   vendor_logs.write(f"Running cargo vendor command for tmp\n")

   # Run Cargo vendor and store the vendored dependencies inside the src directory.
   command = f"cd {crate_dir} && cargo vendor --no-delete --versioned-dirs {src}"
   output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
   output = e.output

# Append the vendor logs to the vendor_log.txt
vendor_logs.write("Vendor logs for tmp\n")
vendor_logs.write(output)
vendor_logs.write("\n")

vendor_logs.close()
print("Cargo vendor logs recorded for all the crates successfully.")
