from argparse import ArgumentParser
from fuse import FUSE

from freyafs import FreyaFS

parser = ArgumentParser(
    description="Freya File System - a Mix&Slice virtual file system"
)

parser.add_argument('mountpoint',
                    metavar='MOUNT',
                    help='mount point of FreyaFS')
parser.add_argument('data',
                    metavar='DATA',
                    help='folder containing your encrypted files')
parser.add_argument('-t', '--multithread',
                    help='run in multi-threaded mode',
                    action='store_true',
                    default=False)

args = parser.parse_args()

if __name__ == '__main__':
    data = args.data
    mountpoint = args.mountpoint

    print(f"[*] Mounting FreyaFS to {mountpoint}")

    FUSE(FreyaFS(data), mountpoint,
         nothreads=not args.multithread, foreground=True)
