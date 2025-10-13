# 🚛 Proyecto ETL: Optimización del Mantenimiento de Tractocamiones de Caña

## 👨‍💻 Autores

Este proyecto fue desarrollado por estudiantes de la **Maestría en Inteligencia Artificial y Ciencia de Datos**:

🎓 **Cesar Moreno** – 22505046  
🎓 **Juan Ortiz** – 22505050  
🎓 **Robert Borja** – 22505056  
🎓 **Jhon Caicedo** – 22505031  

---

## 🔍 Descripción General

El proyecto propone la implementación de un proceso ETL completo orientado a la optimización del mantenimiento de tractocamiones de caña pertenecientes a un ingenio azucarero del Valle del Cauca.  
El propósito central es **integrar, limpiar y analizar** información proveniente de los sistemas **SAP PM** y **Biosalc Agrícola**, con el fin de anticipar fallas, optimizar la programación de mantenimientos y fortalecer la toma de decisiones basada en datos.

---

## 📌 Resumen

Actualmente, el ingenio enfrenta limitaciones por la falta de integración entre sus sistemas de mantenimiento y operación. Los datos sobre órdenes de trabajo, fallas, tiempos de inactividad y producción se almacenan en plataformas distintas y no se analizan de forma conjunta.

Este proyecto construye un **pipeline ETL + modelo predictivo**, capaz de:

- Unificar datos de mantenimiento (SAP PM) y operación (Biosalc Agrícola).  
- Limpiar y normalizar la información mediante reglas estandarizadas.  
- Generar indicadores clave (MTBF, MTTR, disponibilidad, confiabilidad).  
- Entrenar un modelo de predicción para mantenimiento correctivo (PMM1).  
- Exportar resultados en formato Excel para análisis en Power BI.

---

## 🎯 Objetivos

### Objetivo General
Diseñar y ejecutar un **proceso ETL automatizado** para integrar los datos operativos y de mantenimiento de tractocamiones, con el fin de construir una base analítica para el mantenimiento predictivo.

### Objetivos Específicos
- Integrar datos históricos de SAP PM y Biosalc Agrícola.  
- Estandarizar formatos de fechas, nombres de equipos y códigos de falla.  
- Generar un dataset estructurado y auditable.  
- Desarrollar un modelo predictivo (Random Forest) que estime el riesgo de mantenimiento correctivo (PMM1).  
- Presentar resultados en formato compatible con Power BI y desarrollar un tablero analítico para visualización de indicadores clave.
---

## 🧰 Tecnologías y Herramientas

- **Lenguaje:** Python 3.x  
- **Librerías:** `pandas`, `numpy`, `openpyxl`, `scikit-learn`, `datetime`, `os`  
- **Entorno:** Google Colab / VS Code  
- **Salida:** Archivos Excel (`.xlsx`) por tabla  
- **Análisis y Visualización:** Power BI  
- **Control de versiones:** Git / GitHub  

---

## 📁 Fuentes de Datos

### SAP PM (Módulo de Mantenimiento)
- Órdenes de trabajo (preventivas, correctivas, predictivas).  
- Historial de fallas, duración de órdenes y tiempos de inactividad.  
- Datos maestros de equipos y repuestos.  

### Biosalc Agrícola
- Registros de báscula y eventos de maquinaria.  
- Toneladas transportadas, horas de operación y paradas no programadas.  
- Variables de uso y condiciones de trabajo.

### Formato y Volumen
- Datos estructurados en formato tabular (`CSV`, `XLSX`).  
- Volumen aproximado: **25.000 registros por año**, cubriendo un periodo histórico de **9 años**.

---

## 🔁 Proceso ETL

### 1️⃣ Extracción
- Conectores a SAP (RFC, OData o exportación a tablas intermedias).  
- Extracción de eventos operativos desde Biosalc mediante SQL Server o CSV.  
- Descarga de históricos de mantenimiento.

### 2️⃣ Transformación
- Normalización de nombres de equipos, fechas y códigos.  
- Limpieza de duplicados, estandarización de unidades (horas, km).  
- Enriquecimiento de datos:  
  - Cálculo de **disponibilidad**, **Comportamiento de las ordenes por mes, año y equipo**
- Modelado en esquema de **tabla de hechos (fallas/mantenimientos)** y **dimensiones** (vehículo, componente, fecha, centro de trabajo).  

### 3️⃣ Carga
- Exportación de tablas limpias y consolidadas en formato `.xlsx`.  
- Dataset ML con *lags* para entrenamiento y análisis predictivo.  
- Preparación para visualización en Power BI.

---

## 🧱 Estructura del Repositorio

```plaintext
pmm_pipeline_mod/
├─ extract.py              # Extracción desde Excel + normalización
├─ transform.py            # Limpieza y unión por equipo-mes
├─ load.py                 # Exportación a Excel (una hoja por tabla)
├─ model.py                # Dataset ML + entrenamiento RandomForest
├─ main.py                 # Orquestador ETL completo
├─ inputs/                   # Archivos de entrada
└─ outputs/                # Archivos de salida (.xlsx)

```

---

## 🧪 Modelo Predictivo

