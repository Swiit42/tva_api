from tva_validation.countries import dk

# Vérifié indépendamment : somme pondérée (poids 2,7,6,5,4,3,2,1) = 110,
# 110 % 11 == 0.
NUMERO_VALIDE = "12345674"


def test_numero_valide():
    resultat = dk.valider(NUMERO_VALIDE, "DK")
    assert resultat.conforme
    assert resultat.numero_normalise == "DK" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = NUMERO_VALIDE[:7] + "0"  # brise la somme pondérée
    resultat = dk.valider(casse, "DK")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_longueur_invalide():
    resultat = dk.valider("123", "DK")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = dk.valider("1234567A", "DK")
    assert resultat.motif.value == "format_invalide"
