"""CLI de la campagne de vérification VIES.

Usage :
    python scripts/lancer_campagne.py                  # échantillon de 200 (défaut)
    python scripts/lancer_campagne.py --echantillon 50
    python scripts/lancer_campagne.py --tout            # tous les numéros éligibles
    python scripts/lancer_campagne.py --delai 2.0       # espace davantage les appels

Reprise automatique : si une campagne précédente a été interrompue
(Ctrl+C, coupure réseau...), relancer cette même commande reprend
exactement là où elle s'était arrêtée (voir tva_validation.campagne).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from tva_validation.campagne import executer_campagne  # noqa: E402
from tva_validation.db import get_connection  # noqa: E402

LOG_DIR = RACINE / "logs"


def main() -> None:
    parser = argparse.ArgumentParser(description="Campagne de vérification VIES")
    parser.add_argument("--echantillon", type=int, default=200, help="Nombre de numéros à vérifier (défaut : 200)")
    parser.add_argument("--tout", action="store_true", help="Vérifier tous les numéros éligibles, sans limite")
    parser.add_argument("--delai", type=float, default=1.0, help="Délai en secondes entre deux appels VIES (défaut : 1.0)")
    args = parser.parse_args()

    LOG_DIR.mkdir(exist_ok=True)
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / "campagne_vies.log", encoding="utf-8"),
        ],
    )

    taille_echantillon = None if args.tout else args.echantillon

    connexion = get_connection()
    try:
        executer_campagne(connexion, taille_echantillon=taille_echantillon, delai_secondes=args.delai)
    finally:
        connexion.close()


if __name__ == "__main__":
    main()
