#!/usr/bin/env python3
import click
from data_source import get_temperature_data
from data_source import plot_temperature_data


@click.command()
@click.option("--month", default=-1, help="Select a month")
@click.option("--hour", default=-1, help="Select a one-hour slice of a day")
@click.option("--id", default="", help="Select concrete ID of a sensor")
@click.option("--x", default="month", help="What should be displayed on horizontal axis")
@click.option("--y", default="temperature", help="What should be displayed on vertical axis")
@click.argument("output_path")
def batch(x, y, id, output_path, month, hour):
    if not id:
        id = None
    if hour < 0:
        hour = None
    if month < 0:
        month = None
    try:
        data = get_temperature_data(id=id, hour=hour, month=month, axes=(x, y))
    except:
        print("Cannot read data.")
        exit(-1)
    plot_temperature_data(data, output_path)
    print("Output written to {0}.".format(output_path))
    
    
if __name__ == "__main__":
    batch()