from tva_validation.countries import nl

# Vérifié indépendamment : poids (9,8,7,6,5,4,3,2) sur "12345678" -> somme
# 156, 156 % 11 = 2 -> 9e chiffre attendu = 2.
NUMERO_VALIDE = "123456782B01"

# "00000005" -> somme % 11 == 10 : reste "impossible", quel que soit le
# 9e chiffre choisi.
NUMERO_CLE_IMPOSSIBLE = "000000050B01"


def test_numero_valide():
    resultat = nl.valider(NUMERO_VALIDE, "NL")
    assert resultat.conforme
    assert resultat.numero_normalise == "NL" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = "123456780B01"  # 0 != 2
    resultat = nl.valider(casse, "NL")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_cle_de_controle_impossible():
    resultat = nl.valider(NUMERO_CLE_IMPOSSIBLE, "NL")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_impossible"


def test_longueur_invalide():
    resultat = nl.valider("123", "NL")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide_sans_b():
    resultat = nl.valider("123456782X01", "NL")
    assert resultat.motif.value == "format_invalide"
