import hashlib
import os
import sys
import time

import py7zr
import requests
from tqdm import tqdm

from tasks.task import Task

class CompressFile(Task):