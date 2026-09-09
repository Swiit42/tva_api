from tva_validation.countries import pl

# Exemple officiel (biznes.gov.pl) : NIP 2073786728 -> somme pondérée 206,
# 206 % 11 = 8, qui est bien le 10e chiffre.
NUMERO_VALIDE = "2073786728"

# "000000003" -> somme % 11 == 10 : reste "impossible".
NUMERO_CLE_IMPOSSIBLE = "0000000030"


def test_numero_valide():
    resultat = pl.valider(NUMERO_VALIDE, "PL")
    assert resultat.conforme
    assert resultat.numero_normalise == "PL" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = NUMERO_VALIDE[:9] + "0"  # 0 != 8
    resultat = pl.valider(casse, "PL")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_cle_de_controle_impossible():
    resultat = pl.valider(NUMERO_CLE_IMPOSSIBLE, "PL")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_impossible"


def test_longueur_invalide():
    resultat = pl.valider("123", "PL")
    assert resultat.motif.value == "longueur_invalide"


def test_format_invalide():
    resultat = pl.valider("20737867A8", "PL")
    assert resultat.motif.value == "format_invalide"
