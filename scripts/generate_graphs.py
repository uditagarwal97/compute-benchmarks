# Script to generate graphs from the benchmarking results.

import os
import sys
import matplotlib.pyplot as plt
import argparse
import pandas as pd
import pdb
import numpy as np
from scipy.stats import bootstrap
import math

class DataPoint:
    benchmark_name = ""
    compiler_name = ""
    optimization = ""
    backend = ""
    adapter = ""
    ioq = ""
    num_kernels = ""
    kernel_exec_time = ""
    measure_completion = ""
    median_time = ""
    def __init__(self, bench_name, compiler_name, optimization, backend, adapter, ioq, num_kernels, kernel_exec_time, measure_completion, median_time):
        self.benchmark_name = bench_name
        self.compiler_name = compiler_name
        self.optimization = optimization
        self.backend = backend
        self.adapter = adapter
        self.ioq = ioq
        self.num_kernels = num_kernels
        self.kernel_exec_time = kernel_exec_time
        self.measure_completion = measure_completion
        self.median_time = median_time

# "name" : [ list of data points ]
benchmark_results = []

# Pandas DataFrame to store the benchmarking results.
benchmark_df = None

# Output folder to store the generated graphs.
output_folder = ""

# Benchmark name
benchmark_name = ""
# Optimization levels
optimization_levels = []
# Compilers
compiler_list = []

def validateUserInputs(args):

    # Check if the benchmarking file is valid and in CSV format.
    if not os.path.isfile(args.results_in_csv):
        print("Error: The file does not exist: ", args.results_in_csv)
        sys.exit(1)

    try:
        df = pd.read_csv(args.results_in_csv)
        global benchmark_df
        benchmark_df = df
    except:
        print("Error: The file is not in CSV format: ", args.results_in_csv)
        sys.exit(1)

    # Check if the output folder exists.
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
    else:
        if not os.path.isdir(args.output_folder):
            print("Error: The output folder is not a directory: ", args.output_folder)
            sys.exit(1)
    global output_folder
    output_folder = args.output_folder

# Parse CSV file
def parseResults():
    global benchmark_df, benchmark_name, benchmark_results
    global optimization_levels, compiler_list, benchmark_name

    # Go over all other rows of the CSV file and parse the data.
    for _, row in benchmark_df.iterrows():

        # Skip over empty rows
        if pd.isnull(row.iloc[0]):
            continue

        benchmark_name_local = str(row.iloc[0])
        compiler = str(row.iloc[1])
        optimization = str(row.iloc[2])
        backend = str(row.iloc[3])
        adapter = str(row.iloc[4])
        ioq = str(row.iloc[5]) 
        num_kernels = str(row.iloc[6])
        kernel_exec_time = str(row.iloc[7])
        measure_completion = str(row.iloc[8])
        median_time = str(row.iloc[9])

        benchmark_name = benchmark_name_local
        
        # Add the optimization level to the list of optimization levels.
        if optimization not in optimization_levels:
            optimization_levels.append(optimization)

        # Add the compiler to the list of compilers.
        if compiler not in compiler_list:
            compiler_list.append(compiler)

        benchmark_results.append(DataPoint(benchmark_name_local, compiler, optimization, backend, adapter, ioq, num_kernels, kernel_exec_time, measure_completion, median_time))

