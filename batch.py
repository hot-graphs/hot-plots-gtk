#!/usr/bin/env python3
import click
from data_source import get_temperature_data
from data_source import plot_temperature_data


@click.command()
@click.option("--altitude", default="", help="Select a comma-separated temperature range like \"200,300\"")
@click.option("--greenery", default="", help="Select a comma-separated greenery range like \"0.1,0.5\"")
@click.option("--month", default=-1, help="Select a month")
@click.option("--hour", default=-1, help="Select a one-hour slice of a day")
@click.option("--year", default=-1, help="Select a year")
@click.option("--id", default="", help="Select concrete ID of a sensor")
@click.option("--x", default="month", help="What should be displayed on horizontal axis")
@click.option("--y", default="temperature", help="What should be displayed on vertical axis")
@click.option("--width", default=1024)
@click.option("--height", default=768)
@click.argument("output_path")
def batch(x, y, id, output_path, month, hour, year, altitude, greenery, width, height):
    if not id:
        id = None
    if hour < 0:
        hour = None
    if month < 0:
        month = None
    if year < 0:
        year = None
    if altitude:
        altitude=tuple((int(a) for a in altitude.split(",")))
        if len(altitude) != 2:
            print("Altitude must be set as two comma-separated values")
            exit(-1)
    else:
        altitude=None
        
    if greenery:
        greenery=tuple((float(a) for a in greenery.split(",")))
        if len(greenery) != 2:
            print("Greenery must be set as two comma-separated values")
            exit(-1)
    else:
        greenery=None
    try:
        data = get_temperature_data(id=id, hour=hour, month=month, year=year, altitude_range=altitude, greenery_range=greenery, axes=(x, y))
    except RuntimeError as err:
        print("Cannot read data.")
        print(err)
        exit(-1)        

    plot_temperature_data(data, output_path, width=width, height=height)
    print("Output written to {0}.".format(output_path))
    
    
if __name__ == "__main__":
    batch()