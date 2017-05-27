from physt.io import load_json
from time import time
import matplotlib.pyplot as plt


def read_data(path="data/Vinohrady.json"):
    return load_json(path)

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
