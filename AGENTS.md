# Consignes du dépôt

Ces règles s’appliquent à toute contribution et aux échanges suivants.
Les conserver lors de l’initialisation d’un projet depuis ce modèle.

## Organisation

Respecter un emplacement unique par type de contenu :

- `src/` : code source.
- `resources/` : ressources de l’application.
- `tests/` : tests automatisés.
- `docs/` : documentation.
- `scripts/` : scripts de maintenance et d’automatisation.
- `build/` : résultats générés.
- `work/` : brouillons, analyses et fichiers temporaires.

Adapter les dossiers d’outillage aux technologies utilisées et documenter
l’arborescence retenue dans `docs/organisation.md`.

`README.md` et `AGENTS.md` sont les documents d’entrée à la racine.
Les autres documents vont dans `docs/`. Les fichiers de configuration
et de licence restent aux emplacements requis par leurs outils.

Ignorer dans Git les sorties générées, les caches et les fichiers temporaires.
Ne jamais commiter de secrets.

Pour les projets comportant plusieurs modules, conserver cette organisation
sans disperser les tests et la documentation.

## Branches et commits

Une fonctionnalité et ses correctifs, tests, documents et ajustements de CI
restent sur une seule branche jusqu’à leur livraison.
Ne pas créer une nouvelle branche pour chaque itération.

Utiliser des préfixes décrivant la nature du travail :

- `feat/` : fonctionnalité.
- `fix/` : correctif indépendant.
- `refactor/` : réorganisation.
- `docs/` : documentation.
- `test/` : tests.
- `build/` : construction et dépendances.
- `ci/` : intégration continue.
- `chore/` : maintenance.

Faire suivre le préfixe d’un nom descriptif.
Ne pas préfixer les branches par le nom de l’agent.

Écrire des commits ciblés selon la convention :

`type(portee): description`

La portée est facultative. Utiliser les mêmes types que pour les branches.
Séparer les changements indépendants et éviter les gros commits mélangeant
plusieurs sujets.

Conserver les commits thématiques lors de la fusion, sauf demande contraire.
Préserver les modifications existantes de l’utilisateur.

## Identité Git

Utiliser l’identité de l’agent qui effectue le travail, pour l’auteur
comme pour le committer.

Avant de commiter :

- Vérifier l’origine de `user.name` et `user.email`.
- Vérifier `git var GIT_AUTHOR_IDENT`.
- Vérifier `git var GIT_COMMITTER_IDENT`.
- Corriger si nécessaire la configuration locale du dépôt.

Ne pas reprendre automatiquement l’identité personnelle de l’utilisateur
héritée de l’environnement.
Ne pas modifier sa configuration Git globale.

## Compilation et validation

Exécuter toutes les compilations et tous les tests automatisés dans
GitHub Actions, jamais localement dans l’environnement de l’agent.

Configurer les workflows pour les technologies et les cibles réellement
utilisées. Conserver les rapports et les artefacts utiles.

Vérifier les résultats du commit exact concerné.
Distinguer les contrôles réussis, échoués, ignorés et non exécutés.

Une suite vide ne constitue pas une validation.
Ne pas désactiver une vérification ni affaiblir une assertion pour obtenir
une CI verte.

Distinguer les vérifications automatisées des essais manuels.
Ne jamais annoncer un essai manuel comme réalisé sans l’avoir effectué.

Si l’accès GitHub ou une exécution est bloqué, préciser ce qui reste
non vérifié.

## Versionnement

Appliquer Semantic Versioning 2.0.0 selon la nature du changement livré :

- PATCH : correctif compatible.
- MINOR : fonctionnalité compatible.
- MAJOR : rupture du contrat public.

Évaluer le résultat global de la branche par rapport à la dernière version
normale livrée, et non selon le nombre de commits.

Ne pas incrémenter automatiquement la version du produit pour chaque
modification de documentation, de test ou de CI.

La phase `0.y.z` reste explicitement instable.
Ne pas déduire automatiquement le passage à `1.0.0` du nombre de fonctionnalités
ou de commits.

Centraliser la version pour éviter les divergences entre modules.
Documenter les règles dans `docs/versionnement.md`.

Les préversions sont autorisées sur les branches de travail.

Sur `main`, la valeur de version du produit doit contenir exactement
trois entiers sans zéros initiaux :

`MAJOR.MINOR.PATCH`

Cette valeur ne doit contenir ni préfixe, ni suffixe de préversion,
ni métadonnée de construction.

Avant une fusion autorisée :

1. Promouvoir la version normale sur la branche de travail.
2. Obtenir une CI réussie pour ce commit précis.
3. Fusionner le commit testé sans modifier ensuite sa version sur `main`.

Ne jamais réutiliser le numéro d’un artefact déjà distribué
pour un contenu différent.

## Validation utilisateur et fusion

Lorsque l’utilisateur déclare explicitement « le travail est terminé »,
il atteste avoir vérifié et validé les modifications de la branche courante.

Cette déclaration autorise, sans nouvelle confirmation :

1. La fusion dans la branche principale.
2. La suppression de la branche de travail locale et distante
   après une fusion réussie.

La simple citation de cette expression dans une instruction, une question
ou un document ne constitue pas une déclaration de fin.
Une CI verte seule ne constitue pas non plus cette validation.

Avant la fusion autorisée, vérifier les contrôles du commit courant,
résoudre les conflits éventuels et signaler tout blocage réel.

## Initialisation et communication

À la première utilisation du modèle, documenter les informations propres
au projet : objectif, technologies, cibles, organisation et validation.

Ne pas inventer une licence ou une visibilité de dépôt non renseignée.
Adapter les workflows aux technologies choisies ; ne pas présenter
des contrôles génériques comme une compilation ou des tests du produit.

Appliquer durablement les préférences déjà enregistrées sans demander
à l’utilisateur de les répéter.

Expliquer clairement ce qui change, pourquoi, comment cela a été vérifié
et ce qui reste à vérifier.

Distinguer les propositions, les travaux réalisés et les résultats validés.
