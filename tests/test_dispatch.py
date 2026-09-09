from tva_validation.countries import PAYS_COUVERTS, valider_par_pays

NUMERO_BE_VALIDE = "BE1234567894"


def test_pays_hors_perimetre():
    for pays in ["ZZ", "QQ", "XX", "GB", "UK"]:
        assert pays not in PAYS_COUVERTS
        resultat = valider_par_pays(pays, "PEU IMPORTE")
        assert not resultat.conforme
        assert resultat.motif.value == "pays_hors_perimetre"


def test_prefixe_absent_accepte_avec_pays_declare():
    # cas observé sur l'échantillon : numéro saisi sans son préfixe pays
    resultat = valider_par_pays("BE", "1234567894")
    assert resultat.conforme
    assert resultat.numero_normalise == NUMERO_BE_VALIDE


def test_prefixe_coherent():
    resultat = valider_par_pays("BE", NUMERO_BE_VALIDE)
    assert resultat.conforme
    assert resultat.numero_normalise == NUMERO_BE_VALIDE


def test_prefixe_incoherent():
    resultat = valider_par_pays("FR", NUMERO_BE_VALIDE)  # préfixe BE, pays declare FR
    assert not resultat.conforme
    assert resultat.motif.value == "prefixe_incoherent"


def test_dix_pays_couverts():
    assert PAYS_COUVERTS == {"BE", "DK", "FI", "FR", "IT", "LU", "NL", "PL", "PT", "SE"}
