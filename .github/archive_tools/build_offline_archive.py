from pathlib import Path
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):
            h.update(data)
    return h.hexdigest()

def make_bundle(source, output):
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
        for p in sorted(source.rglob('*')):
            if not p.is_file():
                continue
            info=zipfile.ZipInfo(p.relative_to(source.parent).as_posix(),date_time=(2026,10,15,0,0,0))
            info.create_system=3
            info.external_attr=0o100644 << 16
            info.compress_type=zipfile.ZIP_STORED
            info.file_size=p.stat().st_size
            with p.open('rb') as incoming,archive.open(info,'w') as outgoing:
                shutil.copyfileobj(incoming,outgoing,1024*1024)
    return {'bytes':output.stat().st_size,'sha256':digest(output)}

def main():
    repo=Path.cwd()
    mapping=json.loads((repo/'在线资源映射.json').read_text())
    tag=mapping['release_tag']
    name=os.environ['GH_REPO']
    scratch=Path(tempfile.mkdtemp(prefix='offline-archive-',dir=os.environ.get('RUNNER_TEMP')))
    source=scratch/'飞书Skill与教程资料库'
    source.mkdir()
    # Only restore media bytes. Source documents are supplied unchanged in the source snapshot.
    for p in repo.rglob('*'):
        if p.is_file() and '.git' not in p.relative_to(repo).parts and p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'}:
            dest=source/p.relative_to(repo)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
    subprocess.run(['gh','release','download',tag,'-R',name,'-p','offline-document-sources.zip','-D',str(scratch)],check=True)
    snapshot=scratch/'offline-document-sources.zip'
    assert digest(snapshot)==mapping['offline_source_snapshot']['sha256']
    with zipfile.ZipFile(snapshot) as z:
        assert all(not p.startswith('/') and '..' not in Path(p).parts for p in z.namelist())
        z.extractall(source)
    media=scratch/'videos'
    subprocess.run(['gh','release','download',tag,'-R',name,'-p','video-*.mp4','-D',str(media)],check=True)
    for video in mapping['videos']:
        original=media/video['asset_name']
        assert digest(original)==video['sha256'], video['asset_name']
        destination=source/video['offline_path']
        destination.parent.mkdir(parents=True,exist_ok=True)
        os.link(original,destination)
    checks=(source/'SHA256SUMS.txt').read_text().splitlines()
    for line in checks:
        sha,path=line.split('  ',1)
        assert digest(source/path)==sha, path
    output=scratch/mapping['full_offline_archive']['asset_name']
    result=make_bundle(source,output)
    assert result['bytes']==mapping['full_offline_archive']['bytes']
    assert result['sha256']==mapping['full_offline_archive']['sha256']
    subprocess.run(['gh','release','upload',tag,str(output),'-R',name,'--clobber'],check=True)
    print(json.dumps({'verified_original_files':len(checks),'bundle':result}),flush=True)

if __name__=='__main__':
    main()
