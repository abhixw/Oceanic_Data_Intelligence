import pandas as pd

def load_data(path: str = "../data/train.csv"):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df