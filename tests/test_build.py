import unittest
import json
import os
import tempfile
import zipfile
from pathlib import Path
from build_pack import ROOT, TRANSLATIONS, BUILD, inventory, build, read_properties, escaped_property, pieces, render_value, reviewed_value


class ResourceTests(unittest.TestCase):
    def test_java_properties_escapes_and_continuations(self):
        self.assertEqual({'a b': 'café\nlignesuivante', 'path': 'C:\\tmp'}, read_properties('a\\ b=caf\\u00e9\\nligne\\\n suivante\npath=C:\\\\tmp\n'))

    def test_roundtrip(self):
        expected = {' a:=!': ' français\n{0} <html>\\ é 😀', 'x': 'a\tb\r'}
        encoded = '\n'.join(escaped_property(k, True) + '=' + escaped_property(v) for k, v in expected.items())
        self.assertEqual(expected, read_properties(encoded))

    def test_placeholders_markup_and_messageformat_apostrophes(self):
        source = "Open {0} in <b>Settings</b>"
        result = render_value(source, {}, {'Open': 'Ouvrir', 'in': "dans l'onglet", 'Settings': 'Paramètres'})
        self.assertEqual("Ouvrir {0} dans l''onglet <b>Paramètres</b>", result)

    def test_choice_is_preserved(self):
        source = 'Delete {0,choice,0#files|1#file} now'
        self.assertEqual('Supprimer {0,choice,0#files|1#file} maintenant', render_value(source, {}, {'Delete': 'Supprimer', 'now': 'maintenant'}))

    def test_invalid_generated_markup_falls_back(self):
        self.assertEqual('Open {0}', render_value('Open {0}', {'Open': '<script>'}, {}))

    def test_code_and_command_options_are_preserved(self):
        source = 'Open <code>if ($valid) return true;</code> with --no-interaction'
        result = render_value(source, {}, {'Open': 'Ouvrir', 'with': 'avec'})
        self.assertEqual('Ouvrir <code>if ($valid) return true;</code> avec --no-interaction', result)

    def test_review_rejects_changed_source(self):
        with self.assertRaises(ValueError):
            reviewed_value('Open {0}', {'source': 'Close {0}', 'translation': 'Fermer {0}'})

    def test_review_rejects_lost_arguments_markup_and_commands(self):
        for source, target in [('Open {0}', 'Ouvrir'), ('<b>Open</b>', 'Ouvrir'),
                               ('Run --help', 'Exécuter --aide'), ('{0} then {0}', '{0} ensuite'),
                               ('{0,choice,0#none|1#one}', '{0}')]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                reviewed_value(source, {'source': source, 'translation': target})

    @unittest.skipUnless(os.environ.get('PACK_TEST_ARTIFACTS') == '1', 'Requires a local pack build')
    def test_all_reviewed_messages_match_source_and_generated_resources(self):
        inventory = json.loads((BUILD / 'inventory.json').read_text(encoding='utf-8'))
        reviewed = json.loads((TRANSLATIONS / 'reviewed-translations.json').read_text(encoding='utf-8'))
        for bundle, corrections in reviewed.items():
            generated = read_properties((BUILD / 'resources' / bundle).read_text(encoding='utf-8'))
            for key, correction in corrections.items():
                with self.subTest(bundle=bundle, key=key):
                    target = reviewed_value(inventory[bundle][key], correction)
                    self.assertEqual(target, generated[key])

    def test_review_is_contextual(self):
        reviewed = json.loads((TRANSLATIONS / 'reviewed-translations.json').read_text(encoding='utf-8'))
        common = reviewed['messages/CommonBundle.properties']
        self.assertEqual('Définir', common['button.set']['translation'])
        php = reviewed['messages/PhpBundle.properties']
        self.assertEqual('Méthode setUp', php['action.PhpUnitGenerateSetUpMethod.text']['translation'])
        self.assertEqual('composer', php['composer']['translation'])
        self.assertEqual('Fichier composer.json', php['action.NewComposerJsonFile.text']['translation'])

    def test_review_preserves_message_format_with_french_apostrophe(self):
        source = "Driver class ''{0}'' not instantiable"
        target = 'Impossible d’instancier la classe du pilote « {0} »'
        self.assertEqual(target, reviewed_value(source, {'source': source, 'translation': target}))

    def test_all_reviewed_messages_preserve_protected_constructs(self):
        reviewed = json.loads((TRANSLATIONS / 'reviewed-translations.json').read_text(encoding='utf-8'))
        for bundle, corrections in reviewed.items():
            for key, correction in corrections.items():
                with self.subTest(bundle=bundle, key=key):
                    self.assertEqual(correction['translation'], reviewed_value(correction['source'], correction))

    def test_inventory_excludes_other_language_packs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with zipfile.ZipFile(root / 'app.jar', 'w') as archive:
                archive.writestr('messages/TestBundle.properties', 'name=Name')
                archive.writestr('messages/TestBundle_fr.properties', 'name=Nom')
            localized = root / 'plugins/localization-fr'
            localized.mkdir(parents=True)
            with zipfile.ZipFile(localized / 'pack.jar', 'w') as archive:
                archive.writestr('messages/TestBundle.properties', 'name=Other language')
            self.assertEqual({'messages/TestBundle.properties': {'name': 'Name'}}, inventory(root))

    def test_missing_or_incompatible_ide_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(SystemExit, 'IDE not found'):
                build(root, package_only=True)
            (root / 'product-info.json').write_text(json.dumps({'version': '2025.1', 'buildNumber': '251.1'}))
            with self.assertRaisesRegex(SystemExit, 'Expected PhpStorm'):
                build(root, package_only=True)


if __name__ == '__main__':
    unittest.main()
