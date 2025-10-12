
import os
import pandas as pd
from typing import Dict

def run_load_excel_only(tables: Dict[str, pd.DataFrame], out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    for name, df in tables.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.copy().to_excel(os.path.join(out_dir, f"{name}.xlsx"), index=False)
