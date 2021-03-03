import os
import errno
import stat
import shutil

from fuse import FuseOSError, Operations
from manager import Manager
from metadata import Metadata


def is_metadata(path=''):
    return path == ".freyafs"


def join_paths(root, partial):
    return os.path.join(root, partial.lstrip('/'))


def strip_dot_enc(path=''):
    if path.endswith('.enc'):
        return '.'.join(path.split('.')[:-1])

    return path


class FreyaFS(Operations):
    def __init__(self, root, mountpoint):
        self.root = root

        # Retrieve FreyaFS metadata
        self.metadata = Metadata(os.path.join(root, ".freyafs"))

        # File .enc aperti
        self.enc_files = Manager()

        print(f"[*] FreyaFS mounted")
        print(f"Now, through the FreyaFS mountpoint ({mountpoint}), you can use a Mix&Slice encrypted filesystem seemlessly.")
        print(f"FreyaFS will persist your encrypted data at {root}.")

    # --------------------------------------------------------------------- Helpers

    def _full_path(self, path):
        return join_paths(self.root, path)

    def _is_file(self, path):
        if not os.path.exists(self._full_path(path)):
            return False

        attr = self.getattr(path)
        return attr['st_mode'] & stat.S_IFREG == stat.S_IFREG

    # --------------------------------------------------------------------- Filesystem methods

    def access(self, path, mode):
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    # Attributi di path (file o cartella)
    def getattr(self, path, fh=None):
        full_path = self._full_path(path)

        st = os.lstat(full_path)

        def _is_directory(path):
            for file in os.listdir(path):
                if not file.startswith("frag_") or not file.endswith(".dat") or \
                        not os.path.isfile(os.path.join(path, file)):
                    return True
            return False

        if _is_directory(self._full_path(path)):
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

        try:

            if full_path in self.metadata:
                print(f"{full_path} = {self.metadata[full_path]}")
            else:
                print(f"{full_path} = unknown")

            return {
                'st_mode': stat.S_IFREG | (st.st_mode & ~stat.S_IFDIR),
                'st_nlink': 1,
                'st_atime': st.st_atime,
                'st_ctime': st.st_ctime,
                'st_gid': st.st_gid,
                'st_mtime': st.st_mtime,
                'st_size': self.metadata[full_path],
                'st_uid': st.st_uid
            }
        except:
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..']

        if os.path.isdir(full_path):
            real_stuff = os.listdir(full_path)
            virtual_stuff = [
                x for x in real_stuff if not is_metadata(x)]
            dirents.extend(virtual_stuff)

        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        os.rmdir(self._full_path(path))

    def mkdir(self, path, mode):
        os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
                                                         'f_frsize', 'f_namemax'))

    def unlink(self, path):
        full_path = self._full_path(path)
        shutil.rmtree(full_path)
        self.metadata.remove(full_path)
        return

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        full_old_path = self._full_path(old)
        full_new_path = self._full_path(new)

        if self._is_file(old):
            # Rinomino un file
            if self._is_file(new):
                self.unlink(new)

            os.rename(full_old_path, full_new_path)

            if full_old_path in self.enc_files:
                self.enc_files.rename(full_old_path, full_new_path)
            self.metadata.rename(full_old_path, full_new_path)
        else:
            # Rinomino una cartella
            os.rename(full_old_path, full_new_path)
            self.metadata.renamedir(full_old_path, full_new_path)

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        os.utime(self._full_path(path), times)

    # --------------------------------------------------------------------- File methods

    def open(self, path, flags):
        full_path = self._full_path(path)

        attr = self.getattr(path)
        self.enc_files.open(full_path, attr['st_mtime'])
        return 0

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        self.enc_files.create(full_path)
        self.metadata.add(full_path)
        return 0

    def read(self, path, length, offset, fh):
        full_path = self._full_path(path)
        if full_path in self.enc_files:
            return self.enc_files.read_bytes(full_path, offset, length)

        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        full_path = self._full_path(path)
        if full_path in self.enc_files:
            bytes_written = self.enc_files.write_bytes(full_path, buf, offset)
            self.metadata.update(full_path, self.enc_files.cur_size(full_path))
            return bytes_written

        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        if full_path in self.enc_files:
            self.enc_files.truncate_bytes(full_path, length)
            self.metadata.update(full_path, length)
            return

        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        full_path = self._full_path(path)
        if full_path in self.enc_files:
            self.enc_files.flush(full_path)
            return 0

        return os.fsync(fh)

    def release(self, path, fh):
        full_path = self._full_path(path)
        if full_path in self.enc_files:
            self.enc_files.release(full_path)
            return 0

        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)
