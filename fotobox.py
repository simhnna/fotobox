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
from piggyphoto.piggyphoto import piggyphoto

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
        self._id = None  # used to cancel pending show_image() callbacks

        self.camera = None
        self.imglbl = tk.Label(parent)  # it contains current image
        # label occupies all available space
        self.imglbl.pack(fill=tk.BOTH, expand=True)
 
        # start slideshow on the next tick
        self.after = self.imglbl.after(1, self._slideshow, self.slideshow_delay * 1000)
 
    def _slideshow(self, delay_milliseconds):
        self.show_image()
        self.after = self.imglbl.after(delay_milliseconds,
                           self._slideshow, delay_milliseconds)

    def _liveview(self, delay_milliseconds):
        self.show_image(liveview=True)
        self.after = self.imglbl.after(delay_milliseconds,
                           self._liveview, delay_milliseconds)

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
 
    def _show_image_on_next_tick(self):
        # cancel previous callback schedule a new one
        if self._id is not None:
            self.imglbl.after_cancel(self._id)
        self._id = self.imglbl.after(1, self.show_image)
 
    def fit_image(self, event=None, _last=[None] * 2):
        """Fit image inside application window on resize."""
        if event is not None and event.widget is self.ma and (
            _last[0] != event.width or _last[1] != event.height):
            # size changed; update image
            _last[:] = event.width, event.height
            self._show_image_on_next_tick()

    def capture_image(self):
        filename = ''.join(('/tmp/imgs/', self.picture_names, '_', str(self.counter).zfill(4), '.jpg'))
        self.counter += 1
        if self.camera is None:
            self.toggle_camera()
        self.camera.capture_image(filename)

    def toggle_camera(self):
        self.imglbl.after_cancel(self.after)
        self.after = None
        if self.camera is None:
            self.camera = piggyphoto.camera()
            self.camera.leave_locked()
            self.after = self.imglbl.after(1, self._liveview, self.spf)
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
        self.root.bind('a', lambda _: self.window.toggle_camera())
        self.root.bind("<Configure>", self.window.fit_image)  # fit image on resize
        self.root.bind("<space>", lambda _: self.window.capture_image())
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
