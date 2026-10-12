import json
import re
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ASSIGNMENT_DIR = Path(__file__).resolve().parents[2]

NS_PER_MS = 1e6
LATENCY_KEYS = {
    'mean': 'mean',
    '50th': 'p50',
    '90th': 'p90',
    '95th': 'p95',
    '99th': 'p99',
    'max': 'max',
}

IPERF_RE = re.compile(r'iperf_client_report_(\d+)M_run_(\d+)\.json$')
SINGLE_RE = re.compile(r'vegeta_attack_report_(\d+)_run_(\d+)\.json$')
MULTI_RE = re.compile(
    r'vegeta_multi_node_attack_(\w+?)_report_(\d+)_run_(\d+)\.json$'
)
LOG_SESSION_RE = re.compile(r'^Results: .*/(final_\d{8}_\d{6})$', re.M)
LOG_RUN_RE = re.compile(r'^Run: (\d+)$', re.M)
LOG_FIELD_RE = re.compile(
    r'^(Requests|Duration|Latencies|Bytes In|Success|Status Codes)\s+\[[^\]]*\]\s+(.*?)\s*$',
    re.M,
)
GO_DURATION_RE = re.compile(r'([\d.]+)(h|ms|m|s|µs|us|ns)')
GO_UNIT_MS = {
    'h': 3.6e6,
    'm': 6e4,
    's': 1e3,
    'ms': 1.0,
    'µs': 1e-3,
    'us': 1e-3,
    'ns': 1e-6,
}
PIDSTAT_HEADER_RE = re.compile(r'\s(\d{2}/\d{2}/\d{4})\s')
PIDSTAT_ROW_RE = re.compile(
    r'^(\d{2}:\d{2}:\d{2} [AP]M)\s+\d+\s+\d+\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s+([\d.]+)\s+\d+\s+nginx'
)


def load_iperf(root: Path = ASSIGNMENT_DIR) -> pd.DataFrame:
    rows = []
    for path in sorted(Path(root, 'iperf_client').glob('iperf_*/*.json')):
        match = IPERF_RE.search(path.name)
        if not match:
            continue
        report = json.loads(path.read_text())
        if 'error' in report:
            raise ValueError(f'{path}: iperf3 error: {report["error"]}')
        total = report['end']['sum']
        cpu = report['end']['cpu_utilization_percent']
        sent_mbps = total['bits_per_second'] / 1e6
        rows.append(
            {
                'target_mbps': int(match[1]),
                'run': int(match[2]),
                'sent_mbps': sent_mbps,
                'goodput_mbps': sent_mbps * (1 - total['lost_percent'] / 100),
                'lost_percent': total['lost_percent'],
                'lost_packets': total['lost_packets'],
                'packets': total['packets'],
                'jitter_ms': total['jitter_ms'],
                'client_cpu': cpu['host_total'],
                'server_cpu': cpu['remote_total'],
            }
        )
    return pd.DataFrame(rows).sort_values(
        ['target_mbps', 'run'], ignore_index=True
    )


def parse_vegeta(path: Path) -> dict:
    report = json.loads(Path(path).read_text())
    codes = report.get('status_codes') or {}
    row = {
        'requests': report['requests'],
        'achieved_rate': report['rate'],
        'throughput': report['throughput'],
        'success': report['success'],
        'ok': codes.get('200', 0),
        'failed': report['requests'] - codes.get('200', 0),
        'bytes_in': report['bytes_in']['total'],
        'duration_s': report['duration'] / 1e9,
        'start': pd.Timestamp(report['earliest']),
        'end': pd.Timestamp(report['latest']),
        'error_kinds': _error_kinds(report.get('errors') or []),
    }
    for key, name in LATENCY_KEYS.items():
        row[f'lat_{name}_ms'] = report['latencies'][key] / NS_PER_MS
    return row


def _error_kinds(errors: list[str]) -> list[str]:
    kinds = set()
    for error in errors:
        kind = error.split(': ')[-1]
        kinds.add(re.sub(r'\d+\.\d+\.\d+\.\d+:\d+', '<addr>', kind))
    return sorted(kinds)


def parse_pidstat(path: Path) -> pd.DataFrame:
    lines = Path(path).read_text().splitlines()
    header = PIDSTAT_HEADER_RE.search(lines[0]) if lines else None
    if header is None:
        raise ValueError(f'{path}: not a pidstat file')
    day = datetime.strptime(header[1], '%m/%d/%Y').replace(tzinfo=timezone.utc)

    samples, previous = [], None
    for line in lines[1:]:
        match = PIDSTAT_ROW_RE.match(line)
        if not match:
            continue
        clock = datetime.strptime(match[1], '%I:%M:%S %p').time()
        stamp = datetime.combine(day.date(), clock, tzinfo=timezone.utc)
        if previous is not None and stamp < previous:
            day += timedelta(days=1)
            stamp += timedelta(days=1)
        previous = stamp
        samples.append(
            {
                'time': pd.Timestamp(stamp),
                'usr': float(match[2]),
                'sys': float(match[3]),
                'cpu': float(match[4]),
            }
        )
    return pd.DataFrame(samples)


