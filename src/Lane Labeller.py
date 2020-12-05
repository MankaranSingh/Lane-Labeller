import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from tkinter import Tk, Frame, BOTH, TOP, BOTTOM, Button, YES
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
import cv2

def config_plot():
    fig, ax = plt.subplots()
    toolbar = fig.canvas.manager.toolbar
    return (fig, ax, toolbar)

class matplotlibSwitchGraphs:
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        self.fig, self.ax, self.toolbar = config_plot()
        self.lanes = ['r', 'g', 'b', 'y']
        self.lane_idx = 0
        self.canvas = FigureCanvasTkAgg(self.fig, self.master)  
        self.config_window()
        self.frame.pack(expand=YES, fill=BOTH)
        self.epsilon = 7
        self.active_point = None
        self.xs = []
        self.ys = []
        self.categories = []
        self.line = None
        self.point_references = []

    def config_window(self):
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas.mpl_connect('button_release_event', self.button_release_callback)
        toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.button = Button(self.master, text="Quit", command=self._quit)
        self.button.pack(side=BOTTOM)
        self.lane_switch = Button(self.master, text="Switch Lane", command=self.switch_lane)
        self.lane_switch.pack(side=BOTTOM)
        self.button_image = Button(self.master, text="Load Image", command=self.load_image)
        self.button_image.pack(side=BOTTOM)
        self.ax.set(title=self.lanes[self.lane_idx])

    def on_key_press(self, event):
        print("you pressed {}".format(event.key))

    def on_click(self, event):
        print("you pressed {}".format(event.button))
        ret = False
        if not event.inaxes or self.canvas.toolbar._lastCursor in [3, 2]:
            return
        if len(self.xs) > 0:
            ret, self.active_point = self.get_ind_under_point(event)
        print(self.active_point)
        if ret or event.button==3:
            if event.button == 3 and ret:
                self.remove_active_point()
            return
        idx = len(self.xs)
        self.xs.insert(idx, event.xdata)
        self.ys.insert(idx, event.ydata)
        self.categories.insert(idx, self.lanes[self.lane_idx])
        point_reference = self.ax.plot(event.xdata, event.ydata, self.lanes[self.lane_idx] +'o')
        self.point_references.insert(idx, point_reference[0])
        self.canvas.draw_idle()

    def load_image(self):
        img = cv2.imread('8.jpg')[:, :, (2, 1, 0)]
        self.image = img
        self.ax.imshow(img)
        self.canvas.draw()

    def _quit(self):
        self.master.quit()  # stops mainloop

    def switch_lane(self):
        self.lane_idx = (self.lane_idx + 1) % len(self.lanes)
        self.ax.set(title=self.lanes[self.lane_idx])
        self.canvas.draw_idle()

    def get_ind_under_point(self, event):
        is_available = True
        'get the index of the vertex under point if within epsilon tolerance'
        t = self.ax.transData.inverted()
        tinv = self.ax.transData
        xy = t.transform([event.x,event.y])
        x, yvals = np.array(self.xs), np.array(self.ys)
        xr = np.reshape(x,(np.shape(x)[0],1))
        yr = np.reshape(yvals,(np.shape(yvals)[0],1))
        xy_vals = np.append(xr,yr,1)
        xyt = tinv.transform(xy_vals)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.hypot(xt - event.x, yt - event.y)
        indseq, = np.nonzero(d == d.min())
        ind = indseq[0]
        if d[ind] >= self.epsilon:
            is_available = False
        return is_available, ind

    def motion_notify_callback(self, event):
        if self.active_point is None:
            return
        if event.inaxes is None or event.button != 1:
            return
        self.ys[self.active_point] = event.ydata
        self.xs[self.active_point] = event.xdata
        self.update_point()
        self.canvas.draw_idle()

    def button_release_callback(self, event):
        if event.button == 1:
            self.active_point = None
            
    def remove_active_point(self):
        if self.active_point is not None:
            self.point_references[self.active_point].remove()
            self.point_references.pop(self.active_point)
            self.xs.pop(self.active_point)
            self.ys.pop(self.active_point)
            self.categories.pop(self.active_point)
            self.active_point = None
            self.canvas.draw_idle()

    def update_point(self):
        self.point_references[self.active_point].remove()
        if self.line:
            self.line.remove()
        new_point_reference = self.ax.plot(self.xs[self.active_point], self.ys[self.active_point], f'{self.categories[self.active_point]}o')
        self.point_references[self.active_point] = new_point_reference[0]
        self.draw_line()

    def draw_line(self):
        if len(self.xs) > 0:
            xnp, ynp, cats_np = np.array(self.xs), np.array(self.ys), np.array(self.categories)
            xnp = xnp[cats_np == self.categories[self.active_point]]
            ynp = ynp[cats_np == self.categories[self.active_point]]
        self.line = self.ax.plot(xnp, ynp, f'{self.categories[self.active_point]}-')[0]
    
def main():
    root = Tk()
    matplotlibSwitchGraphs(root)
    root.mainloop()

if __name__ == '__main__':
    main()
