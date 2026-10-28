"""Auditable title-derived victim estimates; never modifies reviewed incidents."""
import hashlib
import re
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from src.geography import LOCALITIES, hit, locate
from src.text_analysis import clean_title

VERSION = 'title-victims-v1'
NUMBER = r'(?<![\w.])\d+(?:[.,]\d+)*(?:\s+ribu)?'
PERSON = r'(?:orang|siswa|siswi|murid|pelajar|santri|anak|warga|korban|guru|balita|pasien|penerima)\b'
PERSON_RE = re.compile(rf'(?P<number>{NUMBER})\s+(?:(?:orang|lebih)\s+)?(?P<unit>{PERSON})', re.I)
DIRECT_RE = re.compile(rf'(?P<number>{NUMBER})\s+(?P<unit>keracunan)\b', re.I)
TOTAL_RE = re.compile(rf'\bkorban\b[^,:;!?]{{0,65}}?\b(?:jadi|menjadi|capai|mencapai|tembus|sebanyak|berjumlah|langsung)\s+(?P<number>{NUMBER})(?!\s*(?:ribu|juta|kasus|sekolah|sppg|dapur|persen|%))\b', re.I)
SUBSET = r'\b(?:masih\s+(?:dirawat|diobservasi)|sudah\s+(?:pulang|dipulangkan|sembuh)|dipulangkan|pulih|sembuh|meninggal|rawat\s+inap|picu|kembali\s+dirawat|jalani\s+perawatan)\b'
AGGREGATE = r'\b(?:sepanjang|kumulatif|akumulasi|sejak\s+(?:januari|awal|2025|2026|program)|selama\s+\d+\s+(?:bulan|tahun)|nasional|seluruh\s+indonesia|se\s*indonesia|(?:\d+|satu|dua|tiga|empat|lima|enam|tujuh|delapan|sembilan|sepuluh)\s+(?:pekan|minggu|bulan|tahun))\b'
DISPUTE = r'\b(?:bantah|dibantah|membantah|klarifikasi|luruskan|hoaks|hoax|cek\s+fakta|bukan|tidak\s+(?:ada|benar)|nihil|yang\s+benar)\b'
FOLLOWUP = r'\b(?:hasil\s+(?:uji|sampel|lab|laboratorium)|ada\s+bakteri|positif\s+mengandung|penyebab|pemicu|terungkap|menanti|biaya\s+perawatan|sudah\s+ditangani|sudah\s+pulang)\b'

def number_value(raw):
    raw = raw.lower().strip()
    if raw.endswith('ribu'):
        value = float(raw[:-4].strip().replace('.', '').replace(',', '.')) * 1000
        return int(value) if value.is_integer() else None
    if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', raw):
        return int(re.sub(r'[.,]', '', raw))
    return int(raw) if raw.isdigit() else None

def extract_counts(title):
    """Only explicit numeric people counts, not dates/school numbers/case counts."""
    candidates, positions = [], set()
    for pattern in (PERSON_RE, DIRECT_RE, TOTAL_RE):
        for match in pattern.finditer(title):
            start, end = match.span('number')
            if start in positions:
                continue
            positions.add(start)
            raw = match.group('number')
            value = number_value(raw)
            if value is None:
                continue
            before = title[max(0, start - 35):start].lower()
            # Inspect only this count's clause, not another count after punctuation.
            after = re.split(r'[,;:!?]', title[end:end + 80].lower())[0]
            next_count = re.search(r'\b\d+\s+(?:orang|siswa|guru|pasien)', after)
            if next_count:
                after = after[:next_count.start()]
            explicit_total = bool(re.search(r'(?:total|tembus|capai|mencapai|bertambah\s+jadi|berjumlah)\s*$', before))
            approximation = bool(re.search(r'(?:hampir|nyaris|sekitar|lebih\s+dari|kurang\s+dari|sedikitnya|minimal|setidaknya)\s*$', before)) or raw.endswith('ribu')
            subset = bool(re.search(SUBSET + r'|\b(?:dirujuk|diobservasi)\b', after)) and not explicit_total
            # Counts attached to a stoppage/reach of meals are beneficiaries, not ill people.
            beneficiaries = bool((re.search(r'\bmbg\s*$', before) and re.search(r'\b(?:disetop|dihentikan|diberikan|dibagikan)\b', after))
                                 or re.search(r'\b(?:layani|melayani|jangkau|menjangkau)\s*$', before)
                                 or re.search(r'\bpenerima\s+manfaat\s+(?:dialihkan|dilayani)\b', after))
            status = 'perkiraan/batas' if approximation else 'subkelompok' if subset else 'penerima layanan' if beneficiaries else 'total kandidat'
            candidates.append({'value': value, 'text': match.group(0), 'kind': status, 'start': start,
                               'end': match.end(), 'unit': match.groupdict().get('unit', '')})
    return sorted(candidates, key=lambda x: x['start'])

