from physt.io import load_json
from time import time
import matplotlib.pyplot as plt
from functools import lru_cache
import pandas as pd
from collections import OrderedDict
from czech_sort import sorted as czech_sorted
import os


CSV_FILE = "Adresace_zdroju_s_GPS_vysky_lesy_parsed.csv"


def calculate_greenery(df, a=0.5, b=1/3., c=1/6.):
    return a * df["0.001"] + b * df["0.005"] + c * df["0.01"]


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
    data["greenery"] = calculate_greenery(data)
    return data
    

@lru_cache(1)
def get_available_points():
    """All available point ids (with temperature data).
    
    Returns
    -------
    ids : list
    """
    data = get_all_point_metadata(path=CSV_FILE)
    return sorted([i for i in data.index if has_data(i)])
    
    
def has_data(id):
    """Whether data for a point identifier do exist.
    
    Returns
    -------
    bool
    """
    return os.path.exists(os.path.join("data", "{0}.json".format(id)))

    
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
        

@lru_cache(1)    
def get_point_tree():
    """Tree city part/points in it.
    
    Returns
    -------
    tree : OrderedDict[DataFrame]
        Keys of the dictionary are the city parts.
        Values are full tables of points.
    """
    available = get_available_points()
    data = get_all_point_metadata()
    data = data.loc[available]
    result = OrderedDict()
    for part in czech_sorted(data["Městská část"].unique()):
        result[part] = data[data["Městská část"] == part]
    return result
    
    
@lru_cache(20)
def find_points(address=None, altitude_range=None, greenery_range=None):
    """All points at an address.
    
    Returns
    -------
    points : pd.DataFrame
        Empty or non-empty
    """
    data = get_all_point_metadata()
    if address:
        data = data[data["Adresa"] == address]
    if altitude_range:
        data = data[(data["vyska"] >= altitude_range[0]) & (data["vyska"] <= altitude_range[1])]
    if greenery_range:
        data = data[(data["greenery"] >= greenery_range[0]) & (data["greenery"] <= greenery_range[1])]
    available = get_available_points()
    data = data.loc[set(available) & set(data.index)]
    return data
    

def read_data(id):
    """Read the full histogram for a point.
    
    Returns
    -------
    h : physt.histogram_nd.HistogramND
    """
    path = os.path.join("data", "{0}.json".format(id))
    return load_json(path)
    
    
def get_temperature_data(id=None, altitude_range=None, greenery_range=None, axes=("hour", "temperature")):
    # Select data
    if id:
        data = read_data(id)
    else:
        points = find_points(altitude_range=altitude_range, greenery_range=greenery_range)
        histograms = [read_data(id_) for id_ in points.index]
        data = sum(histograms)
        
    data = data.projection(*axes)
    return data
        

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
