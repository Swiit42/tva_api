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