def cpu_during(
    samples: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.Series:
    window = samples[
        (samples['time'] >= start.floor('s'))
        & (samples['time'] <= end.ceil('s'))
    ]
    return window[['usr', 'sys', 'cpu']].mean()


def load_single_node(root: Path = ASSIGNMENT_DIR) -> pd.DataFrame:
    rows = []
    for session, path in _latest_per_rate(
        Path(root, 'vegeta-results').glob('final_*/*.json'), SINGLE_RE, 1
    ):
        match = SINGLE_RE.search(path.name)
        row = {
            'session': session,
            'rate': int(match[1]),
            'run': int(match[2]),
            **parse_vegeta(path),
        }
        cpu = cpu_during(
            parse_pidstat(path.with_name(path.stem + '_cpu.txt')),
            row['start'],
            row['end'],
        )
        row.update(
            {
                'server_cpu': cpu['cpu'],
                'server_usr': cpu['usr'],
                'server_sys': cpu['sys'],
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(['rate', 'run'], ignore_index=True)


def load_multi_node(root: Path = ASSIGNMENT_DIR) -> pd.DataFrame:
    rows = []
    paths = Path(root).glob('vegeta-results-multi-node_*/final_*/*.json')
    for session, path in _latest_per_rate(paths, MULTI_RE, 2):
        match = MULTI_RE.search(path.name)
        row = {
            'session': session,
            'source': 'json',
            'attacker': match[1],
            'rate': int(match[2]),
            'run': int(match[3]),
            **parse_vegeta(path),
        }
        for server in ('node0', 'node2'):
            cpu_file = path.with_name(f'{path.stem}_{server}_cpu.txt')
            row[f'{server}_cpu'] = cpu_during(
                parse_pidstat(cpu_file), row['start'], row['end']
            )['cpu']
        rows.append(row)

    with_json = {row['attacker'] for row in rows}
    log_rows = [
        row
        for log in sorted(Path(root, 'logs').glob('multi_*/*.log'))
        if log.stem not in with_json
        for row in parse_vegeta_log(log)
    ]
    rows += _keep_latest_session(log_rows)
    return pd.DataFrame(rows).sort_values(
        ['rate', 'attacker', 'run'], ignore_index=True
    )


def parse_vegeta_log(path: Path) -> list[dict]:
    text = Path(path).read_text()
    session = LOG_SESSION_RE.search(text)
    if session is None:
        return []
    rows = []
    for block in text.split('Aggregate target: ')[1:]:
        if '\nCompleted ' not in block:
            continue
        rows.append(
            {
                'session': session[1],
                'source': 'log',
                'attacker': Path(path).stem,
                'rate': int(block.split(' ', 1)[0]),
                'run': int(LOG_RUN_RE.search(block)[1]),
                **_parse_text_report(block),
                'node0_cpu': np.nan,
                'node2_cpu': np.nan,
            }
        )
    return rows


def _parse_text_report(block: str) -> dict:
    fields = dict(LOG_FIELD_RE.findall(block))
    requests, rate, throughput = fields['Requests'].split(', ')
    latencies = [_go_duration_ms(v) for v in fields['Latencies'].split(', ')]
    codes = dict(
        code.split(':') for code in fields.get('Status Codes', '').split()
    )
    ok = int(codes.get('200', 0))
    errors = (
        block.split('Error Set:\n', 1)[1]
        .split('\nCompleted ', 1)[0]
        .splitlines()
    )
    row = {
        'requests': int(requests),
        'achieved_rate': float(rate),
        'throughput': float(throughput),
        'success': float(fields['Success'].rstrip('%')) / 100,
        'ok': ok,
        'failed': int(requests) - ok,
        'bytes_in': int(fields['Bytes In'].split(', ')[0]),
        'duration_s': _go_duration_ms(fields['Duration'].split(', ')[0]) / 1e3,
        'start': pd.NaT,
        'end': pd.NaT,
        'error_kinds': _error_kinds(errors),
    }
    names = ['min', 'mean', 'p50', 'p90', 'p95', 'p99', 'max']
    row.update(
        {
            f'lat_{name}_ms': value
            for name, value in zip(names, latencies)
            if name != 'min'
        }
    )
    return row


def _go_duration_ms(text: str) -> float:
    parts = GO_DURATION_RE.findall(text)
    if not parts:
        raise ValueError(f'not a Go duration: {text!r}')
    return sum(float(value) * GO_UNIT_MS[unit] for value, unit in parts)


def _keep_latest_session(rows: list[dict]) -> list[dict]:
    latest = {}
    for row in rows:
        key = (row['attacker'], row['rate'])
        latest[key] = max(latest.get(key, ''), row['session'])
    return [
        row
        for row in rows
        if row['session'] == latest[(row['attacker'], row['rate'])]
    ]


def _latest_per_rate(
    paths: Iterable[Path], pattern: re.Pattern, rate_group: int
) -> Iterator[tuple[str, Path]]:
    by_key = {}
    for path in paths:
        match = pattern.search(path.name)
        if not match:
            continue
        key = (path.parent.parent.name, match[rate_group])
        by_key.setdefault(key, {}).setdefault(path.parent.name, []).append(path)
    for sessions in by_key.values():
        session = max(sessions)
        for path in sorted(sessions[session]):
            yield session, path
