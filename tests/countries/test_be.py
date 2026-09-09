from tva_validation.countries import be

# Vérifié indépendamment : 8 premiers = 12345678, clé = 97 - (12345678 % 97) = 94
NUMERO_VALIDE = "1234567894"


def test_numero_valide():
    resultat = be.valider(NUMERO_VALIDE, "BE")
    assert resultat.conforme
    assert resultat.numero_normalise == "BE" + NUMERO_VALIDE
    assert resultat.motif is None


def test_cle_de_controle_invalide():
    casse = NUMERO_VALIDE[:8] + "00"  # 00 != 94
    resultat = be.valider(casse, "BE")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_longueur_invalide():
    resultat = be.valider("123", "BE")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = be.valider("1234567A94", "BE")
    assert resultat.motif.value == "format_invalide"
