# Industrial Production ETL Pipeline
Portfolio modernization of a 2023/2024 industrial training project. The PDF shows portions of a roughly 570-line script, not a complete source file. `original_excerpt.py` is a partial transcription with minor structural edits; `etl.py` is a new implementation, not the historical deployment.

## Quick start (Windows PowerShell or terminal)
```sh
python -m pip install -r requirements.txt
python generate_demo.py
python etl.py --input sample_data --output output --config config.json
```
The demo contains fictional data only. The config includes two readable P19 mappings from the report; it is not the complete refinery schema. For real workbooks, confirm sheet names, source columns, row offsets, units and day format, and extend config.json. If the day column is not numeric, adapt the parser or enable sequential_days only after confirming every day occupies exactly one row in order. Excel formula cells require cached values. No actual refinery data is included.

## Output
- master.csv / master.xlsx: normalized plant/date/metric observations for Power BI; missing values retained, invalid values flagged.
- refinery.db: SQLite production and monthly_summary tables with unique key index.
- errors.csv: extraction failures; duplicates.csv if duplicate keys detected.
- Excel Quality and Monthly sheets: counts, averages and maxima (no assumption that all metrics are additive).

The pipeline rebuilds from the full input archive on each successful run; keep historical files in input. Extraction or duplicate-key failures stop publication. Each output is staged and replaced individually, not as a cross-file transaction. Close open output workbooks before running. Use a separate output folder. In Power BI, import master.csv or the Data sheet and set date to Date, value to Decimal Number. Filter quality = ok for analysis. Refresh after rerunning the ETL.
