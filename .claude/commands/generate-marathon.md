Generate marathon mission PHP and JSON files from CSV input.

## Steps

1. Ask the user for the **marathon_id** (integer). Example: `94`

2. Ask the user for the **CSV file path(s)**. They can provide one or more files separated by spaces or newlines. Available files in the project:
   - `untuk isi misi.csv`
   - `untuk isi misi2.csv`

3. Optionally ask for a custom **output prefix** (if they want a different filename than the default `output/marathon_missions_<id>`). Skip if they don't care.

4. Run the generator script with the collected inputs:
   ```bash
   python3 generate_marathon.py "<csv1>" ["<csv2>" ...] --marathon-id <id> [--output <prefix>]
   ```

5. Report the result: how many missions were generated and the output file paths. If there are errors (unmapped missions), show them clearly and tell the user which lookup table to update in `generate_marathon.py`.

## Notes
- The output always goes to the `output/` folder unless `--output` is specified.
- If the user provides both CSVs, their missions are merged into a single output file in date order.
- Common errors and fixes:
  - `FASIH_BY_SURA missing key` → add the surah name + fasih_id to `FASIH_BY_SURA`
  - `KHATAM_INDEX missing key` → add the surah name + surah number to `KHATAM_INDEX`
  - `SURA_INDEX missing key` → add the surah name + surah number to `SURA_INDEX`
  - `DHIKR_TYPE missing key` → add the dhikr variant to `DHIKR_TYPE`
  - `Unmapped mission` → add a new pattern to `parse_mission()` in `generate_marathon.py`
