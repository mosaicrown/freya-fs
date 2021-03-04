import base64
import getpass
import json
import os
import sys

import nacl.pwhash
import nacl.secret
import nacl.utils


class Info:
    def __init__(self, key=None, iv=None, size=None):
        self.key = key if key is not None else nacl.utils.random(16)
        self.iv = iv if iv is not None else nacl.utils.random(16)
        self.size = size if size is not None else 0

class Metadata:
    def __init__(self, path):
        self.path = path

        pw = getpass.getpass("Password: ").encode("utf-8")
        if not os.path.isfile(path):
            confirm = getpass.getpass("Confirm password: ").encode("utf-8")
            if pw != confirm:
                print("ERROR: Your password and confirmation password do not match.")
                sys.exit()
       
        salt = b'\xd0\xe1\x03\xc2Z<R\xaf]\xfe\xd5\xbf\xf8u|\x8f'

        # Generate the key
        kdf = nacl.pwhash.argon2i.kdf
        self.key = kdf(nacl.secret.SecretBox.KEY_SIZE, pw, salt)

        self.metadata = {}
        if os.path.isfile(path):
            # Read the encrypted metadata
            with open(path, 'r') as f:
                content = f.read()
                encrypted = base64.b64decode(content)

            # Decrypt metadata
            box = nacl.secret.SecretBox(self.key)
            # TODO: add try catch on nacl.exceptions.CryptoError
            plaintext = box.decrypt(encrypted)

            # Read JSON metadata
            read = json.loads(plaintext)

            # Recreate metadata data structure
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
        # Convert metadata to JSON-like format
        to_write = {}
        for path, info in self.metadata.items():
            to_write[path] = {
                'key': base64.b64encode(info.key).decode("ascii"),
                'iv': base64.b64encode(info.iv).decode("ascii"),
                'size': info.size
            }
        # Produce JSON string
        plaintext = json.dumps(to_write)

        # Encrypt metadata
        box = nacl.secret.SecretBox(self.key)
        encrypted = box.encrypt(plaintext.encode("utf-8"))

        # Store encrypted metadata
        with open(self.path, 'w') as f:
            content = base64.b64encode(encrypted).decode("ascii")
            f.write(content)
