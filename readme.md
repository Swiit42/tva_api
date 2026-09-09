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
- **FastAPI** (Phase 2) — API REST imposée par le brief.
- **Docker / docker-compose** — isole PostgreSQL sans installation locale.
- **pytest** — tests unitaires du module de validation structurelle
  (53+ tests : un cas conforme et au moins un cas invalide par pays).

## Structure du dépôt

```
data/                       jeu de données fourni (10 000 lignes, CSV + Excel)
db/schema.sql               schéma PostgreSQL du référentiel
src/tva_validation/
  normalize.py               nettoyage générique d'un numéro brut
  countries/                 un validateur par pays (format + clé de contrôle)
  models.py                  ResultatValidation, taxonomie des motifs de rejet
  pipeline.py                normalisation -> dispatch pays -> clé de dédoublonnage
  db.py                      connexion PostgreSQL (lit DATABASE_URL)
scripts/
  charger_referentiel.py     commande unique de chargement (upsert, idempotent)
  rapport_motifs.py          répartition par motif + appels VIES évités
tests/                       tests pytest (module de validation + pipeline)
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

pytest                                  # 58 tests (module de validation structurelle)
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

## Décisions validées avec le commanditaire (Phase 1)

- Les motifs de rejet structurel (`cle_controle_invalide`,
  `longueur_invalide`, `format_invalide`, `cle_controle_impossible`,
  `valeur_absente`, `pays_hors_perimetre`) sont des certitudes
  mathématiques ou de périmètre : verdict **invalide** direct, sans appel
  VIES. Le verdict **indéterminé** est réservé exclusivement aux cas où
  VIES est injoignable (Phase 2) — jamais à un rejet structurel.
- Un doublon est défini par la clé `(pays_declare, numero_normalise)`.
  Toutes les lignes du référentiel sont conservées ; seul l'appel VIES
  est mutualisé par clé unique.

## Auteur

Sacha Tymoshenko
