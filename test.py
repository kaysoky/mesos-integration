import atexit
import os
import tempfile
import time
import unittest

from constants import *
from utils import *

import ssl_utils
from chronos_utils import *
from marathon_utils import *
from mesos_utils import *
from spark_utils import *


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
        self.assertTrue(run_example_marathon_app(self.work_dir))


    def test_spark(self):
        self.assertTrue(run_example_spark_job(self.work_dir))


class SSL_Test(unittest.TestCase):
    """Tests stuff with SSL enabled, without downgrade."""

    @classmethod
    def setUpClass(cls):
        cls.work_dir = tempfile.mkdtemp(prefix='mesos-integration-')

        # Setup SSL things.
        ssl_utils.generate_ssl_stuff(cls.work_dir)
        os.environ['SSL_ENABLED'] = 'true'
        os.environ['SSL_KEY_FILE'] = os.path.join(cls.work_dir, SSL_KEY_FILE)
        os.environ['SSL_CERT_FILE'] = os.path.join(cls.work_dir, SSL_CHAIN_FILE)

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


    def test_chronos(self):
        start_chronos(self.work_dir, is_ssl=True,
                       flags=['--ssl_keystore_path', os.path.join(self.work_dir, SSL_MARATHON_KEYSTORE),
                              '--ssl_keystore_password', SUPER_SECURE_PASSPHRASE])
        self.assertTrue(wait_for_chronos(self.work_dir, is_ssl=True), 'Chronos failed to start in time.')


    def test_marathon(self):
        start_marathon(self.work_dir, is_ssl=True,
                       flags=['--ssl_keystore_path', os.path.join(self.work_dir, SSL_MARATHON_KEYSTORE),
                              '--ssl_keystore_password', SUPER_SECURE_PASSPHRASE])
        self.assertTrue(wait_for_marathon(self.work_dir, is_ssl=True), 'Marathon failed to start in time.')
        self.assertTrue(run_example_marathon_app(self.work_dir, is_ssl=True))


    def test_spark(self):
        self.assertTrue(run_example_spark_job(self.work_dir))


if __name__ == '__main__':
    # Check that `openssl` is available.
    call(['openssl', 'version'])

    # Check that ZooKeeper is available.
    call(['zkserver', 'print-cmd'])

    for var in [MESOS_BIN_PATH, PATH_TO_MARATHON, PATH_TO_CHRONOS, PATH_TO_SPARK]:
        if var not in os.environ:
            print 'Environment variable "%s" not set.' % var
            exit(1)

    atexit.register(cleanup)
    unittest.main()
