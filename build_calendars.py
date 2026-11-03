#!/usr/bin/env python3
"""Build two iCalendar subscriptions from Clusterflick's published venue JSON."""
import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

UTC = timezone.utc
LONDON = ZoneInfo('Europe/London')
VENUES = {
    'princecharlescinema.com': 'Prince Charles Cinema',
    'bfi.org.uk-southbank': 'BFI Southbank',
    'thenickel.co.uk': 'The Nickel',
    'thegardencinema.co.uk': 'The Garden Cinema',
    'riocinema.org.uk': 'Rio Cinema',
    'genesiscinema.co.uk': 'Genesis Cinema',
    'thecastlecinema.com': 'The Castle Cinema',
}
CREDIT = ('Screening data from Clusterflick - https://clusterflick.com (CC BY 4.0: '
          'https://creativecommons.org/licenses/by/4.0/). Filtered and grouped for these calendars.')
SPECIAL = re.compile(r'\b(q\s*&\s*a|q\s+and\s+a|35\s?mm|70\s?mm|16\s?mm|preview|premiere|'
                     r'festival|retrospective|anniversary|double[ -]bill|triple[ -]bill|'
                     r'marathon|all[ -]nighter|sing[ -]along|one[ -]off|special screening|'
                     r'introduction|introduced by|with intro|in conversation|live score)\b', re.I)


def clean(value):
    return html.unescape(re.sub(r'<[^>]+>', '', str(value))).replace('\r\n', '\n').replace('\r', '\n')


def escape(value):
    return clean(value).replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line):
    """RFC 5545: at most 75 UTF-8 octets per physical line, no split codepoints."""
    parts, current = [], ''
    for char in line:
        if len((current + char).encode('utf-8')) > 75:
            parts.append(current)
            current = ' '
        current += char
    return '\r\n'.join(parts + [current])


def stamp(value):
    return value.astimezone(UTC).strftime('%Y%m%dT%H%M%SZ')


def uid(*parts):
    return hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest() + '@cinema-calendar'


def film_key(film):
    # Use the matched numeric ID only as a join key; do not redistribute TMDB prose/art.
    if film.get('category') == 'movie' and film.get('themoviedb', {}).get('id'):
        return 'movie:' + str(film['themoviedb']['id'])
    return '{}:{}:{}'.format(film.get('category'), clean(film['title']).casefold().strip(),
                            film.get('overview', {}).get('year', ''))


def reasons(film, performance):
    result = []
    source = performance.get('format', {}).get('source', '')
    if source in ('35mm', '70mm', 'imax-70mm', '16mm', 'nitrate'):
        result.append(source)
    # Performance notes apply only to that performance, never all showtimes of the film.
    text = film['title'] + ' ' + performance.get('notes', '')
    result.extend(m.group(0) for m in SPECIAL.finditer(text))
    return list(dict.fromkeys(result))


def validate(data, venue):
    if not isinstance(data, list):
        raise ValueError(venue + ': expected a list of showings')
    for film in data:
        if not isinstance(film, dict) or not film.get('title') or not isinstance(film.get('performances'), list):
            raise ValueError(venue + ': invalid showing')
        for performance in film['performances']:
            value = performance.get('time')
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 946684800000 < value < 7258118400000:
                raise ValueError(venue + ': expected a Unix timestamp in milliseconds')
    return data


def fetch(venue):
    url = 'https://clusterflick.com/datasets/venues/' + venue + '.json'
    # curl is included on GitHub's Ubuntu runner and macOS; TLS verification stays enabled.
    result = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                             '--retry', '3', '--connect-timeout', '15', '--max-time', '60', url],
                            check=True, capture_output=True, text=True)
    return validate(json.loads(result.stdout), venue)


def details(film, p, start):
    line = start.astimezone(LONDON).strftime('%a %d %b %Y, %H:%M %Z')
    flags = [p.get('notes', ''), p.get('format', {}).get('source', ''), p.get('screen', '')]
    if p.get('status', {}).get('soldOut'):
        flags.append('Sold out')
    flags.extend(k for k, v in p.get('accessibility', {}).items() if v)
    if any(flags):
        line += ' — ' + '; '.join(clean(x) for x in flags if x)
    return line + '\n' + p.get('bookingUrl', film.get('url', ''))


def event(identifier, title, venue, start, end, description, url, now, all_day=False):
    lines = ['BEGIN:VEVENT', 'UID:' + identifier, 'DTSTAMP:' + stamp(now),
             'SUMMARY:' + escape(title), 'LOCATION:' + escape(venue),
             'DESCRIPTION:' + escape(description + '\n\n' + CREDIT), 'TRANSP:TRANSPARENT']
    if all_day:
        lines += ['DTSTART;VALUE=DATE:' + start.strftime('%Y%m%d'),
                  'DTEND;VALUE=DATE:' + end.strftime('%Y%m%d')]
    else:
        lines += ['DTSTART:' + stamp(start)]
        if end:
            lines.append('DTEND:' + stamp(end))
    if url:
        # URL is a URI property, not an iCalendar TEXT value.
        lines.append('URL:' + str(url).replace('\r', '').replace('\n', ''))
    return lines + ['END:VEVENT']


