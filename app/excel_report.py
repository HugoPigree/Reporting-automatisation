
from __future__ import annotations
import pandas as pd
from pathlib import Path

def _autofit_columns(ws, df, workbook, min_width=8, max_width=40):
    # estimate width based on header and sample of values
    for idx, col in enumerate(df.columns):
        header = str(col)
        max_len = len(header)
        # Check first 100 rows for width
        for val in df[col].astype(str).head(100):
            if len(val) > max_len:
                max_len = len(val)
        width = min(max(max_len + 2, min_width), max_width)
        ws.set_column(idx, idx, width)

def _formats(wb, theme="light"):
    base_fg = "#1f2937" if theme == "dark" else "#111827"
    inv_fg = "#e5e7eb" if theme == "dark" else "#111827"
    header_bg = "#374151" if theme == "dark" else "#e5e7eb"
    money = wb.add_format({"num_format": "#,##0.00 €"})
    percent = wb.add_format({"num_format": "0.00%"})
    h1 = wb.add_format({"bold": True, "font_size": 14, "font_color": inv_fg, "bg_color": header_bg})
    h2 = wb.add_format({"bold": True, "font_size": 12})
    normal = wb.add_format({})
    bold = wb.add_format({"bold": True})
    return {"money": money, "percent": percent, "h1": h1, "h2": h2, "normal": normal, "bold": bold}

def write_report(kpis: dict, out_path: str, theme: str="light", include_sheets=None, include_kpis=None):
    if include_sheets is None:
        include_sheets = ["Données","KPI","Dashboard","Par catégorie","Par produit"]
    if include_kpis is None:
        include_kpis = ["ca_total","ca_M","ca_M1","croissance","ticket_moyen_global"]

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(out, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:
        wb = writer.book
        fmt = _formats(wb, theme=theme)

        # Sheet: Données
        if "Données" in include_sheets:
            kpis["by_month"].to_excel(writer, sheet_name="Données", index=False)
            ws_data = writer.sheets["Données"]
            _autofit_columns(ws_data, kpis["by_month"], wb)
            ws_data.freeze_panes(1, 0)

        # Sheet: KPI
        if "KPI" in include_sheets:
            ws_kpi = wb.add_worksheet("KPI")
            ws_kpi.write(0, 0, "KPI", fmt["h1"])

            row = 2
            labels = {
                "ca_total": "CA total",
                "ca_M": "CA mois courant",
                "ca_M1": "CA mois précédent",
                "croissance": "Croissance M vs M-1",
                "ticket_moyen_global": "Ticket moyen (global)",
            }
            for key in include_kpis:
                ws_kpi.write(row, 0, labels.get(key, key))
                val = kpis.get(key)
                if key in ("ca_total","ca_M","ca_M1","ticket_moyen_global"):
                    ws_kpi.write(row, 1, val, fmt["money"])
                elif key == "croissance":
                    if val is not None:
                        ws_kpi.write(row, 1, val, fmt["percent"])
                    else:
                        ws_kpi.write(row, 1, "n/a")
                else:
                    ws_kpi.write(row, 1, val)
                row += 1

            # Top tables
            ws_kpi.write(row+1, 0, "Top catégories (CA)", fmt["bold"])
            kpis["top_cat"].rename(columns={"montant":"CA"}).to_excel(writer, sheet_name="KPI",
                                                                      startrow=row+2, startcol=0, index=False)
            ws_kpi.write(row+1, 4, "Top produits (CA)", fmt["bold"])
            kpis["top_prod"].rename(columns={"montant":"CA"}).to_excel(writer, sheet_name="KPI",
                                                                       startrow=row+2, startcol=4, index=False)

            # Conditional formatting for growth if present
            ws_kpi.conditional_format(2, 1, row, 1, {
                "type": "3_color_scale"
            })

        # Sheet: Dashboard (charts)
        if "Dashboard" in include_sheets:
            ws_dash = wb.add_worksheet("Dashboard")
            ws_dash.write(0, 0, "Dashboard", fmt["h1"])
            # Chart 1: CA par mois
            chart1 = wb.add_chart({"type":"line"})
            nrows = len(kpis["by_month"]) + 1
            chart1.add_series({
                "name": "CA / mois",
                "categories": f"=Données!$A$2:$A${nrows}",
                "values":     f"=Données!$B$2:$B${nrows}",
            })
            chart1.set_title({"name": "Chiffre d'affaires par mois"})
            ws_dash.insert_chart("A3", chart1, {"x_scale":1.6, "y_scale":1.2})

            chart2 = wb.add_chart({"type":"column"})
            chart2.add_series({
                "name": "Commandes / mois",
                "categories": f"=Données!$A$2:$A${nrows}",
                "values":     f"=Données!$C$2:$C${nrows}",
            })
            chart2.set_title({"name": "Nombre de commandes par mois"})
            ws_dash.insert_chart("A20", chart2, {"x_scale":1.6, "y_scale":1.2})

        # Sheet: Par catégorie (pivot)
        if "Par catégorie" in include_sheets:
            kpis["pivot_cat"].to_excel(writer, sheet_name="Par catégorie", index=False)
            ws = writer.sheets["Par catégorie"]
            _autofit_columns(ws, kpis["pivot_cat"], wb)
            ws.freeze_panes(1, 1)

        # Sheet: Par produit (pivot)
        if "Par produit" in include_sheets:
            kpis["pivot_prod"].to_excel(writer, sheet_name="Par produit", index=False)
            ws = writer.sheets["Par produit"]
            _autofit_columns(ws, kpis["pivot_prod"], wb)
            ws.freeze_panes(1, 1)
