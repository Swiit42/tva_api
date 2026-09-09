"""Validation structurelle du numéro de TVA finlandais (FI).

Format : FI + 8 chiffres (Y-tunnus).

Clé de contrôle : poids 7,9,10,5,8,4,2 appliqués aux 7 premiers chiffres,
somme mod 11 :
- reste 0 -> clé attendue = 0
- reste 1 -> AUCUNE clé n'est mathématiquement valide pour ces 7 premiers
  chiffres (l'administration finlandaise n'attribue jamais un tel
  identifiant) : motif dédié `cle_controle_impossible`, différent d'une
  simple faute de frappe.
- sinon -> clé attendue = 11 - reste

Source : https://hetut.fi/en/business-id-guide/
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 8
POIDS = (7, 9, 10, 5, 8, 4, 2)


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    sept_premiers = partie_nationale[:7]
    cle_fournie = int(partie_nationale[7])
    somme = sum(int(chiffre) * poids for chiffre, poids in zip(sept_premiers, POIDS))
    reste = somme % 11

    if reste == 1:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_IMPOSSIBLE, numero_complet)

    cle_attendue = 0 if reste == 0 else 11 - reste
    if cle_fournie != cle_attendue:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
