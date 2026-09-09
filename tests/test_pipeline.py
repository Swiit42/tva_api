from tva_validation.pipeline import traiter_ligne


def test_valeur_absente_pas_de_cle_dedup():
    ligne = traiter_ligne("FR", "N/A")
    assert ligne.numero_tva_normalise is None
    assert ligne.conforme_structurel is False
    assert ligne.motif_structurel == "valeur_absente"
    assert ligne.cle_dedup is None


def test_numero_conforme():
    ligne = traiter_ligne("BE", "BE 1234567894")  # avec bruit de saisie
    assert ligne.numero_tva_normalise == "BE1234567894"
    assert ligne.conforme_structurel is True
    assert ligne.motif_structurel is None
    assert ligne.cle_dedup == "BE:BE1234567894"


def test_meme_cle_dedup_avec_ou_sans_prefixe():
    avec_prefixe = traiter_ligne("BE", "BE1234567894")
    sans_prefixe = traiter_ligne("BE", "1234567894")
    assert avec_prefixe.cle_dedup == sans_prefixe.cle_dedup


def test_pays_hors_perimetre():
    ligne = traiter_ligne("GB", "GB0749640348")
    assert ligne.conforme_structurel is False
    assert ligne.motif_structurel == "pays_hors_perimetre"


def test_cle_controle_invalide():
    ligne = traiter_ligne("BE", "BE1234567800")  # clé cassée (00 != 94)
    assert ligne.conforme_structurel is False
    assert ligne.motif_structurel == "cle_controle_invalide"
