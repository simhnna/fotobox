#!/usr/bin/env python
"""Show slideshow for images in a given directory (recursively) in cycle.
 
If no directory is specified, it uses the current directory.
"""
import os
import platform
import sys
from collections import deque
from itertools import cycle
 
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from random import shuffle
 
class Slideshow(object):
    def __init__(self, parent, imgdir, slideshow_delay=2, history_size=100):
        self.ma = parent.winfo_toplevel()
        self.imgdir = imgdir
        self.update_files()
        self._files = deque(maxlen=history_size)  # for prev/next files
        self._photo_image = None  # must hold reference to PhotoImage
        self._id = None  # used to cancel pending show_image() callbacks
        self.imglbl = tk.Label(parent)  # it contains current image
        # label occupies all available space
        self.imglbl.pack(fill=tk.BOTH, expand=True)
 
        # start slideshow on the next tick
        self.imglbl.after(1, self._slideshow, slideshow_delay * 1000)
 
    def _slideshow(self, delay_milliseconds):
        self._files.append(next(self.filenames))
        self.show_image()
        self.imglbl.after(delay_milliseconds,
                           self._slideshow, delay_milliseconds)
 
    def show_image(self):
        filename = self._files[-1]
        image = Image.open(filename)  # note: let OS manage file cache
 
        # shrink image inplace to fit in the application window
        w, h = self.ma.winfo_width(), self.ma.winfo_height()
        if image.size[0] > w or image.size[1] > h:
            # note: ImageOps.fit() copies image
            # preserve aspect ratio
            image.thumbnail((w - 2, h - 2), Image.ANTIALIAS)
 
        # note: pasting into an RGBA image that is displayed might be slow
        # create new image instead
        self._photo_image = ImageTk.PhotoImage(image)
        self.imglbl.configure(image=self._photo_image)
 
        # set application window title
        self.ma.wm_title(filename)
 
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

    def toggle(self):
        if self.imglbl.winfo_ismapped():
            self.imglbl.pack_forget()
        else:
            self.update_files()
            self.imglbl.pack(fill=tk.BOTH, expand=True)
    def update_files(self):
        self.filenames = cycle(get_image_files(self.imgdir))


def get_image_files(rootdir):
    for path, dirs, files in os.walk(rootdir):
        #dirs.sort()   # traverse directory in sorted order (by name)
        #files.sort()  # show images in sorted order
        shuffle(dirs)
        shuffle(files)
        for filename in files:
            if filename.lower().endswith('.jpg'):
                yield os.path.join(path, filename)
 
def quit(window):
    if messagebox.askquestion('Quit', 'Do you really want to quit?') == 'yes':
        window.destroy()

def main():
    root = tk.Tk()
    # get image filenames
    imagedir = sys.argv[1] if len(sys.argv) > 1 else '.'
 
    # configure initial size
    if platform.system() == "Windows":
        root.wm_state('zoomed')  # start maximized
    else:
        width, height, xoffset, yoffset = 400, 300, 0, 0
        # double-click the title bar to maximize the app
        # or uncomment:
 
        # # remove title bar
        #root.overrideredirect(True) # <- this makes it hard to kill
        # width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry("%dx%d%+d%+d" % (width, height, xoffset, yoffset))
 
    try:  # start slideshow
        app = Slideshow(root, imagedir, slideshow_delay=2)
    except StopIteration:
        sys.exit("no image files found in %r" % (imagedir,))


    # configure keybindings
    root.bind("q", lambda _: quit(root))  # exit on Esc
    root.bind('a', lambda _: app.toggle())
    root.bind("<Configure>", app.fit_image)  # fit image on resize
    root.focus_set()
    root.mainloop()
 
if __name__ == '__main__':
    main()

