#! /usr/bin/env python3
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from gi.repository import Gtk
from gi.repository import GObject
from physt.io import load_json
import os
from data_source import *
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

        button1 = Gtk.RadioButton.new_from_widget(None)
        button1.set_label("Single sensor")
        button1.connect("toggled", self.on_button_toggled, "1")
        self.grid.attach(button1, 0, 0, 1, 1)

        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label("Comparison")
        button2.connect("toggled", self.on_button_toggled, "2")
        self.grid.attach(button2, 1, 0, 1, 1)

        self.map_button = Gtk.Button(label="Open Map")
        self.map_button.connect("clicked", self.on_map_button_clicked)
        self.grid.attach(self.map_button, 3, 0, 1, 1)

        self.scrolledwindow_opts = Gtk.ScrolledWindow()
        self.scrolledwindow_opts.set_hexpand(True)
        self.scrolledwindow_opts.set_vexpand(True)

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

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_hexpand(True)
        self.scrolledwindow.set_vexpand(True)
        self.grid.attach(self.scrolledwindow, 1, 1, 5, 1)

        self.filesystemTreeStore = Gtk.TreeStore(str, str)
        parents = {}
        # self.paths = []

        for part, points in get_point_tree().items():
            parents[part] = self.filesystemTreeStore.append(None, [part, None])
            for point in points.iterrows():
                self.filesystemTreeStore.append(parents.get(part, None), [point[1]["Adresa"], str(point[0])])


        self.filesystemTreeView = Gtk.TreeView(self.filesystemTreeStore)
        renderer = Gtk.CellRendererText()
        filesystemColumn = Gtk.TreeViewColumn("Files", renderer, text=0)
        self.filesystemTreeView.append_column(filesystemColumn)

        self.scrolledwindow_tree = Gtk.ScrolledWindow()
        self.scrolledwindow_tree.set_hexpand(True)
        self.scrolledwindow_tree.set_vexpand(True)

        self.grid.attach(self.scrolledwindow_tree, 7, 1, 1, 1)
        self.scrolledwindow_tree.add(self.filesystemTreeView)
        self.filesystemTreeView.connect("row-activated", self.on_click)

        self.show_all()

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

    def on_button_toggled(self, widget, name):
        pass

    def on_interval_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            interval = model[tree_iter][0]
            print("Selected: interval=%s of type %s" % (interval, type(interval)))
            self.x = interval
            self._replot()

    def on_click(self, widget, coords, wobble):
        gr_id = self.filesystemTreeStore.get(self.filesystemTreeStore.get_iter(coords), 1)[0]
        # TODO: replot...
        data = get_temperature_data(id=gr_id, axes=("hour", "temperature"))
        plot_temperature_data(data, path="output.svg")
        child = self.scrolledwindow.get_child()
        if child:
            self.scrolledwindow.remove(child)
        self.img = Gtk.Image.new_from_file('output.svg')
        self.scrolledwindow.add(self.img)
        self.show_all()
        """hist = read_data(self.path)
        projection = hist.projection(self.x, self.y)
        fig, ax = plt.subplots()
        t = time()
        projection.plot("image", ax=ax)
        # print("plotting", time() - t)
        t = time()
        fig.tight_layout()
        fig.savefig(path, dpi=dpi)
        # print("saving", time() - t)"""

        """child = self.scrolledwindow.get_child()
        if child:
            self.scrolledwindow.remove(child)
        self._plot_to_file()
        self.img = Gtk.Image.new_from_file('output.svg')
        self.scrolledwindow.add(self.img)
        self.show_all()"""

def main():
    win = IdeaWin()
    Gtk.main()

if __name__ == "__main__":
    main()
    




