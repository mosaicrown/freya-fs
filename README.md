# FreyaFS - a Mix&Slice virtual filesystem

## Prerequisites

- Install the `openssl/crypto` library.
  On Ubuntu you can do so as follows:
  
  ```bash
  sudo apt install libssl-dev
  ```

- Install the `aesmix` and `fusepy` python modules:

  ```bash
  pip install aesmix
  pip install fusepy
  ```

If you want to compile it:

- Install the `pyinstaller` python module:

  ```bash
  pip install pyinstaller
  ```

- Bundle FreyaFS and all its dependencies into a single binary `freyafs`:

  ```bash
  pyinstaller main.py -n freyafs --noconsole --onefile
  ```

## Usage

```
usage: freyafs [-h] -d DATA [-m METADATA] [-t] MOUNT

Freya File System - a Mix&Slice virtual file system

positional arguments:
  MOUNT                 mount point of FreyaFS

optional arguments:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  folder containing your encrypted files
  -m METADATA, --metadata METADATA
                        folder containing your .private and .public metadata files.
                        The metadata files in this folder must have the same name and path as the corresponding encrypted file.
                        If not specified, defaults to the --data folder.
  -t, --multithread     run in multi-threaded mode. If not specified, defaults to the --data folder
```

### From source

You can get usage information with:
```
python3 main.py --help
```

### From binary

After following the instruction to compile FreyaFS, you will find the
`freyafs` executable under the `dist` directory.

You can get usage information with:
```
./dist/freyafs --help
```

## Acknowlegments

This repository has been produced by [Michele Beretta](https://github.com/micheleberetta98) as part of his bachelor thesis.
