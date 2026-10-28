import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from src.collect import collect, parse_feed, windows
from src.core import article_id, load_incidents, province_hint, read_json, relevant, safe_csv, validate_incidents

FEED = b'''<rss><channel><item><title>20 siswa diduga keracunan MBG di Jawa Barat</title><source>Media A</source><link>https://example.org/a</link><pubDate>Thu, 15 Jan 2026 03:00:00 GMT</pubDate></item></channel></rss>'''

class PipelineTests(unittest.TestCase):
    def test_relevance(self):
        self.assertTrue(relevant('Dugaan keracunan makan bergizi gratis'))
        self.assertFalse(relevant('Keracunan makanan di pesta'))

    def test_dates(self):
        rows, _ = parse_feed(FEED, date(2026, 1, 1), date(2026, 1, 16), 'now')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['review_status'], 'Belum ditinjau')
        self.assertEqual(parse_feed(FEED, date(2026, 1, 16), date(2026, 2, 1), 'now')[0], [])

    def test_non_feed_rejected(self):
        with self.assertRaises(ValueError):
            parse_feed(b'<html/>', date(2026, 1, 1), date(2026, 2, 1), 'now')

    def test_province_longest_match(self):
        self.assertEqual(province_hint('MBG Papua Barat Daya'), 'Papua Barat Daya')
        self.assertEqual(province_hint('MBG Bandung'), 'Belum diketahui')

    def test_dedupe_source_aware(self):
        self.assertEqual(article_id('MBG: Keracunan!', 'A'), article_id('mbg keracunan', 'A'))
        self.assertNotEqual(article_id('MBG', 'A'), article_id('MBG', 'B'))

    def test_windows_no_gaps(self):
        spans = list(windows(date(2026, 1, 1), date(2026, 1, 17)))
        self.assertEqual(spans[0][0], date(2026, 1, 1))
        self.assertEqual(spans[-1][1], date(2026, 1, 17))
        self.assertEqual(spans[0][1], spans[1][0])

    @patch('src.collect.time.sleep')
    @patch('src.collect.fetch', return_value=FEED)
    def test_repeat_and_failure_preserve_data(self, fetch, sleep):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            args = (date(2026, 1, 1), date(2026, 1, 16))
            first = collect(*args, data_dir=path)
            second = collect(*args, data_dir=path)
            self.assertEqual(first['added'], 1)
            self.assertEqual(second['added'], 0)
            fetch.side_effect = TimeoutError('offline')
            failed = collect(*args, data_dir=path)
            self.assertEqual(failed['status'], 'failed')
            self.assertEqual(len(read_json(path / 'articles.json', [])), 1)
            self.assertEqual(failed['last_success_at'], second['last_success_at'])

    def test_register_validation(self):
        row = dict(incident_id='one', event_date='2026-01-15', province='Jawa Barat', district='Bandung', location='School', status='Dugaan', affected='', source_urls='https://example.org', evidence='Statement', reviewer='Test', reviewed_at='2026-01-16')
        self.assertEqual(len(validate_incidents([row], date(2026, 2, 1))), 1)
        for change in ({'affected': '-2'}, {'event_date': '2025-12-31'}, {'source_urls': ''}, {'status': 'Confirmed'}):
            with self.assertRaises(ValueError):
                validate_incidents([{**row, **change}], date(2026, 2, 1))
        with self.assertRaises(ValueError):
            validate_incidents([row, row], date(2026, 2, 1))

    def test_actual_register(self):
        load_incidents(Path(__file__).resolve().parents[1] / 'data/incidents.csv')

    def test_csv_formula_escape(self):
        self.assertIn("'=1+1", safe_csv([{'title': '=1+1'}], ['title']).decode('utf-8-sig'))

    @patch('src.collect.time.sleep')
    @patch('src.collect.fetch', return_value=FEED)
    @patch('src.collect.parse_feed', return_value=([], 100))
    def test_capped_feed_splits_until_one_day(self, parse, fetch, sleep):
        with tempfile.TemporaryDirectory() as folder:
            report = collect(date(2026, 1, 1), date(2026, 1, 3), data_dir=Path(folder))
            self.assertEqual(len(report['queries']), 3)
            self.assertTrue(report['queries'][0]['subdivided'])
            self.assertFalse(report['queries'][1].get('subdivided', False))

if __name__ == '__main__':
    unittest.main()