def generateGraphForBenchmarkExecTime(benchmark_name, data_points, Ioq, MeasureCompletion, NumKernels, KernelExecTime):

    global optimization_levels, compiler_list

    # Create a sub-plot for each device. The sub-plot should be a
    # bar chart, grouped by optimization level.
    fig = plt.figure(figsize=(15, 7))

    title = benchmark_name + \
    " (Ioq=" + str(Ioq) + \
    ", MeasureCompletion=" + str(MeasureCompletion) + \
    ", NumKernels=" + str(NumKernels) + \
    ", KernelExecTime=" + str(KernelExecTime) + ")"

    fig.suptitle(title, size=20)

    gs = fig.add_gridspec(1, len(optimization_levels), hspace=0, wspace = 0.05, width_ratios=[2,2,1])
    axs = gs.subplots(sharex=False, sharey=True)

    # Populate the sub-plot for each device.
    for i, optimization_level in enumerate(optimization_levels):
        ax = axs[i]

        is_l0 = False
        if optimization_level == "pvc":
            is_l0 = True
            ax.set_title("O2", fontsize=15)
        else:
            ax.set_title(optimization_level, fontsize=18)

        ax.grid(axis='y', linestyle='--', linewidth=0.5)

        # DS to initialize for each device.
        subplot_xaxis = ['acpp', 'dpcpp_v1', 'dpcpp_v2']
        subplot_labels = ['acpp', 'dpcpp with v1 L0 adapter', 'dpcpp with v2 L0 adapter']
        hist_color = ['c', 'm', 'y']
        subplot_data_points = [0, 0, 0]

        # Populate the DS.
        for data_point in data_points:
            if data_point.ioq == Ioq and \
            data_point.measure_completion == MeasureCompletion and \
            data_point.optimization == optimization_level and \
            data_point.num_kernels == NumKernels and \
            data_point.kernel_exec_time == KernelExecTime:
                compiler_name = data_point.compiler_name
                adapter = data_point.adapter
                median = float(data_point.median_time)
                
                if compiler_name == "acpp":
                    subplot_data_points[0] = median
                elif compiler_name == "dpcpp" and adapter == "v1":
                    subplot_data_points[1] = median
                elif compiler_name == "dpcpp" and adapter == "v2":
                    subplot_data_points[2] = median
                else:
                    print("Shouldn't have reached here")
                    exit(1)
      
        width = 0.5
        if is_l0:
            subplot_xaxis = ["L0", ""]
            subplot_labels = ["L0", ""]
            hist_color = ['g']
            subplot_data_points = [subplot_data_points[0], 0]
            width = 0.5

        # Populate the bar chart.
        ax.bar(subplot_xaxis, subplot_data_points, width, label=subplot_labels, color=hist_color)
        ax.tick_params(axis="x", labelsize=17)

    # Have a common legend for all sub-plots.
    lines_labels = [axs[0].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    lines.append(axs[2].get_legend_handles_labels()[0][0])
    labels.append(axs[2].get_legend_handles_labels()[1][0])
    fig.legend(lines, labels, bbox_to_anchor=(0.5, -0.05), loc='lower right', mode="expand", ncol=2, borderaxespad=0., fontsize=16)

    fig.text(0.07, 0.5, 'Median Execution Time (us)', {'size':16}, va='center', rotation='vertical')

    for ax in fig.get_axes():
        ax.label_outer()

    figure_name = benchmark_name + "_" + str(Ioq) + \
    "_" + str(MeasureCompletion) + "_" + str(NumKernels) +\
    "_" + str(KernelExecTime) + "_exec_time.png"

    global output_folder
    plt.savefig(output_folder + "/" + figure_name, dpi=140, bbox_inches='tight')
    plt.close(fig)

# Generate graphs
def generateGraphs():
    global benchmark_results, benchmark_name

    # Iterate over all possible combination of Ioq, MeasureCompletion, NumKernels, Kernel exec time
    for numKernel in [1, 10, 20, 50, 100]:
        for ioq in [0, 1]:
            for mc in [0, 1]:
                if mc == 1:
                    for kexecTime in [1, 5, 10, 100]:
                        generateGraphForBenchmarkExecTime(benchmark_name, benchmark_results, str(ioq), str(mc), str(numKernel), str(kexecTime))
                else:
                    generateGraphForBenchmarkExecTime(benchmark_name, benchmark_results, str(ioq), str(mc), str(numKernel), "1")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("results_in_csv")

    parser.add_argument("--output_folder", action="store", type=str, default="./results", help="Specify the path to the output folder. \t Default: ./results/")
    args = parser.parse_args()

    validateUserInputs(args)

    parseResults()

    # Generate graphs
    generateGraphs()

# main
if __name__ == "__main__":
    main()