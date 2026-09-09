"""Validation structurelle du numéro de TVA portugais (PT).

Format : PT + 9 chiffres (NIF).

Clé de contrôle : poids 9,8,7,6,5,4,3,2 appliqués aux 8 premiers
chiffres, somme mod 11 :
- reste 0 ou 1 -> clé attendue = 0
- sinon -> clé attendue = 11 - reste

Source : https://www.docuflair.com/en/pages/tools/vat-countries/portugal.html
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 9
POIDS = (9, 8, 7, 6, 5, 4, 3, 2)


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    huit_premiers = partie_nationale[:8]
    cle_fournie = int(partie_nationale[8])
    somme = sum(int(chiffre) * poids for chiffre, poids in zip(huit_premiers, POIDS))
    reste = somme % 11
    cle_attendue = 0 if reste in (0, 1) else 11 - reste

    if cle_fournie != cle_attendue:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