def parse_article(row):
    title = clean_title(row)
    counts = extract_counts(title)
    total_candidates = [c for c in counts if c['kind'] == 'total kandidat']
    values = {c['value'] for c in total_candidates}
    count = next(iter(values)) if len(values) == 1 else None
    reason = ''
    # Explicit disjoint additive construction only, e.g. 75 siswa dan 5 guru.
    if len(total_candidates) == 2:
        a, b = total_candidates
        if re.fullmatch(r'\s*(?:dan|serta)\s*', title[a['end']:b['start']], re.I) and a['unit'].lower() != b['unit'].lower():
            count = a['value'] + b['value']
    disputed = bool(re.search(DISPUTE, title, re.I))
    death_dispute = bool(re.search(r'(?:bantah|hoaks|hoax|cek\s+fakta).{0,100}\b(?:meninggal|tewas)\b', title, re.I))
    if re.search(r'\b202[0-5]\b', title):
        reason = 'Menyebut tahun sebelum 2026; tinjau periode kejadian'
    elif re.search(AGGREGATE, title, re.I):
        reason = 'Rekap lintas periode/nasional; tidak ditambahkan ke insiden'
    elif disputed:
        reason = 'Bantahan/koreksi; perlu tinjauan'
    elif not counts:
        reason = 'Tidak ada angka orang eksplisit yang dapat diekstrak'
    elif not total_candidates:
        reason = 'Hanya subkelompok, angka perkiraan, atau penerima layanan'
    elif count is None:
        reason = 'Beberapa angka total tidak dapat dipisahkan otomatis'
    province, district, locality, location_reason = locate(title)
    stamp = datetime.fromisoformat(row['published_at']).astimezone(ZoneInfo('Asia/Jakarta'))
    return {'article_id': row['id'], 'title': title, 'source': row['source'], 'url': row['url'],
            'published_at': stamp.isoformat(), 'published_date': stamp.date().isoformat(),
            'province': province, 'district': district, 'locality': locality,
            'location_reason': location_reason, 'extracted_counts': counts,
            'candidate_count': count, 'exclusion_reason': reason, 'disputed': disputed,
            'disputed_total': disputed and not death_dispute,
            'cluster_id': '', 'decision': 'Di luar subtotal', 'dedupe_reason': ''}

def days(a, b):
    return abs((datetime.fromisoformat(a) - datetime.fromisoformat(b)).total_seconds()) / 86400

