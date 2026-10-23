# PROGRESS — Audit et corrections SIPTorch

Suivi de l'audit de SIPTorch (suite de tests de torture SIP, RFC 4475) et des corrections apportées.
Branche d'intégration : `develop`. `master` n'a pas été modifiée.

Branches :
- `master` : code d'origine (`cb956ba`), inchangé.
- `develop` : `master` + l'ensemble des corrections, fusionnées par le commit de merge `6208ee5`.
- `claude/amazing-fermat-qsvn2o` : ancienne branche de travail, entièrement contenue dans `develop`. **À supprimer à la main sur GitHub** : la suppression est refusée (403) par la politique réseau de la session Claude.

Dernière mise à jour : 2026-10-23.

## État actuel

- 48 modules, tous comparés aux messages de référence de la RFC 4475 (annexe A).
- Sur le défaut testé : **48 conformes, 0 partiel, 0 non conforme**. 2 cas de la RFC (wsinv, intmeth) n'ont toujours pas de module.
- **Aucune vérification contre un vrai serveur SIP.** Tout a été validé hors réseau : génération des messages et comparaison à la référence.
- **L'outil n'est pas utilisable sur une plateforme de production** : il laisse des appels fantômes (voir P1).

## Fait

| Commit | Contenu |
|---|---|
| `1c8cfb5` | **Contact** : adresse de l'outil au lieu de celle de la cible.<br>**Content-Type** : `application/sdp` quand l'INVITE porte du SDP ; en-tête retiré si le corps est vide.<br>**SDP** : `o=` et `c=` sur l'IP de l'outil.<br>**Via** : IP source réelle, plus `127.0.0.1` (`getSourceHost()`).<br>**Bind** : `0.0.0.0:LPORT` effectué avant l'envoi (`'any'` était invalide).<br>**Échappement** : `urlEncodeStrValid` réparé (cassait esc01). |
| `36258b9` | Alignement des 10 tests non conformes sur leur référence RFC : cparam1, cparam2, escnull, lwsdp, novelscm, badbranch, reginvct, invsdp, insuf, mpmime.<br>`Content-Length` compté en octets UTF-8 et non plus en caractères. |
| `fcb09e6` | `reginvct` construit son propre Contact. Corrige une régression introduite par `36258b9` : plantage quand le module est lancé seul. |
| `54fc279` | Les 6 tests partiels ou non conformes restants alignés sur la RFC (lwsstart, multicl, bigcode, escinv, unksm2, noreason) ; Record-Route ajouté à inv2543. |
| `da23827` | **Point 2** : `DEF_HSET` copié à chaque requête, plus aucun état partagé entre tests. Les REGISTER reçoivent leur propre Contact (`<sip:<extension>@<IP source>:<LPORT>>`). |

| `6208ee5` | Merge de la branche de travail dans `develop`. |

### Vérifications effectuées

Méthode commune : messages générés hors réseau avec une graine aléatoire fixe, dans l'ordre réel de `runAll`, puis comparés avant/après chaque commit et aux messages de référence de l'annexe A.

- `36258b9` et `fcb09e6` : seuls les 10 modules visés changent, les 38 autres sont identiques octet pour octet (hors en-tête `Date`). La régression de `reginvct` (plantage en exécution isolée) a été détectée puis corrigée par `fcb09e6`.
- `54fc279` : seuls les 7 modules visés changent. Le défaut RFC de chacun est vérifié par assertion explicite sur 200 graines différentes : 200/200 pour les 7.
- `da23827` : seule la partie utilisateur du Contact de 6 REGISTER change. Comparaison à l'annexe A identique ligne pour ligne. Les 48 modules lancés seuls ne plantent plus et produisent le même message qu'en exécution complète, ce qui prouve qu'aucun état ne fuit plus.
- Les scripts de vérification et les messages de référence extraits ne sont **pas** dans le dépôt : ils étaient dans le répertoire temporaire de la session. Pour les reproduire, extraire l'archive base64 (tar.gz) de l'annexe A de la RFC, générer les messages en remplaçant `pluginbase` par un module vide, puis comparer ligne de départ et en-têtes ciblés.

## Reste à faire

### P1 — Résultats faussés ou risque d'exploitation

- [ ] **Appels fantômes.** Aucun CANCEL sur 1xx, ni ACK sur réponse finale, ni BYE sur 2xx. Le socket est fermé après la 1ʳᵉ ou la 2ᵉ réponse, ce qui laisse sonneries et transactions pendantes. Envoient un INVITE : insuf, invct, invsdp, multireq, inv2543, baddate, balquote, clerr, escuri, exthdsep, intwdcl, ltgtrequri, lwsstart, lwsuri, negcl, escvalid, longreq.
- [ ] **Aucun verdict.** La première réponse reçue est loggée sans être comparée au comportement attendu par la RFC. À faire : ajouter `rfc`, `ref` et `expect` (par rôle : proxy, UAS, registrar) dans `module_info`, puis évaluer réussi/échoué.
- [ ] **Réponses envoyées comme si c'étaient des requêtes** (bcast, bigcode, respsclarg, noreason, unreason). Un UAS les jette sans répondre, ce qui donne un timeout présenté comme un incident serveur. L'absence de réponse doit être le résultat attendu, et ces tests n'ont de sens que contre un proxy.
- [ ] **`checkBadResponse`** : `BAD_RESP = ['100','182','486','600']` traite des réponses finales (486, 600) comme des provisoires, alors que 180 et 183 sont absents. Une seule réponse supplémentaire est attendue.
- [ ] **Validation de la cible en TCP** (`utils.lookUp`) alors que l'outil parle UDP : faux négatif sur un serveur UDP seul.

### P2 — Robustesse

- [x] **Dictionnaire d'en-têtes partagé** : corrigé, copie de `DEF_HSET` à chaque requête et Contact propre aux REGISTER. Seul effet sur les messages : la partie utilisateur du Contact de 6 REGISTER (cparam1, cparam2, dblreq, regeschd, reqsclarg, unkauth) devient l'extension au lieu d'un utilisateur hérité du test précédent.
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

- [x] Tests partiels/non conformes rendus conformes (2026-10-23) :
  - lwsstart : exactement deux SP entre les éléments de la Request-Line (plus de tirage TAB/Unicode).
  - multicl : corps texte encadré par deux Content-Length en conflit (13 et 5) + `Content-Type: text/plain`.
  - bigcode : code `2**32 + 5`, qui retombe sur 5 en entier 32 bits (le débordement visé).
  - escinv : deux vrais Contact encadrant un nom d'en-tête échappé, + `%` non-échappement dans le branch du Via.
  - unksm2 : To avec le scheme enregistré `isbn:`.
  - noreason : réponse 100 sans corps.
  - inv2543 : ajout du `Record-Route` présent dans le message de référence.
- [ ] Reste des valeurs tirées au hasard, de même nature que la RFC (non bloquant) : méthode et header échappés de escinv, méthode inconnue de metmatch, noms d'en-tête longs de longreq. intwdcl utilise la variante « Content-Length non numérique » explicitement citée par la RFC §3.1.2.3.
- [ ] mpmime : la partie binaire n'est pas bit-exacte (265 octets contre 342 dans la référence). Le module décode le blob en UTF-8 avec `errors='ignore'`, ce qui supprime des octets. Le défaut testé reste présent (octets 0x00 dans la partie binaire, Content-Length exact). Pour le corriger, il faut faire transiter le message en octets bruts dans `buildreq`, `concatMethodxHeaders` et `connector`.
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
