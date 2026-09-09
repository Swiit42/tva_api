"""Dispatch d'un numéro déjà normalisé vers le validateur de son pays.

C'est ici que se fait le "tri en fonction du pays" prévu par le brief,
juste après la normalisation générique (`normalize.py`) et avant toute
validation spécifique à un pays (longueur, format, clé de contrôle).
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation
from . import be, dk, fi, fr, it, lu, nl, pl, pt, se

_VALIDATEURS = {
    "BE": be.valider,
    "DK": dk.valider,
    "FI": fi.valider,
    "FR": fr.valider,
    "IT": it.valider,
    "LU": lu.valider,
    "NL": nl.valider,
    "PL": pl.valider,
    "PT": pt.valider,
    "SE": se.valider,
}

# Les 10 pays confirmés dans le référentiel (cf. exploration Phase 1).
# Tout `pays_declare` hors de cet ensemble (ZZ, QQ, XX, GB, UK...) est
# structurellement hors périmètre : VIES ne le couvre pas, donc aucun
# appel n'y sera jamais fait (décision validée en Phase 1).
PAYS_COUVERTS = frozenset(_VALIDATEURS)


def valider_par_pays(pays_declare: str, numero_normalise: str) -> ResultatValidation:
    """Route un numéro déjà normalisé vers le validateur du pays déclaré.

    `numero_normalise` est la sortie de `normaliser_numero_tva` : sans
    espaces/tirets/points, en majuscules, et jamais None (les valeurs
    vides doivent être écartées par l'appelant avant d'appeler cette
    fonction, avec le motif `valeur_absente`).

    Le préfixe pays éventuellement présent dans le numéro est comparé à
    `pays_declare` : s'il est présent mais différent, c'est un motif de
    rejet à part entière (`prefixe_incoherent`) plutôt qu'une tentative de
    validation avec les mauvaises règles. S'il est absent (numéro saisi
    sans son préfixe, cas observé sur l'échantillon), on considère que
    `pays_declare` fait foi et on valide la partie nationale telle quelle.
    """
    if pays_declare not in PAYS_COUVERTS:
        return ResultatValidation.rejet(MotifRejet.PAYS_HORS_PERIMETRE, numero_normalise)

    partie_nationale = numero_normalise
    prefixe_eventuel = numero_normalise[:2]
    if prefixe_eventuel.isalpha():
        if prefixe_eventuel != pays_declare:
            return ResultatValidation.rejet(MotifRejet.PREFIXE_INCOHERENT, numero_normalise)
        partie_nationale = numero_normalise[2:]

    return _VALIDATEURS[pays_declare](partie_nationale, pays_declare)
