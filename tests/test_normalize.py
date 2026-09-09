from tva_validation.normalize import normaliser_numero_tva


def test_supprime_espaces_tirets_points():
    assert normaliser_numero_tva("SE.751298146001") == "SE751298146001"
    assert normaliser_numero_tva("DK 7170 4289") == "DK71704289"
    assert normaliser_numero_tva(" LU71043234 ") == "LU71043234"


def test_met_en_majuscule():
    assert normaliser_numero_tva("uk26062918") == "UK26062918"


def test_valeurs_vides_reconnues():
    for brut in ["", "   ", "-", "N/A", "n/a", "null", "NULL", "None", "#N/A"]:
        assert normaliser_numero_tva(brut) is None


def test_placeholder_avec_bruit_interne():
    # deux passes de nettoyage : la premiere ne matche pas "N / A" tel
    # quel, la seconde (apres suppression des espaces) si.
    assert normaliser_numero_tva("N / A") is None


def test_numero_valide_inchange_dans_le_fond():
    assert normaliser_numero_tva("FR32123456789") == "FR32123456789"
