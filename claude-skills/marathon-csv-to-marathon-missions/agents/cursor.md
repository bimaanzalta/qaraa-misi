# Cursor Agent Rules — Marathon Mission Generator

Gunakan workspace script `generate_marathon_missions.py` untuk mengubah CSV menjadi payload misi.

## Workflow
1. Pastikan file CSV ada (default: `untuk isi misi.csv`).
2. Jalankan generator:

```bash
python generate_marathon_missions.py --marathon-id <ID>
```

3. Validasi output:

```bash
python -m json.tool marathon_missions_<id>.json
php -l marathon_missions_<id>.php
```

4. Laporkan jumlah item yang berhasil digenerate.

## Jangan
- Jangan edit payload manual kalau generator masih bisa dipakai.
- Jangan ubah mapping mission tanpa menjelaskan alasan.
