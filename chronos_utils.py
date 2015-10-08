import json
import os
import requests
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
            result = requests.get('http%s://localhost:%d/scheduler/jobs' % ('s' if is_ssl else '', 8443 if is_ssl else 8080),
                verify=os.path.join(work_dir, SSL_CHAIN_FILE))
            if result.status_code == 200:
                break
        except requests.ConnectionError as e:
            pass

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    return check_framework_in_state_json(work_dir, 'chronos', is_ssl)
