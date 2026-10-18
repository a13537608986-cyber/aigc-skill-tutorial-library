# 自行重建的补充校验器，非原作者文件；仅检查文本约束，不校验审美或模型出图。
"""Validate image prompt drafts using only Python's standard library.

Accepted inputs: English prompts in `text` fenced code blocks (backticks or
 tildes, three or more), or one plain-text prompt per blank-separated paragraph.
Bash/Python/other fenced blocks are excluded. Chinese numbered titles are allowed
outside prompt blocks. Counts use whitespace-separated terms containing letters or digits, INCLUDING
MJ parameter flags and values; punctuation-only tokens do not count. A successful check does not prove image quality.
"""
from pathlib import Path
import argparse
import json
import math
import re
import sys
import unicodedata

SKILL_KIND = '06'
FENCE = re.compile(r'^\s{0,3}(`{3,}|~{3,})([^\n]*)$')
RATIO = re.compile(r'[1-9]\d*:[1-9]\d*\Z')
VERSION = re.compile(r'\d+(?:\.\d+)?\Z')
PARAMETER = re.compile(r'(?<!\S)--(?:ar|v|raw)(?:\s|=|$)')
SLOT = re.compile(r'\[[^\]\n]+\]|<[^>\n]+>|\{\{[^}\n]+\}\}|\b(?:TODO|TBD|PLACEHOLDER)\b', re.I)
STYLE_ANCHORS = (
    'Clear daylight, warm highlights, green water reflections, photoreal pastoral film still.',
    'Gentle dappled daylight, natural skin tones, softly receding green foliage. Photoreal pastoral film still.',
)
FORBIDDEN = (
    'cinematic', 'moody', 'golden hour', 'sunset', 'dramatic lighting',
    'fashion editorial', 'portrait', 'close-up', 'low angle', 'beautiful woman',
    'village woman', 'luminous skin', 'glowing sleeves', 'flowing sleeves',
    'airy gauze', 'rustic documentary', 'coarse linen', 'letterbox',
)


def normalized_spaces(value):
    return ' '.join(value.split())


def normalized_style(value):
    return normalized_spaces(re.sub(r'[-\u2010-\u2015]', ' ', value.lower()))


