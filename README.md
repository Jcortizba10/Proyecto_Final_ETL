
# 🚜 PMM Pipeline — ETL + Modelo (Excel‑only) para Mantenimiento de Tractomulas

Este proyecto implementa un **pipeline modular de datos y ML** para integrar información operacional (indicadores de transporte) y de mantenimiento (SAP), **agregar por equipo–mes**, limpiar registros inconsistentes y **exportar todo a Excel** (uno por tabla). Además, genera un dataset con *lags* e **entrena un modelo** que estima la probabilidad de **mantenimiento correctivo (CLASE = PMM1)**.

> **Nota:** Por solicitud, se eliminó SQLite. Todas las salidas se generan como Excel (`.xlsx`).

---

## 🧭 Objetivo

1. **Unificar**: `Indicadores Tractomula día` (producción) con `DATOS_SAP` (mantenimiento) por **equipo** y **año/mes**.  
2. **Limpiar**: estandarizar claves de equipo, parsear mes/año robustamente, descartar filas imposibles de cruzar y **equipos sin toneladas**.  
3. **Analizar**: producir tablas limpias para **Power BI** y un dataset ML con *lags* por equipo.  
4. **Predecir**: entrenar un **RandomForest** para estimar riesgo de **PMM1**.

---

## 📁 Estructura del repositorio

```
pmm_pipeline_mod/
├─ extract.py              # Extracción desde Excel (todas las hojas) + normalización de nombres
├─ transform.py            # Unión por equipo–mes, agregaciones, reglas de limpieza
├─ load.py                 # Carga en Excel (un .xlsx por tabla)  ← Excel‑only
├─ model.py                # Dataset ML (lags) + entrenamiento RandomForest (PMM1)
├─ main.py                 # Orquestador: Extract → Transform → Model → Load (Excel)
├─ requirements.txt        # Dependencias del proyecto
├─ .vscode/launch.json     # Configuración VS Code con variables de entorno para rutas
├─ .gitignore              # Ignora data/ y outputs en Git
├─ LICENSE                 # MIT
├─ README.md               # Este documento
├─ data/                   # (vacía) coloca aquí los Excel de entrada
└─ outputs_excel_only/     # (se llena al ejecutar) Excel por tabla
```

---

## 📥 Entradas requeridas

Coloca estos archivos dentro de `pmm_pipeline_mod/data/` (o define variables de entorno: `PMM_FILE1`, `PMM_FILE2`).

- `Indicadores Tractomula dia 2017 - 2025.xlsx`
- `DATOS_SAP_2017-2025.XLSX`

> Se leen **todas las hojas** de cada archivo, se **apilan** y se normalizan los nombres de columna (minúsculas, sin tildes, guiones bajos).

---

## 🔧 Transformaciones clave

### 1) Llave canónica de `equipo`
Para asegurar el cruce:
- **Upper**, sin tildes, limpieza de separadores, y
- Se extrae el **token alfanumérico dominante** (p.ej., `"Tractomula 123"` → `123`; `"DP-2911020104"` → `DP2911020104`).

> Implementado en `transform.py` con `canonicalize_equipo()`.

### 2) Fechas y período (año/mes)
- Indicadores: se detecta `fecha_de_movimiento`/`fecha` y se extraen `year` y `month`.
- SAP: si no hay fecha directa, se **parsea** la columna `mes` o `month` con formatos:
  - `m.yyyy`, `mm/yyyy`, `yyyy-mm`, `"Enero 2020"` o **fechas Excel**.
- Función `split_month_year()` se encarga del parseo robusto.

### 3) Agregaciones por **equipo–año–mes**
- **Indicadores →** `toneladas_total` (suma) y `dias_registros` (conteo).
- **SAP →** `om_total` (conteo), `om_pmm1` (CLASE = PMM1), `om_pmm2` (CLASE = PMM2), `dias_om_prom` (promedio).

### 4) Limpieza (tabla **clean**)
Se descartan:
- Filas **sin `year` o `month` válidos** (fuera de 2000–2100 o 1–12).
- **Equipos sin toneladas** (`toneladas_total <= 0` o NaN).
- Equipos con nombre vacío.

Se recalcula `periodo = DATE(year, month, 1)` y se sincroniza `dim_equipos` y `mantenimiento_detalle` a los **equipos válidos**.

---

## 🧱 Salidas (Excel)

Se generan en `outputs_excel_only/`:

- `dim_equipos.xlsx`  
  - Lista de equipos válidos (`equipo_id`, `equipo`).
- `fct_mes_equipo.xlsx`  
  - Hechos por equipo–año–mes **antes** de limpieza estricta.
- `fct_mes_equipo_clean.xlsx` ✅ *(usar en Power BI / ML)*  
  - Igual que la anterior, pero sin filas no-cruzables o sin producción.
- `mantenimiento_detalle.xlsx`  
  - Subconjunto útil para auditorías (`equipo`, `year`, `month`, `clase`, `dias_om`) si existe.
- `ml_equipo_mes.xlsx` y `ml_equipo_mes_clean.xlsx`  
  - Dataset ML con *lags* por equipo (la versión **clean** parte de `fct_mes_equipo_clean`).

---

## 📊 Esquema de columnas

