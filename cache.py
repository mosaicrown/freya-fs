import os
import threading
from time import time

from filebytecontent import FileByteContent
from mixslice import MixSlice

LOCK = threading.Lock()


class CacheEntry:
    def __init__(self, path, content, mtime=None):
        self.path = path

        self.content = content
        self.opens = 1  # number of concurrent apps with this file open
        self.modified = True if not mtime else False
        self.atimes = int(time())
        self.mtimes = self.atimes if not mtime else mtime


class Cache:
    def __init__(self):
        self.files = {}

    def __contains__(self, path):
        return path in self.files

    # ------------------------------------------------------ Helpers

    def _decrypt(self, path, key, iv):
        return MixSlice.decrypt(path, key, iv)

    def _encrypt(self, path, key, iv):
        plaintext = self.files[path].content.read_all()
        MixSlice.encrypt(plaintext, path, key, iv)

    # ------------------------------------------------------ Methods

    def open(self, path, key, iv, mtime):
        with LOCK:
            if path in self.files:
                self.files[path].opens += 1
                return

            plaintext = FileByteContent(self._decrypt(path, key, iv))
            self.files[path] = CacheEntry(path, plaintext, mtime)

    def create(self, path, key, iv):
        with LOCK:
            if path in self.files:
                self.files[path].opens += 1
                return

            plaintext = FileByteContent(b'')
            self.files[path] = CacheEntry(path, plaintext)

        self.flush(path, key, iv)

    def read_bytes(self, path, offset, length):
        with LOCK:
            if path not in self.files:
                return None
        content = self.files[path].content
        return content.read_bytes(offset, length)

    def write_bytes(self, path, buf, offset):
        with LOCK:
            if path not in self.files:
                return 0

        content = self.files[path].content
        bytes_written = content.write_bytes(buf, offset)
        
        self.files[path].modified = True
        self.files[path].mtimes = int(time())

        return bytes_written

    def truncate_bytes(self, path, length):
        with LOCK:
            if path not in self.files:
                return

        content = self.files[path].content
        content.truncate(length)
        
        self.files[path].modified = True
        self.files[path].mtimes = int(time())

    def flush(self, path, key, iv):
        with LOCK:
            if path not in self.files:
                return

        file_already_exists = os.path.exists(path)
        if file_already_exists:
            os.utime(path, (self.files[path].atimes, self.files[path].mtimes))

        with LOCK:
            if not self.files[path].modified:
                return

            self.files[path].modified = False
            self._encrypt(path, key, iv)
        
        if not file_already_exists:
            os.utime(path, (self.files[path].atimes, self.files[path].mtimes))

    def release(self, path):
        with LOCK:
            if path not in self.files:
                return

            self.files[path].opens -= 1
            if not self.files[path].opens:
                del self.files[path]

    def get_size(self, path):
        with LOCK:
            if path not in self.files:
                return 0

        return len(self.files[path].content)

    def rename(self, old, new):
        with LOCK:
            if old not in self.files:
                return

            self.files[new] = self.files[old]
            del self.files[old]
