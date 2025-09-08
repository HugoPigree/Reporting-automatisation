
from pathlib import Path
import pandas as pd

def test_sample_csv_exists():
    assert (Path('data') / 'sales_sample.csv').exists()

def test_can_read_csv():
    df = pd.read_csv(Path('data') / 'sales_sample.csv')
    assert {'date','produit','categorie','montant','client'}.issubset(df.columns)
