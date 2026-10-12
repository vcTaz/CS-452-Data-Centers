from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy import stats

CONFIDENCE = 0.95
ATTACKERS = 2


def ci95(values: Sequence[float]) -> float:
    x = np.asarray(values, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return np.nan
    return stats.sem(x) * stats.t.ppf((1 + CONFIDENCE) / 2, len(x) - 1)


def summarize(
    df: pd.DataFrame, by: str | list[str], cols: list[str]
) -> pd.DataFrame:
    grouped = df.groupby(by)[cols].agg(['mean', 'std', ci95, 'count'])
    grouped.columns = [
        f'{col}_{stat}'.replace('_count', '_n') for col, stat in grouped.columns
    ]
    return grouped.reset_index()


def combine_attackers(multi: pd.DataFrame) -> pd.DataFrame:
    weighted = multi.assign(_lat_sum=multi['lat_mean_ms'] * multi['requests'])
    out = weighted.groupby(['rate', 'run']).agg(
        n_attackers=('attacker', 'nunique'),
        requests=('requests', 'sum'),
        ok=('ok', 'sum'),
        achieved_rate=('achieved_rate', 'sum'),
        throughput=('throughput', 'sum'),
        _lat_sum=('_lat_sum', 'sum'),
        lat_p99_ms=('lat_p99_ms', 'max'),
        lat_max_ms=('lat_max_ms', 'max'),
        node0_cpu=('node0_cpu', 'mean'),
        node2_cpu=('node2_cpu', 'mean'),
    )
    out = out.assign(
        offered=out.index.get_level_values('rate')
        * out['n_attackers']
        / ATTACKERS,
        success=out['ok'] / out['requests'],
        lat_mean_ms=out['_lat_sum'] / out['requests'],
    )
    return out.drop(columns='_lat_sum').reset_index()


def saturation_rate(
    summary: pd.DataFrame,
    throughput_col: str = 'throughput_mean',
    offered_col: str = 'rate',
    tolerance: float = 0.95,
) -> int | None:
    return _last_passing(
        summary, summary[throughput_col] >= tolerance * summary[offered_col]
    )


def slo_capacity(
    summary: pd.DataFrame, latency_col: str, slo_ms: float
) -> int | None:
    return _last_passing(summary, summary[latency_col] <= slo_ms)


def _last_passing(summary: pd.DataFrame, passing: pd.Series) -> int | None:
    ordered = summary.assign(_ok=passing).sort_values('rate')
    failed = ~ordered['_ok'].to_numpy(dtype=bool)
    if not failed.any():
        return None
    cut = int(failed.argmax())
    return int(ordered['rate'].iloc[cut - 1]) if cut else 0
