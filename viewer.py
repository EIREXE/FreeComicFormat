# The free comic format
# Copyright (C) 2016  Alex Roman
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
import os
import gi
import sys
import copy
import time
import zipfile
from freecomic import FreeComicCollection


gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
from gi.repository.GdkPixbuf import Pixbuf, InterpType, PixbufLoader

class Handler:

    def __init__(self):
        self.previous_allocation_height = 0
        self.previous_allocation_width = 0
        self.comic_language = "en"
        self.new_page_in = False
        self.current_page = 0
        self.comic = False
        self.comic_zip = False

    def load_base(self, number):
        # Loads the base page (aka the page without the speech bubbles) from file.
        # We used to use a different system that allowed us to scale the svg to
        # the size of the page, but we can't do that from memory apparently so now
        # we just assume that the svg has the proper width and height setup
        pixbuf_loader = PixbufLoader.new_with_type('png')
        pixbuf_loader.write(self.comic.get_page_base_from_memory(self.comic_zip,number))
        pixbuf_loader.close()
        pixbuf = pixbuf_loader.get_pixbuf()
        self.comic_pixbuf = pixbuf

    def load_translation(self, number):
        # Gets the translation svg and loads it to memory, I used to use a differe
        pixbuf_loader = PixbufLoader.new_with_type('svg')
        pixbuf_loader.write(self.comic.get_page_translation_from_memory(self.comic_zip,self.comic_language, number))
        pixbuf_loader.close()
        print(pixbuf_loader.get_pixbuf())
        pixbuf = pixbuf_loader.get_pixbuf()
        self.translated_comic_pixbuf = self.comic_pixbuf
        pixbuf.composite(self.translated_comic_pixbuf, 0, 0, self.comic_pixbuf.props.width, self.comic_pixbuf.props.height, 0, 0, 1.0, 1.0, InterpType.HYPER,254)

    def on_draw(self, widget, cr):
        if self.comic:
            allocation = widget.get_allocation()
            if self.temp_height != allocation.height or self.temp_width != allocation.width or self.new_page_in:
                self.new_page_in = False
                self.previous_allocation_height = allocation.height
                self.previous_allocation_width = allocation.width

                # This gets how much we have to scale the original full-size pixbuf when allocation size changes
                difference_ratio = allocation.width/self.translated_comic_pixbuf.get_width()
                new_height = self.translated_comic_pixbuf.get_height()*difference_ratio
                new_width = self.translated_comic_pixbuf.get_width()*difference_ratio
                self.scaled_pixbuf = self.translated_comic_pixbuf.scale_simple(new_width, new_height, InterpType.BILINEAR)
                # If we don't request a specific height the drawingarea won't draw properly
                widget.set_size_request(-1, self.scaled_pixbuf.get_height())
            # This does the actual drawing
            Gdk.cairo_set_source_pixbuf(cr, self.scaled_pixbuf, 0,0)
            cr.paint()

    def set_comic(self, collection):
        # Loads comic from collection
        self.comic = collection.comic_list[0]
        if not os.path.isfile(self.comic.zip_path):
            raise IOError("File does not exist")
        if not zipfile.is_zipfile(self.comic.zip_path):
            raise IOError("File is invalid")

        self.comic_zip = zipfile.ZipFile(self.comic.zip_path)
        self.set_page(0)
    def set_page(self, page):
        # Changes comic page
        if self.comic:
            self.load_base(page)
            self.load_translation(page)
            self.force_draw = True
            self.new_page_in = True
            self.current_page = page
            self.force_draw = True
            self.draw_area.queue_draw()
    def on_back(self, widget):
        if not self.current_page-1 < 0:
            self.set_page(self.current_page-1)

    def open_file(self, widget):
        chooser_dialog = Gtk.FileChooserDialog(title="Open file"
                                               ,action=Gtk.FileChooserAction.OPEN
                                               ,buttons=["Open", Gtk.ResponseType.OK, "Cancel", Gtk.ResponseType.CANCEL]
        )
        pyFilter = Gtk.FileFilter()
        pyFilter.add_pattern('*.fcb')
        pyFilter.set_name('Free comic book file')
        chooser_dialog.add_filter(pyFilter)
        response = chooser_dialog.run()

        if response == Gtk.ResponseType.OK:
            print("ok")
            filename = chooser_dialog.get_filename()
            chooser_dialog.destroy()
            try:
                self.set_comic(FreeComicCollection(filename))
            except Exception as e:
                self.error_message(e)
        chooser_dialog.destroy()

    def error_message(self, exception):
        dialog = Gtk.MessageDialog()
        error = "Error in line {0}!,{1}".format(sys.exc_info()[-1].tb_lineno, str(exception))
        messagedialog = Gtk.MessageDialog(parent=None,
                                          flags=Gtk.DialogFlags.MODAL,
                                          type=Gtk.MessageType.ERROR,
                                          buttons=Gtk.ButtonsType.OK_CANCEL,
                                          message_format=error)
        messagedialog.connect("response", self.dialog_response)
        messagedialog.show()
    def dialog_response(self, widget, response_id):
        widget.destroy()

    def on_forward_pressed(self, widget):
        if not self.current_page+1 > self.comic.number_of_pages:
            self.set_page(self.current_page+1)

builder = Gtk.Builder()
builder.add_from_file("viewertest.glade")

handler = Handler()

builder.connect_signals(handler)

window = builder.get_object("ViewerWindow")
handler.draw_area = builder.get_object("ComicArea")
window.show_all()

Gtk.main()
