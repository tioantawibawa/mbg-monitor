import unittest
from src.text_analysis import classify, clean_title, enrich, word_counts

class TitleAnalysisTests(unittest.TestCase):
    def test_query_word_alone_not_negative(self):
        self.assertEqual(classify('Kasus keracunan MBG')[0], 'Tidak terklasifikasi')

    def test_negation_and_prevention_are_context(self):
        for title in ['Tidak ada korban meninggal', 'Cegah keracunan massal', 'Hoaks siswa meninggal']:
            self.assertEqual(classify(title)[0], 'Perlu konteks')

    def test_mixed_and_recovery(self):
        self.assertEqual(classify('Korban dirawat kini sembuh')[0], 'Campuran')
        self.assertEqual(classify('Siswa pulih dan dipulangkan')[0], 'Pemulihan')

    def test_word_boundaries(self):
        self.assertEqual(classify('Kepulihan program')[0], 'Tidak terklasifikasi')

    def test_source_removed_and_document_frequency(self):
        rows = [{'title': 'Muntah muntah MBG - Media', 'source': 'Media'},
                {'title': 'Muntah muntah MBG - Other', 'source': 'Other'}]
        self.assertEqual(clean_title(rows[0]), 'Muntah muntah MBG')
        self.assertEqual(word_counts(rows), {'muntah': 1})
        self.assertEqual(word_counts(rows, deduplicate=False), {'muntah': 2})
        self.assertEqual(word_counts(rows, 'muntah'), {})

    def test_overlapping_themes_remain_mentions(self):
        data = enrich([{'title': 'Tidak ada siswa mual dirawat', 'source': '', 'published_at': '2026-01-01'}])
        self.assertEqual(data[0]['tone'], 'Perlu konteks')
        self.assertEqual(len(data[0]['themes']), 2)
