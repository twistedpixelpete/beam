"""Build installable extension and source archives; no dependencies."""
from pathlib import Path
import zipfile
import tomllib

root=Path(__file__).resolve().parents[1]
package=root/'projection_study'
version=tomllib.loads((package/'blender_manifest.toml').read_text())['version']
dist=root/'dist'; dist.mkdir(exist_ok=True)

def files(folder):
    return sorted(p for p in folder.rglob('*') if p.is_file() and
                  '__pycache__' not in p.parts and p.name!='.DS_Store' and p.suffix not in {'.pyc','.blend1','.blend2'})

with zipfile.ZipFile(dist/f'beam-{version}.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in files(package): archive.write(path,path.relative_to(package))
with zipfile.ZipFile(dist/f'beam-source-{version}.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for folder in ('projection_study','tests','docs','examples','tools'):
        for path in files(root/folder): archive.write(path,path.relative_to(root))
    for name in ('README.md','TEST_RESULTS.txt','.gitignore'): archive.write(root/name,name)
print(f'Built extension and source archives for {version}')
