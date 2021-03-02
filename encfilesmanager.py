import os
import threading
from time import time

from filebytecontent import FileByteContent
from mixslice import MixSlice

LOCK = threading.Lock()

class EncFilesManager():
    def __init__(self, key=None, iv=None):
        self.key = key if key is not None else b'K' * 16
        self.iv = iv if iv is not None else b'I' * 16

        self.open_files = {}
        self.open_counters = {}
        self.touched_files = {}

        self.atimes = {}
        self.mtimes = {}

    def __contains__(self, path):
        return path in self.open_files

    # ------------------------------------------------------ Helpers

    def _decrypt(self, path):
        return MixSlice.decrypt(path, self.key, self.iv)

    def _encrypt(self, path):
        plaintext = self.open_files[path].read_all()
        MixSlice.encrypt(plaintext, path, self.key, self.iv)

    # ------------------------------------------------------ Methods

    def open(self, path, mtime):
        with LOCK:
            if path in self.open_files:
                self.open_counters[path] += 1
                return

            self.open_files[path] = FileByteContent(self._decrypt(path))
            self.open_counters[path] = 1
        
        self.touched_files[path] = False
        self.atimes[path] = int(time())
        self.mtimes[path] = mtime

    def create(self, path):
        with LOCK:
            if path not in self.open_files:
                
                self.open_files[path] = FileByteContent(b'')
                self.open_counters[path] = 1
                
                self.atimes[path] = int(time())
                self.mtimes[path] = self.atimes[path]
            else:
                self.open_counters[path] += 1

        self.touched_files[path] = True
        self.flush(path)

    def read_bytes(self, path, offset, length):
        with LOCK:
            if path not in self.open_files:
                return None

        return self.open_files[path].read_bytes(offset, length)

    def write_bytes(self, path, buf, offset):
        with LOCK:
            if path not in self.open_files:
                return 0

        bytes_written = self.open_files[path].write_bytes(buf, offset)
        
        self.touched_files[path] = True
        self.mtimes[path] = int(time())

        return bytes_written

    def truncate_bytes(self, path, length):
        with LOCK:
            if path not in self.open_files:
                return

        self.open_files[path].truncate(length)
        
        self.touched_files[path] = True
        self.mtimes[path] = int(time())

    def flush(self, path):
        with LOCK:
            if path not in self.open_files:
                return

        file_already_exists = os.path.exists(path)
        if file_already_exists:
            os.utime(path, (self.atimes[path], self.mtimes[path]))

        with LOCK:
            if not self.touched_files[path]:
                return

            self.touched_files[path] = False
            self._encrypt(path)
        
        if not file_already_exists:
            os.utime(path, (self.atimes[path], self.mtimes[path]))


    def release(self, path):
        with LOCK:
            if path not in self.open_files:
                return

            self.open_counters[path] -= 1

            if self.open_counters[path] > 0:
                return

            del self.open_files[path]
            del self.open_counters[path]
            del self.touched_files[path]
            del self.atimes[path]
            del self.mtimes[path]

    def cur_size(self, path):
        with LOCK:
            if path not in self.open_files:
                return 0

        return len(self.open_files[path])

    def rename(self, old, new):
        with LOCK:
            if old not in self.open_files:
                return

            self.open_files[new] = self.open_files[old]
            self.open_counters[new] = self.open_counters[old]
            self.touched_files[new] = self.touched_files[old]
            self.atimes[new] = self.atimes[old]
            self.mtimes[new] = self.mtimes[old]

            del self.open_files[old]
            del self.open_counters[old]
            del self.touched_files[old]
            del self.atimes[old]
            del self.mtimes[old]
