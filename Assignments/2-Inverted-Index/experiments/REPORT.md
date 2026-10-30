# Assignment 2: Evaluating the inverted index

## Implementation and correctness

The mapper splits text at characters that are not Unicode letters. It emits case-sensitive word and filename pairs. The reducer removes duplicate filenames, sorts them, and returns `count filenames`. Filenames exclude directory paths to match the supplied expected output. The corpus test and the Go framework tests pass.

## Method

Machine: AMD Ryzen 7 7735U (8 cores, 16 logical CPUs); Linux-6.12.113+deb13-amd64-x86_64-with-glibc2.41; go version go1.27.1 linux/amd64. CPU affinity permits 16 logical CPUs. Runs used the existing framework unchanged, with three reduce partitions.

The script builds the executable before timing. Each trial starts a distributed master, waits for its socket, and launches separate worker processes. Timing starts at master launch and ends at master exit. It includes worker registration, scheduling, map and reduce tasks, worker shutdown RPCs, and the final merge. The script then terminates any idle workers. The framework uses Unix-domain RPC sockets. The README arguments such as `localhost:7777` name local socket files.

The datasets contain the first 1, 4, 8, or 16 files in alphabetical filename order. Each configuration has three trials. The script shuffles trial order with seed 452 and gives each trial a separate temporary directory. Both plots use the same measurements for four workers and 16 documents. All 21 distributed outputs match their sequential baselines by SHA-256 hash. Sequential runs check correctness only and do not contribute timings. The repository includes logs and raw timings. The script does not flush file-system caches, and other activity on the machine may affect the measurements.

## Results

![Execution time versus workers and corpus size](performance.png)

Points show median times. Error bars show the minimum and maximum across three trials.

| Workers | Documents | Input MiB | Median seconds | Minimum to maximum seconds |
|---:|---:|---:|---:|---:|
| 1 | 16 | 15.370 | 4.102 | 4.099 to 4.132 |
| 2 | 16 | 15.370 | 4.139 | 4.099 to 4.141 |
| 4 | 16 | 15.370 | 4.140 | 4.136 to 4.145 |
| 8 | 16 | 15.370 | 4.138 | 4.094 to 4.142 |
| 4 | 1 | 0.132 | 4.043 | 4.032 to 4.043 |
| 4 | 4 | 2.252 | 4.038 | 4.034 to 4.039 |
| 4 | 8 | 4.721 | 4.083 | 4.046 to 4.087 |

## Interpretation

Increasing workers from 1 to 8 changes median execution time from 4.102 to 4.138 seconds. The speedup is 0.99 times, so extra worker processes provide no improvement in these trials. The scheduler launches RPC goroutines for every unfinished task and assigns them round-robin. It checks completion once per second. Each worker can execute several task RPCs at once, so even one worker process can use multiple cores. Worker count therefore does not set the number of concurrent tasks.

The scheduler reads and writes completion flags without synchronization. It may also resubmit a task that has not finished after one second. Duplicate tasks can add work and write to the same intermediate files. Matching outputs do not prove that the scheduler has no races. These experiments leave the scheduler unchanged and remove duplicate filenames only in the reducer.

With four workers, increasing the corpus from 1 to 16 documents changes median time from 4.043 to 4.140 seconds, a factor of 1.02. Time grows less than file count over this range. The books differ in size, so the table also gives input bytes. Startup and one-second completion checks can obscure changes in processing time. These results do not establish how execution time scales for larger datasets.

There are only three reduce partitions, which limits useful parallelism during the reduce phase. Each map task processes a whole file, so large books can delay that phase. Serialization, shared storage, memory allocation, garbage collection, and the serial final merge can also limit speedup. These experiments use one machine and do not measure network costs between machines.

## Reproduce

From the assignment directory:

```bash
export PATH=/usr/local/go/bin:$PATH  # if Go is not on PATH
cd starter
sh test/scripts/test-ii.sh
test ! -s diff.out  # the supplied shell script itself does not return failure on mismatch
go test ./... -timeout 180s
cd ..
python3 experiments/run.py
python3 experiments/analyze.py  # requires matplotlib
```

The assignment asks for three performance experiments but lists two. This report covers both listed experiments.
