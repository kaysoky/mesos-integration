import os

from constants import *
from utils import *

"""
A root Certificate Authority configuration file.
Base on https://jamielinux.com/docs/openssl-certificate-authority/appendix/root-configuration-file.html
"""
template = """
[ ca ]
default_ca = CA_default

[ CA_default ]
dir              = {working_dir}/root/ca
certs            = $dir/certs         # Where the issued certs are kept
crl_dir          = $dir/crl           # Where the issued crl are kept
new_certs_dir    = $dir/newcerts      # Default place for new certs
database         = $dir/index.txt     # Database index file
serial           = $dir/serial        # The current serial number
RANDFILE         = $dir/private/.rand # private random number file

# Root key and certificate
private_key      = $dir/private/ca.key.pem
certificate      = $dir/certs/ca.cert.pem

# Certificate Revocation Lists
crlnumber        = $dir/crlnumber
crl              = $dir/crl/ca.crl.pem
crl_extensions   = crl_ext
default_crl_days = 30

# Use public key default MD
default_md      = default

name_opt        = ca_default    # Subject Name options
cert_opt        = ca_default    # Certificate field options
default_days    = 365           # How long to certify for
preserve        = no            # keep passed DN ordering
policy          = policy_strict # How similar each request should look

[ policy_loose ]
countryName            = optional
stateOrProvinceName    = optional
localityName           = optional
organizationName       = optional
organizationalUnitName = optional
commonName             = supplied
emailAddress           = optional

[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
string_mask        = utf8only
default_md         = default
x509_extensions    = v3_ca # For self-signed (x509) certs

# Passwords for private keys
# input_password  = secret
# output_password = secret

[ req_distinguished_name ]
countryName_default         = US
stateOrProvinceName_default = CA
localityName_default        = SF
0.organizationName_default  = Mesosphere

[ v3_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical, CA:true
keyUsage               = critical, digitalSignature, cRLSign, keyCertSign

[ v3_intermediate_ca ]
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints       = critical, CA:true, pathlen:0
keyUsage               = critical, digitalSignature, cRLSign, keyCertSign

[ usr_cert ]
basicConstraints       = CA:FALSE
nsCertType             = client, email
nsComment              = "OpenSSL Generated Client Certificate"
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer
keyUsage               = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage       = clientAuth, emailProtection

[ server_cert ]
basicConstraints       = CA:FALSE
nsCertType             = server
nsComment              = "OpenSSL Generated Server Certificate"
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage               = critical, digitalSignature, keyEncipherment
extendedKeyUsage       = serverAuth

[ crl_ext ]
authorityKeyIdentifier = keyid:always

[ ocsp ]
basicConstraints       = CA:FALSE
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer
keyUsage               = critical, digitalSignature
extendedKeyUsage       = critical, OCSPSigning
"""


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
