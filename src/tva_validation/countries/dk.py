"""Validation structurelle du numéro de TVA danois (DK).

Format : DK + 8 chiffres (numéro CVR).

Clé de contrôle : somme pondérée des 8 chiffres avec les poids
2,7,6,5,4,3,2,1 (de gauche à droite). Le numéro est valide si cette somme
est divisible par 11 (contrairement à d'autres pays, il n'y a pas de
"9e chiffre" séparé : le dernier chiffre fait partie intégrante de la
somme pondérée).

Source : https://metacpan.org/dist/Business-DK-CVR/view/lib/Business/DK/CVR.pm
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 8
POIDS = (2, 7, 6, 5, 4, 3, 2, 1)


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    somme = sum(int(chiffre) * poids for chiffre, poids in zip(partie_nationale, POIDS))

    if somme % 11 != 0:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
