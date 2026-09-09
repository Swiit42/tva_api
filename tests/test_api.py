"""Tests de l'API limités au chemin structurel (aucun accès réseau ni
base de données requis : un numéro non conforme structurellement ne
touche jamais VIES ni PostgreSQL, cf. api.py). Le chemin "conforme"
(cache / appel VIES réel) est démontré manuellement en Phase 2 plutôt que
testé ici, pour ne pas rendre la suite pytest dépendante du réseau ou
d'une base démarrée.
"""

from fastapi.testclient import TestClient

from tva_validation.api import app

client = TestClient(app)


def test_pays_hors_perimetre():
    reponse = client.get("/verification-tva/GB/0749640348")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["verdict"] == "invalide"
    assert corps["origine"] == "structurel"
    assert corps["motif"] == "pays_hors_perimetre"


def test_valeur_absente():
    reponse = client.get("/verification-tva/FR/-")
    corps = reponse.json()
    assert corps["verdict"] == "invalide"
    assert corps["origine"] == "structurel"
    assert corps["motif"] == "valeur_absente"


def test_cle_de_controle_invalide():
    reponse = client.get("/verification-tva/BE/BE1234567800")  # 00 != 94
    corps = reponse.json()
    assert corps["verdict"] == "invalide"
    assert corps["origine"] == "structurel"
    assert corps["motif"] == "cle_controle_invalide"


def test_reponse_contient_toujours_verdict_origine_fraicheur():
    reponse = client.get("/verification-tva/ZZ/PEU-IMPORTE")
    corps = reponse.json()
    assert set(["verdict", "origine", "fraicheur"]).issubset(corps.keys())
