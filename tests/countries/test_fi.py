from tva_validation.countries import fi

# Vérifié indépendamment : poids (7,9,10,5,8,4,2) sur "1234567" -> somme
# 153, reste 153%11=10, clé attendue = 11-10 = 1.
NUMERO_VALIDE = "12345671"

# "1111111" -> somme = 45, reste = 45%11 = 1 : reste "impossible" (aucune
# clé ne peut satisfaire la formule), quel que soit le dernier chiffre.
NUMERO_CLE_IMPOSSIBLE = "11111110"


def test_numero_valide():
    resultat = fi.valider(NUMERO_VALIDE, "FI")
    assert resultat.conforme
    assert resultat.numero_normalise == "FI" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = NUMERO_VALIDE[:7] + "9"  # 9 != 1
    resultat = fi.valider(casse, "FI")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_cle_de_controle_impossible():
    resultat = fi.valider(NUMERO_CLE_IMPOSSIBLE, "FI")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_impossible"


def test_longueur_invalide():
    resultat = fi.valider("123", "FI")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = fi.valider("1234567A", "FI")
    assert resultat.motif.value == "format_invalide"
