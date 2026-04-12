# GitHub Copilot Chat Prompt — CSV to marathon_missions

Bantu user menghasilkan payload `marathon_missions` dari CSV jadwal misi.

## Steps
- Tanyakan `marathon_id` jika belum ada.
- Jalankan command:

```bash
python generate_marathon_missions.py --marathon-id <ID>
```

- Jika user minta nama file custom, gunakan `--out-json` dan `--out-php`.
- Beri ringkasan mapping yang dipakai (`fasih_id`, `material_id`, `index` surah, dsb).
