# The free comic format
# Copyright (C) 2016  Alex Roman
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
import os
import gi
import sys
import zipfile
from freecomic import FreeComicCollection

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository.GdkPixbuf import InterpType, PixbufLoader


class Handler:
    def __init__(self):
        self.previous_allocation_height = 0
        self.previous_allocation_width = 0
        self.comic_language = "es"  # TODO: Fix this
        self.new_page_in = False  # This is True when a new page comes in.
        self.current_page = 0
        self.comic = False  # FreeComicCollection
        self.comic_zip = False  # Comic zip file
        self.comic_base_pixbuf = None  # Base pixbuf
        self.translated_comic_pixbuf = None  # Fullres pixbuf with translations added
        self.scaled_pixbuf = None  # Pixbuf scaled to size

    def load_base(self, number):
        # Loads the base page (aka the page without the speech bubbles) from file.
        # We used to use a different system that allowed us to scale the svg to
        # the size of the page, but we can't do that from memory apparently so now
        # we just assume that the svg has the proper width and height setup
        pixbuf_loader = PixbufLoader.new_with_type('png')
        pixbuf_loader.write(self.comic.get_page_base(number))
        pixbuf_loader.close()
        pixbuf = pixbuf_loader.get_pixbuf()
        self.comic_base_pixbuf = pixbuf

    def load_translation(self, number):
        # Gets the translation svg and loads it to memory, I used to use a different method that allowed for scaling SVG
        # files to the proper resolution (rendering it again), however this method sucks ass and the authors should just
        # make their SVGs be the proper size.
        pixbuf_loader = PixbufLoader.new_with_type('svg')
        pixbuf_loader.write(self.comic.get_page_translation(self.comic_language, number))
        pixbuf_loader.close()
        pixbuf = pixbuf_loader.get_pixbuf()
        self.translated_comic_pixbuf = self.comic_base_pixbuf
        pixbuf.composite(self.translated_comic_pixbuf, 0, 0, self.comic_base_pixbuf.props.width,
                         self.comic_base_pixbuf.props.height, 0, 0, 1.0, 1.0, InterpType.HYPER, 254)

    def on_draw(self, widget, cr):
        if self.comic:
            allocation = widget.get_allocation()
            if self.previous_allocation_height != allocation.height or self.previous_allocation_width != allocation.width or self.new_page_in:
                self.new_page_in = False
                self.previous_allocation_height = allocation.height
                self.previous_allocation_width = allocation.width

                # This gets how much we have to scale the original full-size pixbuf when allocation size changes
                difference_ratio = allocation.width / self.translated_comic_pixbuf.get_width()
                new_height = self.translated_comic_pixbuf.get_height() * difference_ratio
                new_width = self.translated_comic_pixbuf.get_width() * difference_ratio
                self.scaled_pixbuf = self.translated_comic_pixbuf.scale_simple(new_width, new_height,
                                                                               InterpType.BILINEAR)
                # If we don't request a specific height the drawing area won't draw properly
                widget.set_size_request(-1, self.scaled_pixbuf.get_height())
            # This does the actual drawing
            Gdk.cairo_set_source_pixbuf(cr, self.scaled_pixbuf, 0, 0)
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
        if not self.current_page - 1 < 0:
            self.set_page(self.current_page - 1)

    def open_file(self, widget):
        chooser_dialog = Gtk.FileChooserDialog(title="Open file"
                                               , action=Gtk.FileChooserAction.OPEN
                                               ,
                                               buttons=["Open", Gtk.ResponseType.OK, "Cancel", Gtk.ResponseType.CANCEL]
                                               )
        filter = Gtk.FileFilter()
        filter.add_pattern('*.fcb')
        filter.set_name('Free comic book file')
        chooser_dialog.add_filter(filter)
        response = chooser_dialog.run()
        # Did we chose a not correct file? let's find out.
        if response == Gtk.ResponseType.OK:
            filename = chooser_dialog.get_filename()
            chooser_dialog.destroy()
            try:
                self.set_comic(FreeComicCollection(filename))
            except Exception as e:
                self.show_error_message(e)
        chooser_dialog.destroy()

    def show_error_message(self, exception):
        error = "Error in line {0}!,{1}, call a programmer.".format(sys.exc_info()[-1].tb_lineno, str(exception))
        print(error)
        message_dialog = Gtk.MessageDialog(parent=None,
                                           flags=Gtk.DialogFlags.MODAL,
                                           type=Gtk.MessageType.ERROR,
                                           buttons=Gtk.ButtonsType.OK_CANCEL,
                                           message_format=error)
        message_dialog.connect("response", self.dialog_response_callback)
        message_dialog.show()

    def dialog_response_callback(self, widget, response_id):
        widget.destroy()

    def on_forward_pressed(self, widget):
        if not self.current_page + 1 > self.comic.number_of_pages:
            self.set_page(self.current_page + 1)

    def on_window_close(self, widget, what):
        Gtk.main_quit()
handler = Handler()
builder = Gtk.Builder()
builder.add_from_file("viewer.glade")
builder.connect_signals(handler)

window = builder.get_object("ViewerWindow")
handler.draw_area = builder.get_object("ComicArea")

window.show_all()

Gtk.main()
