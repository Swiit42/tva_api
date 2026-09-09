"""Validation structurelle du numéro de TVA belge (BE).

Format : BE + 10 chiffres. Le premier chiffre vaut 0 (numéros attribués
avant 2014) ou 1 (nouvelle tranche ouverte en 2023, l'ancienne tranche "0"
arrivant à épuisement) ; on ne vérifie que la longueur et le format, pas
ce premier chiffre, la donnée n'apportant rien de plus qu'un chiffre
normal pour la clé de contrôle.

Clé de contrôle : ISO 7064 MOD 97-10. Les 2 derniers chiffres doivent
valoir 97 - (les 8 premiers chiffres mod 97).

Sources (croisées) :
- https://vatdb.com/guides/validate-be-vat-number/
- https://www.docuflair.com/en/pages/tools/vat-countries/belgium.html
"""

from __future__ import annotations

from ..models import MotifRejet, ResultatValidation

LONGUEUR = 10


def valider(partie_nationale: str, pays_declare: str) -> ResultatValidation:
    numero_complet = pays_declare + partie_nationale

    if len(partie_nationale) != LONGUEUR:
        return ResultatValidation.rejet(MotifRejet.LONGUEUR_INVALIDE, numero_complet)
    if not partie_nationale.isdigit():
        return ResultatValidation.rejet(MotifRejet.FORMAT_INVALIDE, numero_complet)

    huit_premiers = int(partie_nationale[:8])
    cle_fournie = int(partie_nationale[8:])
    cle_attendue = 97 - (huit_premiers % 97)

    if cle_fournie != cle_attendue:
        return ResultatValidation.rejet(MotifRejet.CLE_CONTROLE_INVALIDE, numero_complet)

    return ResultatValidation.ok(numero_complet)
