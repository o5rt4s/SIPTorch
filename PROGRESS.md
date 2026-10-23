# PROGRESS — Audit et corrections SIPTorch

Suivi de l'audit de SIPTorch (suite de tests de torture SIP, RFC 4475) et des corrections apportées.
Branche de travail : `claude/amazing-fermat-qsvn2o`.

Dernière mise à jour : 2026-10-23.

## État actuel

- 48 modules, tous comparés aux messages de référence de la RFC 4475 (annexe A).
- Sur le défaut testé : 42 conformes, 6 partiels, 0 non conforme. 2 cas de la RFC n'ont pas de module.
- **Aucune vérification contre un vrai serveur SIP.** Tout a été validé hors réseau : génération des messages et comparaison à la référence.
- **L'outil n'est pas utilisable sur une plateforme de production** : il laisse des appels fantômes (voir P1).

## Fait

| Commit | Contenu |
|---|---|
| `1c8cfb5` | **Contact** : adresse de l'outil au lieu de celle de la cible.<br>**Content-Type** : `application/sdp` quand l'INVITE porte du SDP ; en-tête retiré si le corps est vide.<br>**SDP** : `o=` et `c=` sur l'IP de l'outil.<br>**Via** : IP source réelle, plus `127.0.0.1` (`getSourceHost()`).<br>**Bind** : `0.0.0.0:LPORT` effectué avant l'envoi (`'any'` était invalide).<br>**Échappement** : `urlEncodeStrValid` réparé (cassait esc01). |
| `36258b9` | Alignement des 10 tests non conformes sur leur référence RFC : cparam1, cparam2, escnull, lwsdp, novelscm, badbranch, reginvct, invsdp, insuf, mpmime.<br>`Content-Length` compté en octets UTF-8 et non plus en caractères. |
| `fcb09e6` | `reginvct` construit son propre Contact. Corrige une régression introduite par `36258b9` : plantage quand le module est lancé seul. |

### Vérification de non-régression (après `fcb09e6`)

- Génération à graine aléatoire fixe, dans l'ordre réel de `runAll`, avant et après. Seuls les 10 modules visés changent ; les 38 autres messages sont identiques octet pour octet (hors en-tête `Date`).
- Comparaison à l'annexe A : aucun écart ne se dégrade.
- Chaque module lancé seul : plus de nouveau plantage. Les 6 plantages restants existaient avant les corrections (voir P2).
- Les scripts de vérification et les messages de référence extraits ne sont **pas** dans le dépôt : ils étaient dans le répertoire temporaire de la session. Pour les reproduire, extraire l'archive base64 (tar.gz) de l'annexe A de la RFC, générer les messages en remplaçant `pluginbase` par un module vide, puis comparer ligne de départ et en-têtes ciblés.

## Reste à faire

### P1 — Résultats faussés ou risque d'exploitation

- [ ] **Appels fantômes.** Aucun CANCEL sur 1xx, ni ACK sur réponse finale, ni BYE sur 2xx. Le socket est fermé après la 1ʳᵉ ou la 2ᵉ réponse, ce qui laisse sonneries et transactions pendantes. Envoient un INVITE : insuf, invct, invsdp, multireq, inv2543, baddate, balquote, clerr, escuri, exthdsep, intwdcl, ltgtrequri, lwsstart, lwsuri, negcl, escvalid, longreq.
- [ ] **Aucun verdict.** La première réponse reçue est loggée sans être comparée au comportement attendu par la RFC. À faire : ajouter `rfc`, `ref` et `expect` (par rôle : proxy, UAS, registrar) dans `module_info`, puis évaluer réussi/échoué.
- [ ] **Réponses envoyées comme si c'étaient des requêtes** (bcast, bigcode, respsclarg, noreason, unreason). Un UAS les jette sans répondre, ce qui donne un timeout présenté comme un incident serveur. L'absence de réponse doit être le résultat attendu, et ces tests n'ont de sens que contre un proxy.
- [ ] **`checkBadResponse`** : `BAD_RESP = ['100','182','486','600']` traite des réponses finales (486, 600) comme des provisoires, alors que 180 et 183 sont absents. Une seule réponse supplémentaire est attendue.
- [ ] **Validation de la cible en TCP** (`utils.lookUp`) alors que l'outil parle UDP : faux négatif sur un serveur UDP seul.

### P2 — Robustesse