def build_estimates(articles, window_days=14):
    if not 1 <= window_days <= 30:
        raise ValueError('Grouping window must be 1–30 days')
    audit = sorted((parse_article(r) for r in articles), key=lambda r: (r['published_at'], r['article_id']))
    # Resolve locality-only reports only from dated, explicit co-mentions in this archive.
    for row in audit:
        if row['district'] or row['province'] or not row['location_reason'].startswith('Kabupaten'):
            continue
        possible = []
        for district, aliases in LOCALITIES.items():
            for alias in aliases:
                if hit(row['title'], alias):
                    evidence = [r for r in audit if r['district'] == district and alias in r['locality'].split('|') and days(row['published_at'], r['published_at']) <= window_days]
                    if evidence:
                        possible.append((evidence[0]['province'], district, alias))
        if len(set(possible)) == 1:
            row['province'], row['district'], row['locality'] = possible[0]
            row['location_reason'] = 'Inferensi alias dari judul lain dalam jendela waktu'
    usable = [r for r in audit if r['district'] and (not r['exclusion_reason'] or r['disputed'] or not r['extracted_counts'])
              and not re.search(AGGREGATE, r['title'], re.I) and not re.search(r'\b202[0-5]\b', r['title'])]
    clusters = []
    # Locality-specific clusters first; generic district reports cannot bridge two localities.
    # Followups processed last so late lab reports cannot start new victim groups.
    for row in sorted(usable, key=lambda r: (bool(re.search(FOLLOWUP, r['title'], re.I)), not bool(r['locality']), r['published_at'], r['article_id'])):
        followup = bool(re.search(FOLLOWUP, row['title'], re.I))
        compatible = [c for c in clusters if c['district'] == row['district'] and c['province'] == row['province']
                      and days(row['published_at'], c['anchor']) <= (60 if followup else window_days)
                      and (not row['locality'] or not c['locality'] or row['locality'] == c['locality'])]
        if followup:
            compatible = [c for c in compatible if c['anchor'] <= row['published_at']]
        if len(compatible) > 1:
            row['dedupe_reason'] = 'Ambigu: beberapa kelompok lokasi/waktu cocok'
            continue
        if compatible:
            cluster = compatible[0]
        else:
            if followup:
                row['dedupe_reason'] = 'Berita lanjutan tanpa kelompok asal yang pasti'
                continue
            cluster = {'province': row['province'], 'district': row['district'], 'locality': row['locality'],
                       'anchor': row['published_at'], 'rows': []}
            clusters.append(cluster)
        # No rolling chain: every member must fit within one fixed-width interval.
        dates = [r['published_at'] for r in cluster['rows']] + [row['published_at']]
        if not followup and days(min(dates), max(dates)) > window_days:
            row['dedupe_reason'] = 'Di luar jendela kelompok; perlu tinjauan lanjutan'
            continue
        cluster['rows'].append(row)
        if followup:
            row['dedupe_reason'] = 'Berita lanjutan: satu kelompok asal cocok dalam 60 hari'
    result = []
    for cluster in clusters:
        members = sorted(cluster['rows'], key=lambda r: (r['published_at'], r['article_id']))
        candidates = [r for r in members if not r['exclusion_reason'] and r['candidate_count'] is not None]
        if not candidates:
            continue
        first = members[0]
        cluster_id = 'EST-' + hashlib.sha256('|'.join([cluster['province'], cluster['district'], cluster['locality'], first['published_date']]).encode()).hexdigest()[:12]
        # Highest reported TOTAL proxy; never add successive article counts.
        chosen = sorted(candidates, key=lambda r: (r['candidate_count'], r['published_at'], r['article_id']))[-1]
        disputed = any(r['disputed_total'] for r in members)
        accepted = not disputed
        for row in members:
            row['cluster_id'] = cluster_id
            row['dedupe_reason'] = row['dedupe_reason'] or f"Wilayah/lokalitas sama, jendela {window_days} hari"
            row['decision'] = 'Tahan: kelompok dibantah/dikoreksi' if disputed else 'Wakil dihitung' if row is chosen else 'Digabung; tidak ditambahkan'
        result.append({'cluster_id': cluster_id, 'province': cluster['province'], 'district': cluster['district'],
                       'locality': cluster['locality'] or 'Kabupaten/kota; lokasi rinci belum jelas',
                       'first_report_date': first['published_date'], 'last_report_date': members[-1]['published_date'],
                       'estimated_victims': chosen['candidate_count'], 'min_reported_total': min(r['candidate_count'] for r in candidates),
                       'article_count': len(members), 'numeric_article_count': len(candidates),
                       'included': accepted, 'status': 'Estimasi otomatis' if accepted else 'Tahan: ada bantahan/koreksi',
                       'representative_title': chosen['title'], 'representative_url': chosen['url'],
                       'count_source_date': chosen['published_date'], 'first_source_url': first['url'],
                       'source_urls': '|'.join(dict.fromkeys(r['url'] for r in members)),
                       'method': VERSION})
    for row in audit:
        if not row['cluster_id'] and not row['exclusion_reason']:
            row['exclusion_reason'] = row['dedupe_reason'] or row['location_reason']
    return {'clusters': sorted(result, key=lambda c: (c['first_report_date'], c['cluster_id'])), 'audit': audit,
            'summary': {'method': VERSION, 'window_days': window_days, 'article_count': len(audit),
                        'articles_with_counts': sum(bool(r['extracted_counts']) for r in audit),
                        'included_clusters': sum(r['included'] for r in result),
                        'estimated_victims': sum(r['estimated_victims'] for r in result if r['included']),
                        'held_clusters': sum(not r['included'] for r in result)}}

def filter_clusters(clusters, start, end, provinces=(), keyword=''):
    # Build clusters globally BEFORE applying filters so duplicates/date don't shift.
    return [r for r in clusters if start <= r['first_report_date'] <= end
            and (not provinces or r['province'] in provinces)
            and keyword.lower() in (r['district'] + ' ' + r['locality'] + ' ' + r['representative_title']).lower()]

def aggregate(clusters):
    province, daily = Counter(), Counter()
    for row in clusters:
        if row['included']:
            province[row['province']] += row['estimated_victims']
            daily[row['first_report_date']] += row['estimated_victims']
    return dict(sorted(province.items())), dict(sorted(daily.items()))
