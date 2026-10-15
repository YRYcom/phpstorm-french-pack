import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import download_model


class ModelDownloadTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'model').mkdir()
        self.payload = b'test model bytes'
        manifest = {'model.bin': hashlib.sha256(self.payload).hexdigest()}
        (self.root / 'model/sha256.json').write_text(json.dumps(manifest))
        self.patch = patch.object(download_model, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.destination = self.root / 'downloads'

    def test_valid_existing_model_does_not_use_network(self):
        self.destination.mkdir()
        (self.destination / 'model.bin').write_bytes(self.payload)
        with patch.object(download_model, 'urlopen') as request:
            download_model.download_model(self.destination)
        request.assert_not_called()

    def test_download_is_checked_before_becoming_available(self):
        with patch.object(download_model, 'urlopen', return_value=io.BytesIO(self.payload)):
            download_model.download_model(self.destination)
        self.assertEqual(self.payload, (self.destination / 'model.bin').read_bytes())
        self.assertFalse((self.destination / 'model.bin.part').exists())

    def test_corrupt_download_is_rejected_and_partial_file_removed(self):
        with patch.object(download_model, 'urlopen', return_value=io.BytesIO(b'corrupt')):
            with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                download_model.download_model(self.destination)
        self.assertFalse((self.destination / 'model.bin').exists())
        self.assertFalse((self.destination / 'model.bin.part').exists())

    def test_corrupt_existing_file_is_rejected(self):
        self.destination.mkdir()
        (self.destination / 'model.bin').write_bytes(b'corrupt')
        with patch.object(download_model, 'urlopen') as request:
            with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                download_model.download_model(self.destination)
        request.assert_not_called()
