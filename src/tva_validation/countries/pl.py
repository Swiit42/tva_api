"""Validation structurelle du numéro de TVA polonais (PL).

Format : PL + 10 chiffres (NIP).

Clé de contrôle : poids 6,5,7,2,3,4,5,6,7 appliqués aux 9 premiers
chiffres, somme mod 11 = 10e chiffre. Si le reste vaut 10, aucune clé
n'est valide (motif dédié, comme pour la Finlande et les Pays-Bas).

Source : https://poland.gg/tools/nip-checker (algorithme officiel
biznes.gov.pl). Exemple vérifié : NIP 2073786728 -> somme pondérée = 206,
206 mod 11 = 8, qui est bien le 10e chiffre du numéro.
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 10
POIDS = (6, 5, 7, 2, 3, 4, 5, 6, 7)


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    neuf_premiers = partie_nationale[:9]
    cle_fournie = int(partie_nationale[9])
    somme = sum(int(chiffre) * poids for chiffre, poids in zip(neuf_premiers, POIDS))
    reste = somme % 11

    if reste == 10:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_IMPOSSIBLE, numero_complet)
    if cle_fournie != reste:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
