from physt.io import load_json
from time import time
import matplotlib.pyplot as plt
from functools import lru_cache
import pandas as pd
from collections import OrderedDict

CSV_FILE = "Adresace_zdroju_s_GPS_vysky_parsed.csv"

@lru_cache(1)
def get_all_point_metadata(path=CSV_FILE):
    """Cached reading of the master measure point table.

    Returns
    -------
    pd.DataFrame
    """
    data = pd.read_csv(path, sep=";")
    data["id"] = data["Systém"].str.lower()
    data.set_index("id", inplace=True)
    return data

@lru_cache(1)
def get_available_points():
    """All available point ids

    Returns
    -------
    ids : list
    """
    data = get_all_point_metadata(path=CSV_FILE)
    return sorted(list(data.index))

def get_point_meta_data(id):
    """Meta-data for one specific measure point.

    Returns
    -------
    data : pd.Series
    """
    try:
        return get_all_point_metadata(path=CSV_FILE).loc[id]
    except KeyError:
        raise RuntimeError("Point {0} not in the database.".format(id))


@lru_cache(20)
def find_points(address):
    """All points at an address

    Returns
    -------
    points : pd.DataFrame
        Empty or non-empty
    """
    data = get_all_point_metadata(path=CSV_FILE)
    return data[data["Adresa"] == address]

def read_data(path="data/Vinohrady.json"):
    return load_json(path)

# def get_temperature_data(path, id=None, axes=("hour", "temperature")):

def plot_to_axis(source, ax, x="hodina", y="teplota"):
    hist = read_data(source)
    projection = hist.projection(x, y)
    projection.plot(ax = ax)
    
def plot_to_file(source, path="output.png", x="hodina", y="teplota", xsize=1024, ysize=800):
    hist = read_data(source)
    projection = hist.projection(x, y)
    fig, ax = plt.subplots(figsize=(10, ysize/xsize * 10))
    t = time()
    projection.plot("image", ax=ax)
    # print("plotting", time() - t)
    t = time()
    fig.tight_layout()
    fig.savefig(path, dpi=xsize/10)
    # print("saving", time() - t)
