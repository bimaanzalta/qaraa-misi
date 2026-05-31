#!/usr/bin/env python3
"""
Convert marathon mission CSV(s) to PHP/JSON array format.

Usage:
  python3 generate_marathon.py "untuk isi misi.csv" --marathon-id 55
  python3 generate_marathon.py "untuk isi misi.csv" "untuk isi misi2.csv" --marathon-id 94 --output output/marathon_94
"""
import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# ── PHP renderer ─────────────────────────────────────────────────────────────

def _php_val(value, indent, inline):
    sp = '  ' * indent
    inner = '  ' * (indent + 1)
    if isinstance(value, dict):
        if not value:
            return '[]'
        if inline:
            parts = ['"' + k + '" => ' + _php_val(v, 0, True) for k, v in value.items()]
            return '[' + ', '.join(parts) + ']'
        lines = ['[']
        for k, v in value.items():
            lines.append(inner + '"' + k + '" => ' + _php_val(v, indent + 1, k == 'requirement') + ',')
        lines.append(sp + ']')
        return '\n'.join(lines)
    if isinstance(value, list):
        if not value:
            return '[]'
        lines = ['[']
        for item in value:
            lines.append(inner + _php_val(item, indent + 1, False) + ',')
        lines.append(sp + ']')
        return '\n'.join(lines)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return 'null'
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def php_export(value):
    return _php_val(value, 0, False)


# ── Lookup tables ─────────────────────────────────────────────────────────────

FASIH_BY_SURA = {
    'al-alaq':      67,
    "al-'alaq":     67,
    'al-mulk':      99999,
    'al-lail':      71,
    'al-ghasyiyah': 75,
    'al-infitar':   81,
    'al-jinn':      100004,
    'al-lahab':     51,
    'at-takwir':    82,
    'al-fajr':      74,
    'al-fatihah':   47,
    'al-falaq':     49,
    'ad-dhuha':     70,
    'at-takatsur':  61,
}

SURA_INDEX = {
    'ali-imran':    3,
    'al-baqarah':   2,
    'al-kahf':      18,
    'ar-rahman':    55,
    'al-mulk':      67,
    'al-waqiah':    56,
    "al-waqi'ah":   56,
    'al-waqi-ah':   56,
    'al-insyiqaq':  84,
    'al-humazah':   104,
    'al-muzzammil': 73,
    'asy-syura':    42,
    'yasin':        36,
    'ya-sin':       36,
}

KHATAM_INDEX = {
    'al-alaq':      96,
    "al-'alaq":     96,
    'al-mulk':      67,
    'ad-dukhan':    44,
    'an-naba':      78,
    'an-naziat':    79,
    "an-nazi'at":   79,
    'at-takatsur':  102,
}

MATERIAL_ID = {
    'tajwid':   73,
    'hijaiyah': 2,
    'tahsin':   42,
}

EXAM_CFG = {
    'tajwid':   {'exam_id': 29, 'material_id': 73},
    'hijaiyah': {'exam_id': 29, 'material_id': 1},
    'tahsin':   {'exam_id': 30, 'material_id': 42},
}

DHIKR_TYPE = {
    'pagi':            'morning',
    'petang':          'evening',
    'setelah-shalat':  'after_prayer',
    'setelah-sholat':  'after_prayer',
}

AMAL_YAUMI_TYPE = {
    'tahajjud':       'tahajjud',
    'qabliyah-subuh': 'qabliyah_subuh',
    'sedekah-subuh':  'sedekah',
    'dhuha':          'dhuha',
}

