import os
import threading

from aesmix import MixSlice
from time import time

LOCK = threading.Lock()

class EncFilesManager():
    def __init__(self, key=None, iv=None):
        self.key = key if key is not None else b'K' * 16
        self.iv = iv if iv is not None else b'I' * 16

        self.open_files = {}
        self.open_counters = {}
        self.touched_files = {}
        self.public_metafiles = {}
        self.private_metafiles = {}

        self.atimes = {}
        self.mtimes = {}

    def __contains__(self, path):
        return path in self.open_files

    # ------------------------------------------------------ Helpers

    def _decrypt(self, path):
        public_metafiles = self.public_metafiles[path]
        reader = MixSlice.load_from_file(path, public_metafiles)
        return reader.decrypt()

    def _encrypt(self, path):
        plaintext = self.open_files[path]
        public_metafile = self.public_metafiles[path]
        private_metafile = self.private_metafiles[path]

        owner = MixSlice.encrypt(plaintext, self.key, self.iv)
        owner.save_to_files(path, public_metafile, private_metafile)

    # ------------------------------------------------------ Methods

    def open(self, path, public_metafile_path, private_metafile_path, mtime):
        with LOCK:
            if path in self.open_files:
                self.open_counters[path] += 1
                return

            self.public_metafiles[path] = public_metafile_path
            self.private_metafiles[path] = private_metafile_path

            self.open_files[path] = self._decrypt(path)
            self.open_counters[path] = 1
        
        self.touched_files[path] = False
        self.atimes[path] = int(time())
        self.mtimes[path] = mtime

    def create(self, path, public_metafile_path, private_metafile_path):
        with LOCK:
            if path not in self.open_files:
                self.public_metafiles[path] = public_metafile_path
                self.private_metafiles[path] = private_metafile_path
                
                self.open_files[path] = b''
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

            plaintext = self.open_files[path]

        return plaintext[offset:offset + length]

    def write_bytes(self, path, buf, offset):
        bytes_written = len(buf)
        
        with LOCK:
            if path not in self.open_files:
                return 0

            plaintext = self.open_files[path]
            new_text = plaintext[:offset] + buf + \
                plaintext[offset+bytes_written:]

            self.open_files[path] = new_text
        
        self.touched_files[path] = True
        self.mtimes[path] = int(time())

        return bytes_written

    def truncate_bytes(self, path, length):
        with LOCK:
            if path not in self.open_files:
                return

            plaintext = self.open_files[path]
            self.open_files[path] = plaintext[:length]
        
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
            del self.public_metafiles[path]
            del self.private_metafiles[path]
            del self.atimes[path]
            del self.mtimes[path]

    def cur_size(self, path):
        with LOCK:
            if path not in self.open_files:
                return 0

            length = len(self.open_files[path])
        return length

    def rename(self, old, new):
        with LOCK:
            if old not in self.open_files:
                return

            self.open_files[new] = self.open_files[old]
            self.open_counters[new] = self.open_counters[old]
            self.touched_files[new] = self.touched_files[old]
            self.public_metafiles[new] = self.public_metafiles[old]
            self.private_metafiles[new] = self.private_metafiles[old]
            self.atimes[new] = self.atimes[old]
            self.mtimes[new] = self.mtimes[old]

            del self.open_files[old]
            del self.open_counters[old]
            del self.touched_files[old]
            del self.public_metafiles[old]
            del self.private_metafiles[old]
            del self.atimes[old]
            del self.mtimes[old]
