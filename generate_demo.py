"""Generate fictional example workbooks; not actual company data."""
import calendar
from pathlib import Path
import pandas as pd

out = Path('sample_data')
out.mkdir(exist_ok=True)
for year, month in [(2023, 12), (2024, 2)]:
    days = list(range(1, calendar.monthrange(year, month)[1]+1))
    df = pd.DataFrame({'DAILY PRODUCTION REPORT': days, 'Unnamed: 1': [100+d for d in days], 'Unnamed: 2': [200+d for d in days]})
    df.loc[0, 'Unnamed: 2'] = None
    df = pd.concat([pd.DataFrame(index=range(6)), df], ignore_index=True)
    df.to_excel(out / f'Refinery Daily Reports {month:02d}{year%100:02d}.xlsx', sheet_name='P19', index=False)
