# The free comic format
# Copyright (C) 2016  Alex Roman
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.

import os
import json
import zipfile

class FreeComicCollection:
    def __init__(self, path, create=False):
        self.zip_path = path
        if not create:
            if not os.path.isfile(path):
                raise IOError("File does not exist")
            if not zipfile.is_zipfile(path):
                raise IOError("File is invalid")
        self.zip_file = zipfile.ZipFile(path, "a")
        self.comic_list = list()
        self.update_comics()

    def update_comics(self):
        for file_path in self.zip_file.namelist():
            if file_path.endswith(".json") and "/" not in file_path:
                comic_config = FreeComicConfig.from_dict(json.loads(self.zip_file.open(file_path).read().decode("utf-8")), self.zip_file, self.zip_path)
                self.comic_list.append(comic_config)
class FreeComicConfig:
    def __init__(self, series_names, episode_names, languages, short_name, episode_number, number_of_pages, zip_file, zip_path):
        self.series_names = series_names
        self.episode_names = episode_names
        self.languages = languages
        self.short_name = short_name
        self.episode_number = episode_number
        self.number_of_pages = number_of_pages  # Should start from one, because comic artists are not programmers, right?
        self.zip_file = zip_file
        self.zip_path = zip_path
    @staticmethod
    def from_dict(dictionary, zip_file, zip_path):
        return FreeComicConfig(dictionary["series_names"], dictionary["episode_names"], dictionary["languages"],
                               dictionary["short_name"], dictionary["episode_number"], dictionary["number_of_pages"],
                               zip_file, zip_path)

    def get_page_translation(self, language, page_number):
        path = "{0}/{1}/{2}/{3}.svg".format(self.short_name, self.episode_number, language, page_number)
        if path in self.zip_file.namelist():
            return self.zip_file.open(path).read()
        else:
            raise IOError("Translation does not exist")

    def get_page_base(self, page_number):
        path = "{0}/{1}/base/{2}.png".format(self.short_name, self.episode_number, page_number)
        print(path)
        print(self.zip_file.namelist())
        if path in self.zip_file.namelist():
            return self.zip_file.open(path).read()
        else:
            raise IOError("Page does not exist")

