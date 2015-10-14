import json
import os
import requests
import subprocess
import time

from constants import *
from utils import *


def marathon_path():
    """Returns the PATH_TO_MARATHON environment variable."""
    return os.environ.get(PATH_TO_MARATHON)


def start_marathon(work_dir, is_ssl=False, flags=[]):
    """Starts Marathon."""
    print 'Starting Marathon'
    stdout = open(os.path.join(work_dir, 'm_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'm_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    marathon = subprocess.Popen([
        os.path.join(marathon_path(), MARATHON_BIN),
        '--http_port', '8081',
        '--https_port', '8444',
        '--master', MESOS_MASTER_CIDR,
        '--zk', 'zk://localhost:2181/marathon'] + flags,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: marathon.kill())


def wait_for_marathon(work_dir, timeout=25, is_ssl=False):
    """Waits for the Marathon UI to show up."""
    while timeout:
        try:
            result = requests.get('http%s://localhost:%d/ping' % ('s' if is_ssl else '', 8444 if is_ssl else 8081),
                verify=os.path.join(work_dir, SSL_CHAIN_FILE))
            if result.status_code == 200:
                break
        except requests.ConnectionError as e:
            pass

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    return check_framework_in_state_json(work_dir, 'marathon', is_ssl)


def run_example_marathon_app(work_dir, timeout=10, is_ssl=False):
    """Runs a trivial marathon command and checks the result."""
    app_def = {
               "id" : "basic-0",
              "cmd" : "while [ true ]; do echo 'Hello Marathon'; sleep 5; done",
             "cpus" : 0.1,
              "mem" : 10.0,
        "instances" : 1
    }

    # Launch a sleep task.
    requests.post('http%s://localhost:%d/v2/apps' % ('s' if is_ssl else '', 8444 if is_ssl else 8081),
        headers={"Content-Type": "application/json"},
        data=json.dumps(app_def),
        verify=os.path.join(work_dir, SSL_CHAIN_FILE))

    # Wait for it.
    while timeout:
        result = requests.get('http%s://localhost:%d/v2/apps/basic-0/tasks' % ('s' if is_ssl else '', 8444 if is_ssl else 8081),
            verify=os.path.join(work_dir, SSL_CHAIN_FILE))

        result = result.json()
        if len(result['tasks']) == 1 and result['tasks'][0]['appId'] == '/basic-0':
            return True

        time.sleep(1)
        timeout -= 1

    return False
