from __future__ import annotations
import pandas as pd
REQUIRED_COLUMNS=["date","produit","categorie","montant","client"]
def apply_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
  rename={}
  for logical, actual in mapping.items():
    if actual in df.columns: rename[actual]=logical
  return df.rename(columns=rename)
