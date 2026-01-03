# 🖥️ RetroSystem Analyzer

**RetroSystem Analyzer** es un mini “panel de control” estilo retro para **monitorizar recursos del sistema** (CPU, RAM, disco y red) y verlos en un **dashboard web** (HTML/CSS/JS).  
Funciona en dos partes:

1) **Python (`monitor_plot.py`)** → recolecta métricas, guarda historial y genera gráficas.  
2) **Web (XAMPP/Apache)** → muestra las gráficas, un resumen tipo “Última Hora” y alertas en toasts.

Repo: https://github.com/piero7ov/Retrosystem-Analyzer

---

## ✨ Qué hace

- ✅ Mide **CPU**, **memoria**, **disco** y **red** usando `psutil`
- ✅ Guarda mediciones en `data/stats.csv`
- ✅ Genera gráficas `.png` en `plots/` con `matplotlib`
- ✅ Crea **alertas por umbral** y las guarda en `data/alertas.json`
- ✅ Exporta un resumen para el dashboard en `data/stats_summary.json`
- ✅ Dashboard web con:
  - Vista **Última Hora** (promedios + último dato)
  - Vista **Alertas** (lista + toast automático)
  - Vista **Comparativas** (CPU/RAM/Disco y Subida/Descarga)
  - Vista **Reportes** (descarga de CSV/JSON y futuro PDF)

---

## 🧠 Cómo funciona (flujo rápido)

1. `monitor_plot.py` toma una muestra cada `N` segundos.
2. Escribe una línea en `data/stats.csv`.
3. Con las últimas `window` muestras:
   - genera gráficas en `plots/`
   - calcula resumen y lo escribe en `data/stats_summary.json`
4. Si algo supera un umbral → agrega una alerta en `data/alertas.json`
5. El dashboard (JS) **lee esos archivos** y refresca:
   - imágenes cada **5s**
   - resumen/alertas cada **60s**

> Nota: el dashboard no “mide” nada por sí mismo. Solo **visualiza** lo que genera Python.

---

## 📦 Requisitos

- Python 3.x
- XAMPP (o cualquier Apache que sirva el HTML)
- Dependencias Python:

```bash
pip install -r requirements.txt
````

`requirements.txt`:

* `psutil`
* `matplotlib`

---

## 🚀 Instalación y uso (Windows + XAMPP)

### 1) Clonar y colocar en `htdocs`

Copia la carpeta del proyecto dentro de:

* `C:\xampp\htdocs\Retrosystem-Analyzer\`

Luego abre en el navegador:

* `http://localhost/Retrosystem-Analyzer/`

### 2) Instalar dependencias

En una terminal (dentro de la carpeta del proyecto):

```bash
pip install -r requirements.txt
```

### 3) Ejecutar el monitor (dejarlo corriendo)

```bash
python monitor_plot.py --interval 5
```

Listo: se irán creando/actualizando archivos en `data/` y `plots/`.
Para detenerlo: **Ctrl + C**.

---

## 🐧 Uso en Linux / Ubuntu

Los pasos son los mismos:

```bash
sudo apt update
sudo apt install python3 python3-pip
pip install -r requirements.txt
python3 monitor_plot.py --interval 5
```

Y sirves la carpeta con Apache, Nginx o incluso un servidor simple.

---

## ⚙️ Opciones del script (CLI)

Ejemplos útiles:

* Medición cada 5 segundos:

```bash
python monitor_plot.py --interval 5
```

* Solo **una** medición y salir (ideal para probar):

```bash
python monitor_plot.py --once
```

* Ajustar umbrales:

```bash
python monitor_plot.py --cpu-th 80 --ram-th 85 --disk-th 90 --net-th 5000
```

Parámetros principales:

* `--interval` → segundos entre mediciones
* `--window` → cantidad de muestras recientes usadas para gráficas
* `--cpu-th`, `--ram-th`, `--disk-th`, `--net-th` → umbrales de alerta
* `--once` → hace 1 ciclo y termina

---

## 🗂️ Estructura del proyecto

```
Retrosystem-Analyzer/
├── monitor_plot.py
├── index.html
├── styles.css
├── scripts.js
├── requirements.txt
├── data/
│   ├── stats.csv
│   ├── alertas.json
│   └── stats_summary.json
└── plots/
    ├── cpu.png
    ├── mem.png
    ├── disk.png
    ├── net.png
    ├── comparativa_cpu_ram_disco.png
    └── comparativa_red.png
```

---

## 📄 Archivos que genera (importante)

* `data/stats.csv`
  Historial de muestras (timestamp + métricas).

* `data/stats_summary.json`
  Resumen para “Última Hora” (último valor, promedios, samples).

* `data/alertas.json`
  Alertas recientes (se guarda un historial limitado).

* `plots/*.png`
  Gráficas que se refrescan automáticamente en el dashboard.

---

## 🧯 Errores comunes / soluciones rápidas

* **“Esperando datos… ejecuta monitor_plot.py”**
  → Normal: aún no se ha ejecutado el script o no hay archivos en `data/`.

* **No se ven gráficas / se quedan viejas**
  → El JS ya evita caché con `?t=Date.now()`. Asegúrate de que `monitor_plot.py` esté corriendo.

* **Windows: disco en `psutil.disk_usage("/")`**
  → Si te da lecturas raras, cambia en `monitor_plot.py`:

  * Linux: `psutil.disk_usage("/")`
  * Windows: `psutil.disk_usage("C:\\")` (o la unidad que uses)

* **Nombre del archivo JS**
  → En `index.html` se carga `scripts.js`. Asegúrate de que el archivo se llame exactamente así (sin typos tipo `scripsts.js`).

---

## 🛣️ Ideas de mejora (roadmap)

* Exportar reportes en PDF (botón ya preparado)
* Configuración por archivo `.env` o `config.json`
* Más métricas (temperatura, procesos top, uptime)
* Autoinicio como servicio (systemd en Linux / tarea programada en Windows)

---

## 👤 Autor

**Piero Olivares**
