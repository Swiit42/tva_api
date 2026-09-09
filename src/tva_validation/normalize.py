"""Nettoyage des numéros de TVA tels qu'ils arrivent du référentiel brut.

Cette étape ne juge PAS la validité du numéro : elle retire uniquement le
bruit de saisie (espaces, tirets, points, casse) pour que les étapes
suivantes (dédoublonnage, dispatch par pays, validation structurelle)
travaillent sur une forme unique et comparable. C'est la première étape du
pipeline : normaliser -> dédupliquer -> filtrer sur la structure -> VIES.
"""

from __future__ import annotations

# Valeurs observées dans le CSV qui ne représentent aucune tentative de
# numéro (chaîne vide, tiret seul, placeholders textuels). À distinguer
# d'un numéro mal formé, qui lui doit être normalisé PUIS rejeté avec un
# motif structurel explicite (ce n'est pas la responsabilité de ce module).
VALEURS_VIDES = frozenset({"", "-", "N/A", "NA", "NULL", "NONE", "NAN", "#N/A"})


def normaliser_numero_tva(valeur_brute: str | None) -> str | None:
    """Nettoie un numéro de TVA brut, renvoie None si c'est une valeur vide.

    Étapes : suppression des espaces en tête/fin, mise en majuscule, puis
    suppression des espaces internes, tirets et points (bruit de saisie
    identifié sur l'échantillon : "SE.751298146001", "DK 7170 4289", ...).
    """
    if valeur_brute is None:
        return None

    nettoye = valeur_brute.strip().upper()
    if nettoye in VALEURS_VIDES:
        return None

    nettoye = nettoye.replace(" ", "").replace("-", "").replace(".", "")

    # Un placeholder avec du bruit interne ("N / A") ne matche le filtre
    # ci-dessus qu'après cette seconde passe de nettoyage.
    if nettoye in VALEURS_VIDES:
        return None

    return nettoye
