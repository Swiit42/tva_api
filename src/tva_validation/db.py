"""Connexion PostgreSQL partagée par les scripts (chargement, rapport) et,
plus tard, par l'API.

On lit DATABASE_URL dans l'environnement (chargé depuis un fichier .env
si présent) plutôt que de coder l'hôte/port en dur, pour que le même code
fonctionne que la base tourne dans le docker-compose fourni ou ailleurs.
"""

from __future__ import annotations

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://meridian:meridian@localhost:5435/tva"
)


def get_connection():
    return psycopg2.connect(DATABASE_URL)
