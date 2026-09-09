from tva_validation.countries import fr

# Vérifié indépendamment : SIREN 123456789 mod 97 = 39,
# clé = (12 + 3*39) mod 97 = 32.
NUMERO_VALIDE = "32123456789"


def test_numero_valide():
    resultat = fr.valider(NUMERO_VALIDE, "FR")
    assert resultat.conforme
    assert resultat.numero_normalise == "FR" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = "00" + NUMERO_VALIDE[2:]  # 00 != 32
    resultat = fr.valider(casse, "FR")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_longueur_invalide():
    resultat = fr.valider("123", "FR")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = fr.valider("3212345678A", "FR")
    assert resultat.motif.value == "format_invalide"
