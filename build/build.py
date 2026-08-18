#!/usr/bin/env python3
"""Rebuild index.html from current Spotify play counts.

    python3 build/build.py            # fetch fresh numbers from kworb and rebuild
    python3 build/build.py --offline  # rebuild from the cached copy

If Taylor releases a new album, add its track list to albums.py first. The script
stops and tells you if it sees a song it cannot place on an album.
"""
import io, json, os, re, sys, unicodedata, datetime
from urllib.request import urlopen, Request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from albums import ALBUMS, META

SRC = "https://kworb.net/spotify/artist/06HL4z0CvFAxyc27GXpf02_songs.html"
CACHE = os.path.join(HERE, "kworb_songs.html")

# recordings that are not separate songs
DROP = [r' - live\b', r'live/\d', r'live from', r'live at', r'\(live', r'live version',
        r'karaoke', r'remix', r'\bmix\b', r'voice memo', r'long pond studio sessions',
        r'acoustic', r'piano version', r'instrumental', r'track by track',
        r'original demo recording', r'\bdemo\b', r'the short film', r'3d concert experience',
        r'old timey version', r'sad girl autumn version', r'original version',
        r'extended version', r'music video', r'pop version', r'dressing room rehearsal',
        r'video edition', r'recorded at the tracking room', r'candlelight version',
        r'witch version', r"90's trend", r'us version', r'settled down acoustic',
        r'life is a song acoustic', r'alone in my tower', r"now you're home acoustic",
        r'my advice version', r'so glamorous cabaret', r'jingle ball',
        r'academy of country music', r'clear channel']
KEEP = {'Teardrops On My Guitar - Radio Single Remix',
        "All Too Well (10 Minute Version) (Taylor's Version) (From The Vault)"}
# kworb puts summary rows in the same table as the songs
NOT_SONGS = {'total', 'streams', 'daily', 'tracks', 'as lead', 'solo', 'as feature'}


def fetch(offline):
    if offline or os.path.exists(CACHE) and offline:
        return io.open(CACHE, encoding='utf-8').read()
    if offline:
        sys.exit("no cached copy at " + CACHE)
    html = urlopen(Request(SRC, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
    io.open(CACHE, 'w', encoding='utf-8').write(html)
    return html


def rows(html):
    import html as H
    out = []
    for tr in re.findall(r'<tr>(.*?)</tr>', html, re.S):
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)
        if len(cells) < 2:
            continue
        title = H.unescape(re.sub(r'<[^>]+>', '', cells[0])).strip()
        title = title.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
        nums = [re.sub(r'<[^>]+>', '', c).strip().replace(',', '') for c in cells[1:]]
        total = next((int(n) for n in nums if n.isdigit()), None)
        if title and title.lower() not in NOT_SONGS and total is not None:
            out.append((title, total))
    return out


def dropped(t):
    return t not in KEEP and any(re.search(p, t.lower()) for p in DROP)


def canon(t):
    t = re.sub(r"\s*\(Taylor's Version\)", '', t)
    t = re.sub(r'\s*\(From The Vault\)', '', t)
    t = re.sub(r'\s*\(feat\.[^)]*\)|\s*\[feat\.[^\]]*\]|\s*\(with [^)]*\)', '', t)
    t = re.sub(r'\s*-\s*(from|From|Featured in|Radio Single Remix|bonus track).*$', '', t)
    return t.strip(' -')


def key(t):
    k = unicodedata.normalize('NFKD', canon(t)).lower().replace('’', "'")
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', '', k)).strip()


def main():
    offline = '--offline' in sys.argv
    merged = {}
    for title, streams in rows(fetch(offline)):
        if dropped(title):
            continue
        k = key(title)
        if not k:
            continue
        e = merged.setdefault(k, {'title': canon(title), 'streams': 0, 'feature': 0})
        e['streams'] += streams
        e['feature'] |= title.startswith('*')
        if len(canon(title)) < len(e['title']):
            e['title'] = canon(title)

    lookup = {}
    for alb, blob in ALBUMS.items():
        for t in (x.strip() for x in blob.replace('\n', '').split('|')):
            if t:
                lookup[key(t)] = alb

    songs, unplaced = [], []
    for e in merged.values():
        t = e['title'].lstrip('* ').strip()
        alb = lookup.get(key(t))
        if not alb:
            unplaced.append((e['streams'], t))
            continue
        yr, colour, deep, short = META[alb]
        songs.append({'t': t, 's': e['streams'], 'a': alb, 'y': yr,
                      'c': colour, 'd': deep, 'sh': short, 'f': int(bool(e['feature']))})
    if unplaced:
        print("Songs with no album. Add them to build/albums.py, then run again:")
        for s, t in sorted(unplaced, reverse=True):
            print(f"  {s:>14,}  {t}")
        sys.exit(1)

    songs.sort(key=lambda x: -x['s'])
    for i, s in enumerate(songs):
        s['r'] = i + 1

    # top 64, snake-seeded so each quadrant gets one song from every seed band
    REGIONS = ['GLITTER GEL PEN', 'FOUNTAIN PEN', 'QUILL PEN', 'THE VAULT']
    PAIRS = [(1, 16), (8, 9), (5, 12), (4, 13), (6, 11), (3, 14), (7, 10), (2, 15)]
    quads = [[] for _ in range(4)]
    for band in range(16):
        order = [0, 1, 2, 3] if band % 2 == 0 else [3, 2, 1, 0]
        for j in range(4):
            quads[order[j]].append({'seed': band + 1, **songs[band * 4 + j]})
    bracket = [{'name': REGIONS[i],
                'games': [[next(x for x in q if x['seed'] == a),
                           next(x for x in q if x['seed'] == b)] for a, b in PAIRS]}
               for i, q in enumerate(quads)]

    data = {'songs': songs, 'bracket': bracket,
            'total': sum(s['s'] for s in songs), 'count': len(songs),
            'updated': datetime.date.today().isoformat()}
    blob = json.dumps(data, separators=(',', ':'))
    io.open(os.path.join(ROOT, 'data.json'), 'w', encoding='utf-8').write(blob)

    tpl = io.open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    if '__DATA__' not in tpl:
        sys.exit('template.html is missing its __DATA__ marker')
    io.open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(tpl.replace('__DATA__', blob))

    print(f"{len(songs)} songs, {data['total']/1e9:.1f}B streams, cutoff for the field "
          f"{songs[63]['s']:,} ({songs[63]['t']})")
    print("wrote index.html and data.json")


if __name__ == '__main__':
    main()
