from copy import deepcopy
from datetime import datetime, timezone
import unittest
import build_calendars as b

NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)
T = int(datetime(2026, 7, 2, 23, 30, tzinfo=timezone.utc).timestamp() * 1000)
V = next(iter(b.VENUES))

def film():
    return {'title': 'Test, Film; é', 'showingId': 'test', 'category': 'movie',
            'url': 'https://example.com/film', 'overview': {'duration': 7200000},
            'themoviedb': {'id': 123}, 'performances': [
                {'time': T, 'notes': '', 'bookingUrl': 'https://example.com/book', 'format': {}, 'status': {}},
                {'time': T + 86400000, 'notes': 'Q&A with director', 'bookingUrl': 'https://example.com/qa', 'format': {}, 'status': {}}]}

def run(items, now=NOW):
    data = {v: [] for v in b.VENUES}
    data[V] = items
    s, f, counts = b.build(data, now)
    return s.decode().replace('\r\n ', ''), f.decode().replace('\r\n ', ''), counts

class CalendarTests(unittest.TestCase):
    def test_one_film_two_showtimes(self):
        _, f, _ = run([film()])
        self.assertEqual(f.count('BEGIN:VEVENT'), 1)
        self.assertIn('https://example.com/book', f)
        self.assertIn('https://example.com/qa', f)
    def test_special_notes_only_apply_to_one_performance(self):
        s, _, _ = run([film()])
        self.assertEqual(s.count('BEGIN:VEVENT'), 1)
        self.assertIn('https://example.com/qa', s)
    def test_format_detection(self):
        x = film(); x['performances'][0]['format'] = {'source': '70mm'}
        self.assertEqual(run([x])[0].count('BEGIN:VEVENT'), 2)
    def test_london_date_and_exclusive_end(self):
        f = run([film()])[1]
        self.assertIn('DTSTART;VALUE=DATE:20260703', f)
        self.assertIn('DTEND;VALUE=DATE:20260704', f)
    def test_duration_milliseconds(self):
        s = run([film()])[0]
        self.assertIn('DTSTART:20260703T233000Z', s)
        self.assertIn('DTEND:20260704T013000Z', s)
    def test_duplicates_removed(self):
        x = film(); self.assertEqual(run([x, deepcopy(x)])[0].count('BEGIN:VEVENT'), 1)
    def test_same_film_different_listing_grouped(self):
        x = film(); y = film(); y['title'] = 'Test Film + Q&A'; y['showingId'] = 'another'
        y['performances'] = [dict(y['performances'][0], time=T + 172800000)]
        self.assertEqual(run([x, y])[1].count('BEGIN:VEVENT'), 1)
    def test_uid_stable_as_first_showtime_passes(self):
        a = run([film()])[1]; c = run([film()], datetime.fromtimestamp((T+1)/1000, timezone.utc))[1]
        self.assertEqual([x for x in a.splitlines() if x.startswith('UID:')], [x for x in c.splitlines() if x.startswith('UID:')])
    def test_past_showtimes_excluded(self):
        self.assertEqual(run([film()], datetime(2027,1,1,tzinfo=timezone.utc))[1].count('BEGIN:VEVENT'), 0)
    def test_escaping_and_no_injection(self):
        self.assertEqual(b.escape('a,b;c\\d\nEND:VEVENT'), 'a\\,b\\;c\\\\d\\nEND:VEVENT')
    def test_utf8_folding(self):
        raw = b.calendar('é'*100, [])
        self.assertTrue(all(len(line) <= 75 for line in raw.split(b'\r\n')))
        self.assertIn('é'*100, raw.decode().replace('\r\n ', ''))
    def test_bad_time_rejected(self):
        x = film(); x['performances'][0]['time'] = 1790000000
        with self.assertRaises(ValueError): run([x])
    def test_distinct_cinemas(self):
        data = {v: [film()] for v in b.VENUES}
        _, f, _ = b.build(data, NOW)
        self.assertEqual(f.count(b'BEGIN:VEVENT'), 7)
        ids = [x for x in f.decode().replace('\r\n ', '').splitlines() if x.startswith('UID:')]
        self.assertEqual(len(set(ids)), 7)
    def test_sold_out_label(self):
        x = film(); x['performances'][0]['status']['soldOut'] = True
        self.assertIn('Sold out', run([x])[1])
    def test_non_film_excluded_from_film_calendar(self):
        x = film(); x['category'] = 'quiz'
        self.assertEqual(run([x])[1].count('BEGIN:VEVENT'), 0)
    def test_winter_date(self):
        x = film(); x['performances'] = [dict(x['performances'][0], time=int(datetime(2026,12,1,23,30,tzinfo=timezone.utc).timestamp()*1000))]
        self.assertIn('DTSTART;VALUE=DATE:20261201', run([x])[1])

if __name__ == '__main__': unittest.main()
