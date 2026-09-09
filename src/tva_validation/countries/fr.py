"""Validation structurelle du numéro de TVA français (FR).

Format : FR + 2 chiffres de clé + 9 chiffres (SIREN).

Clé de contrôle : clé = (12 + 3 x (SIREN mod 97)) mod 97.

Remarque (hors périmètre ici) : de très rares numéros de gestion interne
DGFiP comportent une lettre dans la clé. Le cas standard couvert par ce
module - largement majoritaire - a une clé et un SIREN entièrement
numériques.

Source : https://www.eurofiscalis.com/calculateur-numero-tva-intracommunautaire/
Vérifié indépendamment (calcul manuel) : SIREN 123456789 -> SIREN mod 97
= 39 -> clé = (12 + 3*39) mod 97 = 32, soit FR32123456789. L'exemple
FR23123456789 donné par certaines sources en ligne repose sur un reste de
36 mod 97, qui est arithmétiquement faux pour ce SIREN.
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 11  # 2 (clé) + 9 (SIREN)


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    cle_fournie = int(partie_nationale[:2])
    siren = int(partie_nationale[2:])
    cle_attendue = (12 + 3 * (siren % 97)) % 97

    if cle_fournie != cle_attendue:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
