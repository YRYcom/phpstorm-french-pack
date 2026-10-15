"""Download the optional EN-FR model and verify its checked-in SHA-256 hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
MODEL_URL = 'https://huggingface.co/manancode/opus-mt-en-fr-ctranslate2-android/resolve/main/'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_model(destination: Path = ROOT / 'model') -> None:
    expected = json.loads((ROOT / 'model/sha256.json').read_text(encoding='utf-8'))
    destination.mkdir(parents=True, exist_ok=True)
    for name, checksum in expected.items():
        target = destination / name
        if target.exists():
            if sha256(target) != checksum:
                raise ValueError(f'Checksum mismatch for {name}; remove the invalid file before retrying')
            continue
        partial = destination / (name + '.part')
        try:
            with urlopen(MODEL_URL + name, timeout=120) as response, partial.open('wb') as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
            if sha256(partial) != checksum:
                raise ValueError(f'Checksum mismatch for downloaded file {name}')
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
    print('Model files verified.')


if __name__ == '__main__':
    download_model()
