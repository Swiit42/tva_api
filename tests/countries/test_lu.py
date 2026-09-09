from tva_validation.countries import lu

# Vérifié indépendamment : 123456 mod 89 = 13.
NUMERO_VALIDE = "12345613"


def test_numero_valide():
    resultat = lu.valider(NUMERO_VALIDE, "LU")
    assert resultat.conforme
    assert resultat.numero_normalise == "LU" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = NUMERO_VALIDE[:6] + "00"  # 00 != 13
    resultat = lu.valider(casse, "LU")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_longueur_invalide():
    resultat = lu.valider("123", "LU")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = lu.valider("12345A13", "LU")
    assert resultat.motif.value == "format_invalide"