MISSION_BASE = {
    1:  {'x': 8,   'target': 8,   'point': 20,  'pro': 1},
    2:  {'x': 40,  'target': 40,  'point': 5,   'pro': 1},
    3:  {'x': 30,  'target': 30,  'point': 25,  'pro': 1},
    8:  {'x': 1,   'target': 1,   'point': 5,   'pro': 1},
    16: {'x': 1,   'target': 1,   'point': 10,  'pro': 1},
    17: {'x': 10,  'target': 10,  'point': 10,  'pro': 1},
    28: {'x': 564, 'target': 564, 'point': 5,   'pro': 1},
    29: {'x': 15,  'target': 15,  'point': 15,  'pro': 1},
    30: {'fasih_id': 72, 'target': 1, 'point': 20, 'pro': 1},
    31: {'x': 10, 'target': 10, 'point': 10, 'pro': 1, 'from_index': '5673', 'to_index': '6236'},
    32: {'x': 70, 'exercise_count': 5, 'target': 5, 'point': 15, 'pro': 1},
    33: {'exam_id': 29, 'material_id': 73, 'target': 1, 'point': 50, 'pro': 1},
    34: {'x': 6,   'target': 6,   'point': 5,   'pro': 1},
    35: {'x': 5,   'target': 5,   'point': 10,  'material_id': 2, 'pro': 1},
    36: {'dhikr': 'morning', 'target': 1, 'point': 15, 'pro': 0},
    37: {'target': 1, 'point': 10, 'pro': 0},
    38: {'x': 5,   'target': 5,   'point': 50,  'pro': 0},
    39: {'index': 93, 'target': 1, 'point': 50, 'pro': 0},
    40: {'target': 1, 'point': 100, 'pro': 0},
    44: {'index': 9,  'target': 1,  'point': 100, 'pro': 0},
    49: {'target': 1, 'point': 100, 'pro': 1},
    54: {'target': 1, 'point': 10,  'pro': 0},
    67: {'target': 1, 'point': 10,  'pro': 0},
}

