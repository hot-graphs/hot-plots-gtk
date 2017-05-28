#! /usr/bin/env python3
import subprocess
import threading
import sys
import os

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
# from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from physt.io import load_json
import os
import gtk
from time import time
from data_source import get_point_tree
import random


class IdeaWin(Gtk.Window):
    def __init__(self):
        GObject.threads_init()
        super().__init__(title="Hot Plots")
        self.x = "hour"
        self.y = "temperature"
        self.spinner = Gtk.Spinner()
        self.map_controller = None
        self.connect("delete-event", self.clean_up)
        self.outerbox = Gtk.VBox()
        self.add(self.outerbox)
        self.outerbox.set_hexpand(True)
        self.outerbox.set_vexpand(True)
        self.toolbox = Gtk.Box()
        self.outerbox.pack_start(self.toolbox, False, False, 0)
        self.set_icon_from_file("logo.png")

        self.cmp_button = Gtk.Button(label="Compare")
        self.cmp_button.connect("clicked", self.on_compare)
        self.cmp_button.set_sensitive(False)
        self.toolbox.pack_start(self.cmp_button, False, False, 0)

        self.single_button = Gtk.Button(label="Single")
        self.single_button.connect("clicked", self.on_single)
        self.single_button.set_sensitive(False)
        self.toolbox.pack_start(self.single_button, False, False, 0)

        self.map_button = Gtk.Button(label="Choose on Map")
        self.map_button.connect("clicked", self.on_map_button_clicked)
        self.toolbox.pack_end(self.map_button, False, False, 0)

        self.mainbox = Gtk.Box()
        self.outerbox.pack_end(self.mainbox, True, True, 0)

        self.comparewindow = Gtk.ScrolledWindow()
        self.comparewindow.set_halign(Gtk.Align.START)
        self.comparewindow.set_hexpand(False)
        self.comparewindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.mainbox.pack_start(self.comparewindow, True, True, 0)

        self.filebox = Gtk.VBox()
        self.filebox.set_halign(Gtk.Align.END)
        self.filebox.set_hexpand(False)
        self.mainbox.pack_end(self.filebox, False, False, 0)

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

        self.listbox_addresses = Gtk.ListBox()
        row = Gtk.ListBoxRow()
        self.listbox_addresses.add(row)
        self.filebox.pack_end(self.listbox_addresses, False, True, 0)

        self.tab_widget = Gtk.Notebook()
        self.filebox.pack_start(self.tab_widget, True, True, 0)
        self.tab_widget.connect('switch-page', self._plot)

        address_scroll_window = Gtk.ScrolledWindow()
        address_scroll_window.add(self.filesystemTreeView)
        self.tab_widget.append_page(address_scroll_window, Gtk.Label('Address'))
        filters_box = Gtk.VBox()
        self.tab_widget.append_page(filters_box, Gtk.Label('Filters'))

        self.filesystemTreeView.connect("row-activated", self.on_click)

        self.graph_box = Gtk.VBox()
        self.mainbox.pack_start(self.graph_box, True, True, 0)

        self.opt_box = Gtk.VBox()
        self.graph_box.pack_end(self.opt_box, False, False, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        #self.opt_box.pack_start(self.listbox, False, False, 0)
        #self.filebox.pack_start(self.listbox, False, False, 0)

        filters_box.pack_start(Gtk.Label("Greenery Filter"), False, False, 0)

        ad1 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)
        ad2 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)

        self.green_min_scale = min_scale = Gtk.Scale(
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
        self.green_max_scale.set_value(100)
        self.green_max_scale.connect("value-changed", self.scale_moved)

        filters_box.pack_start(self.green_min_scale, False, False, 0)

        self.last_slider_move_index = 0
        self.graph_id = 0
        self.run_id = random.randrange(9999, 10000)
        self.worker_process = None

        filters_box.pack_start(self.green_max_scale, False, False, 0)
        min_scale.set_digits(0)
        min_scale.set_hexpand(True)
        min_scale.connect("value-changed", self.scale_moved)


        filters_box.pack_start(Gtk.Box(), False, False, 20)

        row = Gtk.ListBoxRow()
        self.listbox.add(row)
        checkbox = Gtk.Label("Altitude Filter")
        filters_box.pack_start(checkbox, False, False, 0)

        ad1 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)
        ad2 = Gtk.Adjustment(0, 0, 100, 5, 10, 0)

        self.alt_min_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1)
        self.alt_min_scale.set_valign(Gtk.Align.START)
        self.alt_min_scale.set_digits(0)
        self.alt_min_scale.set_hexpand(True)
        self.alt_min_scale.set_range(200, 400)
        self.alt_min_scale.set_value(200)
        self.alt_min_scale.connect("value-changed", self.scale_moved)

        self.alt_max_scale = Gtk.Scale(
            orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad2)
        self.alt_max_scale.set_valign(Gtk.Align.START)
        self.alt_max_scale.set_digits(0)
        self.alt_max_scale.set_hexpand(True)
        self.alt_max_scale.set_range(200, 400)
        self.alt_max_scale.set_value(400)
        self.alt_max_scale.connect("value-changed", self.scale_moved)

        filters_box.pack_start(self.alt_min_scale, False, False, 0)
        filters_box.pack_start(self.alt_max_scale, False, False, 0)

        filters_box.pack_start(Gtk.Box(), True, True, 100)

        self.x_axis_tab_widget = Gtk.Notebook()
        self.filebox.pack_start(self.tab_widget, True, True, 0)
        self.x_axis_tab_widget .connect('switch-page', self._plot)

        address_scroll_window = Gtk.ScrolledWindow()
        address_scroll_window.add(self.filesystemTreeView)
        self.x_axis_tab_widget .append_page(address_scroll_window, Gtk.Label('By Month'))
        filters_box = Gtk.VBox()
        self.x_axis_tab_widget.append_page(filters_box, Gtk.Label('By Hour'))

        self.filebox.pack_end(self.x_axis_tab_widget , False, False, 0)

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
        self.graph_box.pack_start(self.scrolledwindow, True, True, 0)

        self.gr_id = self.filesystemTreeStore.get(self.filesystemTreeStore.get_iter((5,1)), 1)[0]
        self._plot()

        self.show_all()

        self.x_axis_tab_widget.set_current_page(1)

    def _plot(self, *args):
        print(self.x_axis_tab_widget.get_current_page())
        if self.x_axis_tab_widget.get_current_page() == 1:
            self.x = 'month'
        else:
            self.x = 'hour'
        if self.tab_widget.get_current_page() == 1:
            greenery_range = (
                self.green_min_scale.get_value()/100,
                self.green_max_scale.get_value()/100,
            )
            altitude_range = (
                int(self.alt_min_scale.get_value()),
                int(self.alt_max_scale.get_value()),
            )
            self.show_temperature_data(
                greenery_range=greenery_range,
                altitude_range=altitude_range,
                axes=(self.x, self.y),
            )
        else:
            self.show_temperature_data(id=self.gr_id, axes=(self.x, self.y))

    def on_map_point_clicked(self, data):
        print('!')
        self.show_temperature_data(address=data["Adresa"], axes=(self.x, self.y))

    def scale_moved(self, widget):
        self.last_slider_move_index += 1
        GLib.timeout_add(10, self.apply_scale_moves, self.last_slider_move_index)

    def apply_scale_moves(self, index):
        if self.last_slider_move_index == index:
            self._plot()

    def show_temperature_data(self, **kwargs):
        args = [sys.executable, 'batch.py']
        if 'altitude_range' in kwargs:
            args.extend(['--altitude', '{},{}'.format(*kwargs['altitude_range'])])
        if 'greenery_range' in kwargs:
            args.extend(['--greenery', '{},{}'.format(*kwargs['greenery_range'])])
        if 'id' in kwargs:
            args.extend(['--id', kwargs['id']])
        if 'address' in kwargs:
            args.extend(['--address', kwargs['address']])
        args.extend(['--x', self.x])
        args.extend(['--y', self.y])
        args.extend(["--width=640", "--height=480"])
        self.graph_id += 1
        outfile = 'output-{}-{}.png'.format(self.run_id, self.graph_id)
        args.extend([outfile])

        if self.worker_process:
            self.worker_process.kill()

        print('exec', args)
        self.worker_process = worker_process = subprocess.Popen(args)

        child = self.scrolledwindow.get_child()
        if child:
            self.scrolledwindow.remove(child)
        self.scrolledwindow.add(self.spinner)
        self.spinner.start()

        def _target():
            try:
                worker_process.communicate()
                print('done', worker_process.returncode, outfile)
                if worker_process.returncode == 0:
                    GLib.idle_add(self.show_image, outfile)
                else:
                    if os.path.exists(outfile):
                        os.unlink(outfile)
            except Exception:
                if os.path.exists(outfile):
                    os.unlink(outfile)
                raise

        threading.Thread(target=_target).start()

    def show_image(self, filename):
        child = self.scrolledwindow.get_child()
        if child:
            self.scrolledwindow.remove(child)
        print('show', filename)
        self.img = Gtk.Image.new_from_file(filename)
        self.scrolledwindow.add(self.img)
        self.show_all()
        if os.path.exists(filename):
            os.unlink(filename)
        self.cmp_button.set_sensitive(True)


    def on_compare(self, *args):
        self.single_button.set_sensitive(True)

        child = self.comparewindow.get_child()
        if child:
            self.comparewindow.remove(child)

        pixbuf = self.img.get_pixbuf()
        img = Gtk.Image.new_from_pixbuf(pixbuf)

        self.comparewindow.add(img)
        self.show_all()

    def on_single(self, *args):
        self.single_button.set_sensitive(False)

        child = self.comparewindow.get_child()
        if child:
            self.comparewindow.remove(child)

    def on_map_button_clicked(self, widget):
        from map_controller import MapController
        if not self.map_controller:
            self.map_controller = MapController(
                click_callback=self.on_map_point_clicked,
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
    




