
MESOS_BIN_PATH   = 'MESOS_BIN_PATH'
PATH_TO_MARATHON = 'PATH_TO_MARATHON'
PATH_TO_CHRONOS  = 'PATH_TO_CHRONOS'
PATH_TO_SPARK    = 'PATH_TO_SPARK'


SSL_ROOT_CA_DIR    = 'root/ca'
SSL_INDEX_FILE     = SSL_ROOT_CA_DIR + '/index.txt'
SSL_SERIAL_FILE    = SSL_ROOT_CA_DIR + '/serial'
SSL_CRL_FILE       = SSL_ROOT_CA_DIR + '/crlnumber'

SSL_CERT_DIR       = SSL_ROOT_CA_DIR + '/certs'
SSL_CRL_DIR        = SSL_ROOT_CA_DIR + '/crl'
SSL_CSR_DIR        = SSL_ROOT_CA_DIR + '/csr'
SSL_NEWCERTS_DIR   = SSL_ROOT_CA_DIR + '/newcerts'
SSL_PRIVATE_DIR    = SSL_ROOT_CA_DIR + '/private'

SSL_ROOT_KEY_FILE  = SSL_PRIVATE_DIR + '/ca.key.pem'
SSL_ROOT_CERT_FILE = SSL_CERT_DIR + '/ca.cert.pem'
SSL_CSR_FILE       = SSL_CSR_DIR + '/csr.pem'
SSL_CERT_FILE      = SSL_CERT_DIR + '/cert.pem'
SSL_CHAIN_FILE     = SSL_CERT_DIR + '/ca-chain.cert.pem'

SUPER_SECURE_PASSPHRASE     = 'passphrase'
SSL_SUPER_SECURE_PASSPHRASE = 'pass:%s' % SUPER_SECURE_PASSPHRASE
SSL_CONFIG_FILE             = 'openssl.cnf'
SSL_KEY_FILE                = 'key.pem'
SSL_MARATHON_PKCS           = 'marathon.pkcs12'
SSL_MARATHON_KEYSTORE       = 'marathon.jks'

MESOS_MASTER_BIN = 'mesos-master.sh'
MESOS_AGENT_BIN  = 'mesos-slave.sh'
MARATHON_BIN     = 'start'

MESOS_MASTER_IP   = '127.0.0.1'
MESOS_MASTER_CIDR = '%s:5050' % MESOS_MASTER_IP
