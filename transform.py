
import numpy as np
import pandas as pd
import re
import unicodedata

def _strip_accents(text: str) -> str:
    text = str(text)
    text = unicodedata.normalize('NFD', text)
    return ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')

def canonicalize_equipo(val) -> str:
    if pd.isna(val):
        return ""
    s = _strip_accents(str(val)).upper().strip()
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    tokens = re.findall(r"[A-Z0-9]+", s)
    if not tokens:
        return s.replace(" ", "")
    core = max(tokens, key=len)
    compact = "".join(tokens)
    return core if len(core) >= 3 else compact

def find_first_match(columns, patterns) -> str:
    for p in patterns:
        for c in columns:
            if p in c:
                return c
    return ""

def coerce_datetime(s: pd.Series) -> pd.Series:
    try:
        return pd.to_datetime(s, errors="coerce", dayfirst=True)
    except Exception:
        return pd.to_datetime(s, errors="coerce")

def add_year_month(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy()
    if date_col and date_col in df.columns:
        df["year"] = df[date_col].dt.year
        df["month"] = df[date_col].dt.month
    return df

def parse_mes_nombre(x):
    if pd.isna(x): return np.nan
    s = str(x).strip().lower()
    mapa = {
        "enero":1,"ene":1,"january":1,"jan":1,
        "febrero":2,"feb":2,"february":2,
        "marzo":3,"mar":3,"march":3,
        "abril":4,"abr":4,"apr":4,"april":4,
        "mayo":5,"may":5,
        "junio":6,"jun":6,"june":6,
        "julio":7,"jul":7,"july":7,
        "agosto":8,"ago":8,"aug":8,"august":8,
        "septiembre":9,"sept":9,"sep":9,"september":9,
        "octubre":10,"oct":10,"october":10,
        "noviembre":11,"nov":11,"november":11,
        "diciembre":12,"dic":12,"dec":12,"december":12
    }
    return mapa.get(s, pd.to_numeric(x, errors="coerce"))

def split_month_year(val):
    if pd.isna(val): return (np.nan, np.nan)
    s = str(val).strip()
    try:
        dt = pd.to_datetime(val, errors="raise")
        return dt.month, dt.year
    except Exception:
        pass
    if re.match(r"^\d{1,2}\.\d{4}$", s):
        m,y = s.split(".",1); return pd.to_numeric(m, errors="coerce"), pd.to_numeric(y, errors="coerce")
    if re.match(r"^\d{1,2}/\d{4}$", s):
        m,y = s.split("/",1); return pd.to_numeric(m, errors="coerce"), pd.to_numeric(y, errors="coerce")
    if re.match(r"^\d{4}-\d{1,2}$", s):
        y,m = s.split("-",1); return pd.to_numeric(m, errors="coerce"), pd.to_numeric(y, errors="coerce")
    m = re.match(r"^([A-Za-zñÑáéíóúÁÉÍÓÚ]+)\s+(\d{{4}})$", s)
    if m:
        mm = parse_mes_nombre(m.group(1))
        yy = pd.to_numeric(m.group(2), errors="coerce")
        return mm, yy
    mm = parse_mes_nombre(s)
    return mm, np.nan

def run_transform(df1: pd.DataFrame, df2: pd.DataFrame):
    # Llave equipo
    key1 = find_first_match(df1.columns, ["tractor", "tractomula", "equipo"])
    key2 = find_first_match(df2.columns, ["equipo", "tractor", "tractomula"])
    df1["equipo_raw"] = df1[key1] if key1 else ""
    df2["equipo_raw"] = df2[key2] if key2 else ""
    df1["equipo"] = df1["equipo_raw"].astype(str).apply(canonicalize_equipo)
    df2["equipo"] = df2["equipo_raw"].astype(str).apply(canonicalize_equipo)

    # Fechas indicadores
    date1 = find_first_match(df1.columns, ["fecha_de_movimiento", "fecha_movimiento", "fecha", "periodo", "dia"])
    if not date1:
        df1["fecha_mov"] = pd.NaT
        date1 = "fecha_mov"
    df1[date1] = coerce_datetime(df1[date1])
    df1 = add_year_month(df1, date1)

    # Fechas SAP
    candidate_dates2 = [c for c in df2.columns if ("fecha" in c) or (c.endswith("_date"))]
    date2 = candidate_dates2[0] if candidate_dates2 else ""
    if date2:
        df2[date2] = coerce_datetime(df2[date2])
        df2 = add_year_month(df2, date2)

    mes2 = find_first_match(df2.columns, ["mes"])
    ano2 = find_first_match(df2.columns, ["ano", "anio", "year"])

    if ("year" not in df2.columns) or ("month" not in df2.columns) or df2["year"].isna().all():
        if "month" in df2.columns:
            tmp = df2["month"].apply(split_month_year)
            df2["month_parsed"] = [t[0] for t in tmp]
            df2["year_parsed"] = [t[1] for t in tmp]
            if "year" not in df2.columns or df2["year"].isna().all():
                df2["year"] = df2["year_parsed"]
            df2["month"] = pd.to_numeric(df2["month_parsed"], errors="coerce")
        elif mes2 or ano2:
            if mes2:
                tmp2 = df2[mes2].apply(split_month_year)
                df2["month"] = pd.to_numeric([t[0] for t in tmp2], errors="coerce")
                if ("year" not in df2.columns) or df2["year"].isna().all():
                    df2["year"] = pd.to_numeric([t[1] for t in tmp2], errors="coerce")
            if ano2:
                df2["year"] = pd.to_numeric(df2[ano2], errors="coerce")

    # CLASE y duración
    clase2 = find_first_match(df2.columns, ["clase"])
    df2["clase"] = df2[clase2].astype(str).str.upper().str.strip() if clase2 else np.nan

    ini2 = find_first_match(df2.columns, ["fecha_inicio", "inicio", "fecha_creacion"])
    fin2 = find_first_match(df2.columns, ["fecha_fin", "fin", "fecha_cierre"])
    if ini2:
        df2[ini2] = coerce_datetime(df2[ini2])
    if fin2:
        df2[fin2] = coerce_datetime(df2[fin2])
    if ini2 and fin2:
        df2["dias_om"] = (df2[fin2] - df2[ini2]).dt.days
    else:
        dur2 = find_first_match(df2.columns, ["dias_om", "dias", "duracion", "tiempo", "dias_or"])
        df2["dias_om"] = pd.to_numeric(df2[dur2], errors="coerce") if dur2 else np.nan

    # Toneladas
    ton1 = find_first_match(df1.columns, ["peso_neto", "tonelada", "tn", "tm", "peso", "produccion", "carga"])
    df1["toneladas"] = pd.to_numeric(df1[ton1], errors="coerce") if ton1 else np.nan

    # Normalizar numéricas
    for col in ["year","month"]:
        if col not in df1.columns: df1[col] = np.nan
        if col not in df2.columns: df2[col] = np.nan
    df1["year"] = pd.to_numeric(df1["year"], errors="coerce")
    df1["month"] = pd.to_numeric(df1["month"], errors="coerce")
    df2["year"] = pd.to_numeric(df2["year"], errors="coerce")
    df2["month"] = pd.to_numeric(df2["month"], errors="coerce")

    # Aggregations
    agg1 = (df1.groupby(["equipo","year","month"], dropna=False, as_index=False)
              .agg(toneladas_total=("toneladas","sum"),
                   dias_registros=("equipo","count")))

    def is_pmm1(x): return 1 if str(x).upper().strip() == "PMM1" else 0
    def is_pmm2(x): return 1 if str(x).upper().strip() == "PMM2" else 0

    agg2 = (df2.groupby(["equipo","year","month"], dropna=False, as_index=False)
              .agg(om_total=("equipo","count"),
                   om_pmm1=("clase", lambda s: int(np.nansum([is_pmm1(v) for v in s]))),
                   om_pmm2=("clase", lambda s: int(np.nansum([is_pmm2(v) for v in s]))),
                   dias_om_prom=("dias_om","mean")))

    # Merge
    fact = pd.merge(agg1, agg2, on=["equipo","year","month"], how="outer", suffixes=("_ind","_sap"))
    for c in ["om_total","om_pmm1","om_pmm2"]:
        fact[c] = fact[c].fillna(0).astype(int)
    fact["toneladas_total"] = fact["toneladas_total"].fillna(0.0)
    fact["dias_om_prom"] = fact["dias_om_prom"].astype(float)

    # Dim equipos
    dim_equipos = fact[["equipo"]].drop_duplicates().reset_index(drop=True)
    dim_equipos["equipo_id"] = dim_equipos.index + 1
    fact = fact.merge(dim_equipos, on="equipo", how="left")
    fact = fact[["equipo_id","equipo","year","month","toneladas_total","dias_registros",
                 "om_total","om_pmm1","om_pmm2","dias_om_prom"]]

    # ====== Clean + reglas de limpieza ======
    fact_clean = fact.copy()
    fact_clean["year"] = pd.to_numeric(fact_clean["year"], errors="coerce")
    fact_clean["month"] = pd.to_numeric(fact_clean["month"], errors="coerce")

    def fix_year(y):
        if pd.isna(y): return np.nan
        if 2000 <= y <= 2100: return int(y)
        if 100 <= y < 1000: return int(y * 10)
        return np.nan

    fact_clean["year"] = fact_clean["year"].apply(fix_year)
    fact_clean.loc[~fact_clean["month"].between(1,12), "month"] = np.nan

    fact_clean = fact_clean.dropna(subset=["year","month"])
    fact_clean["year"] = fact_clean["year"].astype(int)
    fact_clean["month"] = fact_clean["month"].astype(int)

    # Eliminar equipos sin toneladas (>0) y sin nombre
    fact_clean = fact_clean[fact_clean["toneladas_total"].fillna(0) > 0]
    fact_clean = fact_clean[fact_clean["equipo"].astype(str).str.strip() != ""]

    # Periodo
    fact_clean["periodo"] = pd.to_datetime(dict(year=fact_clean["year"], month=fact_clean["month"], day=1))

    # Sync dimensión y detalle mantenimiento
    equipos_validos = set(fact_clean["equipo"].unique())
    dim_equipos = dim_equipos[dim_equipos["equipo"].isin(equipos_validos)].reset_index(drop=True)

    mant_detalle_cols = [c for c in ["equipo","year","month","clase","dias_om"] if c in df2.columns]
    mantenimiento_detalle = df2[mant_detalle_cols].copy() if mant_detalle_cols else pd.DataFrame()
    if not mantenimiento_detalle.empty:
        mantenimiento_detalle = mantenimiento_detalle[mantenimiento_detalle["equipo"].isin(equipos_validos)].reset_index(drop=True)

    return {
        "dim_equipos": dim_equipos,
        "fct_mes_equipo": fact,
        "fct_mes_equipo_clean": fact_clean,
        "mantenimiento_detalle": mantenimiento_detalle
    }
