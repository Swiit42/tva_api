"""Modèle de résultat pour la validation structurelle.

Un `ResultatValidation` ne dit rien sur l'existence réelle du numéro : il
décrit uniquement la conformité de sa forme (longueur, format, clé de
contrôle). Un numéro `conforme=True` ici peut très bien ne correspondre à
aucune entreprise réelle — seul VIES (Phase 2) peut confirmer ça.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MotifRejet(str, Enum):
    """Taxonomie des motifs de rejet structurel (validée avec le métier).

    Les deux premiers motifs sont tranchés avant même de savoir quel pays
    valider (`valeur_absente` : rien à analyser ; `pays_hors_perimetre` :
    VIES ne couvre pas ce pays, donc aucun appel n'a de sens). Les suivants
    sont produits par le dispatcher ou par le validateur du pays déclaré.
    """

    VALEUR_ABSENTE = "valeur_absente"
    PAYS_HORS_PERIMETRE = "pays_hors_perimetre"
    PREFIXE_INCOHERENT = "prefixe_incoherent"
    LONGUEUR_INVALIDE = "longueur_invalide"
    FORMAT_INVALIDE = "format_invalide"
    CLE_CONTROLE_INVALIDE = "cle_controle_invalide"
    CLE_CONTROLE_IMPOSSIBLE = "cle_controle_impossible"


@dataclass(frozen=True)
class ResultatValidation:
    conforme: bool
    numero_normalise: str | None
    motif: MotifRejet | None  # None si conforme=True

    @staticmethod
    def ok(numero_normalise: str) -> "ResultatValidation":
        return ResultatValidation(conforme=True, numero_normalise=numero_normalise, motif=None)

    @staticmethod
    def rejet(motif: MotifRejet, numero_normalise: str | None) -> "ResultatValidation":
        return ResultatValidation(conforme=False, numero_normalise=numero_normalise, motif=motif)
