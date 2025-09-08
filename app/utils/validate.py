
from __future__ import annotations

REQUIRED_COLS = ["date","produit","categorie","montant","client"]

def ensure_required_columns(df):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes requises manquantes: {missing}")
