"""Optional snapshot export. Dashboard also recalculates from current articles."""
from pathlib import Path
from datetime import date, timedelta
from src.core import PROVINCES, atomic_json, read_json, safe_csv
from src.victim_estimates import aggregate, build_estimates

def rebuild(data_dir):
    result = build_estimates(read_json(data_dir / 'articles.json', []))
    atomic_json(data_dir / 'victim_estimates.json', result)
    province, daily = aggregate(result['clusters'])
    (data_dir / 'victims_by_province.csv').write_bytes(safe_csv([{'province': p, 'estimated_victims': province.get(p, 0)} for p in PROVINCES], ['province', 'estimated_victims']))
    time_rows, running = [], 0
    if daily:
        current, end = date(2026, 1, 1), date.fromisoformat(max(r['published_date'] for r in result['audit']))
        while current <= end:
            value = daily.get(current.isoformat(), 0)
            running += value
            time_rows.append({'first_report_date': current.isoformat(), 'estimated_victims': value, 'cumulative_estimate': running})
            current += timedelta(days=1)
    (data_dir / 'victims_timeseries.csv').write_bytes(safe_csv(time_rows, ['first_report_date', 'estimated_victims', 'cumulative_estimate']))
    return result['summary']

if __name__ == '__main__':
    print(rebuild(Path(__file__).resolve().parents[1] / 'data'))
