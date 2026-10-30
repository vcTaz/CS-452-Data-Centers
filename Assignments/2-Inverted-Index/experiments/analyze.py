"""Create report and plots from results.csv (requires matplotlib)."""
import csv
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
rows = list(csv.DictReader((OUT / 'results.csv').open()))
assert len(rows) == 21 and all(r['correct'] == 'True' for r in rows)
meta = json.loads((OUT / 'environment.json').read_text())

def summarize(workers, documents):
    values = [float(r['seconds']) for r in rows if int(r['workers']) == workers and int(r['documents']) == documents]
    return statistics.median(values), min(values), max(values)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), layout='constrained')
for ax, xs, configs, label in [
    (axes[0], [1, 2, 4, 8], [(w, 16) for w in [1, 2, 4, 8]], 'Worker processes (16 documents)'),
    (axes[1], [1, 4, 8, 16], [(4, n) for n in [1, 4, 8, 16]], 'Documents (4 workers)')]:
    stats = [summarize(*c) for c in configs]
    med = [s[0] for s in stats]
    ax.errorbar(xs, med, yerr=[[s[0]-s[1] for s in stats], [s[2]-s[0] for s in stats]], fmt='o-', capsize=5)
    ax.set(xlabel=label, ylabel='Wall-clock time (seconds)', xticks=xs, ylim=(0, max(s[2] for s in stats)*1.2))
    ax.grid(alpha=.2)
fig.suptitle('Inverted index: median and observed range of 3 runs')
fig.savefig(OUT / 'performance.png', dpi=180)
fig.savefig(OUT / 'performance.svg')
svg = OUT / 'performance.svg'
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
lines = ['# Assignment 2: Evaluating the inverted index', '',
'## Implementation and correctness', '',
'The mapper splits text at characters that are not Unicode letters. It emits case-sensitive word and filename pairs. The reducer removes duplicate filenames, sorts them, and returns `count filenames`. Filenames exclude directory paths to match the supplied expected output. The corpus test and the Go framework tests pass.', '',
'## Method', '',
f"Machine: AMD Ryzen 7 7735U (8 cores, 16 logical CPUs); {meta['platform']}; {meta['go']}. CPU affinity permits {meta['affinity_cpus']} logical CPUs. Runs used the existing framework unchanged, with three reduce partitions.", '',
'The script builds the executable before timing. Each trial starts a distributed master, waits for its socket, and launches separate worker processes. Timing starts at master launch and ends at master exit. It includes worker registration, scheduling, map and reduce tasks, worker shutdown RPCs, and the final merge. The script then terminates any idle workers. The framework uses Unix-domain RPC sockets. The README arguments such as `localhost:7777` name local socket files.', '',
'The datasets contain the first 1, 4, 8, or 16 files in alphabetical filename order. Each configuration has three trials. The script shuffles trial order with seed 452 and gives each trial a separate temporary directory. Both plots use the same measurements for four workers and 16 documents. All 21 distributed outputs match their sequential baselines by SHA-256 hash. Sequential runs check correctness only and do not contribute timings. The repository includes logs and raw timings. The script does not flush file-system caches, and other activity on the machine may affect the measurements.', '',
'## Results', '', '![Execution time versus workers and corpus size](performance.png)', '',
'Points show median times. Error bars show the minimum and maximum across three trials.', '',
'| Workers | Documents | Input MiB | Median seconds | Minimum to maximum seconds |', '|---:|---:|---:|---:|---:|']
for w, n in [(w,16) for w in [1,2,4,8]] + [(4,n) for n in [1,4,8]]:
    m, lo, hi = summarize(w,n)
    size = next(int(r['bytes']) for r in rows if int(r['documents']) == n)
    lines.append(f'| {w} | {n} | {size/2**20:.3f} | {m:.3f} | {lo:.3f} to {hi:.3f} |')
a = summarize(1,16)[0]
b = summarize(8,16)[0]
small = summarize(4,1)[0]
large = summarize(4,16)[0]
lines += ['', '## Interpretation', '',
f'Increasing workers from 1 to 8 changes median execution time from {a:.3f} to {b:.3f} seconds. The speedup is {a/b:.2f} times, so extra worker processes provide no improvement in these trials. The scheduler launches RPC goroutines for every unfinished task and assigns them round-robin. It checks completion once per second. Each worker can execute several task RPCs at once, so even one worker process can use multiple cores. Worker count therefore does not set the number of concurrent tasks.', '',
'The scheduler reads and writes completion flags without synchronization. It may also resubmit a task that has not finished after one second. Duplicate tasks can add work and write to the same intermediate files. Matching outputs do not prove that the scheduler has no races. These experiments leave the scheduler unchanged and remove duplicate filenames only in the reducer.', '',
f'With four workers, increasing the corpus from 1 to 16 documents changes median time from {small:.3f} to {large:.3f} seconds, a factor of {large/small:.2f}. Time grows less than file count over this range. The books differ in size, so the table also gives input bytes. Startup and one-second completion checks can obscure changes in processing time. These results do not establish how execution time scales for larger datasets.', '',
'There are only three reduce partitions, which limits useful parallelism during the reduce phase. Each map task processes a whole file, so large books can delay that phase. Serialization, shared storage, memory allocation, garbage collection, and the serial final merge can also limit speedup. These experiments use one machine and do not measure network costs between machines.', '',
'## Reproduce', '', 'From the assignment directory:', '', '```bash', 'export PATH=/usr/local/go/bin:$PATH  # if Go is not on PATH', 'cd starter', 'sh test/scripts/test-ii.sh', 'test ! -s diff.out  # the supplied shell script itself does not return failure on mismatch', 'go test ./... -timeout 180s', 'cd ..', 'python3 experiments/run.py', 'python3 experiments/analyze.py  # requires matplotlib', '```', '',
'The assignment asks for three performance experiments but lists two. This report covers both listed experiments.']
(OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n')
