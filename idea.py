#! /usr/bin/env python3
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
# from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
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
        self.outerbox = Gtk.VBox()
        self.add(self.outerbox)
        self.outerbox.set_hexpand(True)
        self.outerbox.set_vexpand(True)
        self.toolbox = Gtk.Box()
        self.outerbox.pack_start(self.toolbox, False, False, 0)
        self.set_icon_from_file("logo.png")

        button1 = Gtk.RadioButton.new_from_widget(None)
        button1.set_label("Single sensor")
        button1.connect("toggled", self.on_button_toggled, "1")
        self.toolbox.pack_start(button1, False, False, 0)

        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label("Comparison")
        button2.connect("toggled", self.on_button_toggled, "2")
        self.toolbox.pack_start(button2, False, False, 0)

        self.map_button = Gtk.Button(label="Choose on Map")
        self.map_button.connect("clicked", self.on_map_button_clicked)
        self.toolbox.pack_end(self.map_button, False, False, 0)

        self.mainbox = Gtk.Box()
        self.outerbox.pack_end(self.mainbox, True, True, 0)

        self.filebox = Gtk.Box()
        self.mainbox.pack_end(self.filebox, False, True, 0)

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
        self.scrolledwindow_tree.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        self.outerbox.set_hexpand(False)
        self.outerbox.set_vexpand(True)
        self.scrolledwindow_tree.add(self.filesystemTreeView)
        self.filesystemTreeView.connect("row-activated", self.on_click)
        #self.filebox.pack_start(self.scrolledwindow_tree, True, True, 0)

        self.graph_box = Gtk.VBox()
        self.mainbox.pack_start(self.graph_box, False, False, 0)

        self.opt_box = Gtk.VBox()
        self.graph_box.pack_end(self.opt_box, False, False, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        #self.opt_box.pack_start(self.listbox, False, False, 0)
        self.filebox.pack_start(self.listbox, False, False, 0)

        row = Gtk.ListBoxRow()
        self.listbox.add(row)
        vbox = Gtk.VBox()
        row.add(vbox)
        hbox = Gtk.Box()
        vbox.pack_start(hbox, False, False, 0)
        label = Gtk.Label("X axis: ")
        hbox.pack_start(label, False, False, 0)

        interval_store = Gtk.ListStore(str)
        intervals = ["hour", "month"]
        for interval in intervals:
            interval_store.append([interval])

        self.interval_combo = Gtk.ComboBox.new_with_model(interval_store)
        self.interval_combo.set_active(0)

        self.interval_combo.connect("changed", self.on_interval_combo_changed)
        self.renderer_text = Gtk.CellRendererText()
        self.interval_combo.pack_start(self.renderer_text, False)
        self.interval_combo.add_attribute(self.renderer_text, "text", 0)
        hbox.pack_start(self.interval_combo, False, False, 0)


        row = Gtk.ListBoxRow()
        self.listbox.add(row)
        vbox = Gtk.VBox()
        hbox = Gtk.Box()
        row.add(vbox)
        vbox.pack_start(hbox, False, False, 0)
        check = Gtk.CheckButton("Greenary Filter")
        hbox.pack_start(check, False, False, 0)
        inner_vbox = Gtk.VBox()
        vbox.pack_start(inner_vbox, False, False, 0)
        slider_box = Gtk.Box()
        inner_vbox.pack_start(slider_box, False, False, 15)

        ad1 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)
        ad2 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)

        self.green_min_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1)
        self.green_min_scale.set_valign(Gtk.Align.START)
        self.green_min_scale.set_digits(0)
        self.green_min_scale.set_hexpand(True)
        self.green_min_scale.connect("value-changed", self.scale_moved)

        self.green_max_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad2)
        self.green_max_scale.set_valign(Gtk.Align.START)
        self.green_max_scale.set_digits(0)
        self.green_max_scale.set_hexpand(True)
        self.green_max_scale.connect("value-changed", self.scale_moved)

        slider_box.pack_start(self.green_min_scale, True, True, 0)
        
        slider_box = Gtk.Box()
        inner_vbox.pack_start(slider_box, False, False, 15)

        slider_box.pack_start(self.green_max_scale, True, True, 0)

        row = Gtk.ListBoxRow()
        self.listbox.add(row)
        vbox = Gtk.VBox()
        hbox = Gtk.Box()
        row.add(vbox)
        vbox.pack_start(hbox, False, False, 0)
        check = Gtk.CheckButton("Altitude Filter")
        hbox.pack_start(check, False, False, 0)

        button_box = Gtk.Box()
        inner_vbox.pack_start(button_box, False, False, 15)
        button = Gtk.Button(label="Apply Changes")
        button_box.pack_end(button, False, False, 5)
        button.connect("clicked", self.apply_filters)

        inner_vbox = Gtk.VBox()
        vbox.pack_start(inner_vbox, False, False, 0)
        slider_box = Gtk.Box()
        inner_vbox.pack_start(slider_box, False, False, 15)

        ad1 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)
        ad2 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)

        self.alt_min_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1)
        self.alt_min_scale.set_valign(Gtk.Align.START)
        self.alt_min_scale.set_digits(0)
        self.alt_min_scale.set_hexpand(True)
        self.alt_min_scale.connect("value-changed", self.scale_moved)

        self.alt_max_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad2)
        self.alt_max_scale.set_valign(Gtk.Align.START)
        self.alt_max_scale.set_digits(0)
        self.alt_max_scale.set_hexpand(True)
        self.alt_max_scale.connect("value-changed", self.scale_moved)

        slider_box.pack_start(self.alt_min_scale, True, True, 0)

        slider_box = Gtk.Box()
        inner_vbox.pack_start(slider_box, False, False, 15)

        slider_box.pack_start(self.alt_max_scale, True, True, 0)

        button_box = Gtk.Box()
        inner_vbox.pack_start(button_box, False, False, 15)
        button = Gtk.Button(label="Apply Changes")
        button_box.pack_end(button, False, False, 5)
        button.connect("clicked", self.apply_filters)

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.graph_box.pack_start(self.scrolledwindow, True, True, 0)
        self.gr_id = self.filesystemTreeStore.get(self.filesystemTreeStore.get_iter((5,1)), 1)[0]
        self._plot()

        self.show_all()

    def _plot(self):
        data = get_temperature_data(id=self.gr_id, axes=(self.x, self.y))
        self.show_data(data)

    def on_map_point_clicked(self, data):
        data = get_temperature_data(address=data["Adresa"], axes=(self.x, self.y))
        self.show_data(data)

    def show_data(self, data):
        plot_temperature_data(data, path="output.svg", width= 600, height=400)
        child = self.scrolledwindow.get_child()
        if child:
            self.scrolledwindow.remove(child)
        self.img = Gtk.Image.new_from_file('output.svg')
        self.scrolledwindow.add(self.img)
        self.show_all()

    def on_map_button_clicked(self, widget):
        from map_controller import MapController
        if not self.map_controller:
            self.map_controller = MapController(
                click_callback=self.on_map_point_clicked,
            )
        self.map_controller.send_command(cmd='start')

    def on_button_toggled(self):
        pass

    def scale_moved(self, widget):
        pass

    def apply_filters(self, widget):
        pass

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
            self._plot()

    def on_click(self, widget, coords, wobble):
        self.gr_id = self.filesystemTreeStore.get(self.filesystemTreeStore.get_iter(coords), 1)[0]
        # TODO: replot...
        self._plot()

def main():
    win = IdeaWin()
    Gtk.main()

if __name__ == "__main__":
    main()
    




