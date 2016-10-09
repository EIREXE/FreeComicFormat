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
    def __init__(self, path):
        self.path = path
        if not os.path.isfile(path):
            raise IOError("File does not exist")
        if not zipfile.is_zipfile(path):
            raise IOError("File is invalid")
        zipf = zipfile.ZipFile(path)
        self.comic_list = list()
        for file_path in zipf.namelist():
            if file_path.endswith(".json") and not "/" in file_path:
                print(file_path)
                json_file = zipf.open(file_path)
                comic_config = FreeComicConfig.from_dict(json.loads(zipf.open(file_path).read().decode("utf-8")), path)
                self.comic_list.append(comic_config)
class FreeComicConfig:
    def __init__(self, series_names, episode_names, languages, short_name, episode_number, number_of_pages, zip_path):
        self.series_names = series_names
        self.episode_names = episode_names
        self.languages = languages
        self.short_name = short_name
        self.episode_number = episode_number
        self.number_of_pages = number_of_pages
        self.zip_path = zip_path
    @staticmethod
    def from_dict(dictionary, zip_path):
        return FreeComicConfig(dictionary["series_names"],dictionary["episode_names"], dictionary["languages"], dictionary["short_name"], dictionary["episode_number"], dictionary["number_of_pages"], zip_path)
    def get_page_base(self, page_number):
        if not os.path.isfile(self.zip_path):
            raise IOError("File does not exist")
        if not zipfile.is_zipfile(self.zip_path):
            raise IOError("File is invalid")

        zipf = zipfile.ZipFile(self.zip_path)
        return self.get_page_base_from_memory(zipf, page_number)
    def get_page_translation(self, language, page_number):
        if not os.path.isfile(self.zip_path):
            raise IOError("File does not exist")
        if not zipfile.is_zipfile(self.zip_path):
            raise IOError("File is invalid")

        zipf = zipfile.ZipFile(self.zip_path)
        return self.get_page_translation_from_memory(zipf, language, page_number)
    def get_page_translation_from_memory(self, zipfile, language, page_number):
        path = "{0}/{1}/{2}/{3}.svg".format(self.short_name,self.episode_number,language ,page_number)
        if path in zipfile.namelist():
            return zipfile.open(path).read()
        else:
            raise IOError("Translation does not exist")
    def get_page_base_from_memory(self, zipfile, page_number):
        path = "{0}/{1}/base/{2}.png".format(self.short_name,self.episode_number, page_number)
        if path in zipfile.namelist():
            return zipfile.open(path).read()
        else:
            raise IOError("Page does not exist")
