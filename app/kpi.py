
from __future__ import annotations
import pandas as pd

def compute_kpis(df: pd.DataFrame, top_n_products: int = 10) -> dict:
    df = df.copy()
    df["mois"] = df["date"].dt.to_period("M").dt.to_timestamp()

    by_month = df.groupby("mois", as_index=False).agg(
        CA=("montant","sum"),
        commandes=("montant","size"),
        ticket_moyen=("montant","mean"),
    )
    by_cat = df.groupby(["mois","categorie"], as_index=False).agg(CA=("montant","sum"))
    by_prod = df.groupby(["mois","produit"], as_index=False).agg(CA=("montant","sum"))

    ca_total = df["montant"].sum()
    last_month = by_month["mois"].max()
    prev_month = (last_month - pd.offsets.MonthBegin(1))

    ca_M = by_month.loc[by_month["mois"]==last_month, "CA"].sum()
    ca_M1 = by_month.loc[by_month["mois"]==prev_month, "CA"].sum()

    croissance = None
    if ca_M1 and ca_M1 != 0:
        croissance = (ca_M - ca_M1) / ca_M1

    ticket_moyen_global = df["montant"].mean()

    top_prod_global = (df.groupby("produit", as_index=False)["montant"]
                         .sum().sort_values("montant", ascending=False).head(top_n_products))
    top_cat_global = (df.groupby("categorie", as_index=False)["montant"]
                        .sum().sort_values("montant", ascending=False).head(5))

    # Pivots
    pivot_cat = by_cat.pivot(index="mois", columns="categorie", values="CA").fillna(0).reset_index()
    # For products, keep only top N (global) to limit width
    keep_prods = set(top_prod_global["produit"].tolist())
    by_prod_top = by_prod[by_prod["produit"].isin(keep_prods)]
    pivot_prod = by_prod_top.pivot(index="mois", columns="produit", values="CA").fillna(0).reset_index()

    return {
        "by_month": by_month,
        "by_cat": by_cat,
        "by_prod": by_prod,
        "pivot_cat": pivot_cat,
        "pivot_prod": pivot_prod,
        "ca_total": ca_total,
        "ca_M": ca_M,
        "ca_M1": ca_M1,
        "croissance": croissance,
        "ticket_moyen_global": ticket_moyen_global,
        "top_prod": top_prod_global,
        "top_cat": top_cat_global,
    }
