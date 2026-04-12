---
name: marathon-csv-to-marathon-missions
description: Gunakan skill ini saat user minta ubah CSV jadwal misi menjadi payload marathon_missions dengan marathon_id tertentu, lalu output dalam JSON dan/atau PHP array.
---

# Marathon CSV → marathon_missions

Skill ini untuk Claude agar bisa:
1. baca file CSV (kolom: `Tanggal`, `Misi`),
2. isi `marathon_id` dari input user,
3. hasilkan payload siap import (`marathon_missions_<id>.json` dan `marathon_missions_<id>.php`).

## Kapan dipakai
- User menyebut: "buat payload marathon_missions dari CSV"
- User menyebut `marathon_id` tertentu
- User minta format JSON atau PHP array

## Langkah kerja
1. Pastikan file CSV tersedia (default: `untuk isi misi.csv`).
2. Jalankan generator:

```bash
python generate_marathon_missions.py --marathon-id <ID>
```

Contoh:

```bash
python generate_marathon_missions.py --marathon-id 55
```

3. Kalau user mau nama file khusus, gunakan:

```bash
python generate_marathon_missions.py \
  --csv "untuk isi misi.csv" \
  --marathon-id 55 \
  --out-json custom_55.json \
  --out-php custom_55.php
```

## Output
- JSON: `marathon_missions_<id>.json`
- PHP array: `marathon_missions_<id>.php` (format `<?php return [ ... ];`)

## Agent profiles (opsional)
- `agents/claude.md` untuk Claude
- `agents/cursor.md` untuk Cursor
- `agents/copilot.md` untuk Copilot Chat
- `agents/openai.yaml` untuk metadata UI/agent registry

## Validasi cepat
```bash
python -m json.tool marathon_missions_<id>.json
php -l marathon_missions_<id>.php
```

## Catatan mapping
- `murajaah` (surah tertentu) → requirement pakai `fasih_id`
- `material` (bab tertentu) → requirement pakai `material_id`
- `murottal/khatam` surah tertentu → requirement pakai `index` surah
- `setoran ayat` (mudabbir) → requirement template mudabbir + `sura_index` diturunkan dari `suras.sql`

## Mapping `link`
- `push:/quran`
- `push:/alurBelajar`
- `push:/murajaahHome`
- `push:/kalender`
- `push:/zikir`
- `push:/setorAyatHome:{"index":<index>}`
