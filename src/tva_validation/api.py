"""API REST appelée par la facturation avant chaque émission hors taxe.

Le contrat de réponse est le vrai sujet (brief) : chaque appel renvoie
toujours un verdict, son origine, et sa fraîcheur — jamais un simple
booléen. Un numéro structurellement non conforme ne touche jamais la
base ni VIES : le rejet est immédiat et déterministe (cf. Phase 1).

Comportement VIES injoignable (décisions validées) :
- un cache ferme (< 30 jours) existe -> on le sert (origine="cache")
- pas de cache frais, mais VIES répond fermement -> "appel_frais"
- VIES indéterminé (surcharge, timeout...) et un cache périmé existe ->
  on sert ce cache périmé, explicitement marqué comme tel
  (origine="cache_perime"), plutôt que de perdre une information connue
- VIES indéterminé et rien en cache -> verdict="indetermine". On ne
  répond JAMAIS "invalide" par défaut dans ce cas.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel

from .countries import valider_par_pays
from .db import get_connection
from .normalize import normaliser_numero_tva
from .verdicts_cache import ecrire_cache, est_perime, lire_cache
from .vies_client import interroger_vies

app = FastAPI(title="Vérification TVA intracommunautaire — Meridian Distribution")


class ReponseVerification(BaseModel):
    pays_declare: str
    numero_tva: str
    verdict: str  # "valide" | "invalide" | "indetermine"
    origine: str  # "structurel" | "cache" | "cache_perime" | "appel_frais" | "vies_injoignable_sans_cache"
    fraicheur: datetime | None = None
    motif: str | None = None


@app.get("/verification-tva/{pays_declare}/{numero_tva}", response_model=ReponseVerification)
def verifier_numero_tva(pays_declare: str, numero_tva: str) -> ReponseVerification:
    pays_declare = pays_declare.upper()
    numero_normalise = normaliser_numero_tva(numero_tva)

    if numero_normalise is None:
        return ReponseVerification(
            pays_declare=pays_declare,
            numero_tva=numero_tva,
            verdict="invalide",
            origine="structurel",
            motif="valeur_absente",
            fraicheur=datetime.now(timezone.utc),
        )

    resultat_structurel = valider_par_pays(pays_declare, numero_normalise)
    if not resultat_structurel.conforme:
        return ReponseVerification(
            pays_declare=pays_declare,
            numero_tva=resultat_structurel.numero_normalise or numero_normalise,
            verdict="invalide",
            origine="structurel",
            motif=resultat_structurel.motif.value,
            fraicheur=datetime.now(timezone.utc),
        )

    numero_canonique = resultat_structurel.numero_normalise
    cle_dedup = f"{pays_declare}:{numero_canonique}"

    connexion = get_connection()
    try:
        cache = lire_cache(connexion, cle_dedup)

        if cache is not None and not est_perime(cache.verifie_le):
            return ReponseVerification(
                pays_declare=pays_declare,
                numero_tva=numero_canonique,
                verdict=cache.verdict,
                origine="cache",
                fraicheur=cache.verifie_le,
            )

        numero_national = numero_canonique[len(pays_declare):]
        resultat_vies = interroger_vies(pays_declare, numero_national)

        if resultat_vies.verdict in ("valide", "invalide"):
            ecrire_cache(connexion, cle_dedup, pays_declare, numero_canonique, resultat_vies)
            return ReponseVerification(
                pays_declare=pays_declare,
                numero_tva=numero_canonique,
                verdict=resultat_vies.verdict,
                origine="appel_frais",
                fraicheur=datetime.now(timezone.utc),
            )

        if cache is not None:
            return ReponseVerification(
                pays_declare=pays_declare,
                numero_tva=numero_canonique,
                verdict=cache.verdict,
                origine="cache_perime",
                fraicheur=cache.verifie_le,
            )

        return ReponseVerification(
            pays_declare=pays_declare,
            numero_tva=numero_canonique,
            verdict="indetermine",
            origine="vies_injoignable_sans_cache",
            fraicheur=None,
        )
    finally:
        connexion.close()