def ratio_key(value):
    a, b = map(int, value.split(':'))
    divisor = math.gcd(a, b)
    return (a // divisor, b // divisor)


def parse_draft(draft):
    """Return prompt texts and document-level errors; do not silently pass zero."""
    if not draft.strip():
        return [], ['empty draft']
    lines = draft.splitlines()
    has_fences = any(FENCE.fullmatch(line) for line in lines)
    if not has_fences:
        clean = []
        for line in lines:
            stripped = line.strip()
            is_heading = stripped.startswith('#')
            is_title = bool(re.fullmatch(r'(?:Prompt\s*)?\d{1,3}\s*(?:[｜|.、:：-].*)?', stripped, re.I))
            if (is_heading or is_title) and not PARAMETER.search(stripped):
                clean.append('')
            else:
                clean.append(line)
        return [p.strip() for p in re.split(r'\n\s*\n', '\n'.join(clean)) if p.strip()], []
    prompts, errors = [], []
    active = None
    body = []
    for number, line in enumerate(lines, 1):
        match = FENCE.fullmatch(line)
        if active:
            if match and match[1][0] == active['marker'] and len(match[1]) >= active['length'] and not match[2].strip():
                if active['language'] == 'text':
                    text = '\n'.join(body).strip()
                    if text:
                        prompts.append(text)
                    else:
                        errors.append('empty text code block')
                active = None
                body = []
            elif active['language'] == 'text':
                body.append(line)
        elif match:
            info = match[2].strip()
            language = info.split()[0].lower() if info else ''
            active = {'marker':match[1][0], 'length':len(match[1]), 'language':language}
        elif PARAMETER.search(line):
            errors.append(f'line {number}: prompt parameter outside a text code block')
    if active and active['language'] == 'text':
        errors.append('unclosed text code block')
    if not prompts:
        errors.append('no English prompt text blocks found')
    return prompts, errors


def inspect_prompt(prompt, args):
    errors = []
    tokens = prompt.split()
    words = sum(bool(re.search(r"[A-Za-z0-9]", token)) for token in tokens)
    if not args.min_words <= words <= args.max_words:
        errors.append(f'word count including parameters is {words}; expected {args.min_words}..{args.max_words}')
    if SLOT.search(prompt):
        errors.append('unfilled template slot or placeholder')
    start = next((i for i, token in enumerate(tokens) if token.startswith('--')), len(tokens))
    natural = ' '.join(tokens[:start])
    if not re.search(r'[A-Za-z]', natural):
        errors.append('missing English prompt body')
    if any(c.isalpha() and 'LATIN' not in unicodedata.name(c, '') for c in natural):
        errors.append('prompt body contains non-English script')
    values = {'--ar':[], '--v':[], '--raw':[]}
    i = start
    while i < len(tokens):
        token = tokens[i]
        if token == '--raw':
            values[token].append(True)
            i += 1
        elif token in ('--ar', '--v'):
            if i + 1 >= len(tokens) or tokens[i + 1].startswith('--'):
                errors.append(f'{token} is missing a value')
                i += 1
            else:
                values[token].append(tokens[i + 1])
                i += 2
        else:
            errors.append(f'unrecognized or misplaced parameter token: {token}')
            i += 1
    for flag in ('--ar', '--v'):
        if len(values[flag]) != 1:
            errors.append(f'{flag} must occur exactly once')
    if len(values['--raw']) > 1:
        errors.append('--raw must not be duplicated')
    if args.raw_mode == 'required' and len(values['--raw']) != 1:
        errors.append('--raw is required exactly once')
    if len(values['--ar']) == 1:
        actual = values['--ar'][0]
        if not RATIO.fullmatch(actual):
            errors.append('--ar must be a complete positive width:height ratio')
        elif args.aspect != 'any' and ratio_key(actual) != ratio_key(args.aspect):
            errors.append(f'aspect is {actual}; expected {args.aspect}')
    if len(values['--v']) == 1:
        actual = values['--v'][0]
        if not VERSION.fullmatch(actual):
            errors.append('--v must be a complete numeric version')
        elif actual != args.version:
            errors.append(f'version is {actual}; expected {args.version}')
    if SKILL_KIND == '06' and args.style_profile == 'strict':
        body = normalized_spaces(natural).lower()
        if not any(anchor.lower() in body for anchor in STYLE_ANCHORS):
            errors.append('missing complete original A/B light-color sentence')
        style = normalized_style(natural)
        bad = [term for term in FORBIDDEN if re.search(r'\b' + re.escape(normalized_style(term)) + r'\b', style)]
        if bad:
            errors.append('forbidden default style term(s): ' + ', '.join(bad))
    return {'words_including_parameters':words, 'errors':errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('draft', type=Path)
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--aspect', default='16:9' if SKILL_KIND == '06' else '9:16')
    parser.add_argument('--version', default='8.2')
    parser.add_argument('--min-words', type=int, default=50)
    parser.add_argument('--max-words', type=int, default=80)
    parser.add_argument('--raw-mode', choices=['required','optional'], default='required')
    if SKILL_KIND == '06':
        parser.add_argument('--style-profile', choices=['strict','basic'], default='strict')
    args = parser.parse_args(argv)
    if args.count < 1 or args.min_words < 1 or args.max_words < args.min_words:
        parser.error('count and min-words must be positive; max-words must be >= min-words')
    if args.aspect != 'any' and not RATIO.fullmatch(args.aspect):
        parser.error('aspect must be any or a positive width:height ratio')
    if not VERSION.fullmatch(args.version):
        parser.error('version must be a complete numeric version')
    try:
        text = args.draft.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({'ok':False,'errors':[f'cannot read draft: {exc}']}, ensure_ascii=False))
        return 1
    prompts, errors = parse_draft(text)
    if len(prompts) != args.count:
        errors.append(f'prompt count is {len(prompts)}; expected {args.count}')
    results = [inspect_prompt(prompt, args) for prompt in prompts]
    report = {'ok':not errors and not any(x['errors'] for x in results),'skill':SKILL_KIND,'prompt_count':len(prompts),'word_count_rule':'whitespace-separated terms containing letters/digits, including all parameter flags and values; punctuation-only terms excluded','errors':errors,'prompts':results,'scope':'Text constraints only; no image generation or aesthetic evaluation.'}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
