"""Commande unique de chargement du référentiel TVA en PostgreSQL.

Usage :
    python scripts/charger_referentiel.py [chemin_vers_le_csv]

Étapes : lecture du CSV -> normalisation -> dispatch par pays -> calcul
de la clé de dédoublonnage (voir tva_validation.pipeline) -> upsert en
base sur la clé naturelle `id` du CSV source, pour qu'un rechargement ne
duplique jamais les lignes (ON CONFLICT DO UPDATE plutôt qu'un simple
INSERT).
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8")  # évite les accents corrompus sous PowerShell

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from tva_validation.db import get_connection  # noqa: E402
from tva_validation.pipeline import traiter_ligne  # noqa: E402

CSV_PAR_DEFAUT = RACINE / "data" / "numeros_tva.csv"
SCHEMA_SQL = RACINE / "db" / "schema.sql"

REQUETE_UPSERT = """
    INSERT INTO referentiel (
        id, raison_sociale, pays_declare, numero_tva_brut,
        numero_tva_normalise, date_saisie, source_saisie,
        conforme_structurel, motif_structurel, cle_dedup
    )
    VALUES %s
    ON CONFLICT (id) DO UPDATE SET
        raison_sociale       = EXCLUDED.raison_sociale,
        pays_declare         = EXCLUDED.pays_declare,
        numero_tva_brut       = EXCLUDED.numero_tva_brut,
        numero_tva_normalise = EXCLUDED.numero_tva_normalise,
        date_saisie          = EXCLUDED.date_saisie,
        source_saisie        = EXCLUDED.source_saisie,
        conforme_structurel  = EXCLUDED.conforme_structurel,
        motif_structurel     = EXCLUDED.motif_structurel,
        cle_dedup            = EXCLUDED.cle_dedup,
        charge_le            = now()
"""


def lignes_a_inserer(chemin_csv: Path):
    df = pd.read_csv(chemin_csv, dtype=str, keep_default_na=False)
    for _, ligne in df.iterrows():
        traitee = traiter_ligne(ligne["pays_declare"], ligne["numero_tva"])
        yield (
            int(ligne["id"]),
            ligne["raison_sociale"],
            ligne["pays_declare"],
            ligne["numero_tva"],
            traitee.numero_tva_normalise,
            datetime.strptime(ligne["date_saisie"], "%Y-%m-%d").date(),
            ligne["source_saisie"],
            traitee.conforme_structurel,
            traitee.motif_structurel,
            traitee.cle_dedup,
        )


def main() -> None:
    chemin_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else CSV_PAR_DEFAUT

    lignes = list(lignes_a_inserer(chemin_csv))

    connexion = get_connection()
    try:
        with connexion, connexion.cursor() as curseur:
            curseur.execute(SCHEMA_SQL.read_text(encoding="utf-8"))
            execute_values(curseur, REQUETE_UPSERT, lignes)
    finally:
        connexion.close()

    conformes = sum(1 for l in lignes if l[7])
    print(f"{len(lignes)} lignes chargées ({conformes} conformes structurellement).")


if __name__ == "__main__":
    main()
