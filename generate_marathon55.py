import csv, json, re
from datetime import datetime
from pathlib import Path

CSV_FILE = Path('untuk isi misi.csv')
OUT_JSON_FILE = Path('marathon_missions_55.json')
OUT_PHP_FILE = Path('marathon_missions_55.php')

def php_export(value, indent=0):
    sp = '  ' * indent
    if isinstance(value, dict):
        if not value:
            return '[]'
        lines = ['[']
        for k, v in value.items():
            lines.append(f"{'  ' * (indent + 1)}{json.dumps(str(k), ensure_ascii=False)} => {php_export(v, indent + 1)},")
        lines.append(f"{sp}]")
        return '\n'.join(lines)
    if isinstance(value, list):
        if not value:
            return '[]'
        lines = ['[']
        for item in value:
            lines.append(f"{'  ' * (indent + 1)}{php_export(item, indent + 1)},")
        lines.append(f"{sp}]")
        return '\n'.join(lines)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return 'null'
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False)

FASIH_BY_SURA = {
    'al-alaq': 67,
    'al-mulk': 99999,
    'al-lail': 71,
    'al-ghasyiyah': 75,
    'al-infitar': 81,
    'al-jinn': 100004,
    'al-lahab': 51,
    'at-takwir': 82,
    'al-fajr': 74,
    'al-fatihah': 47,
}

SURA_INDEX = {
    'ali-imran': 3,
    'al-kahf': 18,
    'al-mulk': 67,
    'ar-rahman': 55,
    'al-baqarah': 2,
    'al-waqiah': 56,
    "al-waqi'ah": 56,
}

KHATAM_INDEX = {
    'al-alaq': 96,
    "al-'alaq": 96,
    'al-mulk': 67,
    'ad-dukhan': 44,
    'an-naba': 78,
    'an-naziat': 79,
    "an-nazi'at": 79,
    'at-takatsur': 102,
}

MATERIAL_ID = {'tajwid': 73, 'hijaiyah': 1, 'tahsin': 42}

MISSION_BASE = {
    1: {"target": 8, "point": 20, "x": 8, "pro": 1},
    2: {"target": 40, "point": 5, "x": 40, "pro": 1},
    3: {"target": 30, "point": 25, "x": 30, "pro": 1},
    8: {"target": 1, "point": 5, "x": 1, "pro": 1},
    16: {"target": 1, "point": 10, "x": 1, "pro": 1},
    29: {"target": 15, "point": 15, "x": 15, "pro": 1},
    30: {"target": 15, "point": 20, "fasih_id": 72, "pro": 1},
    31: {"target": 10, "point": 10, "x": 10, "pro": 1, "from_index": "5673", "to_index": "6236"},
    32: {"target": 5, "point": 15, "x": 70, "exercise_count": 5, "pro": 1},
    33: {"target": 1, "point": 50, "exam_id": 29, "material_id": 73, "pro": 1},
    34: {"target": 6, "point": 5, "x": 6, "pro": 1},
    35: {"x": 5, "target": 5, "point": 10, "material_id": 2, "pro": 1},
    36: {"target": 1, "point": 15, "dhikr": "morning", "pro": 0},
    37: {"target": 1, "point": 10, "pro": 0},
    38: {"target": 5, "point": 50, "x": 5, "pro": 0},
    39: {"target": 11, "point": 50, "index": 93, "pro": 0},
    40: {"target": 1, "point": 100, "pro": 0},
    44: {"target": 129, "point": 100, "index": 9, "pro": 0},
    49: {"target": 1, "point": 100, "pro": 1},
}

def norm(s: str) -> str:
    s = s.lower().strip()
    s = s.replace('’', "'").replace('‘', "'").replace('`', "'")
    s = s.replace('qur’an', 'quran')
    s = re.sub(r"[^a-z0-9']+", '-', s)
    return re.sub('-+', '-', s).strip('-')


