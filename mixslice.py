import os as _os
import shutil as _shutil
from io import BytesIO as _BytesIO

from aesmix import mix_and_slice as _mix_and_slice
from aesmix import unslice_and_unmix as _unslice_and_unmix
from aesmix.padder import Padder as _Padder


class MixSlice:

    # These constant variables reflect the definitions within the aesmix
    # library (see aesmix/includes/aes_mix.h)
    MINI_SIZE = 4
    MINI_PER_MACRO = 1024
    MACRO_SIZE = MINI_SIZE * MINI_PER_MACRO

    @staticmethod
    def encrypt(data, path, key, iv, threads=None, padder=None):
        """Creates a MixSlice from plaintext data.

        Args:
            data (bytestr): The data to encrypt (multiple of MACRO_SIZE).
            key (bytestr): The key used for AES encryption (16 bytes long).
            iv (bytestr): The iv used for AES encryption (16 bytes long).
            threads (int): The number of threads used. (default: cpu count).

        Returns:
            A new MixSlice that holds the encrypted fragments.
        """
        padder = padder or _Padder(blocksize=MixSlice.MACRO_SIZE)
        padded_data = padder.pad(data)
        fragments = _mix_and_slice(data=padded_data, key=key,
                                   iv=iv, threads=threads)
        fragments = [_BytesIO(f) for f in fragments]

        if not _os.path.exists(path):
            _os.makedirs(path)

        name = "frag_%%0%dd.dat" % len(str(len(fragments)))
        for fragid in range(len(fragments)):
            fragment = fragments[fragid]
            assert isinstance(fragment, _BytesIO)
            fragment.seek(0)
            destination = _os.path.join(path, name % fragid)
            with open(destination, "wb") as fp:
                _shutil.copyfileobj(fragment, fp)
            fragment.close()

    @staticmethod
    def _read_fragment(fragment):
        if isinstance(fragment, _BytesIO):
            fragment.seek(0)
            data = fragment.read()
            fragment.seek(0)
        else:
            with open(fragment, "rb") as fp:
                data = fp.read()
        return data

    @staticmethod
    def decrypt(path, key, iv, threads=None, padder=None):

        files = sorted(_os.listdir(path))
        assert len(files) == MixSlice.MINI_PER_MACRO, \
            "exactly MINI_PER_MACRO files required in path."
        filenames = [_os.path.join(path, f) for f in files]
        fragments = [MixSlice._read_fragment(f) for f in filenames]

        padded_data = _unslice_and_unmix(
            fragments=fragments,
            key=key,
            iv=iv,
            threads=threads)

        padder = padder or _Padder(blocksize=MixSlice.MACRO_SIZE)
        return padder.unpad(padded_data)
