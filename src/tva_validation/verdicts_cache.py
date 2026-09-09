"""Accès au cache des verdicts VIES fermes (table `verdicts_vies`).

Partagé entre la campagne (Phase 2, remplissage en masse) et l'API
(Phase 2, lecture + remplissage à la demande) pour ne pas dupliquer la
logique d'upsert ni la définition de la fraîcheur.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .config import FRAICHEUR_JOURS
from .vies_client import VerdictVies


@dataclass(frozen=True)
class VerdictEnCache:
    verdict: str  # "valide" | "invalide"
    user_error_vies: str
    nom: str | None
    adresse: str | None
    verifie_le: datetime


def est_perime(verifie_le: datetime) -> bool:
    maintenant = datetime.now(timezone.utc)
    return verifie_le < maintenant - timedelta(days=FRAICHEUR_JOURS)


def lire_cache(connexion, cle_dedup: str) -> VerdictEnCache | None:
    with connexion.cursor() as curseur:
        curseur.execute(
            """
            SELECT verdict, user_error_vies, nom_vies, adresse_vies, verifie_le
            FROM verdicts_vies
            WHERE cle_dedup = %s
            """,
            (cle_dedup,),
        )
        ligne = curseur.fetchone()

    if ligne is None:
        return None
    verdict, user_error_vies, nom, adresse, verifie_le = ligne
    return VerdictEnCache(verdict, user_error_vies, nom, adresse, verifie_le)


def ecrire_cache(connexion, cle_dedup: str, pays_declare: str, numero_normalise: str, resultat: VerdictVies) -> None:
    """N'écrit que les verdicts fermes : un "indéterminé" n'écrase jamais
    un précédent verdict connu (cf. décision "cache périmé servi tel
    quel" plutôt que perdu)."""
    if resultat.verdict not in ("valide", "invalide"):
        return

    with connexion, connexion.cursor() as curseur:
        curseur.execute(
            """
            INSERT INTO verdicts_vies
                (cle_dedup, pays_declare, numero_tva_normalise, verdict, user_error_vies, nom_vies, adresse_vies, verifie_le)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (cle_dedup) DO UPDATE SET
                verdict = EXCLUDED.verdict,
                user_error_vies = EXCLUDED.user_error_vies,
                nom_vies = EXCLUDED.nom_vies,
                adresse_vies = EXCLUDED.adresse_vies,
                verifie_le = now()
            """,
            (
                cle_dedup, pays_declare, numero_normalise,
                resultat.verdict, resultat.user_error_vies, resultat.nom, resultat.adresse,
            ),
        )
