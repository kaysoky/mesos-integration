import json
import os
import requests
import subprocess
import time

from constants import *
from utils import *


def jenkins_path():
    """Returns the PATH_TO_JENKINS environment variable."""
    return os.environ.get(PATH_TO_JENKINS)


def start_jenkins(work_dir, flags=[], is_ssl=False):
    """Starts Jenkins."""
    print 'Starting Jenkins'

    # Copy the configuration over.
    call(['mkdir', '-p', 'work'])
    call(['cp', 'jenkins-config.xml', 'work/config.xml'])

    # TODO: Copy the job configuration over.

    stdout = open(os.path.join(work_dir, 'j_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'j_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    jenkins = subprocess.Popen([
        'mvn', '-f', jenkins_path(), 'hpi:run'] + flags,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: call(['rm', '-rf', 'work']))
    register_exit(lambda: jenkins.kill())


def wait_for_jenkins(work_dir, timeout=45, is_ssl=False):
    """Waits for the Jenkins to start up."""
    while timeout:
        try:
            result = requests.get('http://localhost:8080/jenkins')
            if result.status_code == 200:
                break
        except requests.ConnectionError as e:
            pass

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    return check_framework_in_state_json(work_dir, 'Jenkins Scheduler', is_ssl)


def configure_jenkins(work_dir, is_ssl=False):
    """TODO: Incomplete since this plugin doesn't seem to work."""

    # Disable the default build executor (which doesn't run on mesos).
    result = requests.post('http://localhost:8080/jenkins/computer/(master)/toggleOffline')
    assert result.status_code == 200


