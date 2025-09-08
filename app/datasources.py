
from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List

try:
    import mysql.connector  # type: ignore
except Exception:
    mysql = None  # optional

from .ingestion import apply_mapping, REQUIRED_COLUMNS

def _finalize(df: pd.DataFrame, date_start, date_end) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce")
    df = df.dropna(subset=["date","montant"]).copy()
    if date_start is not None:
        df = df[df["date"] >= date_start]
    if date_end is not None:
        df = df[df["date"] <= date_end]
    return df

def read_csv_file(path: str, mapping: Dict[str,str], date_start, date_end, chunk_size: int|None=None) -> pd.DataFrame:
    if chunk_size:
        chunks = []
        for chunk in pd.read_csv(path, chunksize=int(chunk_size)):
            chunk = apply_mapping(chunk, mapping)
            missing = [c for c in REQUIRED_COLUMNS if c not in chunk.columns]
            if missing:
                raise ValueError(f"Colonnes requises manquantes dans {path}: {missing}")
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=REQUIRED_COLUMNS)
    else:
        df = pd.read_csv(path)
        df = apply_mapping(df, mapping)
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Colonnes requises manquantes dans {path}: {missing}")
    return _finalize(df, date_start, date_end)

def read_csv_dir(path_dir: str, mapping: Dict[str,str], date_start, date_end, chunk_size: int|None=None) -> pd.DataFrame:
    p = Path(path_dir)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Dossier CSV introuvable: {path_dir}")
    frames: List[pd.DataFrame] = []
    for fp in sorted(p.glob("*.csv")):
        frames.append(read_csv_file(str(fp), mapping, date_start, date_end, chunk_size))
    if not frames:
        raise ValueError(f"Aucun CSV trouvé dans {path_dir}")
    return pd.concat(frames, ignore_index=True)

def read_mysql(mysql_cfg: dict, mapping: Dict[str,str], date_start, date_end) -> pd.DataFrame:
    if mysql_cfg is None:
        raise ValueError("Config MySQL manquante")
    try:
        conn = mysql.connector.connect(
            host=mysql_cfg.get("host"),
            port=mysql_cfg.get("port", 3306),
            user=mysql_cfg.get("user"),
            password=mysql_cfg.get("password"),
            database=mysql_cfg.get("database"),
        )
    except Exception as e:
        raise RuntimeError(f"Connexion MySQL échouée: {e}")
    try:
        query = mysql_cfg.get("query") or "SELECT date, produit, categorie, montant, client FROM ventes"
        params = {
            "date_start": None if date_start is None else pd.Timestamp(date_start).strftime("%Y-%m-%d"),
            "date_end": None if date_end is None else pd.Timestamp(date_end).strftime("%Y-%m-%d"),
        }
        df = pd.read_sql(query, conn, params=params)  # type: ignore
    finally:
        try: conn.close()
        except: pass
    df = apply_mapping(df, mapping)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes requises manquantes depuis MySQL: {missing}")
    return _finalize(df, date_start, date_end)

def load_dataframe_from_source(cfg: dict, date_start, date_end) -> pd.DataFrame:
    ds = cfg.get("data_source", {}) or {}
    ds_type = ds.get("type", "csv_file")
    mapping = cfg.get("column_mapping", {})
    chunk_size = ds.get("chunk_size")
    if ds_type == "csv_file":
        path = ds.get("path") or cfg.get("data_path")
        if not path: raise ValueError("Aucun chemin CSV fourni")
        return read_csv_file(path, mapping, date_start, date_end, chunk_size)
    if ds_type == "csv_dir":
        path = ds.get("path")
        if not path: raise ValueError("Aucun dossier CSV fourni")
        return read_csv_dir(path, mapping, date_start, date_end, chunk_size)
    if ds_type == "mysql":
        mysql_cfg = cfg.get("mysql", {})
        return read_mysql(mysql_cfg, mapping, date_start, date_end)
    raise ValueError(f"Type de source inconnu: {ds_type}")
