"""Rapport reproductible : répartition par motif + appels VIES évités.

Usage :
    python scripts/rapport_motifs.py

Suppose que `scripts/charger_referentiel.py` a déjà été exécuté (la table
`referentiel` doit exister et être peuplée).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # évite les accents corrompus sous PowerShell

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from tva_validation.db import get_connection  # noqa: E402

REQUETE_MOTIFS = """
    SELECT
        CASE WHEN conforme_structurel THEN 'conforme' ELSE motif_structurel END AS motif,
        COUNT(*) AS nb
    FROM referentiel
    GROUP BY motif
    ORDER BY nb DESC
"""

REQUETE_CHIFFRAGE = """
    SELECT
        COUNT(*)                                                        AS total_lignes,
        COUNT(*) FILTER (WHERE conforme_structurel)                     AS lignes_conformes,
        COUNT(DISTINCT cle_dedup) FILTER (WHERE conforme_structurel)    AS numeros_uniques_a_verifier
    FROM referentiel
"""


def main() -> None:
    connexion = get_connection()
    try:
        with connexion.cursor() as curseur:
            curseur.execute(REQUETE_MOTIFS)
            repartition = curseur.fetchall()

            curseur.execute(REQUETE_CHIFFRAGE)
            total_lignes, lignes_conformes, numeros_uniques = curseur.fetchone()
    finally:
        connexion.close()

    print("=== Répartition par motif ===")
    for motif, nb in repartition:
        print(f"{motif:30} {nb:6}  ({100 * nb / total_lignes:5.2f}%)")

    evites_par_structure = total_lignes - lignes_conformes
    evites_par_dedup = lignes_conformes - numeros_uniques
    total_evites = total_lignes - numeros_uniques

    print()
    print("=== Appels VIES évités ===")
    print(f"Lignes du référentiel                         : {total_lignes}")
    print(f"  - écartées par le filtre structurel          : {evites_par_structure}")
    print(f"  - conformes mais doublons d'un numéro déjà vu: {evites_par_dedup}")
    print(f"Numéros uniques à réellement interroger sur VIES : {numeros_uniques}")
    print(
        f"Total d'appels VIES évités : {total_evites} "
        f"({100 * total_evites / total_lignes:.2f}% du référentiel)"
    )


if __name__ == "__main__":
    main()
