import sys
import os.path
import threading
import json
import traceback

from kivy.app import App
from kivy.garden.mapview import MapView, MapMarker, MarkerMapLayer
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy import graphics
from kivy.properties import NumericProperty, ObjectProperty, ListProperty, \
    AliasProperty, BooleanProperty, StringProperty
from kivy.core.window import Window
import pandas
import click


# A big hack: we stretch the longitude (x coord) by a constant that makes "circles" in WGS 84 circular
# ideally we'd use another projection, but that would take time
X_STRETCH = 1.531


def arc_params(row, column_name, rpos, mapview):
    value = row[column_name]
    print(column_name)
    if column_name == 'avgtemp':
        minimum = mapview.min_avg_temp
        maximum = mapview.max_avg_temp
        normalized_avgtemp = (value - minimum) / (maximum - minimum)
        n2 = normalized_avgtemp * 2
        if normalized_avgtemp < 1/2:
            return {'rgba': (n2, 0, 1, 1)}
        else:
            return {'rgba': (1, 0, 1-n2, 1)}
    else:
        return {'rgba': (0, rpos, 0, 1), 'end': 360*value}


class CustomMapView(MapView):
    def __init__(self, *args, radiuses, **kwargs):
        self.active_marker = None
        self.radiuses = radiuses
        super().__init__(*args, **kwargs)

        self.bind(
            lat=self.send_position,
            lon=self.send_position,
            zoom=self.send_position,
        )

        shade_layer = MarkerMapLayer()
        self.add_layer(shade_layer)
        self.shade_marker = ShadeMapMarker(lat=0, lon=0, radiuses=self.radiuses)
        self.add_marker(self.shade_marker, layer=shade_layer)

        self.marker_layer = MarkerMapLayer()
        self.add_layer(self.marker_layer)

        #Window.bind(mouse_pos=self.update_mouse_pos)

    def update_mouse_pos(self, window, mouse_pos):
        print('mouse:', mouse_pos)

    def set_active_marker(self, marker):
        if self.active_marker:
            self.active_marker.set_active(False)
            self.shade_marker.active = False
        self.active_marker = marker
        if marker:
            marker.set_active(True)
            self.shade_marker.lat = marker.lat
            self.shade_marker.lon = marker.lon
            data = marker.row.to_dict()
            data['location'] = marker.row.name
            send_command(
                cmd='point_selected',
                row=data,
            )
            self.shade_marker.active = True
        else:
            self.shade_marker.active = False
        self.shade_marker.reposition()

    def send_position(self, *args):
        send_command(
            cmd='pos',
            lat=self.lat,
            lon=self.lon,
            zoom=self.zoom,
        )


class ShadeMapMarker(MapMarker):
    def __init__(self, *args, radiuses, **kwargs):
        self.active_marker = None
        self.radiuses = radiuses
        kwargs['size'] = 40, 40
        kwargs['anchor_y'] = 0.5
        super().__init__(*args, **kwargs)
        self.active = False

        self.canvas.clear()
        with self.canvas:
            self.shade_color = graphics.Color(1, 1, 1, 0)
            self.radius_circles = [graphics.Ellipse() for i in range(3)]
        self.bind(pos=self.reposition)

    def get_mapview(self):
        mapview = self
        while not isinstance(mapview, CustomMapView):
            mapview = mapview.parent
            if mapview is None:
                return
        return mapview

    def reposition(self, *args):
        if self.active:
            self.shade_color.rgba = 1, 1, 1, 0.3
            mapview = self.get_mapview()
            if mapview is None:
                print('NO MAPVIEW!')
                Clock.schedule_once(self.reposition, 0)
                return
            for i, (r, circle) in enumerate(zip(self.radiuses, self.radius_circles)):
                ry = float(r)
                rx = ry * X_STRETCH
                xm, ym, = mapview.get_window_xy_from(self.lat, self.lon, zoom=mapview.zoom)
                x1, y1 = mapview.get_window_xy_from(self.lat - ry, self.lon - rx, zoom=mapview.zoom)
                x2, y2 = mapview.get_window_xy_from(self.lat + ry, self.lon + rx, zoom=mapview.zoom)
                circle.pos = x1, y1
                circle.size = x2-x1, y2-y1
        else:
            self.shade_color.rgba = 1, 1, 1, 0

    def collide_point(self, x, y):
        return False