def parse_mission(text: str):
    t = text.strip()
    l = t.lower()

    if m := re.search(r'setoran ayat\s+(\d+)\s+ayat', l):
        x = int(m.group(1))
        req = dict(MISSION_BASE[31]); req['x']=x; req['target']=x
        return 31, t, req

    if m := re.search(r'mendapatkan bintang 5 .*? (\d+) kali', l):
        x = int(m.group(1)); req = dict(MISSION_BASE[3]); req['x']=x; req['target']=x
        return 3, t, req

    if m := re.search(r'mendapatkan bintang 3 .*? (\d+) kali', l):
        x = int(m.group(1)); req = dict(MISSION_BASE[29]); req['x']=x; req['target']=x
        return 29, t, req

    if m := re.search(r'murajaah\s+(\d+)\s+surah', l):
        x = int(m.group(1)); req = dict(MISSION_BASE[1]); req['x']=x; req['target']=x
        return 1, t, req

    if m := re.search(r'murajaah\s+(\d+)\s+ayat', l):
        x = int(m.group(1)); req = dict(MISSION_BASE[2]); req['x']=x; req['target']=x
        return 2, t, req

    if m := re.search(r'murajaah surah\s+(.+)$', l):
        sura = norm(m.group(1)); req = dict(MISSION_BASE[30]); req['fasih_id']=FASIH_BY_SURA[sura]
        return 30, t, req

    if m := re.search(r'bagikan pencapaian belajar\s+(\d+)\s+kali', l):
        x = int(m.group(1)); req = dict(MISSION_BASE[8]); req['x']=x; req['target']=x
        return 8, t, req

    if m := re.search(r'menyelesaikan\s+(\d+)\s+materi di bab\s+(.+)$', l):
        x = int(m.group(1)); chap = norm(m.group(2)); req = dict(MISSION_BASE[35]); req['x']=x; req['target']=x; req['material_id']=MATERIAL_ID[chap]
        return 35, t, req

    if m := re.search(r'menyelesaikan\s+(\d+)\s+materi$', l):
        x = int(m.group(1)); req = dict(MISSION_BASE[16]); req['x']=x; req['target']=x
        return 16, t, req

    if m := re.search(r'mengulang\s+(\d+)\s+materi', l):
        x = int(m.group(1)); req = dict(MISSION_BASE[34]); req['x']=x; req['target']=x
        return 34, t, req

    if m := re.search(r'dapatkan skor\s+(\d+)%\s+dalam\s+(\d+)\s+latihan', l):
        score, cnt = map(int, m.groups()); req = dict(MISSION_BASE[32]); req['x']=score; req['exercise_count']=cnt; req['target']=cnt
        return 32, t, req

    if 'kerjakan ujian bab' in l:
        req = dict(MISSION_BASE[33]); req['material_id'] = MATERIAL_ID['tajwid']
        return 33, t, req

    if 'mencatat amalan hari ini' in l:
        return 37, t, dict(MISSION_BASE[37])

    if 'kuis spesial' in l or 'misi sebisaku' in l:
        return 49, t, dict(MISSION_BASE[49])

    if 'fitur kurban' in l:
        return 40, t, dict(MISSION_BASE[40])

    if m := re.search(r'membaca dan menyelesaikan counter dzikir\s+(.+)$', l):
        part = norm(m.group(1))
        map_dhikr = {'pagi': 'morning', 'petang': 'evening', 'setelah-shalat': 'after_prayer'}
        req = dict(MISSION_BASE[36]); req['dhikr'] = map_dhikr[part]
        return 36, t, req

    if m := re.search(r"mendengarkan murottal di qur['’]?an sebanyak\s+(\d+)\s+surah", l):
        x = int(m.group(1)); req = dict(MISSION_BASE[38]); req['x']=x; req['target']=x
        return 38, t, req

    if m := re.search(r'mendengarkan murottal\s+(.+)$', l):
        sura = norm(m.group(1))
        sura = re.sub(r'^surah-', '', sura)
        req = dict(MISSION_BASE[39]); req['index']=SURA_INDEX[sura]; req['target']=SURA_INDEX[sura]
        return 39, t, req

    if m := re.search(r'membaca surah\s+(.+?)\s+di fitur khatam', l):
        sura = norm(m.group(1)); req = dict(MISSION_BASE[44]); req['index']=KHATAM_INDEX[sura]; req['target']=KHATAM_INDEX[sura]
        return 44, t, req

    raise ValueError(f'Unmapped mission: {t}')

items = []
with CSV_FILE.open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        mission = (row['Misi'] or '').strip()
        if not mission:
            continue
        date_iso = datetime.strptime(row['Tanggal'].strip(), '%A, %d %B %Y').date().isoformat()
        mission_id, mission_title, requirement = parse_mission(mission)
        items.append({
            'marathon_id': 55,
            'date': date_iso,
            'mission_id': mission_id,
            'mission_title': mission_title,
            'completion_point': requirement.get('point', 0),
            'requirement': requirement
        })

OUT_JSON_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n')
OUT_PHP_FILE.write_text("<?php\n\nreturn " + php_export(items) + ";\n")

print(f'generated {len(items)} missions -> {OUT_JSON_FILE} and {OUT_PHP_FILE}')
