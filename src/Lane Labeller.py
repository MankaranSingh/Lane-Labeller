import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from tkinter import Tk, Frame, BOTH, TOP, BOTTOM, Button, YES, filedialog, RIGHT
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
import cv2
import os

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
        self.last_point = -1
        self.last_point_reference = None
        self.alpha = 0.8
        self.xs = []
        self.ys = []
        self.categories = []
        self.line = None
        self.point_references = []
        self.save_dir = 'annotations'
        self.image_paths = None
        self.current_image = -1
        self.init_save_dir()

    def config_window(self):
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas.mpl_connect('button_release_event', self.button_release_callback)
        toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.file_button = Button(self.master, text="Open", command=self.openfile)  
        self.file_button.pack(side=RIGHT)
        self.button_image = Button(self.master, text="Next Image", command=self.load_image)
        self.button_image.pack(side=RIGHT)
        self.lane_switch = Button(self.master, text="Switch Lane", command=self.switch_lane)
        self.lane_switch.pack(side=RIGHT)
        self.save_button = Button(self.master, text="Save Annotation", command=self.save_annotation)
        self.save_button.pack(side=RIGHT)
        self.ax.set(title=self.lanes[self.lane_idx])

    def on_key_press(self, event):
        print("you pressed {}".format(event.key))

    def openfile(self):
        self.image_paths_file = filedialog.askopenfilename()
        with open(self.image_paths_file, 'r') as file:
            self.image_paths = file.readlines()
        for path in range(len(self.image_paths)):
            self.image_paths[path] = self.image_paths[path].replace('\n', '')

    def on_click(self, event):
        ret = False
        if not event.inaxes or self.canvas.toolbar._lastCursor in [3, 2]:
            return
        if len(self.xs) > 0:
            ret, self.active_point = self.get_ind_under_point(event)
        if ret:
            self.last_point = self.active_point
            self.highlight_active_point()
        if ret or event.button==3:
            if event.button == 3 and ret:
                self.remove_active_point()
                self.last_point -= 1
                if len(self.xs) > 0:
                    self.highlight_active_point()
            return
        idx = self.last_point + 1
        if self.line:
            self.line.remove()
            self.line = None
        self.xs.insert(idx, event.xdata)
        self.ys.insert(idx, event.ydata)
        self.categories.insert(idx, self.lanes[self.lane_idx])
        point_reference = self.ax.plot(event.xdata, event.ydata, self.lanes[self.lane_idx] +'o', alpha=self.alpha)
        self.point_references.insert(idx, point_reference[0])
        self.draw_line(category=self.lanes[self.lane_idx])
        self.last_point += 1
        self.highlight_active_point()
        self.canvas.draw_idle()

    def highlight_active_point(self):
        if self.last_point_reference is not None:
            self.last_point_reference.remove()
        self.last_point_reference = self.ax.plot(self.xs[self.last_point], self.ys[self.last_point], 'ko', alpha=self.alpha)[0]
    
    def load_image(self):
        if self.image_paths == None:
            self.openfile()
        self.save_annotation()
        self.reset_annotation()
        self.ax.clear()
        self.current_image = (self.current_image + 1) % len(self.image_paths)
        img = cv2.imread(self.image_paths[self.current_image])[:, :, (2, 1, 0)]
        self.image = img
        self.ax.imshow(img)
        self.load_annotation()
        self.ax.set(title=self.lanes[self.lane_idx])
        self.canvas.draw()

    def reset_annotation(self):
        self.active_point = None
        self.last_point = -1
        self.last_point_reference = None
        self.xs = []
        self.ys = []
        self.categories = []
        self.line = None
        self.point_references = []

    def save_annotation(self):
        '''saves annotations as 3 x n_points'''
        if len(self.xs) > 0:
            annotations = np.vstack([self.xs, self.ys, self.categories])
            filename = os.path.basename(self.image_paths[self.current_image]).split('.')[0]
            np.save(f'{self.save_dir}/{filename}', annotations)
            return True

    def init_save_dir(self):
         if not os.path.exists(self.save_dir):
             os.mkdir(self.save_dir)        

    def load_annotation(self):
        filename = os.path.basename(self.image_paths[self.current_image]).split('.')[0]
        if os.path.exists(f'{self.save_dir}/{filename}.npy'):
            xs, ys, categories = np.load(f'{self.save_dir}/{filename}.npy')
            self.xs, self.ys, self.categories = list(xs.astype('float32')), list(ys.astype('float32')), list(categories)
            for point in range(len(xs)):
                point_resference = self.ax.plot(self.xs[point], self.ys[point], f'{self.categories[point]}o', alpha=self.alpha)[0]
                self.point_references.append(point_resference)
            self.last_point = 0
            self.highlight_active_point()
                
    def _quit(self):
        self.master.quit()  # stops mainloop

    def switch_lane(self):
        self.lane_idx = (self.lane_idx + 1) % len(self.lanes)
        self.ax.set(title=self.lanes[self.lane_idx])
        self.canvas.draw_idle()

    def get_ind_under_point(self, event):
        '''get the index of the vertex under point if within epsilon tolerance'''
        is_available = True
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
        self.highlight_active_point()
        self.canvas.draw_idle()

    def button_release_callback(self, event):
        if event.button == 1:
            self.active_point = None
        self.canvas.draw_idle()
            
    def remove_active_point(self):
        category = self.categories[self.active_point]
        if self.line:
            self.line.remove()
            self.line = None
        if self.active_point is not None:
            self.point_references[self.active_point].remove()
            self.point_references.pop(self.active_point)
            self.xs.pop(self.active_point)
            self.ys.pop(self.active_point)
            self.categories.pop(self.active_point)
            self.active_point = None
            self.draw_line(category)
            self.canvas.draw_idle()

    def update_point(self):
        self.point_references[self.active_point].remove()
        if self.line:
            self.line.remove()
        new_point_reference = self.ax.plot(self.xs[self.active_point], self.ys[self.active_point], f'{self.categories[self.active_point]}o', alpha=self.alpha)
        self.point_references[self.active_point] = new_point_reference[0]
        self.draw_line()

    def draw_line(self, category=None):
        if category is None:
            category = self.categories[self.active_point]
        if len(self.xs) > 0:
            xnp, ynp, cats_np = np.array(self.xs), np.array(self.ys), np.array(self.categories)
            xnp = xnp[cats_np == category]
            ynp = ynp[cats_np == category]
            self.line = self.ax.plot(xnp, ynp, f'{category}-', alpha=self.alpha)[0]
    
def main():
    root = Tk()
    root.title('Lane Labeller')
    matplotlibSwitchGraphs(root)
    root.mainloop()

if __name__ == '__main__':
    main()
