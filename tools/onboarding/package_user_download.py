"""Build the operator download from an explicit allowlist; preserve internal evidence."""
from pathlib import Path
import shutil
import tempfile
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'output/pdf/onboarding-0.13'
OUTPUT = ROOT / 'output/pdf/Beam_Onboarding'
ARCHIVE = ROOT / 'dist/Beam-Onboarding-0.13.0-beta.zip'
FILES = ('START_HERE.pdf', 'Beam_User_Guide.pdf', 'Beam_Quick_Start.pdf',
         'Beam_Training_Project.blend', 'Beam_Training_Project_Guide.pdf',
         'Install/beam-0.13.0.zip')


def welcome(path):
    c = canvas.Canvas(str(path), pagesize=(595.28, 841.89))
    c.setTitle('Start here - Beam onboarding')
    c.setAuthor('Twisted Pixel')
    ink, muted, mint = map(HexColor, ('#202B30', '#53656C', '#8BD7BD'))
    c.setFillColor(ink); c.rect(0, 660, 596, 182, fill=1, stroke=0)
    c.setFillColor(mint); c.setFont('Helvetica-Bold', 12)
    c.drawString(48, 790, 'BEAM  /  TWISTED PIXEL')
    c.setFillColor(HexColor('#FFFFFF')); c.setFont('Helvetica-Bold', 32)
    c.drawString(48, 736, 'Start here')
    c.setFont('Helvetica', 12); c.drawString(48, 706, 'Your first Beam study, in four steps.')
    c.setFillColor(mint); c.setFont('Helvetica', 10)
    c.drawString(48, 680, '0.13.0  |  Internal Production Beta  |  Still in testing')
    steps = [
        ('Install Beam', 'Install/beam-0.13.0.zip',
         'In Blender, open Preferences > Add-ons > menu > Install from Disk. Select this ZIP and enable Beam. Keep the ZIP zipped. Restart Blender after replacing an older build.'),
        ('Take the Quick Start', 'Beam_Quick_Start.pdf',
         'Follow the two-page walkthrough to create a screen, place a projector and build your first layout.'),
        ('Try the guided exercises', 'Beam_Training_Project.blend',
         'Open the training scene, then use File > Save As to make a working copy. Follow Beam_Training_Project_Guide.pdf alongside it. The original file is your reset point.'),
        ('Keep the full manual nearby', 'Beam_User_Guide.pdf',
         'Use the full guide for detailed workflows and the Where is it reference. Screenshots are included in the guides; no separate image files are needed.'),
    ]
    y = 620
    for i, (title, filename, body) in enumerate(steps, 1):
        c.setFillColor(mint); c.circle(61, y-3, 13, fill=1, stroke=0)
        c.setFillColor(ink); c.setFont('Helvetica-Bold', 11); c.drawCentredString(61, y-7, str(i))
        c.setFont('Helvetica-Bold', 16); c.drawString(86, y-8, title)
        c.setFont('Helvetica-Bold', 10); c.drawString(86, y-29, filename)
        c.setFillColor(muted); c.setFont('Helvetica', 10.5)
        for j, line in enumerate(simpleSplit(body, 'Helvetica', 10.5, 455)):
            c.drawString(48, y-55-j*15, line)
        y -= 124
    c.setStrokeColor(HexColor('#D4DFDB')); c.line(48, 112, 547, 112)
    c.setFillColor(muted); c.setFont('Helvetica', 9)
    c.drawString(48, 91, 'Tested with Blender 5.2.2 LTS / macOS 26.7.')
    c.drawString(48, 75, 'Work on copies and verify your study before production use.')
    c.save()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='beam-onboarding-', dir=OUTPUT.parent) as temp:
        stage = Path(temp)
        welcome(stage / 'START_HERE.pdf')
        for name in FILES[1:]:
            source = SOURCE / ('install/beam-0.13.0.zip' if name.startswith('Install/') else name)
            target = stage / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        # Only replace an existing output if it consists exclusively of known deliverables.
        # Evidence/source directories are never a destination of this builder.
        if OUTPUT.exists():
            unexpected = {p.relative_to(OUTPUT).as_posix() for p in OUTPUT.rglob('*') if p.is_file()} - set(FILES)
            if unexpected: raise ValueError(f'Unexpected files in delivery folder: {sorted(unexpected)}')
        OUTPUT.mkdir(exist_ok=True)
        for name in FILES:
            target = OUTPUT / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(stage / name, target)
    ARCHIVE.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in FILES: archive.write(OUTPUT / name, 'Beam_Onboarding/' + name)
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert set(archive.namelist()) == {'Beam_Onboarding/' + name for name in FILES}
        assert archive.testzip() is None
    print(f'Built {OUTPUT} and {ARCHIVE}: exactly {len(FILES)} files')

if __name__ == '__main__': build()
