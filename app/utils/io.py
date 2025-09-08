from __future__ import annotations
import os,yaml,datetime as dt
from pathlib import Path
DEFAULTS={"data_path":"./data/sales_sample.csv","column_mapping":{"date":"date","produit":"produit","categorie":"categorie","montant":"montant","client":"client"},"report_dir":"./reports","report_prefix":"rapport","date_format":"%Y-%m-%d","period":{"mode":"last_full_month","date_start":None,"date_end":None}}
def load_config():
  p=Path("config.yaml")
  cfg=yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
  merged={**DEFAULTS,**(cfg or {})}
  merged["data_path"]=str(Path(merged["data_path"]).resolve())
  merged["report_dir"]=str(Path(merged["report_dir"]).resolve())
  return merged
def ensure_dir(p): Path(p).mkdir(parents=True, exist_ok=True)
def get_logger():
  logs=Path("logs"); logs.mkdir(exist_ok=True)
  ts=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
  f=logs/f"run_{ts}.log"
  class L:
    def __init__(self,fp): self.fp=open(fp,"w",encoding="utf-8")
    def log(self,m):
      import datetime as _dt
      line=f"[{_dt.datetime.now().isoformat(timespec='seconds')}] {m}"
      print(line); self.fp.write(line+"\n"); self.fp.flush()
    def close(self):
      try: self.fp.close()
      except: pass
  return L(str(f))
