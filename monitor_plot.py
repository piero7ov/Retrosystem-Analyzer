#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recolector + generador de gráficas y alertas
- Genera PNGs en ./plots/
- Guarda datos en ./data/stats.csv
- Guarda alertas en ./data/alertas.json
- Exporta resumen en ./data/stats_summary.json
"""

import os, time, csv, argparse, json, math, datetime as dt
import psutil

# Matplotlib sin GUI
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --------- Rutas y setup ---------
BASE       = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE, "data")
PLOTS_DIR  = os.path.join(BASE, "plots")
CSV_PATH   = os.path.join(DATA_DIR, "stats.csv")
ALERT_PATH = os.path.join(DATA_DIR, "alertas.json")
SUM_PATH   = os.path.join(DATA_DIR, "stats_summary.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

HEADERS = [
    "timestamp","cpu_percent","mem_used_mb","mem_total_mb",
    "disk_used_gb","disk_total_gb","net_sent_kb","net_recv_kb"
]

# --------- Utilidades ---------
def now_ts() -> int:
    return int(time.time())

def ts_to_str(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADERS)

def read_rows(limit_window:int=120):
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-limit_window:] if limit_window>0 and len(rows)>limit_window else rows

def write_row(row_dict: dict):
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            row_dict["timestamp"], row_dict["cpu_percent"],
            row_dict["mem_used_mb"], row_dict["mem_total_mb"],
            row_dict["disk_used_gb"], row_dict["disk_total_gb"],
            row_dict["net_sent_kb"], row_dict["net_recv_kb"]
        ])

def snapshot():
    cpu = psutil.cpu_percent(interval=0.4)
    vm  = psutil.virtual_memory()
    du  = psutil.disk_usage("/")
    n1  = psutil.net_io_counters()
    time.sleep(0.6)  # total ~1s entre CPU y red
    n2  = psutil.net_io_counters()
    sent_kb = (n2.bytes_sent - n1.bytes_sent)/1024.0
    recv_kb = (n2.bytes_recv - n1.bytes_recv)/1024.0

    return {
        "timestamp": now_ts(),
        "cpu_percent": round(cpu, 2),
        "mem_used_mb": round((vm.total - vm.available)/1024/1024, 2),
        "mem_total_mb": round(vm.total/1024/1024, 2),
        "disk_used_gb": round(du.used/1024/1024/1024, 2),
        "disk_total_gb": round(du.total/1024/1024/1024, 2),
        "net_sent_kb": round(sent_kb, 2),
        "net_recv_kb": round(recv_kb, 2),
    }

# --------- Plot helpers ---------
def plot_line(series, title, ylabel, out_path, ymin=None, ymax=None, color=None):
    plt.figure(figsize=(7,3.2))
    x = range(len(series))
    plt.plot(x, series, linewidth=2, color=(color if color else None))
    plt.title(title)
    plt.xlabel("Muestras recientes")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    if ymin is not None or ymax is not None:
        plt.ylim(ymin, ymax)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()

def plot_dual(a, b, labels, title, ylabel, out_path, colors=("#22d3ee", "#a78bfa")):
    plt.figure(figsize=(7,3.2))
    x = range(len(a))
    plt.plot(x, a, linewidth=2, label=labels[0], color=colors[0])
    plt.plot(x, b, linewidth=2, label=labels[1], color=colors[1])
    plt.title(title)
    plt.xlabel("Muestras recientes")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()

def plot_triple(a, b, c, labels, title, ylabel, out_path,
                colors=("#0ea5e9", "#f97316", "#10b981")):
    plt.figure(figsize=(7,3.2))
    x = range(len(a))
    plt.plot(x, a, linewidth=2, label=labels[0], color=colors[0])
    plt.plot(x, b, linewidth=2, label=labels[1], color=colors[1])
    plt.plot(x, c, linewidth=2, label=labels[2], color=colors[2])
    plt.title(title)
    plt.xlabel("Muestras recientes")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()

# --------- Alertas ---------
def load_alerts():
    if not os.path.exists(ALERT_PATH):
        return []
    try:
        with open(ALERT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_alerts(alerts):
    # Conserva solo las últimas 100
    alerts = alerts[-100:]
    with open(ALERT_PATH, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)

def maybe_add_alert(alerts, kind, value, threshold, ts):
    msg = None
    if kind == "CPU" and value > threshold:
        msg = f"CPU alta: {value:.1f}% > {threshold}%"
    elif kind == "RAM" and value > threshold:
        msg = f"RAM alta: {value:.1f}% > {threshold}%"
    elif kind == "DISCO" and value > threshold:
        msg = f"DISCO alto: {value:.1f}% > {threshold}%"
    elif kind == "RED" and value > threshold:
        msg = f"RED alta: {value:.1f} KB/s > {threshold} KB/s"
    if msg:
        alerts.append({
            "ts": ts,
            "time": ts_to_str(ts),
            "type": kind,
            "value": round(value,1),
            "threshold": threshold,
            "message": msg
        })

# --------- Resumen ---------
def save_summary(rows):
    if not rows:
        data = {"ok": False, "msg": "sin datos"}
    else:
        last = rows[-1]
        def f(x): 
            try: return float(x)
            except: return 0.0
        cpu = [f(r["cpu_percent"]) for r in rows]
        mem = [ (f(r["mem_used_mb"])/max(f(r["mem_total_mb"]),1))*100 for r in rows ]
        net = [ f(r["net_sent_kb"]) + f(r["net_recv_kb"]) for r in rows ]

        data = {
            "ok": True,
            "last_time": ts_to_str(int(float(last["timestamp"]))),
            "last": {
                "cpu_percent": f(last["cpu_percent"]),
                "mem_percent": (f(last["mem_used_mb"])/max(f(last["mem_total_mb"]),1))*100,
                "disk_percent": (f(last["disk_used_gb"])/max(f(last["disk_total_gb"]),0.0001))*100,
                "net_kb_s": f(last["net_sent_kb"]) + f(last["net_recv_kb"]),
            },
            "avg": {
                "cpu_percent": sum(cpu)/max(len(cpu),1),
                "mem_percent": sum(mem)/max(len(mem),1),
                "net_kb_s": sum(net)/max(len(net),1),
            },
            "samples": len(rows)
        }
    with open(SUM_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --------- Generación de gráficas ---------
def regenerate_basic_plots(rows):
    if not rows:
        # genera imágenes “vacías” para no romper el UI
        for name in ["cpu","mem","disk","net"]:
            plot_line([0,0], f"Sin datos ({name})", "", os.path.join(PLOTS_DIR, f"{name}.png"))
        return

    def f(x): 
        try: return float(x)
        except: return 0.0

    cpu  = [f(r["cpu_percent"]) for r in rows]
    memp = [ (f(r["mem_used_mb"])/max(f(r["mem_total_mb"]),1))*100 for r in rows ]
    disk = [ (f(r["disk_used_gb"])/max(f(r["disk_total_gb"]),0.0001))*100 for r in rows ]
    net  = [ f(r["net_recv_kb"]) + f(r["net_sent_kb"]) for r in rows ]

    plot_line(cpu,  "Uso de CPU (%)",       "%",   os.path.join(PLOTS_DIR,"cpu.png"),  ymin=0, ymax=100, color="#0ea5e9")
    plot_line(memp, "Uso de Memoria (%)",   "%",   os.path.join(PLOTS_DIR,"mem.png"),  ymin=0, ymax=100, color="#f97316")
    plot_line(disk, "Uso de Disco (%)",     "%",   os.path.join(PLOTS_DIR,"disk.png"), ymin=0, ymax=100, color="#10b981")
    plot_line(net,  "Actividad de Red (KB/s)","KB/s",os.path.join(PLOTS_DIR,"net.png"),  color="#8b5cf6")

def regenerate_comparatives(rows):
    if not rows:
        plot_triple([0,0],[0,0],[0,0], ["CPU","RAM","Disco"], 
                    "Comparativa CPU/RAM/Disco", "%", 
                    os.path.join(PLOTS_DIR, "comparativa_cpu_ram_disco.png"))
        plot_dual([0,0],[0,0], ["Subida","Descarga"], 
                  "Comparativa Red", "KB/s", 
                  os.path.join(PLOTS_DIR, "comparativa_red.png"))
        return

    def f(x): 
        try: return float(x)
        except: return 0.0

    cpu  = [f(r["cpu_percent"]) for r in rows]
    memp = [ (f(r["mem_used_mb"])/max(f(r["mem_total_mb"]),1))*100 for r in rows ]
    disk = [ (f(r["disk_used_gb"])/max(f(r["disk_total_gb"]),0.0001))*100 for r in rows ]
    up   = [ f(r["net_sent_kb"]) for r in rows ]
    dn   = [ f(r["net_recv_kb"]) for r in rows ]

    plot_triple(cpu, memp, disk, ["CPU %","RAM %","Disco %"], 
                "Comparativa CPU vs RAM vs Disco", "%", 
                os.path.join(PLOTS_DIR, "comparativa_cpu_ram_disco.png"))

    plot_dual(up, dn, ["Subida (KB/s)","Descarga (KB/s)"], 
              "Comparativa Red", "KB/s", 
              os.path.join(PLOTS_DIR, "comparativa_red.png"))

# --------- Main loop ---------
def main():
    p = argparse.ArgumentParser(description="Monitor + plots + alertas (XAMPP)")
    p.add_argument("--interval", type=int, default=5,  help="Segundos entre mediciones (def: 5)")
    p.add_argument("--window",   type=int, default=120,help="Muestras recientes para graficar (def: 120)")
    # Umbrales de alerta
    p.add_argument("--cpu-th",   type=float, default=80.0, help="Umbral CPU %")
    p.add_argument("--ram-th",   type=float, default=85.0, help="Umbral RAM %")
    p.add_argument("--disk-th",  type=float, default=90.0, help="Umbral DISCO %")
    p.add_argument("--net-th",   type=float, default=5000.0, help="Umbral RED KB/s (subida+descarga)")
    p.add_argument("--once", action="store_true", help="Solo una medición + gráficos y salir")
    args = p.parse_args()

    ensure_csv()

    alerts = load_alerts()

    def one_cycle():
        # 1) tomar medida y guardar
        row = snapshot()
        write_row(row)

        # 2) leer ventana reciente
        rows = read_rows(args.window)

        # 3) generar gráficas base y comparativas
        regenerate_basic_plots(rows)
        regenerate_comparatives(rows)

        # 4) alertas
        #    calcula % actuales
        m_used = row["mem_used_mb"]; m_tot = max(row["mem_total_mb"], 1)
        d_used = row["disk_used_gb"]; d_tot = max(row["disk_total_gb"], 0.0001)
        mem_pct  = (m_used/m_tot)*100.0
        disk_pct = (d_used/d_tot)*100.0
        net_kb   = row["net_sent_kb"] + row["net_recv_kb"]

        ts = row["timestamp"]
        maybe_add_alert(alerts, "CPU",   row["cpu_percent"], args.cpu_th,  ts)
        maybe_add_alert(alerts, "RAM",   mem_pct,            args.ram_th,  ts)
        maybe_add_alert(alerts, "DISCO", disk_pct,           args.disk_th, ts)
        maybe_add_alert(alerts, "RED",   net_kb,             args.net_th,  ts)
        save_alerts(alerts)

        # 5) resumen
        save_summary(rows)

    if args.once:
        one_cycle()
        print("OK: 1 muestra registrada, gráficas/alertas/resumen generados.")
        return

    print(f"Recolectando cada {args.interval}s • Ventana {args.window} muestras • Ctrl+C para salir")
    print(f"Umbrales -> CPU>{args.cpu_th}% | RAM>{args.ram_th}% | DISCO>{args.disk_th}% | RED>{args.net_th} KB/s")
    try:
        while True:
            one_cycle()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nFinalizado.")

if __name__ == "__main__":
    main()
