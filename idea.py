#! /usr/bin/env python3
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from gi.repository import Gtk
from gi.repository import GObject
from physt.io import load_json
import os
from time import time
from data_source import get_point_tree


class IdeaWin(Gtk.Window):
    def __init__(self):
        GObject.threads_init()
        super().__init__(title="Hot Plots")
        self.x = "hour"
        self.y = "temperature"
        self.map_controller = None
        self.connect("delete-event", self.clean_up)
        self.set_default_size(1280, 720)
        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.scrolledwindow_opts = Gtk.ScrolledWindow()
        self.scrolledwindow_opts.set_hexpand(True)
        self.scrolledwindow_opts.set_vexpand(True)
        self.grid.attach(self.scrolledwindow_opts, 0, 0, 1, 1)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.scrolledwindow_opts.add(self.listbox)

        self.x_control_row = Gtk.ListBoxRow()
        self.x_control_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.x_control_row.add(self.x_control_hbox)

        self.listbox.add(self.x_control_row)

        self.map_button = Gtk.Button(label="Open Map")
        self.map_button.connect("clicked", self.on_map_button_clicked)
        self.map_row = Gtk.ListBoxRow()
        self.map_row.add(self.map_button)
        self.listbox.add(self.map_row)

        interval_store = Gtk.ListStore(str)
        intervals = ["hour", "month"]
        for interval in intervals:
            interval_store.append([interval])

        self.interval_combo = Gtk.ComboBox.new_with_model(interval_store)
        self.interval_combo.set_active(0)

        self.interval_combo.connect("changed", self.on_interval_combo_changed)
        self.renderer_text = Gtk.CellRendererText()
        self.interval_combo.pack_start(self.renderer_text, True)
        self.interval_combo.add_attribute(self.renderer_text, "text", 0)

        self.x_control_hbox.pack_end(self.interval_combo, True, True, 5)

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_hexpand(True)
        self.scrolledwindow.set_vexpand(True)
        self.grid.attach(self.scrolledwindow, 1, 0, 5, 1)
        self.path = "data/vsleistr.json"
        self._plot_to_file()
        self.img = Gtk.Image.new_from_file('output.svg')
        self.scrolledwindow.add(self.img)

        self.filesystemTreeStore = Gtk.TreeStore(str, str)
        parents = {}
        # self.paths = []

        for part, points in get_point_tree().items():
            
        # for (path, dirs, files) in os.walk("data"):
            #print(path)
            #print(dirs)
            #print(files)
            parents[part] = self.filesystemTreeStore.append(None, [part, None])
            for point in points.iterrows():
                self.filesystemTreeStore.append(parents.get(part, None), [point[1]["Adresa"], str(point[0])])
            #for item in files:
            
            # self.paths.append((path, dirs, files))


        self.filesystemTreeView = Gtk.TreeView(self.filesystemTreeStore)
        renderer = Gtk.CellRendererText()
        filesystemColumn = Gtk.TreeViewColumn("Files", renderer, text=0)
        self.filesystemTreeView.append_column(filesystemColumn)

        self.scrolledwindow_tree = Gtk.ScrolledWindow()
        self.scrolledwindow_tree.set_hexpand(True)
        self.scrolledwindow_tree.set_vexpand(True)

        self.grid.attach(self.scrolledwindow_tree, 7, 0, 1, 1)
        self.scrolledwindow_tree.add(self.filesystemTreeView)
        self.filesystemTreeView.connect("row-activated", self.on_click)

        self.show_all()

    def _replot(self):
        child = self.scrolledwindow.get_child()
        if child:
            self.scrolledwindow.remove(child)
        self._plot_to_file()
        self.img = Gtk.Image.new_from_file('output.svg')
        self.scrolledwindow.add(self.img)
        self.show_all()

    def _plot_to_file(self, path="output.svg", dpi=300):
        hist = read_data(self.path)
        projection = hist.projection(self.x, self.y)
        fig, ax = plt.subplots()
        t = time()
        projection.plot("image", ax=ax)
        # print("plotting", time() - t)
        t = time()
        fig.tight_layout()
        fig.savefig(path, dpi=dpi)
        # print("saving", time() - t)

    def on_map_button_clicked(self, widget):
        from map_controller import MapController
        self.map_controller = MapController(
            click_callback=lambda data: print('gtk got:', data),
        )
        self.map_controller.send_command(cmd='start')

    def clean_up(self, *args):
        if self.map_controller:
            self.map_controller.send_command_if_open(cmd='stop')

        Gtk.main_quit()

    def on_interval_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            interval = model[tree_iter][0]
            print("Selected: interval=%s of type %s" % (interval, type(interval)))
            self.x = interval
            self._replot()

    def on_click(self, widget, coords, wobble):
        time_s = time
        id_ = self.filesystemTreeStore.get(self.filesystemTreeStore.get_iter(coords), 1)[0]
        # TODO: replot...
        #dir_num = coords[0]
        #file_num = coords[1]
        # print(coords)

def read_data(path):
    return load_json(path)

def main():
    win = IdeaWin()
    Gtk.main()

if __name__ == "__main__":
    main()
    




