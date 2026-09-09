"""Validation structurelle du numéro de TVA italien (IT).

Format : 11 chiffres (7 chiffres de matricule + 3 chiffres de code bureau
+ 1 chiffre de clé). On ne vérifie pas ici que le code bureau (positions
8-10) correspond à une valeur officiellement attribuée (001-100, 120,
121, 888, 999) : seule la longueur et la clé de contrôle sont couvertes,
comme pour les autres pays de ce module.

Clé de contrôle : variante de l'algorithme de Luhn sur les 10 premiers
chiffres. En numérotant les positions de 1 à 10 (de gauche à droite) :
- positions impaires (1,3,5,7,9) : chiffre pris tel quel
- positions paires (2,4,6,8,10) : chiffre doublé, puis -9 si le résultat
  dépasse 9
La clé = (10 - (somme totale mod 10)) mod 10.

Sources (croisées) :
- https://github.com/stefanoscerra/ItalianVatHelper
- https://pypi.org/project/italian-tax-validators/
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 11


def _cle_luhn_it(dix_premiers_chiffres: str) -> int:
    total = 0
    for position, chiffre in enumerate(dix_premiers_chiffres, start=1):
        valeur = int(chiffre)
        if position % 2 == 0:
            valeur *= 2
            if valeur > 9:
                valeur -= 9
        total += valeur
    return (10 - (total % 10)) % 10


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    dix_premiers = partie_nationale[:10]
    cle_fournie = int(partie_nationale[10])
    cle_attendue = _cle_luhn_it(dix_premiers)

    if cle_fournie != cle_attendue:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
