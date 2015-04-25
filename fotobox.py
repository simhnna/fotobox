#!/usr/bin/env python

import os
import platform
import sys
from collections import deque
from itertools import cycle
import tkinter.filedialog 
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from random import shuffle
from piggyphoto import piggyphoto

class Mainwindow(object):
    def __init__(self, parent, imgdir, slideshow_delay=2, fps=100, picturenames='fotobox'):
        self.ma = parent.winfo_toplevel()
        self.slideshow_delay = slideshow_delay
        self.spf = int(1000 / fps)
        self.imgdir = imgdir

        self.counter = len([f for f in os.listdir(self.imgdir) if "fotobox" in f])
        self.picture_names = picturenames
        self._photo_image = None  # must hold reference to PhotoImage

        self.camera = None
        self.imglbl = tk.Label(parent)  # it contains current image
        self.countdownlbl = tk.Label(parent, font=("Helvetica", 40))
        # label occupies all available space
        self.imglbl.pack(fill=tk.BOTH, expand=True)
        self.after = None 
        self.countdownlbl.pack()
        # start slideshow on the next tick
        self.capture = None
        self.counting_down = None
        self.countdownlbl['text'] = 'Ready to Capture'

    def _liveview(self):
        if not self.counting_down:
            self.countdownlbl['text'] = 'Ready to Capture'
        self.show_image()
        self.after = self.imglbl.after(self.spf,
                           self._liveview)

    def show_image(self):
        filename = '/tmp/liveview.jpg'
        self.camera.capture_preview('/tmp/liveview.jpg')
        image = Image.open(filename)  # note: let OS manage file cache
 
        # shrink image inplace to fit in the application window
        w, h = self.ma.winfo_width(), self.ma.winfo_height()
        if image.size[0] > w or image.size[1] > h:
            # preserve aspect ratio
            image.thumbnail((w - 2, h - 2), Image.ANTIALIAS)
 
        # note: pasting into an RGBA image that is displayed might be slow
        # create new image instead
        self._photo_image = ImageTk.PhotoImage(image)
        self.imglbl.configure(image=self._photo_image)


    def wait_for_next_picture(self):
        self._liveview()
        self.counting_down = None
        if self.capture:
            self.imglbl.after_cancel(self.capture)
        self.capture= self.imglbl.after(10000, self.toggle_camera)


    def capture_image(self):
        self.imglbl.after_cancel(self.after)
        filename = ''.join((self.imgdir, self.picture_names, '_', str(self.counter).zfill(4), '.jpg'))
        self.counter += 1
        self.camera.capture_image(filename)
        self.capture = self.imglbl.after(3000, self.wait_for_next_picture)

    def start_countdown(self):
        if not self.counting_down:
            if self.capture:
                self.imglbl.after_cancel(self.capture)
            if self.camera is None:
                self.toggle_camera()
            self.countdown(3)


    def countdown(self, remaining):
        if remaining >= 0:
            self.countdownlbl['text'] = str(remaining)
            self.counting_down = self.countdownlbl.after(1000, self.countdown, remaining - 1)
        else:
            self.countdownlbl['text'] = ''
            self.capture_image()

    def toggle_camera(self):
        if self.after != None:
            self.imglbl.after_cancel(self.after)
            self.after = None
        if self.camera is None:
            self.countdownlbl['text'] = 'Ready to Capture'
            self.camera = piggyphoto.Camera()
            self.camera.leave_locked()
            self.after = self.imglbl.after(1, self._liveview)
        else:
            self.camera._leave_locked = False
            self.camera = None
            self.countdownlbl['text'] = 'Ready to Capture'

 
class Application:
    def __init__(self):
        self.root = tk.Tk()
        imagedir = tkinter.filedialog.askdirectory(title="Choose where to save pics", parent=self.root)
        if not imagedir:
            self.root.destroy()
            return
        # configure initial size
        if platform.system() == "Windows":
            self.root.wm_state('zoomed')
        else:
            width, height, xoffset, yoffset = 400, 300, 0, 0
            self.root.geometry("%dx%d%+d%+d" % (width, height, xoffset, yoffset))
        self.root.winfo_toplevel().wm_title('Fotobox')
     
        self.window = Mainwindow(self.root, imagedir)


        # configure keybindings
        self.root.bind("q", lambda _: self.quit())  
        self.root.bind("<space>", lambda _: self.window.start_countdown())
        self.root.focus_set()
        self.root.mainloop()

    def quit(self):
        if messagebox.askquestion('Quit', 'Do you really want to quit?') == 'yes':
            if self.window.camera is not None:
                self.window.camera._leave_locked = False
                del self.window.camera 
            self.root.destroy()

if __name__ == '__main__':
    app = Application()
