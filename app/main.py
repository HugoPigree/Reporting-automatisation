
from __future__ import annotations
import argparse, datetime as dt
import pandas as pd
from pathlib import Path
from .utils.io import load_config, ensure_dir, get_logger
from .datasources import load_dataframe_from_source
from .kpi import compute_kpis
from .excel_report import write_report
from .emailer import send_email

def parse_args():
    p = argparse.ArgumentParser(description="Génère un rapport Excel")
    p.add_argument("--data", type=str, help="Chemin CSV (ou dossier) - override data_source.path")
    p.add_argument("--start", type=str, help="Date début YYYY-MM-DD")
    p.add_argument("--end", type=str, help="Date fin YYYY-MM-DD")
    p.add_argument("--no-email", action="store_true", help="Ne pas envoyer d'email même si activé dans la config")
    return p.parse_args()

def resolve_period(cfg_period: dict, cli_start: str|None, cli_end: str|None):
    if cli_start or cli_end:
        ds = pd.to_datetime(cli_start) if cli_start else None
        de = pd.to_datetime(cli_end) if cli_end else None
        return ds, de
    mode = (cfg_period or {}).get("mode", "last_full_month")
    if mode == "range":
        ds = cfg_period.get("date_start")
        de = cfg_period.get("date_end")
        ds = pd.to_datetime(ds) if ds else None
        de = pd.to_datetime(de) if de else None
        return ds, de
    today = pd.Timestamp.today().normalize()
    first_this_month = today.replace(day=1)
    last_month_end = first_this_month - pd.Timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    return last_month_start, last_month_end

def run():
    logger = get_logger()
    try:
        cfg = load_config()
        args = parse_args()
        if args.data:
            from pathlib import Path as _P
            ds_type = "csv_dir" if _P(args.data).is_dir() else "csv_file"
            cfg["data_source"] = {"type": ds_type, "path": args.data}

        report_dir = cfg["report_dir"]; ensure_dir(report_dir)
        ds, de = resolve_period(cfg.get("period", {}), args.start, args.end)
        logger.log(f"Source: {cfg.get('data_source',{})}")
        logger.log(f"Période: {ds} -> {de}")

        df = load_dataframe_from_source(cfg, ds, de)
        if df.empty: raise ValueError("Aucune donnée après filtration.")

        top_n = int(((cfg.get("excel") or {}).get("top_n_products")) or 10)
        logger.log("Calcul KPI...")
        kpis = compute_kpis(df, top_n_products=top_n)

        date_str = dt.date.today().strftime(cfg["date_format"])
        out_file = Path(report_dir) / f"{cfg['report_prefix']}_{date_str}.xlsx"
        theme = ((cfg.get("excel") or {}).get("theme")) or "light"
        include_sheets = (cfg.get("excel") or {}).get("include_sheets")
        include_kpis   = (cfg.get("excel") or {}).get("include_kpis")

        logger.log(f"Génération Excel: {out_file} (theme={theme})")
        write_report(kpis, str(out_file), theme=theme, include_sheets=include_sheets, include_kpis=include_kpis)

        if not args.no_email:
            logger.log("Email (si activé)...")
            try:
                send_email(cfg.get("email", {}), str(out_file), date_str)
                logger.log("Email: OK (ou désactivé).")
            except Exception as e:
                logger.log(f"Email: ERREUR non bloquante: {e}")
        else:
            logger.log("Email ignoré (--no-email).")

        logger.log("OK - Rapport généré.")
    except Exception as e:
        logger.log(f"ERREUR: {e}")
        raise
    finally:
        try: logger.close()
        except: pass

if __name__ == "__main__":
    run()
