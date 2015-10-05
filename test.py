import atexit
import json
import os
import requests
import subprocess
import tempfile
import time
import unittest


MESOS_BIN_PATH = 'MESOS_BIN_PATH'
MESOS_MASTER_BIN = 'mesos-master.sh'
MESOS_AGENT_BIN = 'mesos-slave.sh'


CLEANUP_LAMBDAS = []
def register_exit(func):
    """
    Stores a lambda in a stack for cleanup later.
    All lambdas should be idempotent.
    """

    atexit.register(func)
    CLEANUP_LAMBDAS.append(func)


def cleanup():
    """Calls all cleanup lambdas."""
    while len(CLEANUP_LAMBDAS):
        CLEANUP_LAMBDAS.pop()()


def mesos_path():
    """Returns the MESOS_BIN_PATH environment variable."""
    return os.environ.get(MESOS_BIN_PATH)


def start_master(work_dir, flags=[]):
    """Starts a Master with the given flags."""
    print 'Starting Mesos master at %s' % work_dir
    stdout = open(os.path.join(work_dir, 'stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'stderr.txt'), 'w')
    master = subprocess.Popen(
        [os.path.join(mesos_path(), MESOS_MASTER_BIN),
         '--work_dir=%s' % work_dir] + flags,
        stdin=None,
        stdout=stdout,
        stderr=stderr)

    register_exit(lambda: master.kill())
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())


def wait_for_master(timeout=15, is_ssl=False):
    """Waits for a Master to start."""
    while timeout:
        try:
            result = requests.get('http%s://localhost:5050/master/state.json' % ('s' if is_ssl else ''))
            if result.status_code == 200:
                break
        except requests.ConnectionError:
            pass

        time.sleep(1)
        timeout -= 1

    return timeout > 0


def start_agent(work_dir, flags=[]):
    """Starts an Agent with the given flags."""
    print 'Starting Mesos agent'
    stdout = open(os.path.join(work_dir, 'a_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'a_stderr.txt'), 'w')
    agent = subprocess.Popen(
        [os.path.join(mesos_path(), MESOS_AGENT_BIN),
         '--master=10.141.141.1:5050'] + flags,
        stdin=None,
        stdout=stdout,
        stderr=stderr)

    register_exit(lambda: agent.kill())
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())


def wait_for_agent(num_agents=1, timeout=15, is_ssl=False):
    """Waits for an Agent to start."""
    while timeout:
        try:
            result = requests.get('http%s://localhost:5050/master/state.json' % ('s' if is_ssl else ''))
            if result.status_code == 200:
                result = result.json()
                if len(result['slaves']) == num_agents and all(map(lambda x: x['active'], result['slaves'])):
                    break
        except requests.ConnectionError:
            pass

        time.sleep(1)
        timeout -= 1

    return timeout > 0


class MasterAgentTest(unittest.TestCase):
    """Starts a Master and an Agent."""

    @classmethod
    def setUpClass(cls):
        work_dir = tempfile.mkdtemp(prefix='mesos-integration-')

        start_master(work_dir)
        if not wait_for_master():
            self.fail('Master failed to start in time.')

        start_agent(work_dir)
        if not wait_for_agent():
            self.fail('Agent failed to start in time.')


    @classmethod
    def tearDownClass(cls):
        cleanup()


    def test_foo(self):
        print 'TODO...'


    def test_bar(self):
        print 'TODO...'

if __name__ == '__main__':
    if MESOS_BIN_PATH not in os.environ:
        print 'Environment variable "%s" not set.' % MESOS_BIN_PATH
        exit(1)

    unittest.main()
