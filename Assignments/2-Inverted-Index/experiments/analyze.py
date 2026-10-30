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
lines = ['# Assignment 2: Evaluating the inverted index', '',
'## Implementation and correctness', '',
'The mapper splits on non-Unicode-letter characters and emits case-sensitive word/filename pairs. The reducer removes duplicate filenames, sorts them, and returns `count filenames`. Part A corrected the reducer format and used basename filenames to match the supplied expected output. The supplied corpus test passes. The complete Go framework test suite also passes.', '',
'## Method', '',
f"Machine: AMD Ryzen 7 7735U (8 cores, 16 logical CPUs); {meta['platform']}; {meta['go']}. CPU affinity permits {meta['affinity_cpus']} logical CPUs. Runs used the existing framework unchanged, with three reduce partitions.", '',
'Built the executable once, excluding compilation from timing. Each trial starts a fresh master, waits for its socket, and launches independent worker processes. Timing spans master launch through master exit, including registration, scheduling, map/reduce work, shutdown RPCs, and final merge. Remaining idle worker processes are terminated outside timing. The framework uses Unix-domain RPC sockets, so the README’s `localhost:port` arguments are actually local socket filenames, not TCP connections.', '',
'Used alphabetically sorted filename prefixes of 1, 4, 8, and 16 files. Each configuration has three trials, shuffled with seed 452. The (4 workers, 16 documents) measurements are shared by both plots. Each trial has an isolated temporary working directory. All 21 distributed output SHA-256 hashes match the corresponding sequential baseline. Logs and raw timings are retained. File-system caches were not flushed; these are local warm-cache measurements on a shared, active machine, not isolated cluster benchmarks.', '',
'## Results', '', '![Execution time versus workers and corpus size](performance.png)', '',
'Error bars show the observed minimum and maximum; points show medians. Three repetitions describe variability but do not establish statistical significance.', '',
'| Workers | Documents | Input MiB | Median seconds | Min–max seconds |', '|---:|---:|---:|---:|---:|']
for w, n in [(w,16) for w in [1,2,4,8]] + [(4,n) for n in [1,4,8]]:
    m, lo, hi = summarize(w,n)
    size = next(int(r['bytes']) for r in rows if int(r['documents']) == n)
    lines.append(f'| {w} | {n} | {size/2**20:.3f} | {m:.3f} | {lo:.3f}–{hi:.3f} |')
a = summarize(1,16)[0]
b = summarize(8,16)[0]
small = summarize(4,1)[0]
large = summarize(4,16)[0]
lines += ['', '## Interpretation', '',
f'Increasing workers from 1 to 8 changes median execution time from {a:.3f} to {b:.3f} seconds ({a/b:.2f}× speedup). This measures the supplied scheduler, whose behavior limits what can be concluded about worker scalability. It launches RPC goroutines for every unfinished task, distributes them round-robin, and checks completion only once per second. A single worker can therefore execute multiple task RPCs concurrently and already use several cores. Workers are not restricted to one in-flight task. Increasing process count does not correspond to increasing available task concurrency from one to eight.', '',
'The scheduler also reads/writes its completion flags without synchronization and may resubmit an in-flight task after one second. These are framework limitations; successful hash comparisons in these runs do not prove the scheduler is race-free. Repeated execution can add overhead or contend on intermediate files. No scheduler changes or map-side deduplication optimizations were applied, to preserve the implementation being evaluated.', '',
f'With four workers, increasing the corpus from 1 to 16 documents changes median time from {small:.3f} to {large:.3f} seconds ({large/small:.2f}×). Compare input bytes as well as file count: the books have unequal sizes. Over this range the fixed startup and one-second polling costs prevent interpreting the results as a clean asymptotic scaling law. The observed time increase is sub-linear relative to file count; this does not demonstrate inherently sub-linear computational complexity.', '',
'Only three reducers can run distinct reduce partitions, regardless of additional workers. Map tasks are whole files with unequal sizes; the largest file can dominate a phase. Serialization, shared local storage, memory allocation/garbage collection, and the serial final merge also constrain speedup. These local results do not measure network overhead or multi-machine scalability.', '',
'## Reproduce', '', 'From the assignment directory:', '', '```bash', 'export PATH=/usr/local/go/bin:$PATH  # if Go is not on PATH', 'cd starter', 'sh test/scripts/test-ii.sh', 'test ! -s diff.out  # the supplied shell script itself does not return failure on mismatch', 'go test ./... -timeout 180s', 'cd ..', 'python3 experiments/run.py', 'python3 experiments/analyze.py  # requires matplotlib', '```', '',
'The assignment says “three performance experiments” but enumerates only two. Both listed experiments are covered here.']
(OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n')
