import unittest

from src.geography import locate
from src.victim_estimates import aggregate, build_estimates, extract_counts, filter_clusters, number_value

def article(i, title, day='2026-01-10', hour='08:00:00'):
    return dict(id=str(i), title=title, source='Test', url=f'https://example.org/{i}', published_at=f'{day}T{hour}+07:00')

class EstimateTests(unittest.TestCase):
    def test_school_year_and_people(self):
        c = extract_counts('120 Siswa SMPN 2 Cisarua Keracunan MBG, 1 Orang Masih Dirawat')
        self.assertEqual([(r['value'], r['kind']) for r in c], [(120, 'total kandidat'), (1, 'subkelompok')])
        self.assertEqual(extract_counts('SMPN 2 Bogor keracunan MBG 2026, 14 hari ditutup'), [])

    def test_number_and_approximation(self):
        self.assertEqual(number_value('1.242'), 1242)
        self.assertEqual(number_value('1,2 ribu'), 1200)
        self.assertEqual(extract_counts('Hampir 400 Orang Keracunan MBG')[0]['kind'], 'perkiraan/batas')

    def test_beneficiaries_not_victims(self):
        for title in ['Buntut Keracunan MBG Blora, 2.300 Penerima Manfaat Dialihkan', 'Dapur Keracunan MBG Bontang Kembali Layani 1.127 Siswa']:
            self.assertEqual(extract_counts(title)[0]['kind'], 'penerima layanan')

    def test_additive_groups(self):
        r = build_estimates([article(1, '75 Siswa dan 5 Guru Keracunan MBG di Magelang')])
        self.assertEqual(r['summary']['estimated_victims'], 80)

    def test_updates_and_first_nonnumeric_report(self):
        rows = [article(1, 'Siswa Bogor Diduga Keracunan MBG', '2026-01-09'),
                article(2, '10 Siswa Bogor Keracunan MBG'), article(3, '20 Orang Bogor Keracunan MBG', '2026-01-12'),
                article(4, '20 Orang Bogor Keracunan MBG', '2026-01-12')]
        r = build_estimates(rows)
        self.assertEqual(r['summary']['estimated_victims'], 20)
        self.assertEqual(r['clusters'][0]['first_report_date'], '2026-01-09')
        self.assertEqual(sum(x['decision'] == 'Wakil dihitung' for x in r['audit']), 1)
        self.assertEqual(filter_clusters(r['clusters'], '2026-01-10', '2026-01-20'), [])
        self.assertEqual(r, build_estimates(list(reversed(rows))))

    def test_distinct_localities_not_merged(self):
        rows = [article(1, '10 Siswa Cisarua Bogor Keracunan MBG'), article(2, '20 Siswa Dramaga Bogor Keracunan MBG'),
                article(3, '30 Siswa Bogor Keracunan MBG')]
        r = build_estimates(rows)
        self.assertEqual(r['summary']['estimated_victims'], 30)
        ambiguous = next(x for x in r['audit'] if x['article_id'] == '3')
        self.assertIn('Ambigu', ambiguous['dedupe_reason'])

    def test_new_event_outside_window(self):
        r = build_estimates([article(1, '10 Siswa Bogor Keracunan MBG'), article(2, '20 Siswa Bogor Keracunan MBG', '2026-02-10')])
        self.assertEqual(r['summary']['estimated_victims'], 30)

    def test_late_lab_update_not_new_event(self):
        rows = [article(1, '150 Siswa Dairi Keracunan MBG'), article(2, 'Hasil Lab MBG Penyebab 295 Siswa Dairi Keracunan', '2026-02-01')]
        r = build_estimates(rows)
        self.assertEqual(r['summary']['estimated_victims'], 295)
        self.assertEqual(r['summary']['included_clusters'], 1)

    def test_disputed_cluster_held(self):
        r = build_estimates([article(1, '400 Siswa Bogor Keracunan MBG'), article(2, 'BGN Bantah 400 Siswa Bogor Keracunan MBG: Hanya 13 Orang')])
        self.assertEqual(r['summary']['estimated_victims'], 0)
        self.assertEqual(r['summary']['held_clusters'], 1)

    def test_aggregate_prior_year_and_unknown_not_summed(self):
        rows = [article(1, '743 Orang Purworejo Keracunan MBG dalam Dua Pekan'),
                article(2, '1.000 Orang Bogor Keracunan MBG sejak 2025'),
                article(3, '210 Siswa Keracunan MBG di LokasiBelumDikenal')]
        r = build_estimates(rows)
        self.assertEqual(r['summary']['estimated_victims'], 0)
        self.assertEqual(len(r['audit']), 3)

    def test_scope_and_multi_region(self):
        self.assertEqual(locate('20 Siswa Bogor dan Cirebon Keracunan MBG')[1], '')
        self.assertEqual(locate('20 Siswa Manggarai Barat Keracunan MBG')[:2], ('Nusa Tenggara Timur', 'Manggarai Barat'))
        self.assertEqual(locate('20 Siswa Konawe Selatan Keracunan MBG')[1], 'Konawe Selatan')

    def test_province_and_time_reconcile(self):
        r = build_estimates([article(1, '10 Siswa Bogor Keracunan MBG'), article(2, '20 Siswa Kudus Keracunan MBG', '2026-01-11')])
        p, t = aggregate(r['clusters'])
        self.assertEqual(sum(p.values()), sum(t.values()))
        self.assertEqual(sum(p.values()), r['summary']['estimated_victims'])

    def test_nested_place_alias_not_counted_twice(self):
        rows = [article(1, '72 Siswa Pondok Kelapa Keracunan MBG'), article(2, '72 Siswa Duren Sawit Keracunan MBG'),
                article(3, '72 Siswa Duren Sawit Pondok Kelapa Keracunan MBG')]
        self.assertEqual(build_estimates(rows)['summary']['estimated_victims'], 72)

    def test_repeated_source_suffix_not_location(self):
        row = article(1, '103 Siswa Cisarua Keracunan MBG - Suara Merdeka Banyumas - Suara Merdeka Banyumas')
        row['source'] = 'Suara Merdeka Banyumas'
        r = build_estimates([row])
        self.assertEqual(r['summary']['estimated_victims'], 0)
        self.assertEqual(r['audit'][0]['district'], '')

    def test_death_denial_does_not_cancel_nonfatal_count(self):
        rows = [article(1, '432 Orang Cirebon Keracunan MBG'), article(2, 'Korban Keracunan MBG Cirebon Bertambah, RS Bantah Ada yang Meninggal')]
        self.assertEqual(build_estimates(rows)['summary']['estimated_victims'], 432)

    def test_late_bacteria_and_result_followups(self):
        rows = [article(1, '200 Siswa Surabaya Keracunan MBG'), article(2, 'Hampir Sebulan Hasil Uji MBG 210 Siswa Keracunan Surabaya Belum Keluar', '2026-02-01'),
                article(3, 'Ada Bakteri di Menu MBG yang Bikin 210 Siswa Surabaya Keracunan', '2026-02-03')]
        r = build_estimates(rows)
        self.assertEqual(r['summary']['estimated_victims'], 210)
        self.assertEqual(r['summary']['included_clusters'], 1)
