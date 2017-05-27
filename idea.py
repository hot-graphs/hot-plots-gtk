from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from gi.repository import Gtk
from physt.io import load_json
from functools import lru_cache
import os

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

        self.fig = Figure(figsize=(5,5), dpi=100)
        self.fig.ax = self.fig.add_subplot(111)

        plot(self.fig.ax)
        self.canvas = FigureCanvas(self.fig)
        self.scrolledwindow.add(self.canvas)

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

        self.fig = Figure(figsize=(5,5), dpi=100)
        self.fig.ax = self.fig.add_subplot(111)

        plot(self.fig.ax)
        self.canvas = FigureCanvas(self.fig)
        self.scrolledwindow.add(self.canvas)
        self.show_all()

@lru_cache(1)
def read_data(path):
    return load_json(path)

def plot(ax, x="temperature", y="hour", path="data/Staré Brno/vsleistr.json"):
    hist = read_data(path)
    projection = hist.projection(x, y)
    projection.plot(ax=ax)

def main():
    win = IdeaWin()
    win.connect("delete-event", Gtk.main_quit)
    Gtk.main()

if __name__ == "__main__":
    main()
    



