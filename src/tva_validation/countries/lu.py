"""Validation structurelle du numéro de TVA luxembourgeois (LU).

Format : LU + 6 chiffres + 2 chiffres de clé.

Clé de contrôle : les 2 derniers chiffres = (les 6 premiers chiffres,
lus comme un nombre) mod 89, complétés par un zéro à gauche si besoin.

Source : https://www.commenda.io/blog/luxembourg-vat-number-verification
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 8


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    six_premiers = int(partie_nationale[:6])
    cle_fournie = int(partie_nationale[6:])
    cle_attendue = six_premiers % 89

    if cle_fournie != cle_attendue:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
