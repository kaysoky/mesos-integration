import json
import os
import subprocess
import time

from constants import *


def mesos_path():
    """Returns the MESOS_BIN_PATH environment variable."""
    return os.environ.get(MESOS_BIN_PATH)


def marathon_path():
    """Returns the PATH_TO_MARATHON environment variable."""
    return os.environ.get(PATH_TO_MARATHON)


def chronos_jar():
    """Returns the PATH_TO_CHRONOS environment variable."""
    return os.environ.get(PATH_TO_CHRONOS)


def spark_path():
    """Returns the PATH_TO_SPARK environment variable."""
    return os.environ.get(PATH_TO_SPARK)


def call(command):
    """
    Blocks on subprocess.Popen until the command finishes.
    Returns the stdout and stderr.  Suppresses console output.
    """
    return subprocess.Popen(command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()


def curl_ssl(work_dir):
    """Returns an incomplete curl command string with SSL flags."""
    # TODO: Get rid of this `--insecure` flag.
    return ['curl', '--tlsv1.2', '--insecure']
    # '--cacert', os.path.join(work_dir, SSL_CERT_FILE)


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


def generate_ssl_stuff(work_dir):
    """Generates the required SSL files."""
    # TODO: I think I'm doing this incorrectly.

    # Generate a private key and certificate.
    call([
        'openssl', 'req', '-nodes', '-new', '-x509',
        '-batch', '-days', '365',
        '-subj', '/CN=127.0.0.1/CN=localhost',
        '-keyout', os.path.join(work_dir, SSL_KEY_FILE),
        '-out', os.path.join(work_dir, SSL_CERT_FILE)])

    '''
    These are the calls with passphrase.
    Currently, the passphrase can't be supplied to the master trivially.

    subprocess.Popen([
        'openssl', 'genrsa', '-des3', '-f4',
        '-passout', SSL_SUPER_SECURE_PASSPHRASE,
        '-out', os.path.join(work_dir, SSL_KEY_FILE),
        '4096'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()

    subprocess.Popen([
        'openssl', 'req', '-new', '-x509',
        '-passin', SSL_SUPER_SECURE_PASSPHRASE,
        '-batch', '-days', '365',
        '-subj', '/CN=127.0.0.1/CN=localhost',
        '-key', os.path.join(work_dir, SSL_KEY_FILE),
        '-out', os.path.join(work_dir, SSL_CERT_FILE)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    '''

    # Generate a Java keystore, for Marathon.
    call([
        'openssl', 'pkcs12',
        '-inkey', os.path.join(work_dir, SSL_KEY_FILE),
        '-name', 'marathon',
        '-in', os.path.join(work_dir, SSL_CERT_FILE),
        '-password', SSL_SUPER_SECURE_PASSPHRASE,
        # '-chain', '-CAFile', os.path.join(work_dir, SSL_TRUSTED_AUTHORITY),
        '-export', '-out', os.path.join(work_dir, SSL_MARATHON_PKCS)])

    call([
        'keytool', '-importkeystore',
        '-srckeystore', os.path.join(work_dir, SSL_MARATHON_PKCS),
        '-srcalias', 'marathon',
        '-srcstorepass', SUPER_SECURE_PASSPHRASE,
        '-srcstoretype', 'PKCS12',
        '-destkeystore', os.path.join(work_dir, SSL_MARATHON_KEYSTORE),
        '-deststorepass', SUPER_SECURE_PASSPHRASE])


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
        '--work_dir=%s' % work_dir] + flags,
        stdout=stdout,
        stderr=stderr)

    assert master.returncode is None

    register_exit(lambda: master.kill())


def wait_for_master(work_dir, timeout=5, is_ssl=False):
    """Waits for a Master to start."""
    while timeout:
        try:
            output, _ = call(curl_ssl(work_dir) + ['-I',
                'http%s://%s/master/state.json' % ('s' if is_ssl else '', MESOS_MASTER_CIDR)])
            if '200 OK' in output:
                break
        except subprocess.CalledProcessError as e:
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

    agent = subprocess.Popen([
        os.path.join(mesos_path(), MESOS_AGENT_BIN),
        '--master=%s' % MESOS_MASTER_CIDR,
        '--work_dir=%s' % work_dir] + flags,
        stdout=stdout,
        stderr=stderr)

    assert agent.returncode is None

    register_exit(lambda: call(['rm', '-rf', '/tmp/mesos/meta/slaves/latest']))
    register_exit(lambda: agent.kill())


def wait_for_agent(work_dir, num_agents=1, timeout=7, is_ssl=False):
    """Waits for an Agent to start."""
    while timeout:
        try:
            result, _ = call(curl_ssl(work_dir) + ['http%s://%s/master/state.json' % ('s' if is_ssl else '', MESOS_MASTER_CIDR)])
            result = json.loads(result)
            if len(result['slaves']) == num_agents and all(map(lambda x: x['active'], result['slaves'])):
                break
        except subprocess.CalledProcessError as e:
            pass

        time.sleep(1)
        timeout -= 1

    return timeout > 0


