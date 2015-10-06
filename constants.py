
MESOS_BIN_PATH   = 'MESOS_BIN_PATH'
PATH_TO_MARATHON = 'PATH_TO_MARATHON'
PATH_TO_CHRONOS  = 'PATH_TO_CHRONOS'

SUPER_SECURE_PASSPHRASE     = 'passphrase'
SSL_SUPER_SECURE_PASSPHRASE = 'pass:%s' % SUPER_SECURE_PASSPHRASE
SSL_CONFIG_FILE             = 'config.txt'
SSL_KEY_FILE                = 'key.pem'
SSL_CERT_FILE               = 'cert.pem'
SSL_TRUSTED_AUTHORITY       = 'trustedCA.crt'
SSL_MARATHON_PKCS           = 'marathon.pkcs12'
SSL_MARATHON_KEYSTORE       = 'marathon.jks'

MESOS_MASTER_BIN = 'mesos-master.sh'
MESOS_AGENT_BIN  = 'mesos-slave.sh'
MARATHON_BIN     = 'start'

MESOS_MASTER_IP   = '127.0.0.1'
MESOS_MASTER_CIDR = '%s:5050' % MESOS_MASTER_IP