def calendar(name, events):
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Cinema Calendar//Two Calendars//EN',
             'CALSCALE:GREGORIAN', 'X-WR-CALNAME:' + escape(name),
             'X-WR-TIMEZONE:Europe/London', 'X-WR-CALDESC:' + escape(CREDIT)]
    for item in events:
        lines.extend(item)
    return ('\r\n'.join(fold(line) for line in lines + ['END:VCALENDAR']) + '\r\n').encode('utf-8')


def build(datasets, now):
    special, films, counts = [], [], {}
    for venue, name in VENUES.items():
        data = validate(datasets[venue], venue)
        groups, seen = defaultdict(list), set()
        count = {'upcoming_showtimes': 0, 'special_screenings': 0, 'films_showing': 0}
        for film in data:
            key = film_key(film)
            for p in film['performances']:
                start = datetime.fromtimestamp(p['time'] / 1000, UTC)
                if start < now:
                    continue
                identity = (key, p['time'], p.get('screen', ''))
                if identity in seen:
                    continue
                seen.add(identity)
                count['upcoming_showtimes'] += 1
                if film.get('category') in ('movie', 'multiple-movies', 'shorts'):
                    groups[key].append((start, film, p))
                why = reasons(film, p)
                if why:
                    duration = film.get('overview', {}).get('duration')
                    end = start + timedelta(milliseconds=duration) if isinstance(duration, (int, float)) and duration > 0 else None
                    desc = 'Special screening: ' + ', '.join(why) + '\n' + details(film, p, start)
                    desc += '\nEnd time uses the published running time; introductions and Q&As may run longer.' if end else '\nEnd time unavailable.'
                    special.append((start, event(uid('special', venue, *identity),
                        film['title'] + ' — ' + name, name, start, end, desc,
                        p.get('bookingUrl', film.get('url', '')), now)))
                    count['special_screenings'] += 1
        for key, entries in sorted(groups.items()):
            entries.sort(key=lambda x: x[0])
            start, film, _ = entries[0]
            day = start.astimezone(LONDON).date()
            desc = ('One listing per film per cinema, on its first upcoming date.\n'
                    'All currently published upcoming showtimes (London time):\n\n')
            desc += '\n\n'.join(details(f, p, t) for t, f, p in entries)
            films.append((start, event(uid('film', venue, key), film['title'] + ' — ' + name,
                         name, day, day + timedelta(days=1), desc, film.get('url', ''), now, True)))
            count['films_showing'] += 1
        counts[name] = count
    return (calendar('Cinema: Special Screenings', [e for _, e in sorted(special, key=lambda x: x[0])]),
            calendar('Cinema: Films Showing', [e for _, e in sorted(films, key=lambda x: x[0])]), counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, help='Use saved venue JSON instead of downloading')
    parser.add_argument('--output', type=Path, default=Path('site'))
    parser.add_argument('--now', help='ISO timestamp, for reproducible checks')
    args = parser.parse_args()
    now = datetime.fromisoformat(args.now.replace('Z', '+00:00')) if args.now else datetime.now(UTC)
    if now.tzinfo is None:
        parser.error('--now must include a timezone')
    datasets = {v: json.loads((args.data_dir / (v + '.json')).read_text()) if args.data_dir else fetch(v) for v in VENUES}
    special, films, counts = build(datasets, now)
    # A broken/stale/empty source must not replace the previously published calendars.
    empty = [name for name, count in counts.items() if not count['upcoming_showtimes']]
    if empty:
        raise ValueError('No upcoming listings for: ' + ', '.join(empty) + '. Publication stopped; inspect the source.')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'special-screenings.ics').write_bytes(special)
    (args.output / 'films-showing.ics').write_bytes(films)
    report = {'built_at_utc': now.isoformat(), 'venues': counts}
    (args.output / 'status.json').write_text(json.dumps(report, indent=2) + '\n')
    rows = ''.join('<li>{}: {} films, {} special screenings</li>'.format(html.escape(n), c['films_showing'], c['special_screenings']) for n, c in counts.items())
    (args.output / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Cinema calendars</title>
<style>body{font:18px/1.6 system-ui;max-width:760px;margin:3rem auto;padding:0 1rem}a{color:#164ca0}</style>
<h1>Your cinema calendars</h1><p>Two separate subscriptions for your seven cinemas.</p>
<ul><li><a href="special-screenings.ics">Cinema: Special Screenings</a></li>
<li><a href="films-showing.ics">Cinema: Films Showing</a></li></ul>
<p>Copy each link into Apple Calendar’s Add Subscription Calendar. Subscribe rather than importing a one-time copy.</p>
<p>Updated: ''' + html.escape(now.isoformat()) + '</p><ul>' + rows + '''</ul>
<p>Special screenings are identified from published notes, titles and film formats. Coverage depends on source labelling.
Always confirm details on the cinema’s booking page.</p>
<p>Screening data from <a href="https://clusterflick.com">Clusterflick</a>
(<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>), filtered and grouped.</p></html>''', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
