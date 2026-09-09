from tva_validation.countries import se

# Vérifié indépendamment : "1234567897" passe l'algorithme de Luhn.
NUMERO_VALIDE = "123456789701"


def test_numero_valide():
    resultat = se.valider(NUMERO_VALIDE, "SE")
    assert resultat.conforme
    assert resultat.numero_normalise == "SE" + NUMERO_VALIDE


def test_cle_de_controle_invalide():
    casse = "123456789601"  # dernier chiffre de l'organisationsnummer modifié
    resultat = se.valider(casse, "SE")
    assert not resultat.conforme
    assert resultat.motif.value == "cle_controle_invalide"


def test_suffixe_incorrect():
    casse = "123456789799"  # suffixe "99" au lieu de "01"
    resultat = se.valider(casse, "SE")
    assert not resultat.conforme
    assert resultat.motif.value == "format_invalide"


def test_longueur_invalide():
    resultat = se.valider("123", "SE")
    assert resultat.motif.value == "longueur_invalide"
