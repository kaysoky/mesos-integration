import json
import os
import requests
import subprocess
import time

from constants import *


def call(command):
    """
    Blocks on subprocess.Popen until the command finishes.
    Returns the stdout and stderr.  Suppresses console output.
    """
    stdout, stderr = subprocess.Popen(command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    return stdout


CLEANUP_LAMBDAS = []
def register_exit(func):
    """
    Stores a lambda in a stack for cleanup later.
    All lambdas should be idempotent, as they may be called more than once.
    """

    CLEANUP_LAMBDAS.append(func)


def cleanup():
    """Calls all cleanup lambdas."""
    while len(CLEANUP_LAMBDAS):
        CLEANUP_LAMBDAS.pop()()


def start_zookeeper():
    """Starts ZooKeeper."""
    call(['zkserver', 'start'])
    register_exit(lambda: call(['rm', '-rf', '/usr/local/var/run/zookeeper/data']))
    register_exit(lambda: call(['zkserver', 'stop']))


def check_framework_in_state_json(work_dir, framework, is_ssl=False):
    """Checks master's state.json for the given framework."""
    result = requests.get('http%s://localhost:5050/master/state.json' % ('s' if is_ssl else ''),
        verify=os.path.join(work_dir, SSL_CHAIN_FILE))
    result = result.json()['frameworks']
    result = filter(lambda x: x['name'] == framework, result)
    if len(result) == 1 and result[0]['active']:
        return True

    return False
