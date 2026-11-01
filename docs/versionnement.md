[English](versionnement.en.md) | **Français**

# Versionnement

La propriété `version` de `gradle.properties` définit la version du produit pour
tous les modules, indépendamment des versions de Minecraft et des dépendances.

| Changement livré | Semantic Versioning 2.0.0 | Exemple |
| --- | --- | --- |
| Correctif compatible | PATCH | `1.4.2` → `1.4.3` |
| Fonctionnalité compatible | MINOR, PATCH à zéro | `1.4.2` → `1.5.0` |
| Rupture du contrat public | MAJOR, MINOR et PATCH à zéro | `1.4.2` → `2.0.0` |

Évaluer la branche depuis la dernière version normale livrée, sans compter les
commits. Documentation, tests et CI ne déclenchent pas automatiquement un changement
de version. `0.y.z` reste instable ; aucun passage automatique à `1.0.0`.

Une branche de travail peut utiliser une préversion. Sur `main`, conserver
exactement `MAJOR.MINOR.PATCH` : trois entiers sans zéros initiaux, sauf `0`,
sans préfixe, suffixe de préversion ou métadonnée de construction.

Avant une fusion autorisée :

1. Définir la version normale sur la branche de travail.
2. Obtenir une CI réussie pour ce commit précis.
3. Fusionner le commit testé sans changer ensuite sa version sur `main`.

Ne jamais réutiliser le numéro d’un artefact distribué pour un contenu différent.
Voir la [validation CI](validation.md).
