"""Campagne de vérification VIES : mode échantillon, temporisation,
journalisation, reprise sur interruption.

Mécanisme de reprise : au premier lancement, la campagne tire un plan
fixe (liste de numéros à vérifier) et lui attribue un run_id, persistés
dans un petit fichier d'état sur disque (`.campagne_en_cours.json`).
Chaque tentative est enregistrée immédiatement en base
(`tentatives_vies`) au fur et à mesure — jamais en lot à la fin. Si le
script est interrompu (Ctrl+C, coupure réseau, crash), un nouveau
lancement retrouve le fichier d'état, relit dans `tentatives_vies` ce qui
a déjà été fait pour ce run_id, et ne reprend que sur les numéros
restants du plan : jamais depuis le début, et jamais avec un échantillon
différent tiré une seconde fois. Une fois le plan entièrement traité, le
fichier d'état est supprimé — le prochain lancement tire une nouvelle
campagne.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path

from .config import FRAICHEUR_JOURS
from .verdicts_cache import ecrire_cache
from .vies_client import VerdictVies, interroger_vies

FICHIER_ETAT = Path(__file__).resolve().parent.parent.parent / ".campagne_en_cours.json"

logger = logging.getLogger("campagne_vies")


def _candidats_a_verifier(connexion, limite: int | None) -> list[tuple[str, str, str]]:
    """Numéros conformes structurellement sans verdict ferme, ou périmé."""
    requete = """
        SELECT DISTINCT r.cle_dedup, r.pays_declare, r.numero_tva_normalise
        FROM referentiel r
        LEFT JOIN verdicts_vies v ON v.cle_dedup = r.cle_dedup
        WHERE r.conforme_structurel = TRUE
          AND (v.cle_dedup IS NULL OR v.verifie_le < now() - (%s || ' days')::interval)
        ORDER BY r.cle_dedup
    """
    params: list = [FRAICHEUR_JOURS]
    if limite is not None:
        requete += " LIMIT %s"
        params.append(limite)
    with connexion.cursor() as curseur:
        curseur.execute(requete, params)
        return curseur.fetchall()


def _charger_ou_creer_plan(connexion, taille_echantillon: int | None) -> tuple[str, list]:
    if FICHIER_ETAT.exists():
        etat = json.loads(FICHIER_ETAT.read_text(encoding="utf-8"))
        logger.info(
            "Reprise de la campagne %s (%d numéros dans le plan initial).",
            etat["run_id"],
            len(etat["plan"]),
        )
        return etat["run_id"], etat["plan"]

    candidats = _candidats_a_verifier(connexion, taille_echantillon)
    run_id = str(uuid.uuid4())
    plan = [list(candidat) for candidat in candidats]
    FICHIER_ETAT.write_text(json.dumps({"run_id": run_id, "plan": plan}), encoding="utf-8")
    logger.info("Nouvelle campagne %s : %d numéros à vérifier.", run_id, len(plan))
    return run_id, plan


def _deja_tentes(connexion, run_id: str) -> set[str]:
    with connexion.cursor() as curseur:
        curseur.execute("SELECT cle_dedup FROM tentatives_vies WHERE run_id = %s", (run_id,))
        return {ligne[0] for ligne in curseur.fetchall()}


def _enregistrer_tentative(
    connexion, run_id: str, cle_dedup: str, pays_declare: str, numero_normalise: str,
    resultat: VerdictVies, duree_ms: int,
) -> None:
    with connexion, connexion.cursor() as curseur:
        curseur.execute(
            """
            INSERT INTO tentatives_vies (run_id, cle_dedup, verdict, user_error_vies, duree_ms)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (run_id, cle_dedup) DO NOTHING
            """,
            (run_id, cle_dedup, resultat.verdict, resultat.user_error_vies, duree_ms),
        )
    ecrire_cache(connexion, cle_dedup, pays_declare, numero_normalise, resultat)


def executer_campagne(
    connexion, taille_echantillon: int | None = 200, delai_secondes: float = 1.0
) -> None:
    run_id, plan = _charger_ou_creer_plan(connexion, taille_echantillon)
    deja_faits = _deja_tentes(connexion, run_id)
    restant = [candidat for candidat in plan if candidat[0] not in deja_faits]

    logger.info("%d numéros déjà traités pour ce run, %d restants.", len(deja_faits), len(restant))

    for cle_dedup, pays_declare, numero_normalise in restant:
        numero_national = numero_normalise[len(pays_declare):]

        debut = time.monotonic()
        resultat = interroger_vies(pays_declare, numero_national)
        duree_ms = int((time.monotonic() - debut) * 1000)

        _enregistrer_tentative(connexion, run_id, cle_dedup, pays_declare, numero_normalise, resultat, duree_ms)
        logger.info("%-20s -> %-12s (userError=%s, %dms)", cle_dedup, resultat.verdict, resultat.user_error_vies, duree_ms)

        time.sleep(delai_secondes)

    FICHIER_ETAT.unlink(missing_ok=True)
    logger.info("Campagne %s terminée (%d numéros traités au total).", run_id, len(plan))
