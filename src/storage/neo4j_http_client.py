import requests

from src.config import settings


class Neo4jHTTPClient:

    def __init__(self):

        host = settings.neo4j_uri.replace(
            "neo4j+s://",
            ""
        )

        database = settings.neo4j_database or "neo4j"

        self.url = (
            f"https://{host}"
            f"/db/{database}/query/v2"
        )

        self.auth = (
            settings.neo4j_user,
            settings.neo4j_password
        )

    def run_cypher(self, query, params=None):

        payload = {
            "statement": query,
            "parameters": params or {}
        }

        r = requests.post(
            self.url,
            auth=self.auth,
            json=payload,
            timeout=60
        )

        r.raise_for_status()

        return r.json()


neo4j_http_client = Neo4jHTTPClient()