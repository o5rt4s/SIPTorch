# PROGRESS — Audit et corrections SIPTorch

Suivi de l'audit de SIPTorch (suite de tests de torture SIP, RFC 4475) et des corrections apportées.

Dernière mise à jour : 2026-10-23 (audit complet refait sur `c55cc1f`).

## Branches

- `master` : code d'origine (`cb956ba`), inchangé.
- `develop` : branche d'intégration, contient toutes les corrections.

## État actuel

- **Messages : conformes.** 50 modules couvrent les 49 messages de la RFC 4475 §3 (intwdcl est la variante « Content-Length non numérique » de ncl, citée au §3.1.2.3). Chaque message reproduit le défaut de son message de référence de l'annexe A ; wsinv et intmeth sont identiques octet pour octet à la référence (seul le sent-by du Via est adapté).
- **Résultats : pas encore fiables.** L'outil ne rend pas de verdict et peut attribuer une réponse au mauvais test (voir P1).
- **Exploitation : à proscrire sur une plateforme de production.** 18 modules envoient un INVITE sans jamais l'annuler ni le terminer.
- Rien n'a été testé contre un vrai serveur SIP : toutes les vérifications ont été faites hors réseau.

## Historique des corrections

| Commit | Contenu |
|---|---|
| `1c8cfb5` | Contact sur l'adresse de l'outil ; `Content-Type: application/sdp` sur les INVITE avec SDP ; `o=`/`c=` du SDP sur l'IP de l'outil ; Via avec l'IP source réelle (`getSourceHost()`) ; bind sur `0.0.0.0:LPORT` avant l'envoi ; `urlEncodeStrValid` réparé. |
| `36258b9` | 10 tests alignés sur leur message de référence (cparam1, cparam2, escnull, lwsdp, novelscm, badbranch, reginvct, invsdp, insuf, mpmime) ; `Content-Length` compté en octets UTF-8. |
| `fcb09e6` | reginvct construit son propre Contact (régression de `36258b9` corrigée). |
| `54fc279` | 6 tests partiels alignés (lwsstart, multicl, bigcode, escinv, unksm2, noreason) ; Record-Route ajouté à inv2543. |
| `da23827` | Dictionnaire d'en-têtes copié à chaque requête (plus d'état partagé entre tests) ; Contact propre aux REGISTER. |
| `6208ee5` | Merge de la branche de travail dans `develop`. |
| `968a498` | Modules wsinv (§3.1.1.1) et intmeth (§3.1.1.2) ajoutés ; libellés de noreason et trws corrigés ; `modules.json` régénéré (50 tests). |
| `e9a0268` | wsinv rendu identique octet pour octet à la référence. |
| `c55cc1f` | Paragraphe RFC et message de référence ajoutés dans `module_info` (`rfc`, `ref`) et dans le rapport Markdown. |

## Vérifications effectuées

Méthode : messages générés hors réseau avec une graine aléatoire fixe, dans l'ordre réel d'exécution, comparés avant/après chaque commit et aux messages de référence de l'annexe A (extraits de l'archive base64 de la RFC).

- Chaque commit de correction : seuls les modules visés changent, tous les autres restent identiques octet pour octet (hors en-tête `Date`).
- `54fc279` : défaut RFC vérifié par assertion explicite sur 200 graines aléatoires pour les 7 modules modifiés (200/200).
- `da23827` : les 50 modules lancés seuls produisent le même message qu'en exécution complète et ne plantent plus.
- wsinv et intmeth : comparaison octet par octet avec la référence, et les caractéristiques listées dans la RFC contrôlées une à une (14 pour wsinv, 10 pour intmeth). Pour intmeth, les octets transmis à `sendto()` ont aussi été vérifiés avec un faux socket.
- `c55cc1f` : rapport complet produit avec un faux transport ; 50 entrées portent leur paragraphe RFC.
- Audit du 2026-10-23 : 50 messages, 0 plantage, identiques à l'état vérifié ; analyse statique (pyflakes) sans nom réellement indéfini.

Les scripts de vérification et les messages de référence extraits ne sont pas dans le dépôt (répertoire temporaire de session). Pour les refaire : extraire l'archive de l'annexe A, générer les messages en remplaçant `pluginbase` par un module vide, comparer ligne de départ et en-têtes ciblés.

