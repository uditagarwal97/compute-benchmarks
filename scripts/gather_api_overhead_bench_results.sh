#!/bin/bash

# Gather API overhead benchmark results.

# Iterate over user arguments.
# This script accepts the following arguments:
# --l0 : For L0 backend
# --sycl : For SYCL Backend
# --no-headers
# --output : Output file name
# --help : Show help message
# --acpp : Use ACPP backend

# Default values
BACKEND="--sycl"
OUTPUT_FILE="api_overhead_bench_results.csv"
HEADERS=" --csv "
USE_ADAPTIVECPP=0
DRY_RUN=0

# Function to display help message
show_help() {
    echo "Usage: $0 [--l0 | --sycl] [--no-headers] [--output <output_file>] [--help]"
    echo
    echo "Gather API overhead benchmark results."
    echo
    echo "Options:"
    echo "  --l0            Use L0 backend"
    echo "  --sycl          Use SYCL backend (default)"
    echo "  --no-headers    Do not show headers in the output file"
    echo "  --output        Specify the output file name (default: api_overhead_bench_results.csv)"
    echo "  --help          Show this help message"
    echo "  --acpp          Use ACPP backend"
    echo "  --dry-run       Show the command without executing it"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --l0)
            BACKEND="--l0"
            shift
            ;;
        --sycl)
            BACKEND="--sycl"
            shift
            ;;
        --no-headers)
            HEADERS+=" --noHeaders "
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        --acpp)
            USE_ADAPTIVECPP=1
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if the output file already exists and remove it
if [[ -f "$OUTPUT_FILE" ]]; then
    rm "$OUTPUT_FILE"
fi

# Get directory from which script is called.
DIR=$(pwd)

# Make sure api_overhead_benchmark_sycl binary is present in the current directory.
if [[ ! -f "$DIR/api_overhead_benchmark_sycl" ]]; then
    echo "api_overhead_benchmark_sycl binary not found in the current directory: $DIR"
    exit 1
fi

# Make sure /sys/devices/system/cpu/cpu23/cpufreq/scaling_governor is set to performance.
cat /sys/devices/system/cpu/cpu23/cpufreq/scaling_governor | grep -q "performance"
if [[ $? -ne 0 ]]; then
    echo "Please set CPU governor to performance."
    exit 1
fi

# Run the benchmark command and gather results.
COMMAND="taskset -c 33-63 "
if [[ "$BACKEND" == "--l0" ]]; then
    COMMAND="$COMMAND $DIR/api_overhead_benchmark_l0 " 
else
    COMMAND="$COMMAND $DIR/api_overhead_benchmark_sycl "
fi

ENV_VARS=""
if [[ "$BACKEND" == "--sycl" ]]; then
    # Check if AdaptiveCPP is enabled
    if [[ $USE_ADAPTIVECPP -eq 1 ]]; then
        ENV_VARS="env ZE_AFFINITY_MASK=0 ACPP_VISIBILITY_MASK=ze ACPP_RT_SCHEDULER=unbound ACPP_RT_MAX_CACHED_NODES=1 ACPP_RT_DAG_REQ_OPTIMIZATION_DEPTH=1 ACPP_PERSISTENT_RUNTIME=0 ACPP_ADAPTIVITY_LEVEL=0 ACPP_DEBUG_LEVEL=0 "
    else
        ENV_VARS="env ZE_AFFINITY_MASK=0 ONEAPI_DEVICE_SELECTOR=level_zero:gpu"
    fi
fi

COMMAND="$ENV_VARS $COMMAND $HEADERS "

COMMAND="$COMMAND  --test=SubmitKernel "
COMMAND="$COMMAND  --DiscardEvents=0 "
COMMAND="$COMMAND  --Profiling=0 "
COMMAND="$COMMAND  --iterations=100000 "

# Loop over number of kernels: 1, 10, 20, 50, 100.
for KERNELS in 1 10 20 50 100; do
    COMMAND1="$COMMAND --NumKernels=$KERNELS "
    # Loop over IOQ: 0, 1.
    for IOQ in 0 1; do
        COMMAND2="$COMMAND1 --Ioq=$IOQ "
        # Loop over MEASURE_COMPLETION: 0, 1.
        for MEASURE_COMPLETION in 0 1; do
            COMMAND3="$COMMAND2 --MeasureCompletion=$MEASURE_COMPLETION "

            # If mesure completion is 1, loop over kernel exec time.
            if [[ $MEASURE_COMPLETION -eq 1 ]]; then
                for KERNEL_EXEC_TIME in 1 5 10 100; do
                    COMMAND4="$COMMAND3 --KernelExecTime=$KERNEL_EXEC_TIME "
                    # Run the command and append output to the file.
                    echo "Running: $COMMAND4 "
                    if [[ $DRY_RUN -eq 0 ]]; then
                        $COMMAND4 >> "$OUTPUT_FILE"
                    fi
                done
            else
                COMMAND4="$COMMAND3 --KernelExecTime=1 "
                # Run the command and append output to the file.
                echo "Running: $COMMAND4 "
                if [[ $DRY_RUN -eq 0 ]]; then
                    $COMMAND4 >> "$OUTPUT_FILE"
                fi
            fi
        done
    done
done
