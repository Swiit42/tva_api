"""Constantes de configuration partagées entre le client VIES, la
campagne et l'API.

FRAICHEUR_JOURS = 30 : décision validée avec le commanditaire (compromis
entre détecter rapidement une radiation et ne pas re-vérifier à chaque
facture d'un client récurrent).
"""

from __future__ import annotations

FRAICHEUR_JOURS = 30

VIES_URL_TEMPLATE = "https://ec.europa.eu/taxation_customs/vies/rest-api/ms/{pays}/vat/{numero}"
VIES_TIMEOUT_SECONDES = 10.0
