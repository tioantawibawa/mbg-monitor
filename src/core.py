import csv
import hashlib
import io
import json
import re
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROVINCES = [
    'Aceh', 'Sumatera Utara', 'Sumatera Barat', 'Riau', 'Kepulauan Riau',
    'Jambi', 'Sumatera Selatan', 'Bengkulu', 'Lampung', 'Kepulauan Bangka Belitung',
    'DKI Jakarta', 'Banten', 'Jawa Barat', 'Jawa Tengah', 'DI Yogyakarta', 'Jawa Timur',
    'Bali', 'Nusa Tenggara Barat', 'Nusa Tenggara Timur', 'Kalimantan Barat',
    'Kalimantan Tengah', 'Kalimantan Selatan', 'Kalimantan Timur', 'Kalimantan Utara',
    'Sulawesi Utara', 'Gorontalo', 'Sulawesi Tengah', 'Sulawesi Barat',
    'Sulawesi Selatan', 'Sulawesi Tenggara', 'Maluku Utara', 'Maluku',
    'Papua Barat Daya', 'Papua Barat', 'Papua Tengah', 'Papua Pegunungan',
    'Papua Selatan', 'Papua',
]
INCIDENT_FIELDS = ['incident_id', 'event_date', 'province', 'district', 'location',
                   'status', 'affected', 'source_urls', 'evidence', 'reviewer', 'reviewed_at']

def relevant(title):
    text = title.lower()
    return bool(re.search(r'\bmbg\b|makan(?:an)? bergizi gratis', text)) and 'keracunan' in text

def article_id(title, source):
    normalized = re.sub(r'\W+', ' ', title.lower()).strip()
    return hashlib.sha256(f'{source.lower()}|{normalized}'.encode()).hexdigest()[:24]

def province_hint(title):
    # Longest names first prevents Papua Barat Daya being classified as Papua.
    for province in sorted(PROVINCES, key=len, reverse=True):
        if re.search(r'\b' + re.escape(province.lower()) + r'\b', title.lower()):
            return province
    return 'Belum diketahui'

def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)

def validate_incidents(rows, today=None):
    today = today or datetime.now(ZoneInfo('Asia/Jakarta')).date()
    ids = set()
    for row in rows:
        if not row['incident_id'] or row['incident_id'] in ids:
            raise ValueError('incident_id kosong atau duplikat')
        ids.add(row['incident_id'])
        if not date(2026, 1, 1) <= date.fromisoformat(row['event_date']) <= today:
            raise ValueError('Tanggal kejadian di luar periode 2026–hari ini')
        if row['province'] not in PROVINCES:
            raise ValueError('Provinsi tidak dikenal')
        if row['status'] not in ('Dugaan', 'Terkonfirmasi', 'Dibantah'):
            raise ValueError('Status tidak valid')
        if row['affected'] and (not row['affected'].isdigit()):
            raise ValueError('affected harus bilangan bulat nonnegatif atau kosong')
        if not all(row[k].strip() for k in ('district', 'evidence', 'reviewer', 'reviewed_at')):
            raise ValueError('Bukti, wilayah, reviewer, dan tanggal tinjau wajib diisi')
        date.fromisoformat(row['reviewed_at'])
        if not all(re.match(r'^https?://[^\s]+$', u) for u in row['source_urls'].split('|')):
            raise ValueError('URL sumber tidak valid')
    return rows

def load_incidents(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return validate_incidents(list(csv.DictReader(handle)))

def safe_csv(rows, fields):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: "'" + str(v) if str(v).startswith(('=', '+', '-', '@')) else v
                         for k, v in row.items() if k in fields})
    return output.getvalue().encode('utf-8-sig')
