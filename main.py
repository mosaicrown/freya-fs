from argparse import ArgumentParser
from fuse import FUSE, FuseOSError, Operations

from freyafs import FreyaFS

parser = ArgumentParser(
    description="Freya File System - a Mix&Slice virtual file system")

parser.add_argument('mountpoint',
                    metavar='MOUNT',
                    help='mount point of FreyaFS'
                    )
parser.add_argument('data',
                    metavar='DATA',
                    help='folder containing your encrypted files',
                    )
parser.add_argument('-m', '--metadata',
                    help='''folder containing your .private and .public metadata files.
                    The metadata files in this folder must have the same name and path as the corresponding encrypted file.
                    If not specified, defaults to the --data folder.''',
                    default=None
                    )
parser.add_argument('-t', '--multithread',
                    help='run in multi-threaded mode. If not specified, defaults to the --data folder',
                    action='store_true',
                    default=False
                    )

args = parser.parse_args()

if __name__ == '__main__':
    data = args.data
    metadata = args.metadata
    mountpoint = args.mountpoint

    print(f"[*] Mounting FreyaFS to {mountpoint}")

    FUSE(FreyaFS(data, metadata), mountpoint,
         nothreads=not args.multithread, foreground=True)
