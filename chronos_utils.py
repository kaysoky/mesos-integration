import json
import os
import subprocess
import time

from constants import *
from utils import *


def chronos_jar():
    """Returns the PATH_TO_CHRONOS environment variable."""
    return os.environ.get(PATH_TO_CHRONOS)


def start_chronos(work_dir, flags=[], is_ssl=False):
    """Starts Chronos."""
    print 'Starting Chronos'
    stdout = open(os.path.join(work_dir, 'c_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'c_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    chronos = subprocess.Popen([
        'java', '-cp', chronos_jar(),
        'org.apache.mesos.chronos.scheduler.Main',
        '--mesos_framework_name', 'chronos',
        '--hostname', 'localhost',
        '--http_address', 'localhost',
        '--master', MESOS_MASTER_CIDR,
        '--zk_hosts', 'localhost:2181'] + flags,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: chronos.kill())


def wait_for_chronos(work_dir, timeout=15, is_ssl=False):
    """Waits for the Chronos to start up."""
    while timeout:
        try:
            # Note: Some versions of Python (on OSX) do not have TLSv1.2 support.
            # So we need to use curl to talk via HTTPS.
            output = call(curl_ssl(work_dir) + ['-I', '-m', '2',
                'http%s://localhost:%d/scheduler/jobs' % ('s' if is_ssl else '', 8443 if is_ssl else 8080)])
            if '200 OK' in output:
                break
        except subprocess.CalledProcessError as e:
            pass

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    return check_framework_in_state_json(work_dir, 'chronos', is_ssl)
