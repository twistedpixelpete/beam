"""Writes Start-Here.html and Test-Report.txt for a tester package, from docs/TESTING.md.

    python3 tools/tester_package.py OUT_DIR VERSION

The package is these two files plus the extension zip for VERSION, Learn-Beam.blend
from tools/learn_scene.py and Beam-Test-Scene.blend from tests/feature_scene.py.
The checklist comes from docs/TESTING.md, so update that rather than this file.
"""
import html
import re
import sys
from pathlib import Path

out = Path(sys.argv[1])
VERSION = sys.argv[2]
testing = (Path(__file__).resolve().parents[1] / 'docs' / 'TESTING.md').read_text()

checklist = testing[testing.index('## Hands-on checklist'):testing.index('## Learn Beam scene')]
sections = []
for block in re.split(r'^### ', checklist, flags=re.M)[1:]:
    title, *lines = block.strip().splitlines()
    items = [line[6:] for line in lines if line.startswith('- [ ] ')]
    sections.append((title, items))
learn_block = testing[testing.index('## Learn Beam scene'):testing.index('## Other tests')]
learn_items = [line[6:] for line in learn_block.splitlines() if line.startswith('- [ ] ')]
sections = [s for s in sections] + [('Learn Beam scene', learn_items)]


def inline(text):
    text = html.escape(text)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)


def checklist_html():
    parts = []
    number = 0
    for title, items in sections:
        parts.append(f'<h3>{inline(title)}</h3><ol start="{number + 1}">')
        for item in items:
            number += 1
            parts.append(f'<li>{inline(item)}</li>')
        parts.append('</ol>')
    return '\n'.join(parts)