- [ ] **Dictionnaire d'en-têtes partagé** : `headers = DEF_HSET` sans copie dans `buildreq.makeRequest`, si bien que l'état fuit d'un test à l'autre. Les REGISTER récupèrent le Contact du test précédent. cparam1, cparam2, escinv, escnull, regeschd et reqsclarg plantent quand ils sont lancés seuls ; ils passent en exécution complète.
- [ ] `connector.sendreq` découpe une `str` avec un nombre d'octets : corruption au-delà de 8192 octets en UTF-8.
- [ ] `utils.extractExtension` : `re.compile(motif, addr, re.I)` plante toujours, donc l'option `-F/--from-addr` est inutilisable.
- [ ] `parser.parseSIPMessage` : `split('\r\n\r\n')` sans maxsplit, d'où une `ValueError` si le corps contient une ligne vide.
- [ ] `from libs.config import *` dans `buildreq` : les globales sont capturées par valeur à l'import.
- [ ] `connector.handler` : après le timeout de `select`, un `recvfrom` bloquant attend un second `TIMEOUT`, ce qui double le délai.
- [ ] `options.py` : condition `not (version and build_cache)` qui devrait être `or`, parsing argparse exécuté à l'import, fonctions mortes (`fileWriter`, `readHeader`).
- [ ] `requirements.txt` : `pluginbase` non épinglé, et son build échoue sous Python 3.13 dans l'environnement de test.
- [ ] `libs/data.py` : séquence d'échappement invalide `'\ '` dans l'ASCII art (`SyntaxWarning` sous Python ≥ 3.12).
- [ ] UDP uniquement : longreq et mpmime dépassent 1300 octets (RFC 3261 §18.1.1), et TCP n'est pas implémenté.

### P3 — Fidélité RFC 4475

- [ ] Tests partiels :
  - esc02/escinv : un seul vrai Contact au lieu de deux ;
  - mcl01/multicl : ni corps ni `Content-Type: text/plain` ;
  - bigcode : code tiré au hasard sur 32 bits, au lieu de 2³²+5 (débordement) ;
  - unksm2 : schemes aléatoires non enregistrés ;
  - lwsstart : non déterministe (SP ou espace Unicode selon le tirage) ;
  - noreason : le 100 porte un corps SDP.
- [ ] Tests absents : wsinv (§3.1.1.1), dont la config `EXT_HEADERS` est prévue mais inutilisée, et intmeth (§3.1.1.2).
- [ ] Libellés `module_info['test']` erronés :
  - `noreason` est intitulé « Content Length Larger Than Message » au lieu de « Empty Reason Phrase » ;
  - `trws` est intitulé « Escaped Headers in SIP Request-URI » au lieu de « SP Characters at End of Request-Line ».

## Correspondance modules ↔ RFC 4475

| § | Réf. | Module | | § | Réf. | Module |
|---|---|---|---|---|---|---|
| 3.1.1.1 | wsinv | — | | 3.1.2.11 | escruri | escuri |
| 3.1.1.2 | intmeth | — | | 3.1.2.12 | baddate | baddate |
| 3.1.1.3 | esc01 | escvalid | | 3.1.2.13 | regbadct | reginvct |
| 3.1.1.4 | escnull | escnull | | 3.1.2.14 | badaspec | spacaddr |
| 3.1.1.5 | esc02 | escinv | | 3.1.2.15 | baddn | invdisp |
| 3.1.1.6 | lwsdisp | lwsdp | | 3.1.2.16 | badvers | unkproto |
| 3.1.1.7 | longreq | longreq | | 3.1.2.17 | mismatch01 | cseqmatch |
| 3.1.1.8 | dblreq | dblreq | | 3.1.2.18 | mismatch02 | metmatch |
| 3.1.1.9 | semiuri | semiuri | | 3.1.2.19 | bigcode | bigcode |
| 3.1.1.10 | transports | transports | | 3.2.1 | badbranch | badbranch |
| 3.1.1.11 | mpart01 | mpmime | | 3.3.1 | insuf | insuf |
| 3.1.1.12 | unreason | unreason | | 3.3.2 | unkscm | unkscm |
| 3.1.1.13 | noreason | noreason | | 3.3.3 | novelsc | novelscm |
| 3.1.2.1 | badinv01 | exthdsep | | 3.3.4 | unksm2 | unksm2 |
| 3.1.2.2 | clerr | clerr | | 3.3.5 | bext01 | reqpreq |
| 3.1.2.3 | ncl | negcl, intwdcl | | 3.3.6 | invut | invct |
| 3.1.2.4 | scalar02 | reqsclarg | | 3.3.7 | regaut01 | unkauth |
| 3.1.2.5 | scalarlg | respsclarg | | 3.3.8 | multi01 | multireq |
| 3.1.2.6 | quotbal | balquote | | 3.3.9 | mcl01 | multicl |
| 3.1.2.7 | ltgtruri | ltgtrequri | | 3.3.10 | bcast | bcast |
| 3.1.2.8 | lwsruri | lwsuri | | 3.3.11 | zeromf | mfzero |
| 3.1.2.9 | lwsstart | lwsstart | | 3.3.12 | cparam01 | cparam1 |
| 3.1.2.10 | trws | trws | | 3.3.13 | cparam02 | cparam2 |
| | | | | 3.3.14 | regescrt | regeschd |
| | | | | 3.3.15 | sdp01 | invsdp |
| | | | | 3.4.1 | inv2543 | inv2543 |

## Correction d'un constat antérieur

L'audit initial signalait `Route: <sip:127.0.0.1:5080>` dans mpmime comme absent de la RFC. C'est faux : cet en-tête figure dans le message de référence mpart01. Ce n'est pas un écart à la RFC. L'effet reste à garder en tête en exploitation : un proxy qui applique le loose routing contactera son propre loopback.
