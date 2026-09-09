-- Schéma du référentiel TVA.
--
-- Une ligne = une ligne du CSV source, jamais fusionnée avec une autre :
-- on ne perd aucune trace de qui a saisi quoi, quand, même si plusieurs
-- lignes finissent par pointer vers le même numéro réel (cf. cle_dedup).
--
-- Le schéma distingue explicitement (exigence du brief) :
--   - la valeur brute reçue          -> numero_tva_brut
--   - la valeur normalisée           -> numero_tva_normalise
--   - le verdict structurel + motif  -> conforme_structurel / motif_structurel
--
-- cle_dedup identifie un numéro réel unique (pays + numéro normalisé),
-- indépendamment du nombre de lignes qui le référencent. C'est sur cette
-- clé que la campagne VIES (Phase 2) ne fera qu'un seul appel, même si
-- 6 lignes du référentiel partagent le même numéro (cf. décision prise
-- en Phase 1 : on ne supprime aucune ligne, on mutualise le verdict).

CREATE TABLE IF NOT EXISTS referentiel (
    id                     INTEGER PRIMARY KEY,        -- id du CSV source : clé naturelle, sert à l'upsert
    raison_sociale         TEXT NOT NULL,
    pays_declare           TEXT NOT NULL,
    numero_tva_brut        TEXT NOT NULL,               -- valeur telle que reçue, sans aucune transformation
    numero_tva_normalise   TEXT,                        -- NULL si valeur_absente (rien à normaliser)
    date_saisie            DATE NOT NULL,
    source_saisie          TEXT NOT NULL,
    conforme_structurel    BOOLEAN NOT NULL,
    motif_structurel       TEXT,                        -- NULL si conforme_structurel = TRUE
    cle_dedup              TEXT,                        -- pays_declare || ':' || numero_tva_normalise, NULL si numero_tva_normalise IS NULL
    charge_le              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Une requête "répartition par motif" ou "combien d'appels VIES évités"
-- scanne par motif_structurel / cle_dedup : ces index évitent un scan
-- complet de la table à chaque exécution du rapport.
CREATE INDEX IF NOT EXISTS idx_referentiel_motif      ON referentiel (motif_structurel);
CREATE INDEX IF NOT EXISTS idx_referentiel_cle_dedup  ON referentiel (cle_dedup);
CREATE INDEX IF NOT EXISTS idx_referentiel_pays       ON referentiel (pays_declare);

-- Phase 2 : cache des verdicts VIES *fermes* (valide/invalide uniquement).
-- Un verdict "indéterminé" n'est jamais écrit ici : ce n'est pas un fait
-- stable, donc pas quelque chose qu'on doit mettre en cache comme tel
-- (cf. note d'architecture). C'est cette table qui rend le "un seul appel
-- VIES par numéro unique" possible : la clé primaire est cle_dedup, pas
-- l'id d'une ligne du référentiel.
--
-- verifie_le fait à la fois office de fraîcheur (durée de validité
-- décidée : 30 jours, cf. note d'architecture) et de trace du dernier
-- verdict ferme connu, y compris quand il est devenu périmé (on ne
-- l'écrase jamais tant qu'on n'a pas obtenu un NOUVEAU verdict ferme).
CREATE TABLE IF NOT EXISTS verdicts_vies (
    cle_dedup              TEXT PRIMARY KEY,
    pays_declare           TEXT NOT NULL,
    numero_tva_normalise   TEXT NOT NULL,
    verdict                TEXT NOT NULL CHECK (verdict IN ('valide', 'invalide')),
    user_error_vies        TEXT NOT NULL,               -- champ brut VIES ("VALID", "INVALID"...), utile en soutenance
    nom_vies                TEXT,
    adresse_vies            TEXT,
    verifie_le              TIMESTAMPTZ NOT NULL
);

-- Journal de chaque tentative d'appel VIES, y compris les indéterminés.
-- Sert à la fois de journalisation (brief) et de mécanisme de reprise :
-- une campagne interrompue relance avec le même run_id, et
-- (run_id, cle_dedup) déjà présent = déjà traité, on ne le refait pas.
CREATE TABLE IF NOT EXISTS tentatives_vies (
    id               SERIAL PRIMARY KEY,
    run_id           TEXT NOT NULL,
    cle_dedup        TEXT NOT NULL,
    tente_le         TIMESTAMPTZ NOT NULL DEFAULT now(),
    verdict          TEXT NOT NULL CHECK (verdict IN ('valide', 'invalide', 'indetermine')),
    user_error_vies  TEXT,                              -- NULL si échec réseau (timeout, DNS...) plutôt qu'une réponse VIES
    duree_ms         INTEGER NOT NULL,
    UNIQUE (run_id, cle_dedup)
);

CREATE INDEX IF NOT EXISTS idx_tentatives_run ON tentatives_vies (run_id);
