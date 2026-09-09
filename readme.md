# Vérification TVA intracommunautaire — Meridian Distribution

Mini-brief de data engineering (2 jours) : vérifier la validité des numéros
de TVA intracommunautaire du référentiel client de Meridian Distribution,
en distinguant explicitement trois états — **valide**, **invalide**,
**indéterminé** — plutôt que de confondre "VIES injoignable" avec
"invalide".

## Stack technique

- **Python 3.12** — langage imposé par le brief, écosystème riche pour le
  traitement de données (pandas) et les API (FastAPI).
- **PostgreSQL 16** (via Docker) — base relationnelle pour le référentiel ;
  suffisant pour ce volume (10 000 lignes) et permet des requêtes
  d'agrégation simples pour le rapport de réconciliation.
- **psycopg2** — driver PostgreSQL utilisé en SQL brut (pas d'ORM) : les
  requêtes sont explicites, ce qui facilite la défense du modèle de
  données et de la logique de chargement à l'oral.
- **FastAPI** — API REST imposée par le brief, appelée par la
  facturation avant chaque émission hors taxe.
- **httpx** — client HTTP vers l'API REST VIES (synchrone, simple à
  raisonner pour une campagne séquentielle avec temporisation).
- **Docker / docker-compose** — isole PostgreSQL sans installation locale.
- **pytest** — tests unitaires (module de validation structurelle,
  pipeline, client VIES, API) : 67 tests, aucun ne nécessite le réseau
  ni une base démarrée (les scripts de chargement/campagne/rapports, eux,
  sont démontrés en conditions réelles, cf. plus bas).

Voir aussi [note_architecture.md](note_architecture.md) (décisions et
chiffrage) et [journal.md](journal.md) (déroulé jour par jour).

## Structure du dépôt

```
data/                        jeu de données fourni (10 000 lignes, CSV + Excel)
db/schema.sql                schéma PostgreSQL (référentiel + cache VIES + tentatives)
src/tva_validation/
  normalize.py                nettoyage générique d'un numéro brut
  countries/                  un validateur par pays (format + clé de contrôle)
  models.py                   ResultatValidation, taxonomie des motifs de rejet
  pipeline.py                 normalisation -> dispatch pays -> clé de dédoublonnage
  db.py                       connexion PostgreSQL (lit DATABASE_URL)
  config.py                   constantes partagées (fraîcheur, URL VIES...)
  vies_client.py               appel VIES + interprétation userError -> verdict
  verdicts_cache.py            lecture/écriture du cache de verdicts fermes
  campagne.py                  campagne échantillon, temporisation, reprise
  api.py                       API FastAPI (contrat verdict + origine + fraîcheur)
scripts/
  charger_referentiel.py      commande unique de chargement (upsert, idempotent)
  rapport_motifs.py           répartition par motif + appels VIES évités
  lancer_campagne.py          CLI de la campagne de vérification VIES
  rapport_reconciliation.py   rapport final (une commande)
tests/                        tests pytest (module de validation, pipeline, VIES, API)
note_architecture.md          décisions et chiffrage (une page)
journal.md                    journal de bord jour par jour
```

## Lancer le projet depuis zéro

```bash
git clone <url-du-depot>
cd tva_api

python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell : .venv\Scripts\Activate.ps1)
pip install -r requirements.txt

cp .env.example .env            # ou copy sous Windows
docker compose up -d            # démarre PostgreSQL sur le port 5435

python scripts/charger_referentiel.py   # charge les 10 000 lignes (idempotent)
python scripts/rapport_motifs.py        # répartition par motif + chiffrage VIES

pytest                                  # 67 tests

python scripts/lancer_campagne.py --echantillon 200   # campagne VIES (mode échantillon)
python scripts/rapport_reconciliation.py               # rapport final (une commande)

uvicorn tva_validation.api:app --app-dir src --reload  # API sur http://127.0.0.1:8000
```

## Où en est le pipeline (Phase 1)

Ordre imposé et respecté : **normaliser → dédupliquer → filtrer sur la
structure → (Phase 2) interroger VIES**.

1. **Normalisation** (`normalize.py`) : espaces, tirets, points retirés ;
   valeurs vides détectées sous toutes leurs formes (`""`, `"-"`, `"N/A"`,
   `"null"`, y compris avec du bruit interne comme `"NU.LL"`).
