import json
import os
import requests
import subprocess
import time

from constants import *
from utils import *


def mesos_path():
    """Returns the MESOS_BIN_PATH environment variable."""
    return os.environ.get(MESOS_BIN_PATH)


def start_master(work_dir, flags=[]):
    """Starts a Master with the given flags."""
    print 'Starting Mesos master at %s' % work_dir
    stdout = open(os.path.join(work_dir, 'stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    master = subprocess.Popen([
        os.path.join(mesos_path(), MESOS_MASTER_BIN),
        '--ip=%s' % MESOS_MASTER_IP,
        '--zk=zk://localhost:2181/mesos',
        '--quorum=1',
        '--work_dir=%s' % work_dir] + flags,
        stdout=stdout,
        stderr=stderr)

    assert master.returncode is None

    register_exit(lambda: master.kill())


def wait_for_master(work_dir, timeout=5, is_ssl=False):
    """Waits for a Master to start."""
    while timeout:
        try:
            result = requests.get('http%s://%s/master/state.json' % ('s' if is_ssl else '', MESOS_MASTER_CIDR),
                verify=os.path.join(work_dir, SSL_CHAIN_FILE))
            if result.status_code == 200:
                break
        except requests.ConnectionError as e:
            pass

        time.sleep(1)
        timeout -= 1

    return timeout > 0


def start_agent(work_dir, flags=[], ip=1):
    """Starts an Agent with the given flags."""
    print 'Starting Mesos agent'
    stdout = open(os.path.join(work_dir, 'a%d_stdout.txt' % ip), 'w')
    stderr = open(os.path.join(work_dir, 'a%d_stderr.txt' % ip), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    agent = subprocess.Popen([
        os.path.join(mesos_path(), MESOS_AGENT_BIN),
        '--master=%s' % MESOS_MASTER_CIDR,
        '--work_dir=%s' % work_dir,
        '--ip=127.0.0.%d' % ip,
        '--hostname=127.0.0.%d' % ip] + flags,
        stdout=stdout,
        stderr=stderr)

    assert agent.returncode is None

    register_exit(lambda: call(['rm', '-rf', '/tmp/mesos/meta/slaves/latest']))
    register_exit(lambda: agent.kill())


def wait_for_agent(work_dir, num_agents=1, timeout=7, is_ssl=False):
    """Waits for an Agent to start."""
    timeout *= num_agents
    while timeout:
        try:
            result = requests.get('http%s://%s/master/state.json' % ('s' if is_ssl else '', MESOS_MASTER_CIDR),
                verify=os.path.join(work_dir, SSL_CHAIN_FILE))
            result = result.json()
            if len(result['slaves']) == num_agents and all(map(lambda x: x['active'], result['slaves'])):
                break
        except requests.ConnectionError as e:
            pass

        time.sleep(1)
        timeout -= 1

    return timeout > 0
