import atexit
import json
import os
import requests
import ssl
import subprocess
import time

from constants import *


def mesos_path():
    """Returns the MESOS_BIN_PATH environment variable."""
    return os.environ.get(MESOS_BIN_PATH)


def marathon_path():
    """Returns the PATH_TO_MARATHON environment variable."""
    return os.environ.get(PATH_TO_MARATHON)


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
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    master = subprocess.Popen(
        [os.path.join(mesos_path(), MESOS_MASTER_BIN),
         '--work_dir=%s' % work_dir] + flags,
        stdin=None,
        stdout=stdout,
        stderr=stderr)

    assert master.returncode is None

    register_exit(lambda: master.kill())


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
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    agent = subprocess.Popen(
        [os.path.join(mesos_path(), MESOS_AGENT_BIN),
         '--master=10.141.141.1:5050'] + flags,
        stdin=None,
        stdout=stdout,
        stderr=stderr)

    assert agent.returncode is None

    register_exit(lambda: agent.kill())


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


def start_marathon(work_dir):
    """Starts Marathon."""
    print 'Starting Marathon'
    stdout = open(os.path.join(work_dir, 'm_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'm_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    # Start ZooKeeper.
    subprocess.check_call(['zkserver', 'start'])
    register_exit(lambda: subprocess.check_call(['zkserver', 'stop']))

    marathon = subprocess.Popen(
        [os.path.join(marathon_path(), MARATHON_BIN),
         '--master', '10.141.141.1:5050',
         '--zk', 'zk://localhost:2181/marathon'],
        stdin=None,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: marathon.kill())


def wait_for_marathon(work_dir, timeout=15, is_ssl=False):
    """Waits for the Marathon UI to show up."""
    while timeout:
        try:
            result = requests.get('http%s://localhost:8080/' % ('s' if is_ssl else ''),
                                  verify=os.path.join(work_dir, SSL_CERT_FILE))
            if result.status_code == 200:
                break
        except requests.ConnectionError as e:
            print e

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    # Check that the framework shows up on the master.
    result = requests.get('http%s://localhost:5050/master/state.json' % ('s' if is_ssl else ''),
                          verify=os.path.join(work_dir, SSL_CERT_FILE))
    if result.status_code == 200:
        result = result.json()['frameworks']
        result = filter(lambda x: x['name'] == 'marathon', result)
        if len(result) == 1 and result[0]['active']:
            return True

    return False


