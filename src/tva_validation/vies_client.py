"""Client VIES : un seul rôle, transformer une réponse VIES (ou une
absence de réponse) en un verdict parmi {valide, invalide, indetermine}.

Point non négociable de ce client, découvert en testant manuellement
l'API : le champ `isValid` ne suffit PAS. VIES répond parfois
`isValid: false` alors qu'il n'a même pas pu joindre l'administration du
pays concerné (`userError: "MS_MAX_CONCURRENT_REQ"` observé en direct sur
FR et BE pendant les tests manuels). Se fier à `isValid` seul aurait
classé ces cas en "invalide" à tort. C'est `userError` qui pilote le
verdict, jamais `isValid` seul.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import VIES_TIMEOUT_SECONDES, VIES_URL_TEMPLATE


@dataclass(frozen=True)
class VerdictVies:
    verdict: str  # "valide" | "invalide" | "indetermine"
    user_error_vies: str | None  # champ brut VIES ; None si échec réseau (pas de réponse VIES du tout)
    nom: str | None
    adresse: str | None


def interpreter_reponse_vies(corps_json: dict) -> VerdictVies:
    """Traduit le JSON VIES en verdict. Fonction pure, testée sans réseau."""
    user_error = corps_json.get("userError")

    if user_error == "VALID" and corps_json.get("isValid") is True:
        return VerdictVies("valide", user_error, corps_json.get("name"), corps_json.get("address"))

    if user_error == "INVALID":
        return VerdictVies("invalide", user_error, None, None)

    # Tout le reste (MS_MAX_CONCURRENT_REQ, MS_UNAVAILABLE, TIMEOUT,
    # GLOBAL_MAX_CONCURRENT_REQ, SERVICE_UNAVAILABLE, IP_BLOCKED...) :
    # VIES n'a pas pu trancher. Jamais "invalide" par défaut dans ce cas.
    return VerdictVies("indetermine", user_error, None, None)


def interroger_vies(pays_declare: str, numero_national: str) -> VerdictVies:
    """Appelle VIES pour de vrai. Toute erreur réseau/HTTP -> indéterminé."""
    url = VIES_URL_TEMPLATE.format(pays=pays_declare, numero=numero_national)

    try:
        reponse = httpx.get(url, timeout=VIES_TIMEOUT_SECONDES)
        reponse.raise_for_status()
        corps = reponse.json()
    except (httpx.HTTPError, ValueError):
        return VerdictVies("indetermine", None, None, None)

    return interpreter_reponse_vies(corps)
