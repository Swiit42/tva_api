# Journal de bord

## Jour 1 — Cadrage, module de validation structurelle, chargement

- Exploration du CSV (10 000 lignes) : 10 pays confirmés (BE, DK, FI, FR,
  IT, LU, NL, PL, PT, SE) sur 9 481 lignes ; 519 lignes hors périmètre
  (`ZZ`, `QQ`, `XX`, `GB`, `UK`) ; aucun préfixe `XI` (pas de cas
  particulier Irlande du Nord) ; 260-261 valeurs vides sous 4 formes
  différentes ; 24 à 29 formats bruts distincts par pays.
- Exploration des doublons (normalisation grossière) : 396 numéros
  dupliqués, 834 lignes concernées, **aucun** cas de deux raisons
  sociales différentes pour le même numéro — confirme que ce sont de
  vraies ré-saisies, pas des collisions.
- **Décision validée** : les codes hors périmètre sont rejetés
  structurellement, jamais transmis à VIES (VIES ne les couvre pas).
- Recherche pays par pays des algorithmes de clé de contrôle (sources
  croisées, voir commentaires de chaque fichier `countries/*.py`).
  Erreur trouvée et corrigée en vérifiant par calcul indépendant :
  l'exemple FR communément cité en ligne (FR23123456789) est
  arithmétiquement faux pour le SIREN 123456789 ; la bonne clé est 32,
  pas 23.
- Construction du module (normalisation → dispatch pays → validateur) et
  de 63 tests (un cas conforme + au moins un cas invalide par pays, y
  compris les cas "clé impossible" pour FI/NL/PL).
- Exécution sur les 10 000 lignes : 66,15 % conformes, distribution des 6
  motifs de rejet mesurée.
- **Décision validée** : tous les motifs non-conformes sont des rejets
  directs (verdict "invalide", jamais d'appel VIES) — ce sont des
  certitudes mathématiques, pas des incertitudes.
- **Décision validée** : un doublon = clé `(pays_declare,
  numero_normalisé)`. Aucune ligne supprimée du référentiel ; un seul
  appel VIES sera fait par clé, mutualisé.
- Chargement en PostgreSQL (upsert sur `id`, vérifié idempotent par
  rechargement à blanc) : 10 000 lignes, 6 615 conformes, 6 302 numéros
  uniques à vérifier sur VIES (3 698 appels évités, 36,98 %).
- 3 commits Git (module de validation, chargement DB + rapport).

## Jour 2 — VIES en direct, campagne, API, réconciliation

- Tests manuels de l'API VIES (endpoint REST fourni) : réponse JSON
  complète lue en entier avant tout code. Découverte en direct que FR et
  BE renvoyaient `isValid: false` avec `userError: "MS_MAX_CONCURRENT_REQ"`
  (administration surchargée) — preuve concrète, non cherchée, que
  `isValid` seul ne suffit pas.
- Mesure de temps (10 appels séquentiels ≈ 1,0 s/appel) et extrapolation :
  sans filtrage Phase 1, une campagne complète prendrait ≈ 2 h 47.
- **Décisions validées** : fraîcheur d'un verdict = 30 jours ; en cas de
  VIES injoignable avec un cache périmé disponible, on sert ce cache
  périmé (marqué comme tel) plutôt que de perdre l'information.
- Construction du client VIES (`userError` pilote le verdict, jamais
  `isValid` seul) avec tests sur les réponses réelles capturées.
- Construction de la campagne (mode échantillon, temporisation,
  journalisation, reprise sur interruption). Reprise démontrée en
  conditions réelles : campagne de 5 numéros interrompue deux fois de
  suite (timeout forcé), reprise exacte à chaque relance, jamais de
  redémarrage à zéro ni de ré-échantillonnage.
- Construction de l'API (`/verification-tva/{pays}/{numero}`) : contrat
  verdict + origine + fraîcheur. Les 4 chemins testés en conditions
  réelles : `cache`, `appel_frais`, `cache_perime` (VIES injoignable
  simulé + cache périmé), `vies_injoignable_sans_cache` (VIES injoignable
  simulé + rien en cache).
- Rapport de réconciliation (une commande) combinant structurel + cache
  VIES : verdicts finaux, motifs, doublons, indéterminés déjà tentés vs
  jamais soumis.
