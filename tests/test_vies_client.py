from tva_validation.vies_client import interpreter_reponse_vies

# Fixtures capturées lors des tests manuels de la Phase 2 (appels réels à
# l'endpoint VIES le 2026-09-09).

REPONSE_VALIDE = {
    "isValid": True,
    "requestDate": "2026-09-09T10:19:50.704Z",
    "userError": "VALID",
    "name": "EDP, S.A.",
    "address": "AV 24 DE JULHO N 12\nLISBOA\n1249-300 LISBOA",
    "originalVatNumber": "500697256",
    "vatNumber": "500697256",
}

REPONSE_CLE_FAUSSE = {
    "isValid": False,
    "userError": "INVALID",
    "name": "---",
    "address": "---",
    "originalVatNumber": "500697257",
    "vatNumber": "500697257",
}

REPONSE_INVENTE_NON_TROUVE = {
    "isValid": False,
    "userError": "INVALID",
    "name": "",
    "address": "",
    "originalVatNumber": "123456789",
    "vatNumber": "123456789",
}

REPONSE_ADMINISTRATION_SURCHARGEE = {
    "isValid": False,
    "userError": "MS_MAX_CONCURRENT_REQ",
    "name": "---",
    "address": "---",
    "originalVatNumber": "27552032534",
    "vatNumber": "27552032534",
}


def test_numero_valide():
    resultat = interpreter_reponse_vies(REPONSE_VALIDE)
    assert resultat.verdict == "valide"
    assert resultat.nom == "EDP, S.A."


def test_cle_fausse_est_invalide():
    resultat = interpreter_reponse_vies(REPONSE_CLE_FAUSSE)
    assert resultat.verdict == "invalide"


def test_invente_non_trouve_est_invalide():
    resultat = interpreter_reponse_vies(REPONSE_INVENTE_NON_TROUVE)
    assert resultat.verdict == "invalide"


def test_administration_surchargee_est_indetermine_pas_invalide():
    # Le cœur du sujet : isValid=false ne veut PAS dire invalide ici.
    resultat = interpreter_reponse_vies(REPONSE_ADMINISTRATION_SURCHARGEE)
    assert resultat.verdict == "indetermine"
    assert resultat.user_error_vies == "MS_MAX_CONCURRENT_REQ"


def test_reponse_inattendue_est_indetermine():
    resultat = interpreter_reponse_vies({"isValid": False, "userError": "TIMEOUT"})
    assert resultat.verdict == "indetermine"
