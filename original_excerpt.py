"""Partial transcription from report pages 19–20; not the full original program.
Private network paths omitted. The clipped date expression and missing mapping
sections are intentionally not reconstructed as original code.
"""
import pandas as pd
import os
from glob import glob
from openpyxl import load_workbook
from openpyxl.styles import Font, Border
import re
import calendar

# Readable beginning of extract_data (page 19); excerpt ends before later mappings.
def extract_data_excerpt(file_path, sheet_name, selected_columns):
    file_name = os.path.basename(file_path)
    match = re.search(r'(\d{2})(\d{2})', file_name)
    if match:
        month_number = int(match.group(1))
        month_name = calendar.month_name[month_number]
        year = int(match.group(2))
        full_year = f'20{year}'
        month_year = f'{month_name}-{year}'
    else:
        raise ValueError('Unable to extract month and year from file name')
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    rows_to_remove = [0, 1, 2, 3, 4, 5, 37] + list(range(38, 80))
    df = df.drop(rows_to_remove, axis=0, errors='ignore')
    selected_data = df[selected_columns] if all(col in df.columns for col in selected_columns) else pd.DataFrame()
    selected_data = selected_data[selected_columns]
    selected_data = selected_data.fillna(0)
    selected_data.insert(1, 'Month', month_name)
    selected_data.insert(2, 'Year', full_year)
    selected_data = selected_data.drop(columns=['DAILY PRODUCTION REPORT'], errors='ignore')
    selected_data.insert(0, 'Plant', f'{sheet_name}')
    # Remaining original code not fully visible. Return added for excerpt usability.
    return selected_data