MISSION_LINK = {
    1:  'push:/murajaahHome',
    2:  'push:/murajaahHome',
    3:  'push:/murajaahHome',
    8:  'push:/alurBelajar',
    16: 'push:/alurBelajar',
    17: 'push:/alurBelajar',
    28: 'push:/murajaahHome',
    29: 'push:/murajaahHome',
    30: 'push:/murajaahHome',
    31: 'push:/setorAyatHome:{"index":3}',
    32: 'push:/alurBelajar',
    33: 'push:/alurBelajar',
    34: 'push:/alurBelajar',
    35: 'push:/alurBelajar',
    36: 'push:/zikir',
    37: 'push:/kalender',
    38: 'push:/quran',
    39: 'push:/quran',
    40: 'push:/kurban',
    44: 'push:/quran',
    49: 'push:/sebisaku',
    54: 'push:/quran',
    67: 'push:/kalender',
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def norm(s):
    s = s.lower().strip()
    s = s.replace('‘', "'").replace('’', "'").replace('`', "'")
    s = s.replace('qur’an', 'quran').replace("qur'an", 'quran')
    s = re.sub(r"[^a-z0-9']+", '-', s)
    return re.sub('-+', '-', s).strip('-')


def _one(mid, title, req):
    return [(mid, title, req)]


# ── Mission parser ────────────────────────────────────────────────────────────

def parse_mission(text):
    """Return list of (mission_id, title, requirement) — usually one item."""
    t = text.strip()
    l = t.lower()

    # Setoran ayat X ayat
    m = re.search(r'setoran ayat\s+(\d+)\s+ayat', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[31]); req['x'] = x; req['target'] = x
        return _one(31, t, req)

    # Bintang 5 murajaah X kali
    m = re.search(r'mendapatkan bintang 5\b.*?(\d+)\s+kali', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[3]); req['x'] = x; req['target'] = x
        return _one(3, t, req)

    # Bintang 3 murajaah X kali
    m = re.search(r'mendapatkan bintang 3\b.*?(\d+)\s+kali', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[29]); req['x'] = x; req['target'] = x
        return _one(29, t, req)

    # Murajaah sebanyak-banyaknya
    if re.search(r'murajaah\b.+sebanyak.?banyaknya', l):
        return _one(28, t, dict(MISSION_BASE[28]))

    # Murajaah X surah
    m = re.search(r'murajaah\s+(\d+)\s+surah', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[1]); req['x'] = x; req['target'] = x
        return _one(1, t, req)

    # Murajaah X ayat
    m = re.search(r'murajaah\s+(\d+)\s+ayat', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[2]); req['x'] = x; req['target'] = x
        return _one(2, t, req)

    # Murajaah surah <name>
    m = re.search(r'murajaah\s+surah\s+(.+)$', l)
    if m:
        sura = norm(m.group(1))
        if sura not in FASIH_BY_SURA:
            raise ValueError('FASIH_BY_SURA missing key ' + repr(sura) + '  (source: ' + repr(t) + ')')
        req = dict(MISSION_BASE[30]); req['fasih_id'] = FASIH_BY_SURA[sura]
        return _one(30, t, req)

    # Bagikan pencapaian belajar X kali
    m = re.search(r'bagikan pencapaian belajar\s+(\d+)\s+kali', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[8]); req['x'] = x; req['target'] = x
        return _one(8, t, req)

    # Menyelesaikan X materi di bab Y
    m = re.search(r'menyelesaikan\s+(\d+)\s+materi\s+di\s+bab\s+(.+)$', l)
    if m:
        x = int(m.group(1)); chap = norm(m.group(2))
        if chap not in MATERIAL_ID:
            raise ValueError('MATERIAL_ID missing key ' + repr(chap) + '  (source: ' + repr(t) + ')')
        req = dict(MISSION_BASE[35]); req['x'] = x; req['target'] = x; req['material_id'] = MATERIAL_ID[chap]
        return _one(35, t, req)

    # Menyelesaikan X materi (bare)
    m = re.search(r'menyelesaikan\s+(\d+)\s+materi$', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[16]); req['x'] = x; req['target'] = x
        return _one(16, t, req)

    # Mengulang X materi
    m = re.search(r'mengulang\s+(\d+)\s+materi', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[34]); req['x'] = x; req['target'] = x
        return _one(34, t, req)

    # Dapatkan skor X% dalam Y latihan
    m = re.search(r'dapatkan skor\s+(\d+)%?\s+dalam\s+(\d+)\s+latihan', l)
    if m:
        score, cnt = int(m.group(1)), int(m.group(2))
        req = dict(MISSION_BASE[32]); req['x'] = score; req['exercise_count'] = cnt; req['target'] = cnt
        return _one(32, t, req)

    # Menyelesaikan X latihan dengan skor Y% (alternate form)
    m = re.search(r'menyelesaikan\s+(\d+)\s+latihan\s+dengan\s+skor\s+(\d+)%?', l)
    if m:
        cnt, score = int(m.group(1)), int(m.group(2))
        req = dict(MISSION_BASE[32]); req['x'] = score; req['exercise_count'] = cnt; req['target'] = cnt
        return _one(32, t, req)

    # Kerjakan ujian bab X
    m = re.search(r'kerjakan ujian bab\s+(.+)$', l)
    if m:
        chap = norm(m.group(1))
        cfg = EXAM_CFG.get(chap)
        if cfg is None:
            raise ValueError('EXAM_CFG missing key ' + repr(chap) + '  (source: ' + repr(t) + ')')
        req = dict(MISSION_BASE[33]); req.update(cfg)
        return _one(33, t, req)

    # Mencatat amalan
    if 'mencatat amalan' in l:
        return _one(37, t, dict(MISSION_BASE[37]))

    # Kuis spesial / Sebisaku
    if 'kuis spesial' in l or 'misi sebisaku' in l:
        return _one(49, t, dict(MISSION_BASE[49]))

    # Menabung / fitur kurban
    if 'fitur kurban' in l or ('menabung' in l and 'sebisaku' in l):
        return _one(40, t, dict(MISSION_BASE[40]))

    # Dzikir (with or without "counter")
    m = re.search(r'membaca dan menyelesaikan(?:\s+counter)?\s+dzikir\s+(.+)$', l)
    if m:
        part = norm(m.group(1))
        if part not in DHIKR_TYPE:
            raise ValueError('DHIKR_TYPE missing key ' + repr(part) + '  (source: ' + repr(t) + ')')
        req = dict(MISSION_BASE[36]); req['dhikr'] = DHIKR_TYPE[part]
        return _one(36, t, req)

    # Mendengarkan murottal di Quran sebanyak X surah
    m = re.search(r"mendengarkan murottal di qur[‘’']?an sebanyak\s+(\d+)\s+surah", l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[38]); req['x'] = x; req['target'] = x
        return _one(38, t, req)

    # Mendengarkan murottal <surah>
    m = re.search(r'mendengarkan murottal\s+(.+)$', l)
    if m:
        sura = norm(m.group(1))
        sura = re.sub(r'^surah-', '', sura)
        if sura not in SURA_INDEX:
            raise ValueError('SURA_INDEX missing key ' + repr(sura) + '  (source: ' + repr(t) + ')')
        idx = SURA_INDEX[sura]
        req = dict(MISSION_BASE[39]); req['index'] = idx; req['target'] = idx
        return _one(39, t, req)

    # Membaca surah X di Fitur Khatam
    m = re.search(r'membaca surah\s+(.+?)\s+di\s+(?:fitur\s+)?khatam', l)
    if m:
        sura = norm(m.group(1))
        if sura not in KHATAM_INDEX:
            raise ValueError('KHATAM_INDEX missing key ' + repr(sura) + '  (source: ' + repr(t) + ')')
        idx = KHATAM_INDEX[sura]
        req = dict(MISSION_BASE[44]); req['index'] = idx; req['target'] = idx
        return _one(44, t, req)

    # Belajar X menit
    m = re.search(r'belajar\s+(\d+)\s+menit', l)
    if m:
        x = int(m.group(1))
        req = dict(MISSION_BASE[17]); req['x'] = x; req['target'] = x
        return _one(17, t, req)

    # ODOJ
    if l.strip() == 'odoj':
        return _one(54, t, dict(MISSION_BASE[54]))

    # Shalat Wajib → expand to 5 shalat missions
    if 'shalat wajib' in l:
        prayers = [
            ('subuh',   'Shalat Subuh'),
            ('dzuhur',  'Shalat Dzuhur'),
            ('ashar',   'Shalat Ashar'),
            ('maghrib', 'Shalat Maghrib'),
            ('isya',    'Shalat Isya'),
        ]
        result = []
        for prayer_type, title in prayers:
            req = dict(MISSION_BASE[67]); req['type'] = prayer_type
            result.append((67, title, req))
        return result

    # Amal Yaumi (Tahajjud, Dhuha, Qabliyah Subuh, …)
    aml_key = norm(re.sub(r'\(.*?\)', '', l))
    if aml_key in AMAL_YAUMI_TYPE:
        req = dict(MISSION_BASE[67]); req['type'] = AMAL_YAUMI_TYPE[aml_key]
        return _one(67, t, req)

    raise ValueError('Unmapped mission: ' + repr(t))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='Generate marathon PHP/JSON from CSV')
    ap.add_argument('csv_files', nargs='+', metavar='CSV')
    ap.add_argument('--marathon-id', '-m', required=True, type=int)
    ap.add_argument('--output', '-o', default=None,
                    help='Output file prefix (default: output/marathon_missions_<id>)')
    args = ap.parse_args()

    out_dir = Path('output')
    out_dir.mkdir(exist_ok=True)
    prefix = args.output or str(out_dir / ('marathon_missions_' + str(args.marathon_id)))
    items = []
    errors = []

    for csv_path in args.csv_files:
        path = Path(csv_path)
        if not path.exists():
            print('Error: ' + csv_path + ' not found', file=sys.stderr)
            sys.exit(1)

        with path.open(encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for lineno, row in enumerate(reader, 2):
                mission = (row.get('Misi') or '').strip()
                date_raw = (row.get('Tanggal') or '').strip()
                if not mission or not date_raw:
                    continue
                try:
                    date_iso = datetime.strptime(date_raw, '%A, %d %B %Y').date().isoformat()
                except ValueError:
                    print('  Warning (' + csv_path + ':' + str(lineno) + '): cannot parse date ' + repr(date_raw), file=sys.stderr)
                    continue
                try:
                    parsed = parse_mission(mission)
                except ValueError as e:
                    errors.append('  ' + csv_path + ':' + str(lineno) + ': ' + str(e))
                    continue

                for mission_id, mission_title, requirement in parsed:
                    items.append({
                        'marathon_id':      args.marathon_id,
                        'mission_id':       mission_id,
                        'mission_title':    mission_title,
                        'date':             date_iso,
                        'completion_point': 1,
                        'requirement':      requirement,
                        'link':             MISSION_LINK.get(mission_id, 'push:/home'),
                    })

    if errors:
        print('Errors found — fix these entries before output is generated:', file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)

    out_json = Path(prefix + '.json')
    out_php  = Path(prefix + '.php')

    out_json.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    out_php.write_text('<?php\n\nreturn ' + php_export(items) + ';\n', encoding='utf-8')

    print('Generated ' + str(len(items)) + ' missions -> ' + str(out_json) + '  ' + str(out_php))


if __name__ == '__main__':
    main()
