# Corriger les traductions

## Une correction dans son contexte

Privilégie `translations/reviewed-translations.json` pour corriger un message complet. Ce fichier associe le nom du bundle et la clé du message au texte anglais d’origine et à sa traduction :

```json
{
  "messages/CommonBundle.properties": {
    "button.set": {
      "source": "Set",
      "translation": "Définir",
      "review": "manual"
    }
  }
}
```

Le champ `source` doit correspondre exactement au message extrait de l’IDE. Consulte `build/inventory.json` après une construction locale pour retrouver son bundle, sa clé et son texte anglais. Le constructeur refuse une correction si la source a changé ou si elle modifie une structure protégée.

Préserve les paramètres `{0}`, les expressions `choice`, les balises HTML, les URL, les commandes et les extraits de code. Utilise de préférence l’apostrophe typographique `’` dans les messages français : l’apostrophe ASCII possède un rôle particulier dans Java MessageFormat.

Le champ `review` vaut `manual` pour une correction contextuelle relue ; `terminology` identifie les corrections limitées au vocabulaire technique. Les compteurs du rapport distinguent ces deux catégories.

## Les fragments partagés

`translations/overrides.json` agit sur un fragment anglais partout où il apparaît. Utilise-le seulement lorsque la traduction convient à tous les contextes. Pour un mot ambigu comme « Set », corrige plutôt les messages individuellement.

`translations/translation-cache.json` contient les résultats du modèle automatique. Les corrections relues prennent la priorité sur le cache. Ne lance pas une retraduction globale pour une correction ponctuelle.

`translations/format-fallbacks.tsv` contient les couples bundle/clé forcés en anglais pour éviter des erreurs de format. Ces exceptions s’appliquent après les corrections. Leur suppression exige une validation Java réussie.

## Valider une contribution

1. Ajoute ou adapte un test pertinent dans `tests/`.
2. Lance `python3 -m unittest discover -s tests -v`.
3. Reconstruis le ZIP avec `--package-only` et le chemin de ton IDE.
4. Lance les tests avec `PACK_TEST_ARTIFACTS=1`, puis le validateur Java, comme indiqué dans le README.
5. Vérifie le résultat dans PhpStorm pour les écrans concernés.

N’ajoute pas les fichiers de `build/`, `dist/`, `.venv/` ni les poids du modèle à ta contribution. Le chemin de ton installation PhpStorm se passe en argument ou via `PHPSTORM_HOME`.
