"""Config-driven monthly refinery report ETL; Python 3.10+."""
import argparse
import calendar
import json
import logging
import re
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

LOG = logging.getLogger(__name__)


def period(path):
    match = re.search(r'(?<!\d)(0[1-9]|1[0-2])(\d{2})$', path.stem)
    if not match:
        raise ValueError(f'Expected MMYY suffix: {path.name}')
    return 2000 + int(match[2]), int(match[1])


def extract(path, sheet, mapping, skip_rows, day_column, sequential=False):
    year, month = period(path)
    df = pd.read_excel(path, sheet_name=sheet, engine='openpyxl')
    df = df.iloc[skip_rows:skip_rows + calendar.monthrange(year, month)[1]].copy()
    missing = set(mapping) - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if len(df) != calendar.monthrange(year, month)[1]:
        raise ValueError('Incomplete monthly row block')
    if sequential:
        days = pd.Series(range(1, len(df)+1), index=df.index)
    else:
        days = pd.to_numeric(df[day_column], errors='raise')
        if set(days) != set(range(1, len(df)+1)):
            raise ValueError('Day column must contain each day of month exactly once')
    dates = pd.to_datetime({'year': year, 'month': month, 'day': days})
    records = []
    for source, metric in mapping.items():
        raw = df[source]
        values = pd.to_numeric(raw, errors='coerce')
        invalid = raw.notna() & values.isna()
        for idx in df.index:
            value = values.loc[idx]
            status = 'invalid' if invalid.loc[idx] else ('missing' if pd.isna(value) else 'ok')
            records.append({'plant': sheet, 'date': dates.loc[idx], 'year': year,
                            'month': month, 'metric': metric, 'value': value,
                            'quality': status, 'source_file': path.name,
                            'source_row': int(idx)+2})
    return pd.DataFrame(records)


def run(input_dir, output_dir, config):
    files = sorted(p for p in input_dir.rglob('*.xlsx') if not p.name.startswith('~$'))
    if not files:
        raise ValueError('No Excel files found')
    frames, errors = [], []
    for path in files:
        for sheet, mapping in config['plants'].items():
            try:
                frames.append(extract(path, sheet, mapping, config['skip_rows'],
                                      config['day_column'], config.get('sequential_days', False)))
            except Exception as exc:
                errors.append({'file': path.name, 'sheet': sheet, 'error': str(exc)})
                LOG.error('%s / %s: %s', path.name, sheet, exc)
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(errors, columns=['file','sheet','error']).to_csv(output_dir/'errors.csv', index=False)
    if errors:
        raise ValueError('Extraction failed; master outputs not replaced. See errors.csv')
    data = pd.concat(frames, ignore_index=True)
    keys = ['plant','date','metric']
    if data.duplicated(keys).any():
        data.loc[data.duplicated(keys, keep=False)].to_csv(output_dir/'duplicates.csv', index=False)
        raise ValueError('Duplicate keys; master outputs not replaced. See duplicates.csv')
    data = data.sort_values(keys).reset_index(drop=True)
    quality = data.groupby(['plant','metric','quality']).size().reset_index(name='rows')
    monthly = data.groupby(['plant','year','month','metric']).value.agg(valid_days='count', mean='mean', maximum='max').reset_index()
    with TemporaryDirectory(dir=output_dir) as tmp:
        tmp = Path(tmp)
        data.to_csv(tmp/'master.csv', index=False)
        with pd.ExcelWriter(tmp/'master.xlsx', engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name='Data', index=False)
            quality.to_excel(writer, sheet_name='Quality', index=False)
            monthly.to_excel(writer, sheet_name='Monthly', index=False)
        with sqlite3.connect(tmp/'refinery.db') as conn:
            data.to_sql('production', conn, index=False)
            conn.execute('CREATE UNIQUE INDEX production_key ON production(plant,date,metric)')
            monthly.to_sql('monthly_summary', conn, index=False)
        for artifact in tmp.iterdir():
            artifact.replace(output_dir/artifact.name)
    LOG.info('Published %s observations from %s workbooks', len(data), len(files))
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('config.json'))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    if args.output.resolve().is_relative_to(args.input.resolve()):
        parser.error('Output must be outside input directory')
    run(args.input, args.output, json.loads(args.config.read_text()))
