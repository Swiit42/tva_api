# Note d'architecture — Vérification TVA intracommunautaire

## Le problème central : trois états, pas deux

La question n'est pas "ce numéro est-il valide ?" mais "peut-on facturer
hors taxe en confiance ?". Un numéro peut être **valide**, **invalide**,
ou **indéterminé** — et confondre "indéterminé" avec "invalide" a un
coût réel (refuser une exonération légitime) tout comme confondre
"indéterminé" avec "valide" (l'incident qui a motivé ce projet). L'API
ne renvoie donc jamais un simple booléen : toujours un triplet
**verdict + origine + fraîcheur**.

## Réduire les appels VIES avant de les faire (Phase 1)

Ordre imposé : normaliser → dédupliquer → filtrer sur la structure →
seulement ensuite interroger VIES. Sur les 10 000 lignes du référentiel :

| Étape | Lignes restantes | Appels VIES évités |
|---|---:|---:|
| Brut | 10 000 | — |
| Après filtre structurel (10 validateurs pays, algorithmes sourcés) | 6 615 conformes | 3 385 |
| Après dédoublonnage (clé `pays_declare:numero_normalisé`) | 6 302 numéros uniques | 313 de plus |
| **Total évité** | | **3 698 (36,98 %)** |

Les motifs de rejet structurel (`cle_controle_invalide`,
`longueur_invalide`, `format_invalide`, `cle_controle_impossible`,
`valeur_absente`, `pays_hors_perimetre`) sont des **certitudes
mathématiques ou de périmètre** : un numéro réellement attribué respecte
toujours le format et la clé de contrôle de son pays. Ces lignes sont
donc classées **invalide** sans jamais interroger VIES — ce n'est pas un
raccourci risqué, c'est la même certitude qui fait que VIES lui-même les
rejette avant recherche (vérifié manuellement : `userError=INVALID` avec
`name="---"` sur une clé de contrôle cassée, contre `name=""` sur un
numéro structurellement valide mais inexistant).

Mesure empirique : ~1,0 s/appel VIES en séquentiel. Sans filtrage,
interroger les 10 000 lignes prendrait ≈ 2 h 47 (hors temporisation,
qu'une campagne réelle doit ajouter pour rester correcte vis-à-vis du
service). Le filtrage n'est donc pas cosmétique : c'est ce qui rend une
campagne complète réalisable dans un temps raisonnable.

## Pourquoi `userError`, jamais `isValid` seul

Découverte en testant manuellement l'API (Phase 2) : VIES a renvoyé, à
deux reprises (FR et BE), `isValid: false` avec
`userError: "MS_MAX_CONCURRENT_REQ"` — l'administration du pays était
surchargée, VIES n'a **rien vérifié du tout**. Un client qui se fierait à
`isValid` aurait classé ces numéros "invalide" à tort. Le mapping retenu :
- `userError == "VALID"` → **valide**
- `userError == "INVALID"` → **invalide**
- tout le reste (surcharge, timeout, service indisponible, erreur
  réseau...) → **indéterminé**, jamais invalide par défaut

## Fraîcheur d'un verdict et cache périmé (décisions validées)

- Un verdict ferme (valide/invalide) reste valable **30 jours** avant
  re-vérification. Compromis entre détecter une radiation récente et ne
  pas re-solliciter VIES à chaque facture d'un client récurrent.
- Un verdict **indéterminé n'est jamais mis en cache** comme un fait
  stable : ce n'est pas un fait, donc rien à figer. Chaque appel retente
  VIES tant qu'aucun verdict ferme n'a été obtenu.
- Si VIES est injoignable et qu'un verdict ferme **périmé** existe, on le
  sert quand même, explicitement marqué `origine="cache_perime"` avec sa
  vraie date — on ne jette jamais une information connue à cause d'une
  panne ponctuelle de VIES. Si VIES est injoignable et qu'**aucun**
  verdict n'existe, la réponse est `indeterminé` /
  `vies_injoignable_sans_cache` — jamais "invalide" par défaut.

## Modèle de données

- `referentiel` : une ligne = une ligne source, jamais fusionnée.
  Distingue explicitement valeur brute / normalisée / verdict structurel
  + motif. La clé de dédoublonnage (`cle_dedup`) identifie un numéro réel
  unique sans supprimer aucune ligne (traçabilité des re-saisies
  multiples conservée).
- `verdicts_vies` : cache des verdicts **fermes** uniquement, clé =
  `cle_dedup`. Un `indéterminé` n'écrase jamais un verdict ferme
  précédent.
- `tentatives_vies` : journal de chaque appel (y compris indéterminés),
  sert aussi de mécanisme de reprise de campagne : `(run_id, cle_dedup)`
  déjà présent = déjà traité, on ne le refait pas au redémarrage.
