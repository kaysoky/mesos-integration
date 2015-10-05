import atexit
import json
import os
import requests
import ssl
import subprocess
import tempfile
import time
import unittest


SSL_SUPER_SECURE_PASSPHRASE = 'pass:passphrase'
SSL_CONFIG_FILE = 'config.txt'
SSL_KEY_FILE = 'key.pem'
SSL_CERT_FILE = 'cert.pem'
MESOS_BIN_PATH = 'MESOS_BIN_PATH'
MESOS_MASTER_BIN = 'mesos-master.sh'
MESOS_AGENT_BIN = 'mesos-slave.sh'


CLEANUP_LAMBDAS = []
def register_exit(func):
    """
    Stores a lambda in a stack for cleanup later.
    All lambdas should be idempotent, as they may be called more than once.
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


def generate_ssl_stuff(work_dir):
    """Generates the required SSL files."""
    subprocess.check_call(
        ['openssl', 'req', '-nodes', '-new', '-x509',
         '-batch', '-days', '365',
         '-subj', '/CN=localhost',
         '-keyout', os.path.join(work_dir, SSL_KEY_FILE),
         '-out', os.path.join(work_dir, SSL_CERT_FILE)])


    '''
    These are the calls with passphrase.
    Currently, the passphrase can't be supplied to the master trivially.

    subprocess.check_call(
        ['openssl', 'genrsa', '-des3', '-f4',
         '-passout', SSL_SUPER_SECURE_PASSPHRASE,
         '-out', os.path.join(work_dir, SSL_KEY_FILE),
         '4096'])

    subprocess.check_call(
        ['openssl', 'req', '-new', '-x509',
         '-passin', SSL_SUPER_SECURE_PASSPHRASE,
         '-batch', '-days', '365',
         '-subj', '/CN=localhost',
         '-key', os.path.join(work_dir, SSL_KEY_FILE),
         '-out', os.path.join(work_dir, SSL_CERT_FILE)])
    '''


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

    assert master.returncode is None

    register_exit(lambda: master.kill())
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())


def wait_for_master(work_dir, timeout=5, is_ssl=False):
    """Waits for a Master to start."""
    while timeout:
        try:
            result = requests.get('http%s://localhost:5050/master/state.json' % ('s' if is_ssl else ''),
                                  verify=os.path.join(work_dir, SSL_CERT_FILE))
            if result.status_code == 200:
                break
        except requests.ConnectionError as e:
            print e

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

    assert agent.returncode is None

    register_exit(lambda: agent.kill())
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())


def wait_for_agent(work_dir, num_agents=1, timeout=5, is_ssl=False):
    """Waits for an Agent to start."""
    while timeout:
        try:
            result = requests.get('http%s://localhost:5050/master/state.json' % ('s' if is_ssl else ''),
                                  verify=os.path.join(work_dir, SSL_CERT_FILE))
            if result.status_code == 200:
                result = result.json()
                if len(result['slaves']) == num_agents and all(map(lambda x: x['active'], result['slaves'])):
                    break
        except requests.ConnectionError as e:
            print e

        time.sleep(1)
        timeout -= 1

    return timeout > 0


class MasterAgentTest(unittest.TestCase):
    """
    Enables SSL.
    Starts a Master and an Agent.
    """

    @classmethod
    def setUpClass(cls):
        work_dir = tempfile.mkdtemp(prefix='mesos-integration-')

        # Setup SSL things.
        generate_ssl_stuff(work_dir)
        os.environ['SSL_ENABLED'] = 'true'
        os.environ['SSL_KEY_FILE'] = os.path.join(work_dir, SSL_KEY_FILE)
        os.environ['SSL_CERT_FILE'] = os.path.join(work_dir, SSL_CERT_FILE)

        # This is less secure.  But SSL_ENABLE_TLS_V1_2 is not available.
        os.environ['SSL_ENABLE_TLS_V1_0'] = 'true'

        # Start Mesos.
        start_master(work_dir)
        if not wait_for_master(work_dir, is_ssl=True):
            assert False, 'Master failed to start in time.'

        start_agent(work_dir)
        if not wait_for_agent(work_dir, is_ssl=True):
            assert False, 'Agent failed to start in time.'


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
