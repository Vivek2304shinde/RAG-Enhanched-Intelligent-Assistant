import ssl
import socket

hostname = "e4bb0e99.databases.neo4j.io"

ctx = ssl._create_unverified_context()

with socket.create_connection((hostname, 7687), timeout=10) as sock:
    with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
        print("CONNECTED")
        print(ssock.version())
        print(ssock.getpeercert())

import ssl
import socket

hostname = "e4bb0e99.databases.neo4j.io"

ctx = ssl._create_unverified_context()

with socket.create_connection((hostname, 7687)) as sock:
    with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
        cert = ssock.getpeercert(binary_form=True)

print(len(cert))

from cryptography import x509
from cryptography.hazmat.backends import default_backend

cert_obj = x509.load_der_x509_certificate(
    cert,
    default_backend()
)

print(cert_obj.subject)
print(cert_obj.issuer)

import ssl
print(ssl.get_default_verify_paths())

import certifi
import ssl

ctx = ssl.create_default_context(cafile=certifi.where())

print(certifi.where())

import ssl
import socket
import certifi

hostname = "e4bb0e99.databases.neo4j.io"

ctx = ssl.create_default_context(
    cafile=certifi.where()
)

with socket.create_connection((hostname, 7687), timeout=10) as sock:
    with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
        print("SUCCESS")
        print(ssock.version())

import ssl
import certifi
from neo4j import GraphDatabase

ssl_context = ssl.create_default_context(
    cafile=certifi.where()
)

driver = GraphDatabase.driver(
    "neo4j+s://e4bb0e99.databases.neo4j.io",
    auth=(
        "e4bb0e99",
        "YOUR_PASSWORD"
    ),
    ssl_context=ssl_context
)

with driver.session(database="neo4j") as session:
    result = session.run("RETURN 1 AS x")
    print(result.single())

driver.close()