# Installer le pack français dans PhpStorm

**Auteur : YRYcom - Yannick LALLEAU**

Ce pack traduit une grande partie de l’interface de **PhpStorm 2026.2.3, build 262.10968.76**. Il est expérimental : les traductions sont principalement automatiques, les commandes courantes ont été relues et certains textes restent en anglais.

## Vérifier la version de PhpStorm

Sur Mac, ouvre **PhpStorm → About PhpStorm**. Vérifie la version **2026.2.3** et le build **262.10968.76**.

Le plugin est limité à ce build exact. Pour une autre version, il faut reconstruire et vérifier le pack à partir des ressources de cette version.

## Choisir le bon fichier

Dans le projet, utilise :

```text
dist/phpstorm-french-pack-2026.2.3.zip
```

Les archives distribuées peuvent aussi porter le nom :

```text
phpstorm-french-local-2026.2.3-0.1.2.zip
```

Ces deux fichiers contiennent le même plugin. **Ne décompresse pas le ZIP avant l’installation.** L’archive contenant `sources` dans son nom sert au développement, pas à l’installation dans PhpStorm.

## Installer le plugin

1. Ouvre **PhpStorm → Settings…** avec le raccourci **⌘ ,** sur Mac. Sous Windows ou Linux, ouvre **File → Settings**.
2. Sélectionne **Plugins**.
3. Clique sur la roue dentée **⚙️**, puis sur **Install Plugin from Disk…**.
4. Sélectionne le ZIP du plugin.
5. Confirme l’installation. Si PhpStorm demande de faire confiance à ce plugin local, vérifie qu’il s’agit bien de **French Language Pack (local experimental)**.
6. Redémarre PhpStorm si l’application le demande.

## Activer le français

1. Retourne dans **Settings**.
2. Ouvre **Appearance & Behavior → System Settings → Language and Region**.
3. Dans **Language**, sélectionne **Français**.
4. Clique sur **Apply**, puis sur **OK**.
5. Redémarre PhpStorm pour appliquer la langue à toute l’interface.

## Vérifier le résultat

Ouvre les menus et les paramètres : les boutons courants doivent afficher notamment **Annuler**, **Appliquer** et **Enregistrer**.

Des descriptions d’inspections, des astuces, des expressions techniques et des textes de plugins externes peuvent rester en anglais. Le pack ne traduit ni le code des projets ni leurs fichiers.

## Revenir à l’anglais ou désinstaller le pack

Pour revenir à l’anglais, retourne dans les paramètres de langue, sélectionne **English**, puis redémarre.

Pour retirer le plugin, ouvre **Settings → Plugins → Installed**, recherche **French Language Pack (local experimental)** et choisis **Disable** ou **Uninstall**. Redémarre si PhpStorm le demande.

## Résoudre les problèmes courants

- **Le ZIP est refusé comme incompatible** : vérifie le build exact dans **About PhpStorm**. Ne force pas la compatibilité avec une autre version.
- **Français n’apparaît pas** : vérifie que le plugin est présent et activé dans **Plugins → Installed**, puis redémarre.
- **Un autre pack français est déjà installé** : désactive cet autre pack avant d’activer celui-ci.
- **Un texte est incorrect ou reste en anglais** : relève le texte affiché et l’écran concerné pour permettre sa correction. Les corrections par message se trouvent dans `translations/reviewed-translations.json`, avec le texte anglais d’origine ; `translations/overrides.json` contient les corrections de fragments partagés.

## Contrôles effectués

Le vérificateur JetBrains a déclaré le plugin compatible avec le build **262.10968.76**. Les contrôles de ressources vérifient les clés et les formats de messages Java. Ils ne remplacent pas une relecture visuelle et linguistique de tous les écrans.
