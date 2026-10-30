"""Run from any directory: PATH=/usr/local/go/bin:$PATH python3 experiments/run.py."""
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments'
DATA = sorted((ROOT / 'starter/test/data').glob('pg-*.txt'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    metadata = dict(platform=platform.platform(), cpu=platform.processor(),
                    logical_cpus=os.cpu_count(), affinity_cpus=len(os.sched_getaffinity(0)),
                    go=subprocess.check_output(['go', 'version'], text=True).strip(),
                    files=[dict(name=p.name, bytes=p.stat().st_size) for p in DATA],
                    repetitions=3, seed=452, reducers=3)
    (OUT / 'environment.json').write_text(json.dumps(metadata, indent=2) + '\n')
    with tempfile.TemporaryDirectory(prefix='ii-exp-') as tmp:
        tmp = Path(tmp)
        binary = tmp / 'ii'
        subprocess.run(['go', 'build', '-o', str(binary), './cmd/invertedindex'],
                       cwd=ROOT / 'starter', check=True)
        expected = {}
        for n in (1, 4, 8, 16):
            d = tmp / f'seq{n}'
            d.mkdir()
            subprocess.run([str(binary), 'master', 'sequential', *map(str, DATA[:n])],
                           cwd=d, stdout=subprocess.DEVNULL, check=True, timeout=120)
            expected[n] = digest(d / 'mrtmp.iiseq')
        configs = [(w, 16) for w in (1, 2, 4, 8)] + [(4, n) for n in (1, 4, 8)]
        runs = [(w, n, r) for r in range(1, 4) for w, n in configs]
        random.Random(452).shuffle(runs)
        with (OUT / 'results.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=['workers', 'documents', 'bytes', 'repetition',
                                                  'seconds', 'correct', 'sha256'])
            writer.writeheader()
            for index, (w, n, r) in enumerate(runs):
                d = tmp / f'run{index}'
                d.mkdir()
                master_socket = str(d / 'master.sock')
                processes = []
                with (OUT / f'run-{index:02d}.log').open('w') as log:
                    start = time.perf_counter()
                    try:
                        master = subprocess.Popen([str(binary), 'master', master_socket,
                                                   *map(str, DATA[:n])], cwd=d, stdout=log, stderr=log)
                        processes.append(master)
                        deadline = time.monotonic() + 10
                        while not Path(master_socket).exists():
                            if master.poll() is not None or time.monotonic() > deadline:
                                raise RuntimeError('Master failed to start')
                            time.sleep(.005)
                        for k in range(w):
                            processes.append(subprocess.Popen([str(binary), 'worker', master_socket,
                                             str(d / f'w{k}.sock')], cwd=d, stdout=log, stderr=log))
                        if master.wait(timeout=120):
                            raise RuntimeError('Master failed')
                        elapsed = time.perf_counter() - start
                        actual = digest(d / 'mrtmp.iiseq')
                        row = dict(workers=w, documents=n, bytes=sum(p.stat().st_size for p in DATA[:n]),
                                   repetition=r, seconds=elapsed, correct=actual == expected[n], sha256=actual)
                        writer.writerow(row)
                        f.flush()
                        print(row, flush=True)
                        if not row['correct']:
                            raise RuntimeError('Distributed output differs from sequential baseline')
                    finally:
                        for proc in processes:
                            if proc.poll() is None:
                                proc.terminate()
                        for proc in processes:
                            proc.wait(timeout=10)
                shutil.rmtree(d)


if __name__ == '__main__':
    main()
