import atexit
import os
import tempfile
import time
import unittest

from constants import *
from utils import *


class NoSSL_Test(unittest.TestCase):
    """Sanity tests stuff without SSL."""

    @classmethod
    def setUpClass(cls):
        cls.work_dir = tempfile.mkdtemp(prefix='mesos-integration-')

        os.environ['SSL_ENABLED'] = 'false'

        # Start Mesos.
        start_master(cls.work_dir)
        if not wait_for_master(cls.work_dir):
            assert False, 'Master failed to start in time.'

        start_agent(cls.work_dir)
        if not wait_for_agent(cls.work_dir):
            assert False, 'Agent failed to start in time.'

        start_zookeeper()


    @classmethod
    def tearDownClass(cls):
        cleanup()


    def test_chronos(self):
        start_chronos(self.work_dir)
        self.assertTrue(wait_for_chronos(self.work_dir), 'Chronos failed to start in time.')


    def test_marathon(self):
        start_marathon(self.work_dir)
        self.assertTrue(wait_for_marathon(self.work_dir), 'Marathon failed to start in time.')


class SSL_Test(unittest.TestCase):
    """Tests stuff with SSL enabled, without downgrade."""

    @classmethod
    def setUpClass(cls):
        cls.work_dir = tempfile.mkdtemp(prefix='mesos-integration-')

        # Setup SSL things.
        generate_ssl_stuff(cls.work_dir)
        os.environ['SSL_ENABLED'] = 'true'
        os.environ['SSL_KEY_FILE'] = os.path.join(cls.work_dir, SSL_KEY_FILE)
        os.environ['SSL_CERT_FILE'] = os.path.join(cls.work_dir, SSL_CERT_FILE)

        # This is less secure.  But SSL_ENABLE_TLS_V1_2 is not available.
        os.environ['SSL_ENABLE_TLS_V1_0'] = 'true'

        # Start Mesos.
        start_master(cls.work_dir)
        if not wait_for_master(cls.work_dir, is_ssl=True):
            assert False, 'Master failed to start in time.'

        start_agent(cls.work_dir)
        if not wait_for_agent(cls.work_dir, is_ssl=True):
            assert False, 'Agent failed to start in time.'

        start_zookeeper()


    @classmethod
    def tearDownClass(cls):
        cleanup()


    def test_marathon(self):
        start_marathon(self.work_dir, is_ssl=True,
                       flags=['--ssl_keystore_path', os.path.join(self.work_dir, SSL_MARATHON_KEYSTORE),
                              '--ssl_keystore_password', SUPER_SECURE_PASSPHRASE])
        self.assertTrue(wait_for_marathon(self.work_dir, is_ssl=True), 'Marathon failed to start in time.')


if __name__ == '__main__':
    # Check that `openssl` is available.
    subprocess.check_call(['openssl', 'version'])

    # Check that ZooKeeper is available.
    subprocess.check_call(['zkserver', 'print-cmd'])

    for var in [MESOS_BIN_PATH, PATH_TO_MARATHON, PATH_TO_CHRONOS]:
        if var not in os.environ:
            print 'Environment variable "%s" not set.' % var
            exit(1)

    atexit.register(cleanup)
    unittest.main()
