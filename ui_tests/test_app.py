import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def test_dashboard_renders(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
        self.assertEqual(len(app.exception), 0)

    def test_empty_first_run(self):
        with patch('src.core.read_json', side_effect=lambda path, default: default), patch('src.core.load_incidents', return_value=[]):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.metric[1].value, '—')

    def test_estimate_intervals_and_unknown_location_filter(self):
        fixtures = [dict(id='estimate-ui', title='20 Siswa Bogor Keracunan MBG', source='Test',
                         published_at='2026-01-10T08:00:00+07:00', province_hint='Belum diketahui', url='https://example.org/test')]
        with patch('src.core.read_json', side_effect=lambda path, default: fixtures if path.name == 'articles.json' else default):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.metric[4].value, '20')
            interval = next(r for r in app.radio if r.label == 'Interval waktu')
            interval.set_value('Mingguan').run()
            self.assertEqual(len(app.exception), 0)
            next(r for r in app.radio if r.label == 'Interval waktu').set_value('Bulanan').run()
            self.assertEqual(len(app.exception), 0)
            app.sidebar.multiselect[0].set_value(['Belum diketahui']).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.metric[4].value, '0')

    def test_incident_kpi_excludes_refuted(self):
        base = dict(incident_id='test', event_date='2026-01-15', province='Jawa Barat', district='Test', location='Test', status='Dugaan', affected='10', source_urls='https://example.org', evidence='Test fixture only', reviewer='Test', reviewed_at='2026-01-16')
        rows = [base, {**base, 'incident_id': 'refuted', 'status': 'Dibantah', 'affected': '100'}]
        with patch('src.core.load_incidents', return_value=rows):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=30)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.metric[1].value, '1')
            self.assertEqual(app.metric[3].value, '10')
        self.assertEqual(len(app.metric), 8)
        app.sidebar.text_input[0].set_value('no-match-123').run()
        self.assertEqual(len(app.exception), 0)

if __name__ == '__main__':
    unittest.main()