def start_zookeeper():
    """Starts ZooKeeper."""
    call(['zkserver', 'start'])
    register_exit(lambda: call(['rm', '-rf', '/usr/local/var/run/zookeeper/data']))
    register_exit(lambda: call(['zkserver', 'stop']))


def check_framework_in_state_json(work_dir, framework, is_ssl=False):
    """Checks master's state.json for the given framework."""
    result, _ = call(curl_ssl(work_dir) + ['http%s://localhost:5050/master/state.json' % ('s' if is_ssl else '')])
    result = json.loads(result)['frameworks']
    result = filter(lambda x: x['name'] == framework, result)
    if len(result) == 1 and result[0]['active']:
        return True

    return False


def start_marathon(work_dir, is_ssl=False, flags=[]):
    """Starts Marathon."""
    print 'Starting Marathon'
    stdout = open(os.path.join(work_dir, 'm_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'm_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    marathon = subprocess.Popen([
        os.path.join(marathon_path(), MARATHON_BIN),
        '--http%s_port' % ('s' if is_ssl else ''), '8444' if is_ssl else '8081',
        '--master', MESOS_MASTER_CIDR,
        '--zk', 'zk://localhost:2181/marathon'] + flags,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: marathon.kill())


def wait_for_marathon(work_dir, timeout=25, is_ssl=False):
    """Waits for the Marathon UI to show up."""
    while timeout:
        try:
            # Note: Some versions of Python (on OSX) do not have TLSv1.2 support.
            # So we need to use curl to talk via HTTPS.
            output, _ = call([
                'curl', '-I', '--tlsv1.2',
                '--cacert', os.path.join(work_dir, SSL_CERT_FILE),
                'http%s://localhost:%d/ping' % ('s' if is_ssl else '', 8444 if is_ssl else 8081)])
            if '200 OK' in output:
                break
        except subprocess.CalledProcessError as e:
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
    call([
        'curl', '--tlsv1.2', '-m', '2',
        '--cacert', os.path.join(work_dir, SSL_CERT_FILE),
        '-X', 'POST',
        'http%s://localhost:%d/v2/apps' % ('s' if is_ssl else '', 8444 if is_ssl else 8081),
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(app_def)])

    # Wait for it.
    while timeout:
        result, _ = call([
            'curl', '--tlsv1.2', '-m', '2',
            '--cacert', os.path.join(work_dir, SSL_CERT_FILE),
            'http%s://localhost:%d/v2/apps/basic-0/tasks' % ('s' if is_ssl else '', 8444 if is_ssl else 8081)])

        result = json.loads(result)
        if len(result['tasks']) == 1 and result['tasks'][0]['appId'] == '/basic-0':
            return True

        time.sleep(1)
        timeout -= 1

    return False


def start_chronos(work_dir, flags=[], is_ssl=False):
    """Starts Chronos."""
    print 'Starting Chronos'
    stdout = open(os.path.join(work_dir, 'c_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 'c_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    chronos = subprocess.Popen([
        'java', '-cp', chronos_jar(),
        'org.apache.mesos.chronos.scheduler.Main',
        '--mesos_framework_name', 'chronos',
        '--hostname', 'localhost',
        '--http_address', 'localhost',
        '--master', MESOS_MASTER_CIDR,
        '--zk_hosts', 'localhost:2181'] + flags,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: chronos.kill())


def wait_for_chronos(work_dir, timeout=15, is_ssl=False):
    """Waits for the Chronos to start up."""
    while timeout:
        try:
            # Note: Some versions of Python (on OSX) do not have TLSv1.2 support.
            # So we need to use curl to talk via HTTPS.
            output, _ = call([
                'curl', '-I', '--tlsv1.2', '-m', '2',
                '--cacert', os.path.join(work_dir, SSL_CERT_FILE),
                'http%s://localhost:%d/scheduler/jobs' % ('s' if is_ssl else '', 8443 if is_ssl else 8080)])
            if '200 OK' in output:
                break
        except subprocess.CalledProcessError as e:
            pass

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    return check_framework_in_state_json(work_dir, 'chronos', is_ssl)


def run_example_spark_job(work_dir, timeout=25):
    """Runs a Spark job and checks the result."""
    print 'Starting Spark job'
    stdout = open(os.path.join(work_dir, 's_stdout.txt'), 'w')
    stderr = open(os.path.join(work_dir, 's_stderr.txt'), 'w')
    register_exit(lambda: stdout.close())
    register_exit(lambda: stderr.close())

    spark = subprocess.Popen([
        os.path.join(spark_path(), 'bin/spark-submit'),
        '--master', 'mesos://%s' % MESOS_MASTER_CIDR,
        os.path.join(spark_path(), 'examples/src/main/python/pi.py'), '5'],
        stdin=None,
        stdout=stdout,
        stderr=stderr)
    register_exit(lambda: spark.kill() if spark.poll() is None else '')

    while timeout:
        if spark.poll() is not None:
            break

        time.sleep(1)
        timeout -= 1

    if timeout <= 0:
        return False

    with open(os.path.join(work_dir, 's_stdout.txt'), 'r') as f:
        result = f.read()
        return 'Pi is roughly 3' in result
