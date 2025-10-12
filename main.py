
import os, pandas as pd
from extract import run_extract
from transform import run_transform
from load import run_load_excel_only
from model import build_ml_tables, train_eval_rf

OUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")

def main():
    df1, df2 = run_extract()
    tables = run_transform(df1, df2)

    # Usar la tabla limpia para ML
    ml_equipo_mes_clean = build_ml_tables(tables["fct_mes_equipo_clean"])
    ml_equipo_mes = ml_equipo_mes_clean.copy()

    to_export = dict(tables)
    to_export.update({
        "ml_equipo_mes": ml_equipo_mes,
        "ml_equipo_mes_clean": ml_equipo_mes_clean,
    })

    run_load_excel_only(to_export, OUT_DIR)

    metrics = train_eval_rf(ml_equipo_mes_clean)
    if metrics["report"] is not None:
        print("\n--- Evaluación del modelo (PMM1 vs no-PMM1) ---")
        print(metrics["report"])
        print("Matriz de confusión:\n", metrics["cm"])

    # QC simple
    fact = to_export["fct_mes_equipo_clean"]
    print("\nQC: filas con OM_total>0:", int((fact["om_total"]>0).sum()))
    print("QC: filas con toneladas>0:", int((fact["toneladas_total"]>0).sum()))

    return to_export, metrics

if __name__ == "__main__":
    main()
