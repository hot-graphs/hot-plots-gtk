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
    
    
def get_temperature_data(id=None, address=None, altitude_range=None, greenery_range=None,
                         year=None, month=None, hour=None,
                         axes=None):
    """Get a histogram based on various criteria.
    
    Parameters
    ----------
    id : str
    year : int
        In range 2013..2015
    month : int
    hour : int
    address : str
    altitude_range : (float, float)
    greenery_range : (float, float)
    axes : tuple(str...)
        All axes we want to have in the final data as projection.
    
    Returns
    -------
    h : physt.histogram_base.HistogramBase
    """
    # Select data
    if id:
        data = read_data(id)
    else:
        points = find_points(address=address, altitude_range=altitude_range, greenery_range=greenery_range)
        histograms = [read_data(id_) for id_ in points.index]
        data = sum(histograms)
        
    # Do the projections / slicing
    if year:
        data = data.select("year", year - 2013)
    if month:
        data = data.select("month", month - 1)
    if hour:
        data = data.select("hour", hour)
    
    if axes:
        data = data.projection(*axes)
    return data


def plot_temperature_data(histogram, path=None, ax=None, width=1024, height=800, histtype=None):
    """Plot histogram data.
    
    Parameters
    ----------
    histogram: physt.histogram_base.HistogramBase
    path: str (optional)
    ax: matplotlib.pyplot.Axes (optional)
    width: int
    height: int
    histtype: str (optional)
    
    Returns
    -------
    None
    
    """
    if not ax:
        fig, ax = plt.subplots(figsize=(10, height/width * 10))
    else:
        fig = ax.figure
    if histtype is None:
        histtype = ["bar", "image"][histogram.ndim - 1]
    histogram.plot(kind=histtype, ax=ax)
    ax.set_ylim(-20, 40)
    if path:
        fig.tight_layout()
        fig.savefig(path, dpi=width/10)
        
        
# Deprecated!
def plot_to_axis(source, ax, x="hodina", y="teplota"):
    hist = read_data(source)
    projection = hist.projection(x, y)
    projection.plot(ax = ax)

    
# Deprecated!
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
