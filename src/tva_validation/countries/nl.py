"""Validation structurelle du numéro de TVA néerlandais (NL).

Format : NL + 9 chiffres + "B" + 2 chiffres (indice d'établissement,
normalement 01-99). On ne vérifie pas ici que cet indice est bien >= 01 :
seules la longueur, la présence du "B" et la clé de contrôle sont
couvertes.

Clé de contrôle : poids 9,8,7,6,5,4,3,2 appliqués aux 8 premiers des 9
chiffres, somme mod 11 = 9e chiffre. Si le reste vaut 10, aucune clé
n'est valide (motif dédié, comme pour la Finlande et la Pologne).

Source : https://www.oecd.org/content/dam/oecd/en/topics/policy-issue-focus/aeoi/netherlands-tin.pdf
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 12  # 9 chiffres + "B" + 2 chiffres
POIDS = (9, 8, 7, 6, 5, 4, 3, 2)


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)

    neuf_chiffres, separateur, indice = (
        partie_nationale[:9],
        partie_nationale[9],
        partie_nationale[10:],
    )
    if not (neuf_chiffres.isdigit() and separateur == "B" and indice.isdigit()):
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    huit_premiers = neuf_chiffres[:8]
    cle_fournie = int(neuf_chiffres[8])
    somme = sum(int(chiffre) * poids for chiffre, poids in zip(huit_premiers, POIDS))
    reste = somme % 11

    if reste == 10:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_IMPOSSIBLE, numero_complet)
    if cle_fournie != reste:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
