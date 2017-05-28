"""Functions to prepare aggregate data from raw CSV data."""

import os
import numpy as np
import pandas as pd
from physt import histogramdd


def parse_data_file(path, min_year=2013, max_year=2015, min_temp=-50, max_temp=50):
    """Prepare dataframe from CSV source.
    
    Parameters
    ----------
    path : str
        Path to the CSV file (can be a zip file containing a single CSV inside)
    min_year : int
    max_year : int
    min_temp : float
    max_temp : float
    
    Returns
    -------
    data : pd.DataFrame 
        containing the following:
    
        datetime         datetime64[ns]
        temperature             float64
        id                       object
        year                      int64
        month                     int64
        hour                      int64
        day_of_year               int64
        day_of_week               int64
        second_of_day             int64
    """
    
    data = pd.read_csv(path, delimiter=";", decimal=",", header=None, names=["datetime", "place", "temperature"])
    data["datetime"] = pd.to_datetime(data["datetime"])
    data["id"] = data.place.str.extract("(?<=\\\\)(.*)(?=\\\\)", expand=False).str.lower()
    data["year"] = data.datetime.dt.year
    data["month"] = data.datetime.dt.month
    data["hour"] = data.datetime.dt.hour
    data["day_of_year"] = data.datetime.dt.dayofyear
    data["day_of_week"] = (data.datetime.dt.dayofweek - 1) % 7 + 1
    data["second_of_day"] = data.datetime.dt.hour * 3600 + data.datetime.dt.minute * 60 + data.datetime.dt.second

    # Clean up
    data = data[(data["temperature"] <= max_temp) & (data["temperature"] >= min_temp)]
    data = data[(data["year"] <= max_year) & (data["year"] >= min_year)] 
    return data.drop("place", axis=1)
    
    
def create_histogram(data, id):
    """From dataset, create a histogram for one sensor.
    
    Returns
    -------
    histogram : physt.histogram_nd.HistogramND
        4D histogram along these axes: year, month, hour, temperature
    """
    subdata = data[data.id == id]
    array = np.concatenate([item[:, np.newaxis] for item in [subdata.year, subdata.month, subdata.hour, subdata.temperature]], axis=1)
    return histogramdd(array,
                       ("integer", "integer", "fixed_width", "fixed_width"),
                       bin_width=(1, 1, 1, 1), adaptive=True,
                       name=id,
                       axis_names=["year", "month", "hour", "temperature"])


def create_histogram_files(data, dir_path="data"):
    """For each sensor in a dataset, create a 4D histogram.
    
    Parameters
    ----------
    data : pd.DataFrame
        Dataset with data from different sensors.
        (as prepared using parse_data_file)
    
    Returns
    -------
    files : list
        Names of files produced
    """
    os.makedirs(dir_path, exist_ok=True)
    result = []
    for id in data["id"].unique():
        histogram = create_histogram(data, id)
        path = os.path.join(dir_path, "{0}.json".format(id))
        result.append(path)
        histogram.to_json(path=path)
    return result