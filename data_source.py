from physt.io import load_json
from functools import lru_cache


@lru_cache(1)
def read_data(path="data/Vinohrady.json"):
    return load_json(path)

def plot(ax, x="hodina", y="teplota"):
    hist = read_data()
    projection = hist.projection(x, y)
    projection.plot(ax=ax)