class CustomMapMarker(MapMarker):
    def __init__(self, *args, row, radiuses, columns, mapview, **kwargs):
        self.row = row
        self.radiuses = radiuses
        self.columns = columns
        self.lat, self.lon = row.name
        super().__init__(*args, **kwargs)
        self.anchor_x = 0
        self.anchor_y = 0
        self.radius = 20
        self.size = self.radius * 2, self.radius * 2
        self.active = False

        self.canvas.clear()

        with self.canvas.after:
            graphics.PushMatrix()
            self.translation = graphics.Translate(0, 0)

            self.border_color = graphics.Color(0, 0, 0, 0.3)
            sz = self.size[0] + 2
            hsz = -sz/2
            graphics.Ellipse(size=(sz, sz), pos=(hsz, hsz))

            n = len(columns)
            for pos, r in enumerate(reversed(columns)):
                value = self.row[str(r)]
                rpos = (n - pos) / n
                params = arc_params(row, r, rpos, mapview)
                sz = self.size[0] / n * (n - pos)
                hsz = -sz/2
                graphics.Color(1-rpos/20, 1-rpos/20, 1, 1)
                graphics.Ellipse(size=(sz, sz), pos=(hsz, hsz))
                if value:
                    graphics.Color(*params['rgba'])
                    graphics.Ellipse(size=(sz, sz), pos=(hsz, hsz), angle_end=params.get('end', 360))
            graphics.PopMatrix()
        self.bind(pos=self.reposition)
        self.set_active(False)

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            mapview = self.get_mapview()
            if mapview is None:
                return
            if self.active:
                mapview.set_active_marker(None)
            else:
                mapview.remove_widget(self)
                mapview.add_marker(self, layer=mapview.marker_layer)
                mapview.set_active_marker(self)
            return True

    def set_active(self, active):
        self.canvas.before.clear()
        self.active = active
        self.reposition()
        if active:
            self.border_color.rgba = 0, 0, 0, 0.5
        else:
            self.border_color.rgba = 0, 0, 0, 0.1

    def collide_point(self, x, y):
        mapview = self.get_mapview()
        if mapview is None:
            return
        lat, lon = mapview.get_window_xy_from(self.lat, self.lon, zoom=mapview.zoom)
        x -= self.pos[0]
        y -= self.pos[1]
        return x**2 + y**2 < self.radius ** 2

    def get_mapview(self):
        mapview = self
        while not isinstance(mapview, CustomMapView):
            mapview = mapview.parent
            if mapview is None:
                return
        return mapview

    def reposition(self, *args):
        self.translation.xy = self.pos


def send_command(**kwargs):
    print(json.dumps(kwargs), flush=True)


class MapViewApp(App):
    def __init__(self, points, radiuses, columns, *args, **kwargs):
        kwargs.setdefault('icon', 'logo.png')
        super().__init__(*args, **kwargs)
        self.points = points
        self.radiuses = radiuses
        self.columns = columns

        self.min_avg_temp = points['avgtemp'].min()
        self.max_avg_temp = points['avgtemp'].max()

        input_thread = threading.Thread(target=self.do_input)
        input_thread.daemon = True
        input_thread.start()

        self.bind(on_stop=lambda *a: send_command(cmd='stop'))
        send_command(cmd='started')

    def build(self):
        VEJROSTOVA = {'zoom': 18, 'lat': 49.22025828658787, 'lon': 16.50821292434091}
        JINDRICHOVA = {'zoom': 18, 'lat': 49.213795607926734, 'lon': 16.58214582519531}
        BRNO = {'zoom': 13, 'lat': 49.205243666554054, 'lon': 16.58976135996045}
        self.mapview = CustomMapView(**BRNO, radiuses=self.radiuses)
        self.points_iter = iter(enumerate(self.points.iterrows()))
        self.add_next_points()
        return self.mapview

    def add_next_points(self, *args):
        for n in range(50):
            try:
                i, (idx, row) = next(self.points_iter)
            except StopIteration:
                print('loaded', file=sys.stderr)
                send_command(cmd='loaded')
                return
            #mark = CustomMapMarker(lon=row['GPS lon'], lat=row['GPS lat'], source='noun_9209_cc_red.png')
            mark = CustomMapMarker(row=row, radiuses=self.radiuses, columns=self.columns, mapview=self)
            self.mapview.add_marker(mark, layer=self.mapview.marker_layer)
        Clock.schedule_once(self.add_next_points, 0)
        print('{}/{}'.format(i, len(self.points)), file=sys.stderr)

    def do_input(self):
        for line in sys.stdin:
            try:
                print('map: got ', line, file=sys.stderr)
                data = json.loads(line)
                cmd = data['cmd']
                self.handle_command(cmd, data)
            except Exception:
                traceback.print_exc()

    def handle_command(self, cmd, data):
        if cmd == 'stop':
            self.stop()
        elif cmd == 'pos':
            if 'zoom' in data:
                self.mapview.zoom = int(data['zoom'])
            self.mapview.center_on(float(data['lat']), float(data['lon']))
        else:
            print('map: ignoring command', cmd, data, file=sys.stderr)


@click.command()
def main():
    radiuses = 0.001, 0.005, 0.01
    adresace = pandas.read_csv('teplarny-adresace-teplota.csv', sep=';').set_index(['GPS lat', 'GPS lon'])
    radiuses = [str(r) for r in radiuses]
    columns = radiuses + ['avgtemp']
    points = adresace.loc[:, columns + ['Adresa']].drop_duplicates()
    MapViewApp(points, radiuses, columns).run()

if __name__ == '__main__':
    main()
