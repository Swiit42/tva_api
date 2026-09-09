from tva_validation.countries import it

# Vérifié indépendamment : Luhn (variante italienne) sur "1234567123"
# donne une clé de 9.
NUMERO_VALIDE = "12345671239"


def test_numero_valide():
    resultat = it.valider(NUMERO_VALIDE, "IT")
    assert resultat.conforme
    assert resultat.numero_normalise == "IT" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = NUMERO_VALIDE[:10] + "0"  # 0 != 9
    resultat = it.valider(casse, "IT")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_longueur_invalide():
    resultat = it.valider("123", "IT")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = it.valider("1234567123A", "IT")
    assert resultat.motif.value == "format_invalide"
