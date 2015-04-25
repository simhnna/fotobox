#!/usr/bin/env python

import os
import platform
import sys
from collections import deque
from itertools import cycle
 
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
        self.counter = 0
        self.picture_names = picturenames
        self.update_files()
        self._photo_image = None  # must hold reference to PhotoImage

        self.camera = None
        self.imglbl = tk.Label(parent)  # it contains current image
        self.countdownlbl = tk.Label(parent, font=("Helvetica", 40))
        # label occupies all available space
        self.imglbl.pack(fill=tk.BOTH, expand=True)
 
        self.countdownlbl.pack()
        # start slideshow on the next tick
        self.after = self.imglbl.after(1, self._slideshow, self.slideshow_delay * 1000)
        self.capture = None
        self.counting_down = None
 
    def _slideshow(self, delay_milliseconds):
        self.show_image()
        self.after = self.imglbl.after(delay_milliseconds,
                           self._slideshow, delay_milliseconds)

    def _liveview(self):
        self.show_image(liveview=True)
        self.after = self.imglbl.after(self.spf,
                           self._liveview)

    def show_image(self, liveview=False):
        if liveview:
            filename = '/tmp/liveview.jpg'
            self.camera.capture_preview('/tmp/liveview.jpg')
        else:
            filename = next(self.filenames)
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

    def show_taken_picture(self):
        self.imglbl.after_cancel(self.after)
        self.capture = self.imglbl.after(3000, self.wait_for_next_picture)

    def capture_image(self):
        
        filename = ''.join(('/tmp/imgs/', self.picture_names, '_', str(self.counter).zfill(4), '.jpg'))
        self.counter += 1
        self.camera.capture_image(filename)
        self.show_taken_picture()

    def start_countdown(self):
        if not self.counting_down:
            if self.capture:
                self.imglbl.after_cancel(self.capture)
            if self.camera is None:
                self.toggle_camera()
            else:
                self.countdown(3)


    def countdown(self, remaining):
        if remaining >= 0:
            self.countdownlbl['text'] = str(remaining)
            self.counting_down = self.countdownlbl.after(1000, self.countdown, remaining - 1)
        else:
            self.countdownlbl['text'] = ''
            self.capture_image()

    def toggle_camera(self):
        self.imglbl.after_cancel(self.after)
        self.after = None
        if self.camera is None:
            self.camera = piggyphoto.camera()
            self.camera.leave_locked()
            self.after = self.imglbl.after(1, self._liveview)
        else:
            self.camera._leave_locked = False
            self.camera = None
            self.update_files()
            self.after = self.imglbl.after(1, self._slideshow, self.slideshow_delay * 1000)

    def update_files(self):
        self.filenames = cycle(get_image_files(self.imgdir))


def get_image_files(rootdir):
    for path, dirs, files in os.walk(rootdir):
        shuffle(dirs)
        shuffle(files)
        for filename in files:
            if filename.lower().endswith('.jpg'):
                yield os.path.join(path, filename)
 
class Application:
    def __init__(self):
        self.root = tk.Tk()

        imagedir = sys.argv[1] if len(sys.argv) > 1 else '.'
     
        # configure initial size
        if platform.system() == "Windows":
            self.root.wm_state('zoomed')  # start maximized
        else:
            width, height, xoffset, yoffset = 400, 300, 0, 0
            self.root.geometry("%dx%d%+d%+d" % (width, height, xoffset, yoffset))
        self.root.winfo_toplevel().wm_title('Fotobox')
     
        try:  # start slideshow
            self.window = Mainwindow(self.root, imagedir, slideshow_delay=2)
        except StopIteration:
            sys.exit("no image files found in %r" % (imagedir,))


        # configure keybindings
        self.root.bind("q", lambda _: self.quit())  # exit on Esc
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