page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Beam Tester Guide</title>
<style>
:root {{ --ink:#1b1f24; --muted:#5b6470; --line:#dde2e8; --accent:#1f6feb; --panel:#f5f7fa; }}
body {{ margin:0; background:#fff; color:var(--ink); font:16px/1.55 -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width:760px; margin:0 auto; padding:40px 20px 80px; }}
h1 {{ font-size:30px; margin:0 0 4px; }} h2 {{ margin-top:44px; border-top:1px solid var(--line); padding-top:24px; }}
h3 {{ margin:28px 0 6px; font-size:17px; }}
.sub {{ color:var(--muted); margin:0 0 24px; }}
.box {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px 18px; margin:16px 0; }}
code {{ background:var(--panel); border:1px solid var(--line); border-radius:4px; padding:1px 5px; font-size:14px; }}
table {{ border-collapse:collapse; width:100%; }} td {{ border-top:1px solid var(--line); padding:8px 6px; vertical-align:top; }}
td:first-child {{ white-space:nowrap; font-weight:600; padding-right:16px; }}
li {{ margin:4px 0; }}
@media print {{ h2 {{ break-before:page; }} }}
</style></head><body><main>
<h1>Testing Beam {VERSION}</h1>
<p class="sub">Beam is an open-source Blender extension for planning projection: throw, coverage, blends and exports for media servers. Thank you for testing it.</p>

<div class="box"><strong>What's being tested.</strong> A new interface: a shorter header, a Surface tab, a project dropdown above the tabs, and the Projector tab in job order. Results and exports shouldn't change from 0.14.0. Most useful of all is anything that's hard to find, confusing or slow.</div>

<h2>What's in this folder</h2>
<table>
<tr><td>beam-{VERSION}.zip</td><td>The Beam extension. Install it, but don't unzip it.</td></tr>
<tr><td>Learn-Beam.blend</td><td>A guided scene. Start here to learn Beam.</td></tr>
<tr><td>Beam-Test-Scene.blend</td><td>Every feature in one scene, including deliberate stress cases. Used for the checklist.</td></tr>
<tr><td>Test-Report.txt</td><td>Fill this in and send it back.</td></tr>
</table>

<h2>1. Install</h2>
<ol>
<li>Use <strong>Blender 5.2 LTS</strong>. Beam is mostly tested on 5.2.2 on a Mac with Apple silicon. Testing on Windows or Linux is especially welcome.</li>
<li>Use a Blender where you have no important work open, and save anything you care about first.</li>
<li>Open <strong>Edit › Preferences › Get Extensions</strong>. In the menu at the top right, choose <strong>Install from Disk</strong>, then select <code>beam-{VERSION}.zip</code>.</li>
<li>Make sure <strong>Beam</strong> is ticked under <strong>Add-ons</strong>. This replaces any Beam you already have.</li>
</ol>

<h2>2. Learn Beam (about 20 minutes)</h2>
<ol>
<li>Open <code>Learn-Beam.blend</code>. It opens on the Beam workspace, with Beam in the column on the right.</li>
<li>Click the <strong>Views</strong> tab, press <strong>View</strong>, then <strong>Next</strong> to visit each station. Press <strong>Exit</strong> to look around freely.</li>
<li>Follow the steps on each sign. The same steps are in Blender's Text Editor, in the text called <strong>Learn Beam</strong>.</li>
<li>To start again, reopen the file without saving.</li>
</ol>
<p>Please note any step you couldn't follow as written, any control you couldn't find, and anywhere you got stuck.</p>

<h2>3. Check every feature</h2>
<p>Open <code>Beam-Test-Scene.blend</code>. Each section has a numbered label on the floor. Work through the list below and record each item in <code>Test-Report.txt</code>. Some items are meant to fail on purpose. For example, one projector has nothing to hit, so CSV export should refuse.</p>
<p>The scene is deliberately heavy: a large venue scan and 3,000 extra objects. A short pause when it opens is expected.</p>
{checklist_html()}

<h2>4. Report back</h2>
<p>Fill in <code>Test-Report.txt</code> and send it with any screenshots. For each problem, the most useful details are:</p>
<ul>
<li>what you did, step by step</li>
<li>what you expected, and what happened instead</li>
<li>the exact text of any message, especially a red <strong>Beam needs attention</strong> box</li>
<li>a screenshot of the whole Blender window</li>
</ul>
<p>Opinions count as much as bugs. "I couldn't find X", "this name didn't make sense" or "this felt slow" are all useful.</p>

<h2>Good to know</h2>
<ul>
<li>This is an unreleased test build, not a public release. Please don't share it.</li>
<li>Beam treats alpha cut-outs as solid in normal planning. Only <strong>Cycles Render</strong> mode lets light through them.</li>
<li>Surface Analysis can freeze Blender for a few seconds on big meshes while it works.</li>
<li>To go back to the released Beam, install the 0.14.0 zip the same way.</li>
</ul>
</main></body></html>
'''
(out / 'Start-Here.html').write_text(page)

lines = [
    f'BEAM {VERSION} TEST REPORT',
    '',
    'Tester:',
    'Date:',
    'Computer and operating system (e.g. MacBook Pro M3, macOS 15):',
    'Blender version (Help > About):',
    'Keymap (Blender default or Industry Compatible):',
    '',
    'For each item, write PASS, FAIL or SKIP, and a note if useful.',
    'Example:   12. FAIL  Overlap changed but the projectors did not move.',
    '',
    '=' * 60,
    'PART 1: LEARN BEAM',
    '=' * 60,
    'Steps I could not follow as written, or controls I could not find:',
    '',
    '',
    'Where I got stuck or confused:',
    '',
    '',
    '=' * 60,
    'PART 2: FEATURE CHECKLIST (Beam-Test-Scene.blend)',
    '=' * 60,
]
number = 0
for title, items in sections:
    lines += ['', title.upper()]
    for item in items:
        number += 1
        lines.append(f'{number:>3}. ____  {item.replace("`", "")}')
lines += [
    '',
    '=' * 60,
    'PART 3: PROBLEMS',
    '=' * 60,
    'Copy this block for each problem.',
    '',
    'What I did:',
    'What I expected:',
    'What happened:',
    'Exact message text, if any:',
    'Screenshot file name:',
    '',
    '=' * 60,
    'PART 4: OVERALL',
    '=' * 60,
    'What was hard to find?',
    '',
    'What names or labels did not make sense?',
    '',
    'What felt slow?',
    '',
    'Anything else?',
    '',
]
(out / 'Test-Report.txt').write_text('\n'.join(lines))
print(number, 'checklist items')