2. **Validation structurelle par pays** (`countries/`) : les 10 pays
   couverts par le référentiel (BE, DK, FI, FR, IT, LU, NL, PL, PT, SE)
   ont chacun leur format et leur clé de contrôle, recherchés et vérifiés
   indépendamment (voir les sources citées en commentaire de chaque
   fichier). Les 5 codes hors périmètre (`ZZ`, `QQ`, `XX`, `GB`, `UK`)
   sont rejetés sans jamais être transmis à VIES (VIES ne les couvre pas).
3. **Dédoublonnage** : la clé `pays_declare:numero_normalise` identifie un
   numéro réel unique. Aucune ligne du référentiel n'est supprimée (on
   garde la traçabilité de chaque saisie), mais un seul appel VIES sera
   fait par clé unique en Phase 2.

Résultat sur les 10 000 lignes (reproductible via
`python scripts/rapport_motifs.py`) :

| Motif | Lignes | % |
|---|---:|---:|
| conforme | 6 615 | 66,15% |
| cle_controle_invalide | 1 306 | 13,06% |
| longueur_invalide | 726 | 7,26% |
| format_invalide | 537 | 5,37% |
| pays_hors_perimetre | 519 | 5,19% |
| valeur_absente | 261 | 2,61% |
| cle_controle_impossible | 36 | 0,36% |

**Impact sur les appels VIES** : sur 10 000 lignes, seuls **6 302 numéros
uniques** doivent réellement être interrogés sur VIES — soit **3 698
appels évités (36,98%)** grâce au filtrage structurel et au
dédoublonnage, avant même de lancer la campagne de vérification en ligne
(Phase 2).

## Phase 2 — VIES en direct, campagne, API

Tests manuels sur l'endpoint REST VIES fourni (réponse JSON lue en
entier avant tout code) : découverte, non cherchée, que FR et BE
renvoient parfois `isValid: false` avec `userError: "MS_MAX_CONCURRENT_REQ"`
(administration surchargée, VIES n'a rien vérifié). D'où la règle
retenue : **c'est `userError` qui pilote le verdict, jamais `isValid`
seul** (détails et mapping complet dans `vies_client.py` et la note
d'architecture).

**Campagne** (`scripts/lancer_campagne.py`) : mode échantillon par
défaut, temporisation entre appels, journalisation (`logs/campagne_vies.log`),
reprise sur interruption — testée en conditions réelles (campagne
interrompue deux fois de suite, reprise exacte sans redémarrer à zéro ni
retirer un nouvel échantillon).

**API** (`src/tva_validation/api.py`) : `GET /verification-tva/{pays}/{numero}`
renvoie toujours `verdict` + `origine` + `fraicheur` :

```bash
curl http://127.0.0.1:8000/verification-tva/PT/500697256
# {"pays_declare":"PT","numero_tva":"PT500697256","verdict":"valide",
#  "origine":"appel_frais","fraicheur":"...","motif":null}
```

| Origine | Signifie |
|---|---|
| `structurel` | rejeté avant tout appel VIES (certitude mathématique/périmètre) |
| `cache` | verdict ferme connu, encore frais (< 30 jours) |
| `appel_frais` | VIES vient de répondre fermement |
| `cache_perime` | VIES injoignable, on sert un verdict ferme connu mais périmé |
| `vies_injoignable_sans_cache` | VIES injoignable, rien en cache → `indetermine`, jamais `invalide` par défaut |

## Décisions validées avec le commanditaire

**Phase 1**
- Les motifs de rejet structurel (`cle_controle_invalide`,
  `longueur_invalide`, `format_invalide`, `cle_controle_impossible`,
  `valeur_absente`, `pays_hors_perimetre`) sont des certitudes
  mathématiques ou de périmètre : verdict **invalide** direct, sans appel
  VIES. Le verdict **indéterminé** est réservé exclusivement aux cas où
  VIES est injoignable — jamais à un rejet structurel.
- Un doublon est défini par la clé `(pays_declare, numero_normalise)`.
  Toutes les lignes du référentiel sont conservées ; seul l'appel VIES
  est mutualisé par clé unique.

**Phase 2**
- Un verdict ferme (valide/invalide) reste valable **30 jours**.
- Si VIES est injoignable et qu'un verdict ferme périmé existe, on le
  sert quand même, marqué `cache_perime` avec sa vraie date — jamais
  perdu à cause d'une panne ponctuelle de VIES.

## Auteur

Sacha Tymoshenko
