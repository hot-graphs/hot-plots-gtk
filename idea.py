from matplotlib.figure import Figure
from numpy import arange, pi, random, linspace
import matplotlib.cm as cm
#Possibly this rendering backend is broken currently
#from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from gi.repository import Gtk

class IdeaWin(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.connect("delete-event", Gtk.main_quit)
        self.set_default_size(1280, 720)
        self.show_all()
    def add_plot(self, x, y):
        self.set_default_size(1280, 720)

        fig = Figure(figsize=(5,5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(x, y)

        canvas = FigureCanvas(fig)
        self.add(canvas)
        self.show_all()
        
def get_xy():
    x = [1, 3, 8, 11] 
    y = [2, 3, 10, 20]
    return (x, y) 

def main():
    win = IdeaWin()
    x, y = get_xy()
    win.add_plot(x, y)
    Gtk.main()

if __name__ == "__main__":
    main()
    



