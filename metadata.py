import json
import os

class Metadata:
    def __init__(self, path):
        self.path = path

        self.metadata = {}
        if os.path.isfile(path):
            with open(path) as f:
                self.metadata = json.load(f)

    def __contains__(self, path):
        return path in self.metadata

    def __setitem__(self, path, size):
        print("__setitem__")
        self.metadata[path] = size

    def __getitem__(self, path):
        return self.metadata[path]

    def add(self, path):
        print("add")
        self.metadata[path] = 0

    def update(self, path, size):
        print("update")
        self.metadata[path] = size

    def renamedir(self, old, new):
        print("renamedir")
        for path in list(self.metadata):
            if path.startswith(old):
                to = path.replace(old, new, 1)
                self.rename(path, to)

    def rename(self, old, new):
        print("rename")
        self.metadata[new] = self.metadata[old]
        del self.metadata[old]

    def remove(self, path):
        print("remove")
        del self.metadata[path]
    
    def dump(self):
        with open(self.path, 'w') as f:
            json.dump(self.metadata, f)
