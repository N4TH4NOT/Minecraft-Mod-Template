# Versionnement

La version du mod est centralisée dans la propriété `version` de
`gradle.properties` et partagée par tous les modules. Les numéros de version
Minecraft, modloader et bibliothèques sont indépendants de cette version.

Appliquer Semantic Versioning 2.0.0 : PATCH pour un correctif compatible,
MINOR pour une fonctionnalité compatible et MAJOR pour une rupture du
contrat public. Évaluer les changements de la branche par rapport à la
dernière version normale livrée ; ne pas incrémenter pour chaque commit.

Les changements de documentation, de tests ou de CI ne déclenchent pas
automatiquement une nouvelle version du produit. Une préversion peut être
utilisée sur une branche de travail. Sur la branche principale, conserver
une version normale `MAJOR.MINOR.PATCH`, sans préfixe ni suffixe, validée
par la CI sur le commit exact avant la fusion.

Ne pas réutiliser un numéro d’artefact déjà distribué pour un contenu différent.
