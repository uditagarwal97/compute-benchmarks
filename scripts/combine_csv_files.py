# Script to combine CSV files outputed by compute-bench.

import os
import sys
import pdb

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

data_points = []

# function to take CSV directory as input and parse CSV files.
def parse_csv_files(csv_dir):
    global data_points
    
    # Get absolute path.
    csv_dir = os.path.abspath(csv_dir)

    for file in os.listdir(csv_dir):
        if file.endswith(".csv"):
            with open(csv_dir + "/" + file, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("TestCase"):
                        continue
                    data = line.split(",")
                    BenchmarkName = data[0].split('(')[0]
                    median = data[2]
                    api = ""
                    profiling = ""
                    ioq = ""
                    num_kernels = ""
                    kernel_exec_time = ""
                    measure_completion = ""
                    discard_event = ""
        
                    compiler = ""
                    optimization = ""
                    backend = ""
                    adapter = ""

                    for bench_config in data[0].split('(')[1].split(')')[0].split():
                        bench_config = bench_config.split('=')
                        if bench_config[0] == "api":
                            api = bench_config[1]
                        elif bench_config[0] == "Profiling":
                            profiling = bench_config[1]
                        elif bench_config[0] == "Ioq":
                            ioq = bench_config[1]
                        elif bench_config[0] == "NumKernels":
                            num_kernels = bench_config[1]
                        elif bench_config[0] == "KernelExecTime":
                            kernel_exec_time = bench_config[1]
                        elif bench_config[0] == "MeasureCompletion":
                            measure_completion = bench_config[1]
                        elif bench_config[0] == "DiscardEvents":
                            discard_event = bench_config[1]
                        else:
                            print("Invalid config: " + bench_config[0])
                            exit(1)

                    # Parse file name to get compiler, optimization, backend and adapter.
                    file_name = file.split(".")[0].split("_")
                    backend = file_name[0]
                    compiler = file_name[1]
                    optimization = file_name[-1]
                    adapter = "NA"
                    if compiler == "dpcpp":
                        adapter = file_name[3]

                    data_points.append(DataPoint(BenchmarkName, compiler, optimization, backend, adapter, ioq, num_kernels, kernel_exec_time, measure_completion, median))

def output_combined_csv():
    pdb.set_trace()
    with open("combined.csv", "w") as f:
        f.write("BenchmarkName,Compiler,Optimization,Backend,Adapter,Ioq,NumKernels,KernelExecTime,MeasureCompletion,MedianTime\n")
        for data_point in data_points:
            f.write(data_point.benchmark_name + "," + data_point.compiler_name + "," + data_point.optimization + "," + data_point.backend + "," + data_point.adapter + "," + data_point.ioq + "," + data_point.num_kernels + "," + data_point.kernel_exec_time + "," + data_point.measure_completion + "," + data_point.median_time + "\n")

# main
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python combine_csv_files.py <csv_dir>")
        exit(1)
    csv_dir = sys.argv[1]
    parse_csv_files(csv_dir)
    output_combined_csv()
