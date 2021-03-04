import base64
import json
import os
import secrets

class Info:
    def __init__(self, key=None, iv=None, size=None):
        self.key = key if key is not None else secrets.token_bytes(16)
        self.iv = iv if iv is not None else secrets.token_bytes(16)
        self.size = size if size is not None else 0

class Metadata:
    def __init__(self, path):
        self.path = path

        read = {}
        if os.path.isfile(path):
            with open(path) as f:
                read = json.load(f)
        
        self.metadata = {}
        for path, info in read.items():
            key = base64.b64decode(info['key'].encode("ascii"))
            iv = base64.b64decode(info['iv'].encode("ascii"))
            self.metadata[path] = Info(key, iv, info['size'])

    def __contains__(self, path):
        return path in self.metadata

    def __setitem__(self, path, size):
        print("__setitem__")
        self.metadata[path].size = size

    def __getitem__(self, path):
        return self.metadata[path]

    def add(self, path):
        print("add")
        info = Info()
        self.metadata[path] = info
        return info.key, info.iv

    def update(self, path, size):
        print("update")
        self.metadata[path].size = size

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
        to_write = {}
        for path, info in self.metadata.items():
            to_write[path] = {
                'key': base64.b64encode(info.key).decode("ascii"),
                'iv': base64.b64encode(info.iv).decode("ascii"),
                'size': info.size
            }
        with open(self.path, 'w') as f:
            json.dump(to_write, f)