### `fct_mes_equipo_clean`
| Columna            | Tipo    | Descripción                                              |
|--------------------|---------|----------------------------------------------------------|
| `equipo_id`        | int     | Id de `dim_equipos`                                      |
| `equipo`           | string  | Clave canónica del equipo                                |
| `year`             | int     | Año (2000–2100)                                          |
| `month`            | int     | Mes (1–12)                                               |
| `periodo`          | date    | Primer día del mes                                       |
| `toneladas_total`  | float   | Suma de toneladas/producción del mes (indicadores)       |
| `dias_registros`   | int     | # de filas en indicadores para ese equipo–mes            |
| `om_total`         | int     | Ordenes de mantto totales (SAP)                          |
| `om_pmm1`          | int     | Ordenes CLASE = PMM1 (correctivo)                        |
| `om_pmm2`          | int     | Ordenes CLASE = PMM2 (programado)                        |
| `dias_om_prom`     | float   | Promedio de duración de OM (días)                        |

### `ml_equipo_mes_clean`
- Todas las columnas de `fct_mes_equipo_clean` +
- Features con *lag 1* por equipo:  
  `toneladas_total_lag1`, `om_total_lag1`, `om_pmm1_lag1`, `om_pmm2_lag1`, `dias_om_prom_lag1`  
- Target: `y_pmm1` (1 si hubo algún PMM1 en el mes, 0 en caso contrario)

---

## 🤖 Modelo (PMM1 vs no‑PMM1)

- **Algoritmo**: `RandomForestClassifier` (con `class_weight="balanced_subsample"`).  
- **Features**: lags de las variables operacionales y de mantenimiento + `toneladas_total`.  
- **Label**: `y_pmm1` (1 si `om_pmm1 > 0` en el mes).  
- **Evaluación**: *time‑based split* (último 10% de periodos para test si hay suficientes meses; si no, 80/20).  
- **Métricas impresas en consola**: `classification_report` y `confusion_matrix`.

> El modelo es un **baseline** para riesgo de correctivo. Puede ampliarse con más lags, ventanas móviles, y variables exógenas (horas de uso, combustible, etc.).

---

## ▶️ Cómo ejecutar

### Opción A: Terminal

```bash
cd pmm_pipeline_mod
python -m venv venv
# Activar venv:
#   Windows: venv\Scripts\activate
#   Mac/Linux: source venv/bin/activate

pip install -r requirements.txt

# Coloca los Excel en ./data/ o usa variables de entorno:
#   set PMM_FILE1=...  (Windows)   | export PMM_FILE1=... (Mac/Linux)
#   set PMM_FILE2=...
python main.py
```

**Resultado**: Excel por tabla dentro de `outputs_excel_only/`.

### Opción B: VS Code (recomendada)
- Se incluye `.vscode/launch.json` con las rutas por defecto a `./data/`.
- Abre la carpeta del repo en VS Code → pestaña **Run and Debug** → **Run PMM Pipeline**.

---

## 🧪 Validación rápida (QC)

En `main.py` se imprimen contadores de control:
- `filas con OM_total>0`
- `filas con toneladas>0`

> Si alguno da 0, revisa el **parseo de mes** y la **llave canónica**.

---

## 🧷 Power BI (sugerencias)

- Importa `fct_mes_equipo_clean.xlsx` (o todas las tablas que necesites).  
- Crea la columna **Periodo** si no deseas usar el `periodo` ya generado: `DATE([year], [month], 1)`.  
- Relaciona con `dim_equipos` por `equipo` o `equipo_id`.  
- Métricas sugeridas: toneladas por equipo, tasa de PMM1, duración promedio de OM, etc.

---

## 🧹 Reglas de limpieza aplicadas (resumen)

1. `year` en [2000, 2100] y `month` en [1, 12].  
2. `toneladas_total > 0`.  
3. Sin `equipo` vacío.  
4. `dim_equipos` y `mantenimiento_detalle` se filtran a **equipos válidos**.

---

## 🆘 Solución de problemas

- **“No se encuentra FILE1/FILE2”** → verifica rutas en `data/` o define las variables `PMM_FILE1` y `PMM_FILE2`.  
- **Todos los `om_*` en 0** → típico de un problema de **parseo de mes** o **llave de equipo**. Revisa `transform.py`:  
  - `split_month_year()` soporta `m.yyyy`, `mm/yyyy`, `yyyy-mm`, `"Enero 2020"` y fechas Excel.  
  - `canonicalize_equipo()` estandariza la clave (puedes adaptar reglas según tu nomenclatura).  
- **Excel muy grandes** → Power BI puede importar directamente `.xlsx`. Si necesitas un único libro con varias hojas, ver **Siguiente sección**.

---

## 🧩 Extensiones opcionales

- Exportar **todo en un solo Excel** con varias hojas mediante `pd.ExcelWriter`.  
- Agregar **más lags** y **ventanas móviles**.  
- Calibrar horizonte de predicción (próximo mes, próximos 30 días, etc.).  
- Integrar alertas o semáforos en Power BI.

---

## 📄 Licencia
Distribuido bajo **MIT** (ver `LICENSE`).

---

## 👤 Contacto
Si necesitas adaptar reglas de llave o formatos específicos de tu SAP/indicadores, ajustamos `transform.py` para tu estándar y dejamos pruebas automatizadas para los casos más frecuentes.
