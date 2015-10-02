import os
import requests
import subprocess
import tempfile
import time
import unittest


MESOS_BIN_PATH = 'MESOS_BIN_PATH'
MESOS_MASTER_BIN = 'mesos-master.sh'

def mesos_path():
    """Returns the MESOS_BIN_PATH environment variable."""
    return os.environ.get(MESOS_BIN_PATH)

class TestIncomplete(unittest.TestCase):
    """Incomplete."""

    def setUp(self):
        """Starts a Master and an Agent."""
        self.work_dir = tempfile.mkdtemp(prefix='mesos-integration-')

        print 'Starting Mesos master at %s' % self.work_dir
        stdout = open(os.path.join(self.work_dir, 'stdout.txt'), 'w')
        stderr = open(os.path.join(self.work_dir, 'stderr.txt'), 'w')
        self.master = subprocess.Popen(
            [os.path.join(mesos_path(), MESOS_MASTER_BIN),
             '--work_dir=%s' % self.work_dir],
            stdin=None,
            stdout=stdout,
            stderr=stderr)

        print 'Waiting for Mesos master...'
        timeout = 15
        while timeout:
            try:
                result = requests.get('http://localhost:5050/master/state.json')
                if result.status_code == 200:
                    break
                print result.text
            except requests.ConnectionError:
                pass

            time.sleep(1)
            timeout -= 1

        if not timeout:
            self.tearDown()
            self.fail('Master failed to start in time.')

    def test_something(self):
        print 'TODO...'

    def tearDown(self):
        """Stops the Master and Agent."""
        self.master.kill()

if __name__ == '__main__':
    if MESOS_BIN_PATH not in os.environ:
        print 'Environment variable "%s" not set.' % MESOS_BIN_PATH
        exit(1)

    unittest.main()
