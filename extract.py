
import os, re, unicodedata
from typing import Tuple
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
FILE1 = os.environ.get("PMM_FILE1", os.path.join(BASE_DIR, "Inputs", "Indicadores Tractomula dia 2017 - 2025.xlsx"))
FILE2 = os.environ.get("PMM_FILE2", os.path.join(BASE_DIR, "Inputs", "DATOS_SAP_2017-2025.XLSX"))

def strip_accents(text: str) -> str:
    text = str(text)
    text = unicodedata.normalize('NFD', text)
    return ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"[^a-z0-9_]", "", re.sub(r"\s+", "_", strip_accents(str(c)).strip().lower())) for c in df.columns]
    return df

def read_all_sheets(xlsx_path: str) -> pd.DataFrame:
    xl = pd.ExcelFile(xlsx_path)
    frames = []
    for sh in xl.sheet_names:
        try:
            df = xl.parse(sh, dtype=object)
            df["__origen_hoja__"] = sh
            frames.append(df)
        except Exception as e:
            print(f"[WARN] No se pudo leer hoja {sh} en {os.path.basename(xlsx_path)}: {e}")
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["__origen_file__"] = os.path.basename(xlsx_path)
    return out

def run_extract() -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not os.path.exists(FILE1):
        raise FileNotFoundError(f"No se encuentra FILE1: {FILE1}")
    if not os.path.exists(FILE2):
        raise FileNotFoundError(f"No se encuentra FILE2: {FILE2}")
    df1_raw = read_all_sheets(FILE1)
    df2_raw = read_all_sheets(FILE2)
    return normalize_cols(df1_raw), normalize_cols(df2_raw)
