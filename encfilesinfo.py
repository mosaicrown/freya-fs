import json
import os

from mixslice import MixSlice


class EncFilesInfo():
    def __init__(self, path, file_finfo, key=None, iv=None):
        self._path = path
        self._file_finfo = file_finfo
        self.key = key if key is not None else b'K' * 16
        self.iv = iv if iv is not None else b'I' * 16
        
        self._size = None

    # ------------------------------------------------------ Helpers

    def _read_finfo(self):
        finfo = None
        if os.path.isfile(self._file_finfo):
            with open(self._file_finfo) as f:
                finfo = json.load(f)
        return finfo

    def _get_plaintext_size(self):
        return len(MixSlice.decrypt(self._path, self.key, self.iv))

    def _write_finfo(self):
        with open(self._file_finfo, 'w') as f:
            json.dump({'size': self._size}, f)

    # ------------------------------------------------------ Methods

    def rename(self, path, file_finfo):
        self._path = path
        self._file_finfo = file_finfo

        self._size = None

    # ------------------------------------------------------ Size

    @property
    def size(self):
        # Retrieve plaintext size when necessary
        if self._size is None:
            # Reuse info written to file when available, otherwise compute it
            finfo = self._read_finfo()
            if not finfo:
                self._size = self._get_plaintext_size()
                self._write_finfo()
            else:
                self._size = finfo["size"]
                
        return self._size

    @size.setter
    def size(self, value):
        if self._size == value:
            return
        self._size = value
        self._write_finfo()
