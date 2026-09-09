from tva_validation.countries import pt

# Vérifié indépendamment : poids (9,8,7,6,5,4,3,2) sur "12345678" -> somme
# 156, reste 156%11=2 -> clé attendue = 11-2 = 9.
NUMERO_VALIDE = "123456789"


def test_numero_valide():
    resultat = pt.valider(NUMERO_VALIDE, "PT")
    assert resultat.conforme
    assert resultat.numero_normalise == "PT" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = NUMERO_VALIDE[:8] + "0"  # 0 != 9
    resultat = pt.valider(casse, "PT")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_longueur_invalide():
    resultat = pt.valider("123", "PT")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = pt.valider("1234567A9", "PT")
    assert resultat.motif.value == "format_invalide"
