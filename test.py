from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

response = client.responses.create(
    model="openai/gpt-oss-20b",
    input="Hello!"
)

print(response.output_text)

import ssl
print(ssl.OPENSSL_VERSION)

import certifi
print(certifi.where())

import requests

r = requests.get("https://e4bb0e99.databases.neo4j.io")
print(r.status_code)