- **Tipo de modelo:** RandomForestClassifier (`class_weight="balanced_subsample"`)  
- **Variable objetivo:** `y_pmm1` → 1 si hubo mantenimiento correctivo (PMM1).  
- **Features:** toneladas, órdenes de mantenimiento, duración promedio, *lags* por equipo.  
- **Evaluación:** división temporal (80/20) con métricas de precisión, recall y matriz de confusión.  

> El modelo constituye un **baseline** para mantenimiento predictivo. Se puede mejorar incorporando variables exógenas como clima, tipo de ruta o antigüedad del equipo.

---

## 📊 Resultados y Tablas de Salida

Se generan los siguientes archivos Excel en la carpeta `outputs_excel_only/`:

| Archivo | Descripción |
|----------|--------------|
| `dim_equipos.xlsx` | Lista de equipos válidos |
| `fct_mes_equipo_clean.xlsx` | Hechos por equipo–mes (base principal) |
| `mantenimiento_detalle.xlsx` | Detalle de órdenes SAP |
| `ml_equipo_mes_clean.xlsx` | Dataset ML con *lags* |
| `ml_equipo_mes.xlsx` | Dataset sin limpieza estricta |

---

### **Diagrama de Arquitectura** 🏗️
┌────────────────────────────┐                     ┌──────────────────────────────┐
│        Fuentes de Datos     │                     │     Entorno de Procesamiento │
│                            │                     │          (Python / Colab)    │
│  ┌──────────────────────┐  │                     │  ┌────────────────────────┐  │
│  │ SAP PM (Mantenimiento)│──┐    Extracción      │  │  Extracción de Datos   │  │
│  │  - Órdenes OM         │  │  ───────────────►  │  │  (extract.py)          │  │
│  │  - Avisos de Fallas   │  │                   │  └────────────────────────┘  │
│  └──────────────────────┘  │                   │                               │
│                            │                   │  ┌────────────────────────┐  │
│  ┌──────────────────────┐  │                   │  │  Transformación de Datos│  │
│  │ BIOSALC Agrícola     │──┘  Integración ETL  │  │  (transform.py)        │  │
│  │  - Toneladas, viajes │───────►              │  └────────────────────────┘  │
│  │  - Paradas / eventos │                     │                               │
│  └──────────────────────┘                     │  ┌────────────────────────┐  │
│                                               │  │  Limpieza y Validación │  │
│                                               │  │  - Fechas y equipos    │  │
│                                               │  │  - MTBF / MTTR         │  │
│                                               │  └────────────────────────┘  │
│                                               │                               │
│                                               │  ┌────────────────────────┐  │
│                                               │  │  Modelado Predictivo   │  │
│                                               │  │  (model.py)            │  │
│                                               │  │  - Random Forest       │  │
│                                               │  │  - Target: PMM1        │  │
│                                               │  └────────────────────────┘  │
└────────────────────────────┘                   │                               │
                                                 │  ┌────────────────────────┐  │
                                                 │  │  Carga de Resultados   │  │
                                                 │  │  (load.py)             │  │
                                                 │  │  - Excel .xlsx         │  │
                                                 │  │  - Dataset ML limpio   │  │
                                                 │  └────────────────────────┘  │
                                                 └──────────────────────────────┘
                                                            │
                                                            ▼
                                            ┌─────────────────────────────────────┐
                                            │         Salidas y Visualización     │
                                            │─────────────────────────────────────│
                                            │  - fct_mes_equipo_clean.xlsx        │
                                            │  - ml_equipo_mes_clean.xlsx         │
                                            │  - mantenimiento_detalle.xlsx       │
                                            │─────────────────────────────────────│
                                            │  Analítica y Dashboards:            │
                                            │  • Power BI                         │
                                            │  • Reportes MTBF / MTTR             │
                                            │  • Riesgo PMM1 por equipo           │
                                            └─────────────────────────────────────┘


![Diagrama del Pipeline](/diagrama_pipeline.png)
## 🧩 Indicadores Clave

- **MTBF (Mean Time Between Failures)**  
- **MTTR (Mean Time To Repair)**  
- **Tasa de PMM1**  
- **Disponibilidad (%)**  
- **Costo promedio por tipo de avería**

Estos indicadores fortalecen la toma de decisiones sobre confiabilidad, priorización de inversiones y planificación de mantenimiento.

---

## 🧠 Conclusiones

En conclusión, este proyecto permitió pasar de datos desordenados y difíciles de cruzar a un **pipeline estructurado, auditable y automatizado**, capaz de integrar la información operacional y de mantenimiento de los equipos de transporte de caña.  
La implementación de una llave canónica de equipo, el parseo robusto de fechas y la limpieza de registros inconsistentes garantizan una base sólida para el análisis y la toma de decisiones.  

El modelo predictivo desarrollado constituye un primer paso hacia un sistema de mantenimiento inteligente, que anticipa posibles correctivos (PMM1) y puede evolucionar con más variables operativas y retroalimentación continua.  

Aunque inicialmente se contempló implementarlo en **Microsoft Fabric**, se optó por una solución local en **Python y Excel**, garantizando portabilidad, transparencia y compatibilidad con herramientas como **Power BI**.  

El proyecto sienta así las bases para un **ecosistema analítico sostenible**, orientado a mejorar la disponibilidad de la maquinaria, reducir costos de mantenimiento y fortalecer la cultura de decisiones basadas en datos dentro del proceso agrícola-industrial.


