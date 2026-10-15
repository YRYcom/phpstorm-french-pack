# Pack français pour PhpStorm

Pack de langue français indépendant pour **PhpStorm 2026.2.3 — build 262.10968.76**.

**Auteur : YRYcom - Yannick LALLEAU** · **Version : 0.1.2**

Les traductions sont générées localement puis corrigées progressivement. La version actuelle contient 48 614 messages dans 344 ensembles de ressources. La relecture linguistique reste partielle. Les descriptions HTML d’inspections, les astuces et les plugins externes ne sont pas tous couverts.

## Installer le plugin

Consulte [INSTALLATION.md](INSTALLATION.md). Le ZIP produit dans `dist/` s’installe depuis **Plugins → Install Plugin from Disk…**. Il est limité au build indiqué ci-dessus.

## Organisation

```text
.github/workflows/tests.yml        Tests automatiques sur GitHub
build_pack.py                      Extraction, traduction et création du plugin
project.json                       Version, auteur et build PhpStorm ciblé
download_model.py                  Téléchargement et contrôle du modèle facultatif
requirements.txt                   Dépendances de traduction automatique
translations/
  reviewed-translations.json       Corrections par message et texte anglais de référence
  overrides.json                   Corrections de fragments partagés
  translation-cache.json           Cache des traductions automatiques
  format-fallbacks.tsv             Messages conservés en anglais pour compatibilité
model/sha256.json                  Empreintes attendues du modèle
tests/                            Tests Python
tools/ValidatePack.java            Validation Java des ressources et formats
build/                            Fichiers générés, ignorés par Git
dist/                             Plugin JAR et ZIP générés, ignorés par Git
```

## Reconstruire depuis le cache

Prérequis : **Python 3.12 ou supérieur** et une installation locale du build exact de PhpStorm. Aucun paquet Python supplémentaire ni modèle de traduction n’est nécessaire pour cette commande :

```bash
python3 build_pack.py --package-only --ide-path /Applications/PhpStorm.app/Contents
```

Pour une installation située ailleurs, remplace le chemin par le répertoire de l’IDE contenant `product-info.json` ou `Resources/product-info.json`. Le chemin peut aussi être défini avec la variable `PHPSTORM_HOME`.

Les fichiers produits sont :

- `dist/phpstorm-french-pack-2026.2.3.zip` : plugin installable ;
- `dist/phpstorm-french-pack-0.1.2.jar` : ressources du plugin ;
- `dist/coverage.json` : couverture et empreinte SHA-256 du ZIP ;
- `build/inventory.json` : messages anglais extraits ;
- `build/fallback.json` : messages restés identiques à l’anglais.

`--package-only` utilise les traductions disponibles. Un fragment absent du cache et des corrections reste en anglais.

La version, l’auteur et le build cible se configurent dans `project.json`. Changer le build nécessite aussi de vérifier les corrections et de valider le pack sur le nouvel IDE.

## Traduction automatique facultative

Cette étape n’est utile que pour traduire de nouveaux fragments. Les textes sont traités localement ; seul le téléchargement initial du modèle utilise le réseau.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python download_model.py
python build_pack.py --ide-path /Applications/PhpStorm.app/Contents
```

Sous Windows, active l’environnement avec `.venv\Scripts\activate`. Le téléchargement vérifie les empreintes de `model/sha256.json`. Les fichiers du modèle ne sont pas versionnés dans Git.

## Vérifier les changements

Tests autonomes, également exécutés par GitHub Actions :

```bash
python3 -m unittest discover -s tests -v
```

Un test d’intégration est ignoré par défaut car il nécessite les ressources générées. Après une construction locale, exécute tous les tests avec :

```bash
PACK_TEST_ARTIFACTS=1 python3 -m unittest discover -s tests -v
```

Validation des clés et des formats Java, avec le Java fourni par PhpStorm sur macOS :

```bash
/Applications/PhpStorm.app/Contents/jbr/Contents/Home/bin/java \
  tools/ValidatePack.java \
  /Applications/PhpStorm.app/Contents \
  dist/phpstorm-french-pack-0.1.2.jar
```

Sur les autres plateformes, utilise un JDK 21 ou supérieur et adapte le chemin de l’IDE. Le validateur ne modifie aucun fichier avec ces deux arguments.

Pour le contrôle complémentaire JetBrains, télécharge le [Plugin Verifier officiel](https://github.com/JetBrains/intellij-plugin-verifier), puis exécute :

```bash
java -jar tools/verifier.jar check-plugin \
  dist/phpstorm-french-pack-2026.2.3.zip \
  /Applications/PhpStorm.app/Contents
```

Les tests GitHub ne téléchargent pas PhpStorm et ne valident donc pas la compatibilité avec l’IDE. Cette validation s’effectue localement avant de distribuer une version.

## Publier sur GitHub

Le dossier constitue un dépôt Git autonome, sur la branche `main`. Les environnements Python, le modèle, les rapports et les archives générées sont exclus du dépôt.

Crée un dépôt GitHub vide, puis, depuis ce dossier :

```bash
git add .
git diff --cached --stat
git commit -m "Initialise le pack français PhpStorm"
git remote add origin https://github.com/VOTRE-COMPTE/phpstorm-french-pack.git
git push -u origin main
```

Pour distribuer le plugin, crée une GitHub Release avec un tag tel que `v0.1.2` et joins le ZIP de `dist/`. Les binaires ne sont pas ajoutés à l’historique Git. La configuration GitHub Actions vérifie les contributions ; elle ne publie aucune release automatiquement.

## Contribuer et provenance

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) pour corriger une traduction et [NOTICE.md](NOTICE.md) pour la provenance des ressources et outils tiers.
