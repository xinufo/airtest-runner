# -*- coding: utf-8 -*-

import os
import inspect

def img(name):
    folder = inspect.stack()[1][1]
    index = folder.find(".")
    if index >= 0:
        folder = folder[ : folder.find(".")]
    folder = os.path.join(folder, name) + ".png"
    return folder