#!/bin/bash

# build-crates - build crates required for the VxWorks Auto Rust application development
#
# This program builds source code and test code for specified crates in a VxWorks
# environment.

ts=`date`
csv_ts=`date +"%Y%m%d%H%M"`
progname=`basename $0`
script_dir=`dirname $0`
script_dir=`cd $script_dir; pwd`
src_dir=`cd $script_dir/../src; pwd`
csv_file_name=crate_status_${csv_ts}.csv


savecmd="$@"
error () {
    echo "$@" 1>&2
    exit 1
}

log () {
    echo "$@" | tee -a $logfile
}

usage () {
cat << EOH
$progname -h
$progname --workspace directory [--default-features|--all-features] [--log logfile] [--verbose] [--csv file] [--clean|--no-tests] [crate [crate] ...]

-h                    - print this message
--workspace           - put all generated artifacts and intermedidate files
                        in specified directory. REQUIRED.
--default-features    - build with default features enabled. Default.
--all-features        - build with all features enabled.
--log logfile         - append log to specfied file.  Defaults to build-crates.log
                        in the current directory
--verbose             - verbose output
--no-tests            - runs only 'cargo build'. Does not run 'cargo test'
--clean               - runs 'cargo clean'
--csv                 - Specify full path to the file to write crate name and 
                        build/test status in CSV format. The filename defaults to 
                        $csv_file_name under the workspace directory.

Specify one or more crates to build. If no crate is specified then 
all available crates are built.
EOH
}

# Function to write crate status to CSV file
write_status_to_csv() {
    local crate_name=$1
    local status=$2

    # Append crate status to the CSV file
    echo "$crate_name,$status" >> "$csv_file"
}

# crates specified in requirements
crate_list_file=$script_dir/crates-list.txt

crate_list () { 
    [ -f $crate_list_file ] || error "Cannot find list of crates"
    grep -v '^#' $crate_list_file
}

all_crates=`crate_list`
all_features=false
do_clean=false
do_build=true
do_test_build=true
crates=""
logfile=build-crates.log
verbose=false
csv_file=""

while [ $# != 0 ]; do
    case $1 in
    --default-features) all_features=false ;;
    --all-features) all_features=true ;;
    --clean) do_clean=true ; do_build=false ; do_test_build=false ;;
    --no-tests) do_test_build=false ;;
    --log) logfile=$2 ; shift ;;
    --workspace) workspace=$2; shift ;;
    --verbose) verbose=true ;;
    --csv) csv_file=$2; shift ;;
    -h|--help) usage ; exit 0 ;;
    -*) error "Unknown option $1. Run $progname -h for help" ;;
    *) crates="$crates $1" ;;
    esac
    shift
done

[ -n "$WIND_CC_SYSROOT=" ] || error "WIND_CC_SYSROOT not set"
[ -n "$RUSTC" ] || error "RUSTC not set"
[ -f "$RUSTC" ] || error "Cannot find rust compiler wrapper at $RUSTC"
[ -n "$CARGO_HOME=" ] || error "CARGO_HOME not set"

[ -n "$workspace" ] || error "Specify workspace. Run $progname -h for help"
[ -d "$workspace" ] || mkdir -p $workspace
[ -d "$workspace" ] || error "could not create workspace $workspace"
workspace=`cd $workspace; pwd`


# create status CSV file with headers
[ -n "$csv_file" ] || csv_file=$workspace/$csv_file_name
d=`dirname $csv_file`
b=`basename $csv_file`
d=`cd $d; pwd`
csv_file=$d/$b
echo "Crate Name,Status" > "$csv_file"
[ -w $csv_file ] || error "Cannot write $csv_file"

[ -n "$crates" ] || crates="$all_crates"

logdir=`dirname $logfile`
[ -z "$logdir" ] && logdir=`pwd`
logdir=`cd $logdir; pwd`
logfileb=`basename $logfile`
logfile="$logdir/$logfileb"

log "$0 invoked on $ts with $savecmd"
log "log being written to $logfile"

cargo_opts=""
if $all_features;  then 
    cargo_opts="$cargo_opts --all-features"
fi
if $verbose; then
    cargo_opts="$cargo_opts --verbose"
fi

cargo_clean_cmd="cargo clean $cargo_opts"
cargo_build_cmd="cargo build $cargo_opts"
cargo_test_build_cmd="cargo test --no-run $cargo_opts"
for c in $crates; do
    if [ ! -d $src_dir/$c ]; then 
        log "Skipping $c: no such crate"
        write_status_to_csv $c "fail"
	continue
    fi
    wsopt="--target-dir $workspace/$c"
    if $do_clean;  then
        log "Cleaning crate $c with $cargo_clean_cmd"
	(cd $src_dir/$c; $cargo_clean_cmd $wsopt) 2>&1 | tee -a $logfile
    fi
    if $do_build; then
        log "Building source for crate $c with $cargo_build_cmd"
	(cd $src_dir/$c; rm -rf Cargo.lock; $cargo_build_cmd $wsopt) 2>&1 | tee -a $logfile
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            write_status_to_csv $c "fail"
            continue
        else
            write_status_to_csv $c "pass"
        fi
    fi
    if $do_test_build; then
        log "Building tests for crate $c with $cargo_test_build_cmd"
	(cd $src_dir/$c; $cargo_test_build_cmd $wsopt) 2>&1 | tee -a $logfile
    fi
done
