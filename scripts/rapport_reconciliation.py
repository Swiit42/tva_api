"""Rapport de réconciliation final, reproductible par une commande.

Usage :
    python scripts/rapport_reconciliation.py

Combine la validation structurelle (Phase 1) et le cache de verdicts VIES
(Phase 2, rempli par scripts/lancer_campagne.py ou par l'API au fil de
l'eau) sans jamais déclencher de nouvel appel VIES : c'est un rapport de
lecture, pas une nouvelle vérification.

Règle de verdict final par ligne du référentiel :
- non conforme structurellement -> invalide (motif structurel)
- conforme, verdict ferme connu en cache -> ce verdict (valide/invalide),
  qu'il soit frais ou périmé (on ne perd jamais un fait déjà établi)
- conforme, aucun verdict ferme connu -> indéterminé (jamais vérifié, ou
  vérifié sans succès jusqu'ici)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from tva_validation.db import get_connection  # noqa: E402

REQUETE_VERDICT_FINAL = """
    SELECT
        CASE
            WHEN NOT r.conforme_structurel THEN 'invalide'
            WHEN v.verdict IS NOT NULL THEN v.verdict
            ELSE 'indetermine'
        END AS verdict_final,
        COUNT(*) AS nb_lignes,
        COUNT(DISTINCT r.cle_dedup) AS nb_numeros_uniques
    FROM referentiel r
    LEFT JOIN verdicts_vies v ON v.cle_dedup = r.cle_dedup
    GROUP BY verdict_final
    ORDER BY nb_lignes DESC
"""

REQUETE_MOTIFS_STRUCTURELS = """
    SELECT motif_structurel, COUNT(*)
    FROM referentiel
    WHERE NOT conforme_structurel
    GROUP BY motif_structurel
    ORDER BY COUNT(*) DESC
"""

REQUETE_DOUBLONS = """
    SELECT COUNT(*) AS lignes, COUNT(DISTINCT cle_dedup) AS numeros_uniques
    FROM referentiel
    WHERE cle_dedup IS NOT NULL
"""

REQUETE_INDETERMINES_DEJA_TENTES = """
    SELECT COUNT(DISTINCT r.cle_dedup)
    FROM referentiel r
    LEFT JOIN verdicts_vies v ON v.cle_dedup = r.cle_dedup
    WHERE r.conforme_structurel AND v.cle_dedup IS NULL
      AND r.cle_dedup IN (SELECT DISTINCT cle_dedup FROM tentatives_vies)
"""


def main() -> None:
    connexion = get_connection()
    try:
        with connexion.cursor() as curseur:
            curseur.execute(REQUETE_VERDICT_FINAL)
            verdicts = curseur.fetchall()

            curseur.execute(REQUETE_MOTIFS_STRUCTURELS)
            motifs = curseur.fetchall()

            curseur.execute(REQUETE_DOUBLONS)
            lignes, numeros_uniques = curseur.fetchone()

            curseur.execute(REQUETE_INDETERMINES_DEJA_TENTES)
            (indetermines_deja_tentes,) = curseur.fetchone()
    finally:
        connexion.close()

    total_lignes = sum(nb for _, nb, _ in verdicts)

    print("=== Verdict final (référentiel complet) ===")
    for verdict_final, nb_lignes, nb_uniques in verdicts:
        print(f"{verdict_final:15} {nb_lignes:6} lignes  ({nb_uniques} numéros uniques)")

    print()
    print("=== Motifs de rejet structurel ===")
    for motif, nb in motifs:
        print(f"{motif:30} {nb:6}")

    print()
    print("=== Doublons ===")
    print(f"Lignes avec un numéro exploitable : {lignes}")
    print(f"Numéros uniques (clé pays+numéro) : {numeros_uniques}")
    print(f"Doublons (lignes en trop)         : {lignes - numeros_uniques}")

    print()
    print("=== Indéterminés ===")
    indetermines_total = next((nb for v, nb, _ in verdicts if v == "indetermine"), 0)
    print(f"Total indéterminé                         : {indetermines_total} lignes")
    print(f"  dont déjà tenté au moins une fois sur VIES : {indetermines_deja_tentes} numéros")
    print(f"  dont jamais encore soumis à VIES           : {indetermines_total - indetermines_deja_tentes} lignes (environ, avant dédup)")


if __name__ == "__main__":
    main()
