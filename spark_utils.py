import json
import os
import subprocess
import time

from constants import *
from utils import *


def spark_path():
    """Returns the PATH_TO_SPARK environment variable."""
    return os.environ.get(PATH_TO_SPARK)


def run_example_spark_job(work_dir, timeout=25):
    """Runs a Spark job and checks the result."""
    print 'Starting Spark job'
    stdout = open(os.path.join(work_dir, 's_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 's_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    spark = subprocess.Popen([
        os.path.join(spark_path(), 'bin/spark-submit'),
        '--master', 'mesos://%s' % MESOS_MASTER_CIDR,
        os.path.join(spark_path(), 'examples/src/main/python/pi.py'), '5'],
        stdin=None,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: spark.kill() if spark.poll() is None else '')

    while timeout:
        if spark.poll() is not None:
            break

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    with open(os.path.join(work_dir, 's_stdout.txt'), 'r') as f:
        result = f.read()
        return 'Pi is roughly 3' in result