## Reste à faire

### P1 — Résultats faussés ou risque d'exploitation

- [ ] **Réponses attribuées au mauvais test** *(nouveau)*. `connector.handler` renvoie le premier datagramme reçu sur `LPORT`, sans vérifier Call-ID, CSeq ni branch. Comme l'outil n'envoie jamais d'ACK, le serveur retransmet ses réponses finales aux INVITE (Timer G, pendant jusqu'à 32 s). Ces retransmissions arrivent pendant les tests suivants, qui réutilisent le même port, et sont enregistrées comme leur réponse.
- [ ] **Appels fantômes.** Aucun CANCEL sur 1xx, ni ACK sur réponse finale, ni BYE sur 2xx. 18 modules envoient un INVITE : baddate, balquote, clerr, escuri, escvalid, exthdsep, insuf, intwdcl, inv2543, invct, invsdp, longreq, ltgtrequri, lwsstart, lwsuri, multireq, negcl, wsinv.
- [ ] **Aucun verdict.** La réponse est loggée sans être comparée au comportement attendu. `rfc` et `ref` sont dans `module_info` ; reste à ajouter `expect` (par rôle : proxy, UAS, registrar) et à évaluer réussi/échoué.
- [ ] **Réponses envoyées comme si c'étaient des requêtes** (bcast, bigcode, noreason, respsclarg, unreason). Un UAS les jette sans répondre : le timeout est alors présenté comme un incident serveur, alors que c'est le résultat attendu.
- [ ] **`checkBadResponse`** : `BAD_RESP = ['100','182','486','600']` traite des réponses finales (486, 600) comme provisoires, sans 180 ni 183, et n'attend qu'une seule réponse de plus.
- [ ] **Pas de retransmission des requêtes en UDP** *(nouveau)* (Timers A/E de RFC 3261) : un seul datagramme perdu donne un timeout présenté comme un incident serveur.
- [x] **Validation de la cible** — corrigée. `utils.validateHost` résout l'IP puis envoie un SIP OPTIONS en UDP (`sipOptionsProbe`) et accepte toute réponse `SIP/2.0` (pas seulement 200 OK : un 405/404/403 prouve aussi la joignabilité). L'ancienne sonde TCP (`lookUp`) est supprimée, ce qui corrige le faux négatif sur serveur UDP seul et le bug `-p` (le port est lu à l'exécution, plus figé à 5060 à l'import). Corrigé ensuite par audit : le Via de la sonde annonce son vrai port local (sinon un serveur sans `rport` répondait sur un port où personne n'écoute), et `-t` est appliqué avant la sonde. Limites connues : une réponse émise depuis une autre IP ou un autre port que celui interrogé (certains SBC ou clusters) est ignorée ; toute réponse `SIP/2.0` est acceptée sans vérifier qu'elle reprend le Call-ID de la sonde.

### P2 — Robustesse

- [x] Dictionnaire d'en-têtes partagé — corrigé (`da23827`).
- [x] Partie utilisateur non-`\w` — corrigé. escvalid plantait (`.group(1)` sur `None`) et escnull/escinv rataient leur substitution en silence dès que l'extension contenait un caractère hors `\w` (ex. une extension E.164 `+33612345678` via `-e`). Les regex ciblent désormais la userpart réelle (`sip:[^@\s]+@`) et le display name quoté (`"[^"]*"`).
- [x] `EADDRINUSE` (Errno 98) en cascade — corrigé. `runPlugin` ne fermait pas le socket si `sendreq`/`handler` levait une erreur : le port local restait lié et tous les tests suivants échouaient au `bind`. Fermeture garantie par `finally` ; `SO_REUSEADDR` ajouté avant le `bind` ; message explicite renvoyant vers `-P/--lport` quand un autre process occupe déjà le port (le bind échoue toujours dans ce cas — `SO_REUSEADDR` n'est pas `SO_REUSEPORT`).
- [ ] `connector.sendreq` découpe une `str` avec un nombre d'octets : corruption au-delà de 8192 octets en UTF-8.
- [ ] `utils.extractExtension` : `re.compile(motif, addr, re.I)` plante toujours, donc l'option `-F/--from-addr` est inutilisable.
- [ ] `parser.parseSIPMessage` : `split('\r\n\r\n')` sans maxsplit, d'où une `ValueError` si le corps contient une ligne vide.
- [ ] `from libs.config import *` dans `buildreq` : valeurs capturées à l'import.
- [ ] `connector.handler` : après le timeout de `select`, un `recvfrom` bloquant attend un second `TIMEOUT`, ce qui double le délai.
- [ ] `options.py` : condition `not (version and build_cache)` qui devrait être `or` ; parsing exécuté à l'import. *Nouveau* : les messages de log émis pendant ce parsing, avant que `startEngine` installe le handler, sont perdus.
- [ ] Code mort *(nouveau)* : 7 mutateurs jamais utilisés (addrheader, convshort, insertbklash, lwsinsert, nullinsert, permcase, randuplow) ; `fileWriter`, `readHeader` ; config `CONTACT`, `IP6_SUPPORT`, `EXT_HEADERS` (seulement lu par addrheader) ; 21 imports inutilisés.
- [ ] Rapport Markdown *(nouveau)* : les messages sont écrits bruts, octets de contrôle compris (NUL de intmeth et mpmime), ce qui gêne certains visualiseurs.
- [ ] `requirements.txt` : `pluginbase` non épinglé, et son build échoue sous Python 3.13 dans l'environnement de test.
- [ ] `libs/data.py` : séquence d'échappement `'\ '` invalide dans l'ASCII art (`SyntaxWarning`, et erreur avec `-W error`).
- [ ] UDP uniquement : longreq et mpmime dépassent 1300 octets (RFC 3261 §18.1.1), et TCP n'est pas implémenté.
- [ ] Options mineures *(nouveau)* : `-t` n'accepte que des entiers ; `-e 0` est ignoré (test `if args.exten`).
- [ ] CI *(nouveau)* : `.travis.yml` cible Python 3.7 sur travis-ci.org (service arrêté) et lance un vrai scan contre une IP tierce (`172.104.142.43`). Envoyer des messages de torture à un hôte qu'on ne maîtrise pas est à retirer.

### P3 — Fidélité RFC 4475 et documentation

- [x] Les 50 modules reproduisent le défaut de leur message de référence ; wsinv et intmeth ajoutés ; libellés corrigés ; paragraphe RFC dans le rapport.
- [ ] mpmime : partie binaire non identique à la référence (265 octets contre 342), car le blob est décodé en UTF-8 avec `errors='ignore'`. Le défaut testé reste présent (octets 0x00, Content-Length exact). Correction : faire transiter le message en octets bruts dans `buildreq`, `concatMethodxHeaders` et `connector`.
- [ ] Valeurs tirées au hasard mais de même nature que dans la RFC (non bloquant) : méthode et en-tête échappés d'escinv, méthode inconnue de metmatch, noms longs de longreq.
- [ ] README obsolète *(nouveau)* : annonce 48 modules et ne liste ni wsinv ni intmeth.
- Décision prise : le Via d'intmeth reste en `SIP/2.0/TCP`, comme dans la référence, bien que l'outil envoie en UDP. Un serveur strict répondra en TCP et l'outil verra un timeout.

## Correspondance modules ↔ RFC 4475

Portée aussi par chaque module (`module_info['rfc']`, `module_info['ref']`) et affichée dans le rapport, sous la forme `- RFC 4475: §3.1.1.3 (message `esc01`)`.

| § | Réf. | Module | | § | Réf. | Module |
|---|---|---|---|---|---|---|
| 3.1.1.1 | wsinv | wsinv | | 3.1.2.11 | escruri | escuri |
| 3.1.1.2 | intmeth | intmeth | | 3.1.2.12 | baddate | baddate |
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

L'audit initial signalait `Route: <sip:127.0.0.1:5080>` dans mpmime comme absent de la RFC. C'est faux : cet en-tête figure dans le message de référence mpart01. L'effet reste à connaître en exploitation : un proxy qui applique le loose routing contactera son propre loopback.
