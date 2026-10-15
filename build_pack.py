"""Build a private, resource-only French language pack from a local IDE."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import time
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
TRANSLATIONS = ROOT / 'translations'
BUILD = ROOT / 'build'
PROJECT = json.loads((ROOT / 'project.json').read_text(encoding='utf-8'))
AUTHOR = PROJECT['author']
VERSION = PROJECT['version']


def unescape(value: str) -> str:
    def replace(match):
        token = match.group(1)
        if token.startswith('u'):
            return chr(int(token[1:], 16))
        return {'t': '\t', 'r': '\r', 'n': '\n', 'f': '\f'}.get(token, token)
    result = re.sub(r'\\(u[0-9a-fA-F]{4}|.)', replace, value)
    return result.encode('utf-16', 'surrogatepass').decode('utf-16')


def read_properties(text: str) -> dict[str, str]:
    result = {}
    logical = ''
    continuing = False
    for physical in text.splitlines():
        line = physical.lstrip(' \t\f') if continuing else physical
        logical += line
        count = len(logical) - len(logical.rstrip('\\'))
        if count % 2:
            logical = logical[:-1]
            continuing = True
            continue
        line = logical.lstrip(' \t\f')
        logical = ''
        continuing = False
        if not line or line.startswith(('#', '!')):
            continue
        escaped = False
        end = len(line)
        for index, char in enumerate(line):
            if not escaped and char in '=:\t \f':
                end = index
                break
            escaped = not escaped if char == '\\' else False
        value = line[end:].lstrip(' \t\f')
        if value.startswith(('=', ':')):
            value = value[1:].lstrip(' \t\f')
        result[unescape(line[:end])] = unescape(value)
    if logical:
        result.update(read_properties(logical + '\n'))
    return result


def escaped_property(value: str, key: bool = False) -> str:
    result = []
    for index, char in enumerate(value):
        code = ord(char)
        if char in '\\\n\r\t\f':
            result.append({'\\': '\\\\', '\n': '\\n', '\r': '\\r', '\t': '\\t', '\f': '\\f'}[char])
        elif (key and char in ' =:#!') or (index == 0 and char == ' '):
            result.append('\\' + char)
        elif code < 32 or code > 126:
            if code > 0xffff:
                code -= 0x10000
                result.append('\\u%04x\\u%04x' % (0xd800 + (code >> 10), 0xdc00 + (code & 1023)))
            else:
                result.append('\\u%04x' % code)
        else:
            result.append(char)
    return ''.join(result)


def inventory(ide_path: Path) -> dict[str, dict[str, str]]:
    bundles = {}
    for jar in sorted(ide_path.rglob('*.jar')):
        if any(part.startswith('localization-') for part in jar.parts):
            continue
        with zipfile.ZipFile(jar) as archive:
            for name in archive.namelist():
                if not name.startswith('messages/') or not name.endswith('.properties') or '/' in name[9:]:
                    continue
                if re.search(r'_(?:fr|en|ja|ko|zh)(?:_[A-Z]+)?\.properties$', name):
                    continue
                properties = read_properties(archive.read(name).decode('utf-8'))
                target = bundles.setdefault(name, {})
                for key, value in properties.items():
                    if key in target and target[key] != value:
                        raise ValueError(f'Conflicting resource: {name}:{key}')
                    target[key] = value
    return bundles


# These constructs are copied byte-for-byte after properties decoding.
PROTECTED = re.compile(r"(?is:<(?:code|pre|kbd|samp)\b[^>]*>.*?</(?:code|pre|kbd|samp)>)|`[^`]+`|\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|<[^>]+>|&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);|https?://[^\s<>]+|\$\w+\$|\$[A-Za-z_]\w*|%\d*\$?[a-zA-Z]|[\r\n\t\f]|''|\b[A-Z][\w$]*(?:\\[A-Za-z_][\w$]*)+|\\[^\s]+|\b[A-Za-z_$][\w$]*(?:\.[\w$]+){2,}\b|--[a-zA-Z][\w-]+|(?<!\w)(?:~?/)(?:[\w.-]+/)*[\w.-]+")


def pieces(text: str) -> list[tuple[bool, str]]:
    output = []
    cursor = 0
    for match in PROTECTED.finditer(text):
        if match.start() > cursor:
            output.append((False, text[cursor:match.start()]))
        output.append((True, match.group()))
        cursor = match.end()
    if cursor < len(text):
        output.append((False, text[cursor:]))
    return output


def eligible(text: str) -> bool:
    return bool(re.search('[A-Za-z]{2}', text)) and len(text) <= 900


def clean(text: str) -> str:
    return re.sub(r'(?<!&)&(?!&)', '', text).replace('&&', '&').replace('_', '').strip()


def translate(bundles, cache, overrides):
    import ctranslate2
    import sentencepiece
    source = sentencepiece.SentencePieceProcessor(model_file=str(ROOT / 'model/source.spm'))
    target = sentencepiece.SentencePieceProcessor(model_file=str(ROOT / 'model/target.spm'))
    model = ctranslate2.Translator(str(ROOT / 'model'), device='cpu', compute_type='int8', intra_threads=6)
    pending = set()
    for properties in bundles.values():
        for text in properties.values():
            for protected, segment in pieces(text):
                segment = clean(segment)
                if not protected and eligible(segment) and segment not in cache and segment not in overrides:
                    pending.add(segment)
    pending = sorted(pending, key=len)
    print(f'{len(pending)} unique segments to translate locally', flush=True)
    started = time.monotonic()
    for start in range(0, len(pending), 64):
        batch = pending[start:start + 64]
        inputs = [source.encode(text, out_type=str) + ['</s>'] for text in batch]
        translations = model.translate_batch(inputs, beam_size=2, max_decoding_length=384, repetition_penalty=1.05)
        for english, output in zip(batch, translations):
            french = target.decode(output.hypotheses[0])
            # Never introduce MessageFormat placeholders or markup through MT.
            if not french.strip() or re.search(r'[{}<>\r\n]', french):
                french = english
            if len(french) > max(180, len(english) * 4):
                french = english
            cache[english] = french
        if start % 640 == 0 or start + 64 >= len(pending):
            (TRANSLATIONS / 'translation-cache.json').write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
            print(f'{min(start + 64, len(pending))}/{len(pending)} segments; {time.monotonic() - started:.0f}s', flush=True)
    (TRANSLATIONS / 'translation-cache.json').write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def render_value(text: str, cache: dict, overrides: dict) -> str:
    has_parameters = bool(re.search(r'\{\d+', text))
    result = []
    for protected, segment in pieces(text):
        source = clean(segment)
        if protected or not eligible(source):
            result.append(segment)
            continue
        french = overrides.get(source, cache.get(source, source))
        if has_parameters:
            french = french.replace("'", "''")
        prefix = segment[:len(segment) - len(segment.lstrip())]
        suffix = segment[len(segment.rstrip()):]
        result.append(prefix + french + suffix)
    translated = ''.join(result)
    signature = lambda value: collections.Counter(token for token in PROTECTED.findall(value) if token != "''")
    if signature(text) != signature(translated):
        return text
    return translated


def reviewed_value(source: str, correction: dict) -> str:
    if correction['source'] != source:
        raise ValueError('Reviewed translation no longer matches its English source')
    target = correction['translation']
    signature = lambda value: collections.Counter(token for token in PROTECTED.findall(value) if token != "''")
    if signature(source) != signature(target):
        raise ValueError('Reviewed translation changes a protected construct')
    return target


def build(ide_path: Path, package_only: bool = False):
    info_path = ide_path / 'Resources/product-info.json'
    if not info_path.exists():
        info_path = ide_path / 'product-info.json'
    if not info_path.exists():
        raise SystemExit('IDE not found: use --ide-path or PHPSTORM_HOME')
    info = json.loads(info_path.read_text(encoding='utf-8'))
    if info['version'] != PROJECT['ide_version'] or info['buildNumber'] != PROJECT['ide_build']:
        raise SystemExit(f"Expected PhpStorm {PROJECT['ide_version']}, build {PROJECT['ide_build']}")
    BUILD.mkdir(exist_ok=True)
    bundles = inventory(ide_path)
    if not bundles:
        raise SystemExit('No English message bundles found in the selected IDE')
    (BUILD / 'inventory.json').write_text(json.dumps(bundles, ensure_ascii=False), encoding='utf-8')
    overrides = json.loads((TRANSLATIONS / 'overrides.json').read_text(encoding='utf-8'))
    reviewed = json.loads((TRANSLATIONS / 'reviewed-translations.json').read_text(encoding='utf-8'))
    for name, corrections in reviewed.items():
        for key, correction in corrections.items():
            try:
                reviewed_value(bundles[name][key], correction)
            except (KeyError, ValueError) as error:
                raise ValueError(f'{name}:{key}: {error}') from error
    cache_path = TRANSLATIONS / 'translation-cache.json'
    cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    if not package_only:
        translate(bundles, cache, overrides)
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    resource_dir = BUILD / 'resources'
    counts = collections.Counter()
    fallback = []
    repairs_path = TRANSLATIONS / 'format-fallbacks.tsv'
    repairs = {tuple(line.split('\t', 1)) for line in repairs_path.read_text(encoding='utf-8').splitlines()} if repairs_path.exists() else set()
    for name, properties in bundles.items():
        translated = {}
        for key, value in properties.items():
            result = render_value(value, cache, overrides)
            if key in reviewed.get(name, {}):
                correction = reviewed[name][key]
                result = reviewed_value(value, correction)
                counts['reviewed_' + correction.get('review', 'manual')] += 1
            if (name, key) in repairs:
                result = value
                counts['format_fallbacks'] += 1
            translated[key] = result
            counts['entries'] += 1
            counts['changed'] += result != value
            counts['preserved_technical_constructs'] += len(PROTECTED.findall(value))
            if result == value and eligible(clean(value)):
                fallback.append([name, key, value])
        text = '# French translation for private use; generated from local English resources.\n'
        text += '\n'.join(escaped_property(k, True) + '=' + escaped_property(v) for k, v in translated.items()) + '\n'
        path = resource_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='ascii')
        assert read_properties(text) == translated, name
    descriptor = f'''<idea-plugin>
  <id>fr.local.language.pack</id>
  <name>French Language Pack (local experimental)</name>
  <version>{VERSION}</version>
  <vendor>{escape(AUTHOR)}</vendor>
  <description>French user interface translations generated locally and partially reviewed. This experimental pack targets the exact IDE build shown in its compatibility range. Unsupported resources remain in English. Independent project, not affiliated with JetBrains.</description>
  <idea-version since-build="{escape(info['buildNumber'])}" until-build="{escape(info['buildNumber'])}"/>
  <depends>com.intellij.modules.platform</depends>
  <extensions defaultExtensionNs="com.intellij">
    <languageBundle locale="fr" displayName="Français"/>
  </extensions>
</idea-plugin>'''
    jar_path = output / f'phpstorm-french-pack-{VERSION}.jar'
    with zipfile.ZipFile(jar_path, 'w', zipfile.ZIP_DEFLATED) as jar:
        jar.writestr('META-INF/plugin.xml', descriptor)
        for path in sorted(resource_dir.rglob('*.properties')):
            jar.write(path, path.relative_to(resource_dir))
    zip_path = output / f"phpstorm-french-pack-{PROJECT['ide_version']}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(jar_path, 'phpstorm-french-pack/lib/' + jar_path.name)
    report = dict(counts, author=AUTHOR, bundles=len(bundles), build=info['buildNumber'], ide_version=info['version'],
                  sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),
                  fallback_entries=len(fallback), fully_reviewed=False,
                  scope='Message bundles only; HTML inspection descriptions, tips, hardcoded strings and external plugins are not covered.')
    (output / 'coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (BUILD / 'fallback.json').write_text(json.dumps(fallback, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    print(zip_path, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ide-path', type=Path, default=Path(os.environ.get('PHPSTORM_HOME', '/Applications/PhpStorm.app/Contents')),
                        help='IDE installation directory (on macOS: PhpStorm.app/Contents)')
    parser.add_argument('--package-only', action='store_true', help='Use the checked-in translation cache without loading the translation model')
    args = parser.parse_args()
    build(args.ide_path.expanduser().resolve(), package_only=args.package_only)
