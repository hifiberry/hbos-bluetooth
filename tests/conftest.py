import os
import sys
import tempfile

# ConfigFileManager reads and creates ~/.config/hifiberry/bluetooth.conf at
# import time; keep the tests out of the real home directory.
os.environ["HOME"] = tempfile.mkdtemp(prefix="hbos-bluetooth-test-")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
