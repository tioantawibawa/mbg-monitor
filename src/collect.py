"""Fetch public RSS metadata only; no article-body or paywall scraping."""
import argparse
from collections import deque
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from src.core import PROVINCES, article_id, atomic_json, province_hint, read_json, relevant

ROOT = Path(__file__).resolve().parents[1]
WIB = ZoneInfo('Asia/Jakarta')

def fetch(url):
    for attempt in range(3):
        try:
            request = Request(url, headers={'User-Agent': 'MBGNewsMonitor/1.0 (RSS metadata research)'})
            with urlopen(request, timeout=25) as response:
                data = response.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError('Feed exceeds size limit')
            return data
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def parse_feed(payload, start, end, now):
    root = ET.fromstring(payload)
    if root.tag != 'rss' or root.find('channel') is None:
        raise ValueError('Response is not an RSS feed')
    rows = []
    items = root.findall('./channel/item')
    for item in items:
        title = item.findtext('title', '').strip()
        source = item.findtext('source', '').strip()
        url = item.findtext('link', '').strip()
        try:
            published = parsedate_to_datetime(item.findtext('pubDate', '')).astimezone(WIB)
        except (TypeError, ValueError, OverflowError):
            continue
        if not relevant(title) or not start <= published.date() < end or not url.startswith('https://'):
            continue
        rows.append({'id': article_id(title, source), 'title': title, 'source': source,
                     'url': url, 'published_at': published.isoformat(),
                     'province_hint': province_hint(title), 'first_seen': now,
                     'last_seen': now, 'review_status': 'Belum ditinjau'})
    return rows, len(items)

def windows(start, end, days=7):
    while start < end:
        stop = min(start + timedelta(days=days), end)
        yield start, stop
        start = stop

def collect(start, end, regional=False, data_dir=ROOT / 'data'):
    now = datetime.now(WIB).isoformat()
    old = read_json(data_dir / 'articles.json', [])
    records = {row['id']: row for row in old}
    report = {'started_at': now, 'requested_start': str(start), 'requested_end_exclusive': str(end),
              'queries': [], 'added': 0, 'status': 'running'}
    areas = [''] + PROVINCES if regional else ['']
    pending = deque((left, right, area) for left, right in windows(start, end) for area in areas)
    while pending:
        left, right, area = pending.popleft()
        query = f'(MBG OR "makan bergizi gratis") keracunan {area} after:{left - timedelta(days=1)} before:{right}'
        url = 'https://news.google.com/rss/search?' + urlencode({'q': query, 'hl': 'id', 'gl': 'ID', 'ceid': 'ID:id'})
        entry = {'start': str(left), 'end': str(right), 'area': area or 'Nasional', 'url': url}
        try:
            rows, count = parse_feed(fetch(url), left, right, now)
            entry.update(status='ok', feed_items=count, accepted=len(rows), possibly_capped=count >= 100)
            if count >= 100 and (right - left).days > 1:
                midpoint = left + timedelta(days=(right - left).days // 2)
                pending.extend([(left, midpoint, area), (midpoint, right, area)])
                entry['subdivided'] = True
            for row in rows:
                if row['id'] in records:
                    records[row['id']]['last_seen'] = now
                else:
                    records[row['id']] = row
                    report['added'] += 1
        except Exception as exc:
            entry.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        report['queries'].append(entry)
        print(f"{left} {area or 'Nasional'}: {entry['status']}", flush=True)
        time.sleep(0.5)
    failures = sum(q['status'] == 'failed' for q in report['queries'])
    report.update(finished_at=datetime.now(WIB).isoformat(), total_articles=len(records),
                  failed_queries=failures, status='failed' if failures == len(report['queries']) else 'partial' if failures else 'ok')
    atomic_json(data_dir / 'articles.json', sorted(records.values(), key=lambda row: row['published_at'], reverse=True))
    previous = read_json(data_dir / 'health.json', {})
    report['last_success_at'] = report['finished_at'] if not failures else previous.get('last_success_at')
    atomic_json(data_dir / 'health.json', report)
    history = read_json(data_dir / 'runs.json', [])
    atomic_json(data_dir / 'runs.json', (history + [report])[-90:])
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=date.fromisoformat)
    parser.add_argument('--end', type=date.fromisoformat, help='Inclusive final date, WIB')
    parser.add_argument('--regional', action='store_true', help='Add searches for all 38 provinces')
    parser.add_argument('--backfill', action='store_true', help='Start at January 1, 2026')
    args = parser.parse_args()
    today = datetime.now(WIB).date()
    start = args.start or (date(2026, 1, 1) if args.backfill else max(date(2026, 1, 1), today - timedelta(days=7)))
    end = args.end or today
    if not date(2026, 1, 1) <= start <= end <= today:
        parser.error('Use a date range within January 1, 2026 and today')
    result = collect(start, end + timedelta(days=1), args.regional)
    raise SystemExit(0 if result['status'] == 'ok' else 1)

if __name__ == '__main__':
    main()
