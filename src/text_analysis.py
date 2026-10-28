"""Transparent title-level signals, not clinical or public-opinion inference."""
import re
from collections import Counter
from io import BytesIO
from random import Random

THEMES = {
    'Keluhan kesehatan': ('mual', 'muntah', 'diare', 'pusing', 'sakit perut', 'demam', 'lemas'),
    'Perawatan medis': ('dirawat', 'rawat inap', 'rumah sakit', 'dilarikan', 'puskesmas', 'igd'),
    'Gangguan layanan': ('dihentikan', 'ditutup', 'diliburkan', 'penutupan', 'stop', 'suspend'),
    'Mutu & kontaminasi': ('basi', 'bakteri', 'salmonella', 'e coli', 'kontaminasi', 'belatung', 'busuk'),
    'Pemeriksaan & pengawasan': ('investigasi', 'laboratorium', 'sampel', 'evaluasi', 'bpom', 'inspeksi'),
    'Pemulihan': ('sembuh', 'pulih', 'dipulangkan', 'membaik'),
}
NEGATIVE = ('korban', 'dirawat', 'meninggal', 'muntah', 'diare', 'mual', 'dilarikan',
            'marak', 'massal', 'basi', 'busuk', 'kritis', 'cemas', 'khawatir', 'trauma', 'gagal')
POSITIVE = ('sembuh', 'pulih', 'membaik', 'dipulangkan', 'teratasi')
CONTEXT = ('tidak', 'bukan', 'hoaks', 'hoax', 'bantah', 'dibantah', 'membantah',
           'cegah', 'mencegah', 'pencegahan', 'antisipasi', 'jangan', 'nihil', 'tanpa')
LABELS = ['Negatif / dampak', 'Pemulihan', 'Campuran', 'Perlu konteks', 'Tidak terklasifikasi']
COLORS = ['#C2413B', '#0F766E', '#C58A22', '#6366A1', '#94A3B8']
STOPWORDS = set('yang dan di ke dari untuk dengan pada ini itu jadi menjadi dalam usai setelah saat karena oleh atau juga akan ada hingga atas tentang terkait disebut kata sebut soal kini lagi masih tahun hari orang siswa anak pelajar mbg makan makanan bergizi gratis keracunan diduga dugaan kasus indonesia berita news com id www the of a an is are to'.split())

def clean_title(row):
    title = row['title']
    source = row.get('source', '')
    if source:
        previous = None
        while title != previous:
            previous = title
            title = re.sub(r'\s+[-–—|]\s*' + re.escape(source) + r'\s*$', '', title, flags=re.I)
    return title

def normalize(text):
    return ' '.join(re.findall(r'[a-z]+', text.lower()))

def matches(text, words):
    padded = ' ' + normalize(text) + ' '
    return [word for word in words if ' ' + word + ' ' in padded]

def classify(title):
    negative, positive, context = matches(title, NEGATIVE), matches(title, POSITIVE), matches(title, CONTEXT)
    if context:
        label = 'Perlu konteks'
    elif negative and positive:
        label = 'Campuran'
    elif negative:
        label = 'Negatif / dampak'
    elif positive:
        label = 'Pemulihan'
    else:
        label = 'Tidak terklasifikasi'
    return label, ', '.join(negative + positive + context) or 'Tidak ada kata dalam kamus'

def enrich(rows):
    result = []
    for row in rows:
        title = clean_title(row)
        label, evidence = classify(title)
        themes = [theme for theme, words in THEMES.items() if matches(title, words)]
        result.append({**row, 'clean_title': title, 'tone': label, 'trigger_words': evidence,
                       'themes': themes, 'month': row['published_at'][:7]})
    return result

def word_counts(rows, extra_stopwords='', deduplicate=True):
    excluded = STOPWORDS | set(normalize(extra_stopwords).split())
    counts, seen = Counter(), set()
    for row in rows:
        title = normalize(clean_title(row))
        if deduplicate and title in seen:
            continue
        seen.add(title)
        # Document frequency: a word counts at most once in each title.
        counts.update({word for word in title.split() if len(word) > 2 and word not in excluded})
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

def cloud_png(frequencies, max_words=60):
    """Deterministic, non-overlapping word cloud; size encodes title frequency."""
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new('RGB', (1200, 550), '#F0F5F8')
    draw, rng, boxes = ImageDraw.Draw(image), Random(42), []
    words = list(frequencies.items())[:max_words]
    if not words:
        return None
    largest = max(v for _, v in words)
    for word, value in words:
        size = int(16 + 66 * (value / largest) ** 0.7)
        placed = False
        while size >= 13 and not placed:
            font = ImageFont.load_default(size=size)
            box = draw.textbbox((0, 0), word, font=font)
            w, h = box[2] - box[0] + 14, box[3] - box[1] + 12
            if w >= 1180 or h >= 530:
                size -= 4
                continue
            for _ in range(100):
                x, y = rng.randint(10, 1190 - w), rng.randint(10, 540 - h)
                candidate = (x, y, x + w, y + h)
                if all(candidate[2] < b[0] or candidate[0] > b[2] or candidate[3] < b[1] or candidate[1] > b[3] for b in boxes):
                    draw.text((x + 7 - box[0], y + 6 - box[1]), word, font=font,
                              fill=rng.choice(['#164E63', '#0F766E', '#334155', '#7C3A31']))
                    boxes.append(candidate)
                    placed = True
                    break
            size -= 4
    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()
