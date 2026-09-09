"""Validation structurelle du numéro de TVA suédois (SE).

Format : SE + 10 chiffres (organisationsnummer) + "01" (suffixe fixe
d'unité TVA, ce n'est pas une clé calculée : VIES n'accepte que "01").

Clé de contrôle : les 10 chiffres de l'organisationsnummer doivent passer
l'algorithme de Luhn (norme SKV 709 de Skatteverket) - le même algorithme
qu'un numéro de carte bancaire, pas une clé propre à la TVA. C'est un bon
exemple pour la soutenance : le "checksum TVA" suédois est en réalité
hérité d'un identifiant national préexistant.

Source : https://cran.r-project.org/web/packages/sweidnumbr/sweidnumbr.pdf
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 12  # 10 chiffres + "01"
SUFFIXE_ATTENDU = "01"


def _luhn_valide(dix_chiffres: str) -> bool:
    total = 0
    for position, chiffre in enumerate(reversed(dix_chiffres)):
        valeur = int(chiffre)
        if position % 2 == 1:
            valeur *= 2
            if valeur > 9:
                valeur -= 9
        total += valeur
    return total % 10 == 0


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)

    organisationsnummer, suffixe = partie_nationale[:10], partie_nationale[10:]
    if not organisationsnummer.isdigit() or suffixe != SUFFIXE_ATTENDU:
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    if not _luhn_valide(organisationsnummer):
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
