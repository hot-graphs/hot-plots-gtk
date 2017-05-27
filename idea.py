#encoding: utf-8
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from gi.repository import Gtk
from physt.io import load_json
import os
from time import time


class IdeaWin(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.connect("delete-event", Gtk.main_quit)
        self.set_default_size(1280, 720)
        self.grid = Gtk.Grid()
        self.add(self.grid)
        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_hexpand(True)
        self.scrolledwindow.set_vexpand(True)
        self.grid.attach(self.scrolledwindow, 0, 0, 6, 1)

        plot_to_file("data/Staré Brno/vsleistr.json")
        self.img = Gtk.Image.new_from_file('output.svg')
        self.scrolledwindow.add(self.img)
        self.show_all()

        filesystemTreeStore = Gtk.TreeStore(str)
        self.parents = {}

        for (path, dirs, files) in os.walk("data"):
            for subdir in dirs:
                self.parents[os.path.join(path, subdir)] = filesystemTreeStore.append(self.parents.get(path, None), [subdir])
            for item in files:
                filesystemTreeStore.append(self.parents.get(path, None), [item])

        self.filesystemTreeView = Gtk.TreeView(filesystemTreeStore)
        renderer = Gtk.CellRendererText()
        filesystemColumn = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.filesystemTreeView.append_column(filesystemColumn)

        self.scrolledwindow_tree = Gtk.ScrolledWindow()
        self.scrolledwindow_tree.set_hexpand(True)
        self.scrolledwindow_tree.set_vexpand(True)

        self.grid.attach(self.scrolledwindow_tree, 7, 0, 1, 1)
        self.scrolledwindow_tree.add(self.filesystemTreeView)
        self.filesystemTreeView.connect("row-activated", self.on_click)


        self.show_all()
        
    def on_click(self, widget, coords, wobble):
        time_s = time()
        dir_num = coords[0]
        file_num = coords[1]

        dirs = []
        for item in os.listdir("data"):
            if os.path.isdir(os.path.join("data", item)):
                dirs.append(item)

        path = dirs[dir_num]
        path = os.path.join("data", path)
        files = os.listdir(path)
        path = os.path.join(path, files[file_num])
        time_s = time() - time_s
        time_s = time()
        self.scrolledwindow.remove(self.img)
        time_s = time()

        plot_to_file(path)
        time_s = time() - time_s
        print("Replotting: ", time_s)
        time_s = time()

        self.img = Gtk.Image.new_from_file('output.svg')
        self.scrolled_window.remove(self.scrolled_window.get_child())
        self.show_all()
        time_s = time() - time_s
        print("Showing: ", time_s)

def read_data(path):
    return load_json(path)

def plot(ax, x="temperature", y="hour", path="data/Staré Brno/vsleistr.json"):
    hist = read_data(path)
    projection = hist.projection(x, y)
    projection.plot(ax=ax)

def plot_to_file(source, path="output.svg", x="hour", y="temperature", dpi=300):
    hist = read_data(source)
    projection = hist.projection(x, y)
    fig, ax = plt.subplots()
    t = time()
    projection.plot("image", ax=ax)
    # print("plotting", time() - t)
    t = time()
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    # print("saving", time() - t)



def main():
    win = IdeaWin()
    Gtk.main()

if __name__ == "__main__":
    main()
    



