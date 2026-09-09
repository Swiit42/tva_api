"""Pipeline complet de traitement d'une ligne du référentiel brut.

Combine normalisation -> dispatch par pays -> calcul de la clé de
dédoublonnage. C'est la fonction que le script de chargement (et les
tests d'intégration) appellent pour transformer une ligne brute du CSV en
ligne prête à être upsertée en base.
"""

from __future__ import annotations

from dataclasses import dataclass

from .countries import valider_par_pays
from .models import MotifRejet
from .normalize import normaliser_numero_tva


@dataclass(frozen=True)
class LigneTraitee:
    numero_tva_normalise: str | None
    conforme_structurel: bool
    motif_structurel: str | None
    cle_dedup: str | None  # None si numero_tva_normalise est None (valeur_absente)


def traiter_ligne(pays_declare: str, numero_tva_brut: str) -> LigneTraitee:
    numero_normalise = normaliser_numero_tva(numero_tva_brut)

    if numero_normalise is None:
        return LigneTraitee(
            numero_tva_normalise=None,
            conforme_structurel=False,
            motif_structurel=MotifRejet.VALEUR_ABSENTE.value,
            cle_dedup=None,
        )

    resultat = valider_par_pays(pays_declare, numero_normalise)

    # Le validateur pays reconstruit le numéro complet avec son préfixe
    # (utile quand le préfixe manquait dans la saisie d'origine) : c'est
    # cette forme canonique qui sert de base à la clé de dédoublonnage,
    # pour que deux lignes du même numéro, avec ou sans préfixe, partagent
    # bien la même clé.
    numero_canonique = resultat.numero_normalise or numero_normalise
    cle_dedup = f"{pays_declare}:{numero_canonique}"

    return LigneTraitee(
        numero_tva_normalise=numero_canonique,
        conforme_structurel=resultat.conforme,
        motif_structurel=None if resultat.conforme else resultat.motif.value,
        cle_dedup=cle_dedup,
    )
