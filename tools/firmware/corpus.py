#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below
# this header.
#
# Read-only query/build tool for the six-release firmware catalog (list, show, changes, find, functions). Depends on the research layout and local inventories that are NOT published (they describe extracted firmware). Kept for method reference.
#
# Original path in the research tree: firmware/tools/corpus.py
# Original SHA-256 (before this header was added): de092d331c2d9a504552fab922aca0eab603fb741ea735814ff57f227dcff2bf
# License: MIT (see repository LICENSE). No firmware or key is included.
# ---------------------------------------------------------------------------
"""Read-only bounded queries; explicit build writes only firmware catalog derivatives."""
import argparse
from collections import Counter, defaultdict
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import tarfile
import zlib

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'firmware'
PROFILE='source-metadata-v1-full-UTC;separate-payloads;no-nested'
RELEASES={'1.20':('TORAIZSP16_ver120/TORAIZSP16.UPD','decode/output/1.20','c1c77707c1a223fb09e6be32deb34bd2f7af7d333b340052ace10eae2ed8d8e4'),
 '1.30':('TORAIZSP16_ver130/TORAIZSP16.UPD','decode/output/1.30','6bb85a6638cee13411d8b3bfb603256194fd0c91bf92ee1ff51774ca76dbbde4'),
 '1.31':('TORAIZSP16_ver131/TORAIZSP16.UPD','decode/output/1.31','34cb5a861f8af001ed2b557e60c13b943f12dd15e594fbb04b50c8d1a1611dee'),
 '1.40':('TORAIZSP16_ver140/TORAIZSP16.UPD','decode/output/1.40','0d4f2792736f0bab92ac8014018d8593a5ddc6d7e95d4f56b5ca5f7c00ec3fe3'),
 '1.50':('ResearchSourceFiles/TORAIZSP16VER150.UPD','decode/output/image1','11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a'),
 '1.60':('ResearchSourceFiles/TORAIZSP16.UPD','decode/output/image2','ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4')}


def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()


def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def save(p,obj):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
def lines(p,rows):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w') as f:
  for r in rows: f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
def rel(p): return Path(p).relative_to(ROOT).as_posix()
def require(b,m):
 if not b: raise ValueError(m)

def safe(s):
 p=Path(s); require(not p.is_absolute() and '..' not in p.parts,'Unsafe member path')
 return p.as_posix()


def symbolic(s):
 bits=0
 for i,bit in enumerate((0o400,0o200,0o100,0o040,0o020,0o010,0o004,0o002,0o001),1):
  if s[i] in 'rwxst': bits|=bit
 for i,chars,bit in ((3,'sS',0o4000),(6,'sS',0o2000),(9,'tT',0o1000)):
  if s[i] in chars: bits|=bit
 return bits


def sfs_metadata(src):
 key=digest({'sha256':sha(src),'profile':PROFILE,'unsquashfs':sha(Path('/opt/homebrew/bin/unsquashfs'))})
 cache=BASE/'cache'/key
 if not cache.with_suffix('.json').exists():
  r=subprocess.run(['unsquashfs','-lln','-full','-UTC','-no-progress',str(src)],capture_output=True,timeout=120,
                   env={**os.environ,'LC_ALL':'C','TZ':'UTC'})
  cache.parent.mkdir(exist_ok=True)
  cache.with_suffix('.stdout.txt').write_bytes(r.stdout); cache.with_suffix('.stderr.txt').write_bytes(r.stderr)
  require(r.returncode==0,'SquashFS source listing failed')
  rows=[]
  pat=re.compile(r'^([-dlcbps][rwxstST-]{9})\s+(\d+)/(\d+)\s+(\S+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(.+)$')
  for line in r.stdout.decode().splitlines():
   if not line.strip(): continue
   m=pat.fullmatch(line); require(m is not None,'Unparsed SquashFS metadata: '+line)
   mode,uid,gid,size,date,t,name=m.groups()
   kind={'-':'file','d':'directory','l':'symlink','c':'character_device','b':'block_device','p':'fifo','s':'socket'}[mode[0]]
   target=None
   if kind=='symlink': name,mark,target=name.partition(' -> '); require(bool(mark),'Missing link')
   require(name=='squashfs-root' or name.startswith('squashfs-root/'),'Listing prefix')
   member=safe(name.removeprefix('squashfs-root').lstrip('/') or '.')
   row=dict(path=member,type=kind,mode=symbolic(mode),uid=int(uid),gid=int(gid),mtime_utc=date+' '+t)
   if kind=='file': row['size']=int(size)
   if target is not None: row['target']=target
   rows.append(row)
  save(cache.with_suffix('.json'),rows)
 return read(cache.with_suffix('.json'))


def category(path):
 if path.endswith('EP085_Main_R'): return 'application'
 if path=='images/uImage': return 'kernel'
 if 'u-boot' in path: return 'bootloader'
 if re.search(r'PANELCOM|\.mot$',path): return 'subcontrollers'
 if path.endswith('.so') or '.so.' in path: return 'shared-libraries'
 if 'Resource/' in path or any(x in path for x in ('/picture/','/font/','gui/','share/')): return 'ui-and-data'
 if path.endswith('.sh') or 'init.d/' in path or path.endswith('inittab'): return 'boot-and-scripts'
 if path.startswith('etc/') or 'setting' in path.lower(): return 'settings-and-config'
 return 'other'


def inventory(version,output):
 b=ROOT/output; report=read(b/'report.json'); iso=read(b/'iso-manifest.json')
 host={r['path']:r for r in read(b/'payload-manifest.json')}
 rows=[]
 for r in iso:
  mode=r['mode']; kind='file' if stat.S_ISREG(mode) else 'directory' if stat.S_ISDIR(mode) else 'symlink'
  row=dict(release=version,container='decoded.iso',container_sha256=report['decoded_sha256'],path=r['path'],type=kind,
           metadata={'mode':stat.S_IMODE(mode),'uid':None,'gid':None,'mtime':None}, metadata_source='Rock Ridge; owner/time not exported')
  for k in ('sha256','target'): 
   if k in r: row[k]=r[k]
  if kind=='file': row['size']=r['size']
  row['category']=category(r['path']); rows.append(row)
 for archive in sorted((b/'iso/images').iterdir()):
  if not (archive.name.endswith('.tar.gz') or archive.suffix=='.sfs'): continue
  container=archive.name; ch=sha(archive); prefix=container.removesuffix('.tar.gz').removesuffix('.sfs')
  require(next(r for r in iso if r['path']=='images/'+container)['sha256']==ch,'Archive identity disagrees with retained manifest')
  if archive.suffix=='.sfs':
   source=sfs_metadata(archive)
   # Relationships are verified from the accepted byte extraction, never used for source permissions.
   groups=defaultdict(list)
   for p in (b/'payloads'/prefix).rglob('*'):
    st=p.lstat()
    if stat.S_ISREG(st.st_mode): groups[(st.st_dev,st.st_ino)].append(p.relative_to(b/'payloads'/prefix).as_posix())
   links={p:sorted(g) for g in groups.values() if len(g)>1 for p in g}
  else:
   source=[]; links={}
   # Read actual source headers. Old reports remain read-only; retained metadata is compared below.
   with tarfile.open(archive,'r:gz') as tf:
    for m in tf:
     kind=next((k for yes,k in [(m.isfile(),'file'),(m.isdir(),'directory'),(m.issym(),'symlink'),(m.islnk(),'hardlink'),(m.ischr(),'character_device'),(m.isblk(),'block_device'),(m.isfifo(),'fifo')] if yes),'other')
     r=dict(path=safe(m.name),type=kind,mode=m.mode,uid=m.uid,gid=m.gid,mtime=m.mtime)
     if kind=='file': r['size']=m.size
     if kind in ('symlink','hardlink'): r['target']=m.linkname
     if kind in ('character_device','block_device'): r.update(devmajor=m.devmajor,devminor=m.devminor)
     source.append(r)
  for r in source:
   path=r['path']; hp=prefix+('/'+path if path!='.' else '')
   row=dict(release=version,container=container,container_sha256=ch,path=path,type=r['type'],
            metadata={k:v for k,v in r.items() if k in ('mode','uid','gid','mtime','mtime_utc','devmajor','devminor')},
            metadata_source='SquashFS source listing' if archive.suffix=='.sfs' else 'tar header', extracted_path=output+'/payloads/'+hp)
   if r['type'] in ('file','hardlink'):
    hr=host.get(hp); require(hr is not None and hr['type']=='file','Missing accepted file: '+hp)
    row.update(sha256=hr['sha256'],size=hr['bytes'])
    if 'size' in r: require(r['size']==hr['bytes'],'Source/retained size disagreement')
   elif r['type']=='symlink':
    require(host.get(hp,{}).get('target')==r['target'],'Link target disagreement')
   if 'target' in r: row['target']=r['target']
   if path in links: row['hardlink_members']=links[path]
   # Candidate root-relative path; archive provenance remains authoritative.
   row['logical_path']= (prefix+'/'+path if archive.suffix=='.sfs' else path)
   row['category']=category(row['logical_path']); rows.append(row)
 rows.sort(key=lambda r:(r['container'],r['path']))
 require(len({(r['container'],r['path']) for r in rows})==len(rows),'Duplicate inventory keys')
 return rows


def load_inventory(version):
 return [json.loads(l) for l in (BASE/'versions'/version/'inventory.jsonl').read_text().splitlines()]


def compare(left,right):
 a={(r['container'],r['path']):r for r in left}; b={(r['container'],r['path']):r for r in right}
 changes=[]; counts=Counter(); link_changes=[]
 for key in sorted(a.keys()|b.keys()):
  x=a.get(key); y=b.get(key)
  if x is None: status='added'
  elif y is None: status='removed'
  elif x['type']!=y['type'] or x.get('sha256')!=y.get('sha256') or x.get('size')!=y.get('size'): status='content-changed'
  elif x.get('target')!=y.get('target') or x.get('hardlink_members')!=y.get('hardlink_members'): status='link-changed'
  elif x['metadata']!=y['metadata']: status='metadata-only-changed'
  else: status='identical'
  counts[status]+=1
  if status!='identical':
   row=dict(container=key[0],path=key[1],status=status,source=x,destination=y); changes.append(row)
  if x and y and (x.get('target')!=y.get('target') or x.get('hardlink_members')!=y.get('hardlink_members')):
   link_changes.append(dict(container=key[0],path=key[1],source_target=x.get('target'),destination_target=y.get('target'),source_members=x.get('hardlink_members'),destination_members=y.get('hardlink_members')))
 # Candidate moves retain all same-byte alternatives; no unique installed-root assertion.
 removed=defaultdict(list); added=defaultdict(list)
 for k,x in a.items():
  if k not in b and x.get('sha256'): removed[x['sha256']].append('/'.join(k))
 for k,y in b.items():
  if k not in a and y.get('sha256'): added[y['sha256']].append('/'.join(k))
 source_occurrences=Counter(r.get('sha256') for r in a.values() if r.get('sha256'))
 destination_occurrences=Counter(r.get('sha256') for r in b.values() if r.get('sha256'))
 moves=[dict(sha256=h,source=removed[h],destination=added[h],source_occurrences=source_occurrences[h],destination_occurrences=destination_occurrences[h],
             ambiguous=source_occurrences[h]!=1 or destination_occurrences[h]!=1)
        for h in sorted(removed.keys()&added.keys())]
 return dict(counts=dict(sorted(counts.items())),source_entries=len(a),destination_entries=len(b),union_entries=len(a.keys()|b.keys()),
             changed_links=link_changes,candidate_moves=moves),changes



def logical_compare(left,right):
 """Compare candidate root paths without choosing overlay order or flattening collisions."""
 def group(rows):
  out=defaultdict(list)
  for r in rows:
   if r['container']=='decoded.iso': continue
   if r['path']=='.': continue
   out[r['logical_path']].append(r)
  return out
 a,b=group(left),group(right); counts=Counter(); changes=[]; placements=[]; collisions=[]
 def payload(r): return (r['type'],r.get('sha256'),r.get('size'),r.get('target'))
 for path in sorted(a.keys()|b.keys()):
  x,y=a.get(path,[]),b.get(path,[])
  cx=Counter(payload(r) for r in x);cy=Counter(payload(r) for r in y)
  if not x: status='added'
  elif not y: status='removed'
  elif cx!=cy: status='content-or-link-changed'
  elif Counter(digest(r['metadata']) for r in x)!=Counter(digest(r['metadata']) for r in y): status='metadata-only-changed'
  else: status='identical'
  counts[status]+=1
  if len(x)>1 or len(y)>1: collisions.append(path)
  origins=lambda rs:[dict(container=r['container'],path=r['path'],type=r['type'],sha256=r.get('sha256'),target=r.get('target')) for r in rs]
  if status not in ('identical','metadata-only-changed'): changes.append(dict(logical_path=path,status=status,source=origins(x),destination=origins(y)))
  if cx==cy and {r['container'] for r in x}!={r['container'] for r in y}: placements.append(dict(logical_path=path,source=origins(x),destination=origins(y)))
 return dict(counts=dict(sorted(counts.items())),source_paths=len(a),destination_paths=len(b),union_paths=len(a.keys()|b.keys()),
             collision_paths=collisions,placement_change_count=len(placements),mapping='Candidate root-relative member paths; SquashFS bin/lib/share prefix. No boot overlay order inferred.'),changes,placements


def component_index(rows):
 groups=defaultdict(list)
 for r in rows: groups[r['category']].append(r)
 summary={k:dict(entries=len(v),regular_bytes=sum(r.get('size',0) for r in v),
                content_inventory_digest=digest([{n:r.get(n) for n in ('container','path','type','sha256','size','target','hardlink_members')} for r in v]),
                source_metadata_digest=digest([{n:r.get(n) for n in ('container','path','metadata')} for r in v])) for k,v in sorted(groups.items())}
 selected=[r for r in rows if r['category'] in ('application','kernel','bootloader','subcontrollers') and r['type']=='file']
 containers=[dict(path=r['path'],sha256=r['sha256'],bytes=r['size']) for r in rows if r['container']=='decoded.iso' and r['path'].startswith('images/') and r['type']=='file']
 return dict(categories=summary,selected=selected,containers=containers)


def build():
 catalog=dict(schema_version=1,profile=PROFILE,releases={},coverage={'nested':'not expanded for new releases; retained old expansions not joined',
       'installed_root':'unresolved; logical paths are candidates, archive/path keys authoritative',
       'functions':'two-candidate 1.30--1.31 reader pilot; firmware/functions.json; other families/releases deferred','external_release_dates':'vendor history in firmware/release-notes.json; build timestamps are separate'})
 for v,(inp,out,expected) in RELEASES.items():
  vd=BASE/'versions'/v; vd.mkdir(parents=True,exist_ok=True)
  b=ROOT/out; report=read(b/'report.json')
  raw=(ROOT/inp).read_bytes(); require(hashlib.sha256(raw).hexdigest()==expected==report['input_sha256'],'Raw input identity: '+v)
  require(raw[-20:-9]==b'LIVESAMPLER' and raw[-9:-4].split(b'\0')[0].decode()==v==report['version_metadata']['release.txt'].strip(),'Version join: '+v)
  require(zlib.crc32(raw[:-20])==struct.unpack('<I',raw[-4:])[0],'Raw CRC: '+v)
  require(sha(b/'decoded.iso')==report['decoded_sha256'],'Decoded identity: '+v)
  app=b/'payloads/pdj/pdj/EP085_Main_R'; actual_app=sha(app)
  cachekey=digest(dict(raw=expected,report=sha(b/'report.json'),iso=sha(b/'iso-manifest.json'),payload=sha(b/'payload-manifest.json'),profile=PROFILE,tool_sha256=sha(Path(__file__))))
  inventory_path=vd/'inventory.jsonl'
  if (vd/'summary.json').exists() and read(vd/'summary.json').get('cache_key')==cachekey and sha(inventory_path)==read(vd/'summary.json')['inventory_sha256']:
   rows=load_inventory(v)
  else:
   rows=inventory(v,out); lines(inventory_path,rows)
  require(next(r['sha256'] for r in rows if r.get('extracted_path')==rel(app))==actual_app,'Original app binding: '+v)
  components=component_index(rows); save(vd/'components.json',components)
  summary=dict(schema_version=1,release=v,status='inventoried',cache_key=cachekey,counts=dict(Counter(r['type'] for r in rows)),
               inventory=rel(inventory_path),inventory_sha256=sha(inventory_path),components=rel(vd/'components.json'))
  save(vd/'summary.json',summary)
  metadata=report['version_metadata']; rev=metadata.get('system.rev','')
  analysis=[]
  if v=='1.60': analysis=[dict(project='ghidra/projects/SP16_1_60_ELF.gpr',program='/EP085_Main_R_fw160',original_elf_sha256=actual_app,annotations='preserved; not opened by catalog build')]
  if v=='1.50': analysis=[dict(project='experiments/provider-binding-20261010-072803/projects/SP16_1_50_provider.gpr',program='/EP085_Main_R',reference='experiments/provider-binding-20261010-072803/HANDOFF.md',original_elf_sha256=actual_app,status='existing focused research; consult handoff for project identities')]
  entry=dict(status=['discovered','validated','extracted','inventoried','compared'],raw=dict(path=inp,bytes=len(raw),sha256=expected,source_url=None,download_date=None),
             versions=dict(observed_trailer=v,decoded_release=metadata['release.txt'].strip(),app=metadata.get('app.rev','').strip(),
                           system=metadata.get('system.rev'),subcontrollers={k:val.strip() for k,val in metadata.items() if k.startswith('subucom')},
                           build_metadata=rev.split('BuildDate=',1)[-1].strip() if 'BuildDate=' in rev else None,external_release_date=read(BASE/'release-notes.json')['releases'][v]['release_date'],external_release_date_source=read(BASE/'release-notes.json')['source']),
             extraction=dict(path=out,report=out+'/report.json',report_sha256=sha(b/'report.json'),decoded_iso_sha256=report['decoded_sha256'],
                             reused=v in ('1.50','1.60'),payload_manifest=out+'/payload-manifest.json',payload_manifest_sha256=sha(b/'payload-manifest.json')),
             inventory=summary,analysis=analysis,application=dict(path=rel(app),sha256=actual_app,bytes=app.stat().st_size))
  kernel=(b/'iso/images/uImage').read_bytes()
  entry['kernel']=dict(container_sha256=sha(b/'iso/images/uImage'),payload_sha256=hashlib.sha256(kernel[64:]).hexdigest(),name=report['uImage']['name'],
                       header_timestamp=struct.unpack_from('>I',kernel,8)[0],load=hex(struct.unpack_from('>I',kernel,16)[0]),entry=hex(struct.unpack_from('>I',kernel,20)[0]),
                       os_arch_type_compression=list(kernel[28:32]))
  if v in ('1.30','1.31'):
   entry['status'].append('partially analyzed')
   entry['analysis'].append(dict(project='ghidra/versions/1.30--1.31/attempt-2/projects/SP16_130_131_ELF.gpr',program='/EP085_Main_R_fw'+v.replace('.',''),
                               original_elf_sha256=actual_app,scope='two reader candidates; no global autoanalysis; no annotation transfer',version_tracking_session='/SP16_130_131_reader_pilot'))
  catalog['releases'][v]=entry
  (vd/'README.md').write_text(f'# Firmware {v}\n\nVerified trailer and decoded release: {v}; app {entry["versions"]["app"]}. Source and build identities are in [catalog](../../catalog.json).\n\n[Components](components.json), [inventory summary](summary.json); complete local `inventory.jsonl` retains source metadata and separate container paths. Extraction: `{out}`'+(' (reused unchanged).\n' if v in ('1.50','1.60') else '.\n'))
  print(v,summary['counts'],flush=True)
 versions=list(RELEASES)
 for a,b in zip(versions,versions[1:]):
  d=BASE/'comparisons'/f'{a}--{b}'; d.mkdir(parents=True,exist_ok=True)
  pair_key=digest(dict(source=sha(BASE/'versions'/a/'inventory.jsonl'),destination=sha(BASE/'versions'/b/'inventory.jsonl'),profile=PROFILE,tool_sha256=sha(Path(__file__))))
  if (d/'summary.json').exists():
   prior=read(d/'summary.json')
   if prior.get('cache_key')==pair_key and all((d/name).is_file() and sha(d/name)==h for name,h in prior.get('output_identities',{}).items()) and len(prior.get('output_identities',{}))==5:
    print(a,b,'cached',prior['counts'],flush=True)
    continue
  summary,changes=compare(load_inventory(a),load_inventory(b))
  lines(d/'changes.jsonl',changes)
  summary['metadata_field_changes']=dict(sorted(Counter(','.join(sorted(k for k in r['source']['metadata'].keys()|r['destination']['metadata'].keys() if r['source']['metadata'].get(k)!=r['destination']['metadata'].get(k))) for r in changes if r['status']=='metadata-only-changed').items()))
  summary.update(schema_version=1,source_release=a,destination_release=b,source_inventory_sha256=sha(BASE/'versions'/a/'inventory.jsonl'),
                 destination_inventory_sha256=sha(BASE/'versions'/b/'inventory.jsonl'),profile=PROFILE,changes_sha256=sha(d/'changes.jsonl'))
  # Compact portable non-metadata changes; large provenance join stays local.
  save(d/'content-changes.json',[{k:r[k] for k in ('container','path','status')}|{'source_sha256':(r['source'] or {}).get('sha256'),'destination_sha256':(r['destination'] or {}).get('sha256')} for r in changes if r['status']!='metadata-only-changed'])
  lines(d/'candidate-moves.jsonl',summary.pop('candidate_moves'))
  summary['candidate_move_groups']=sum(1 for _ in (d/'candidate-moves.jsonl').open())
  logical,lchanges,placements=logical_compare(load_inventory(a),load_inventory(b))
  lines(d/'placement-changes.jsonl',placements)
  save(d/'logical-changes.json',lchanges)
  summary['logical_candidates']=logical
  summary['cache_key']=pair_key
  summary['output_identities']={name:sha(d/name) for name in ('changes.jsonl','content-changes.json','candidate-moves.jsonl','placement-changes.jsonl','logical-changes.json')}
  save(d/'summary.json',summary)
  ca=read(BASE/'versions'/a/'components.json'); cb=read(BASE/'versions'/b/'components.json')
  ah={r['path']:r['sha256'] for r in ca['selected']}; bh={r['path']:r['sha256'] for r in cb['selected']}
  core={p:('identical' if ah.get(p)==bh.get(p) else 'changed') for p in sorted(ah.keys()|bh.keys())}
  (d/'README.md').write_text(f'# {a} → {b}\n\nSeparate archive/path join: '+', '.join(f'{k}={v}' for k,v in summary['counts'].items())+'.\n\nSelected shipped components: '+', '.join(f'{p}: {s}' for p,s in core.items())+'.\n\n[Summary](summary.json), [candidate logical changes](logical-changes.json). Separate archive/path content changes are in local `content-changes.json`; local `candidate-moves.jsonl` and `placement-changes.jsonl` retain relocation alternatives. Full local `changes.jsonl` includes source and destination records. Metadata includes source mtime, so rebuild timestamp changes are counted. Candidate moves are not an installed-root reconstruction. Function/behavior coverage is separate.\n')
  print(a,b,summary['counts'],flush=True)
 save(BASE/'catalog.json',catalog)


def query(a):
 cat=read(BASE/'catalog.json')
 if a.command=='list':
  for v,e in cat['releases'].items(): print(v,','.join(e['status']),e['versions']['app'],e['application']['sha256'][:12])
 elif a.command=='show':
  e=cat['releases'][a.release]
  if a.component:
   cs=read(BASE/'versions'/a.release/'components.json')
   if a.component in cs['categories']: print(json.dumps(cs['categories'][a.component],indent=2))
   for r in cs['selected']+cs['containers']:
    if a.component in r.get('path','') or a.component==r.get('category'): print(json.dumps(r,sort_keys=True))
  else: print(json.dumps(e,indent=2))
 elif a.command=='changes':
  summary,rows=compare(load_inventory(a.source),load_inventory(a.destination))
  print(json.dumps(summary['counts'],sort_keys=True))
  selected=[r for r in rows if (a.metadata or r['status']!='metadata-only-changed') and (not a.pattern or a.pattern in r['path'])]
  for r in selected[:a.limit]: print(r['status'],r['container']+'/'+r['path'])
  print(f'{len(selected)} matching changes; showing {min(a.limit,len(selected))}')
 elif a.command=='find':
  found=[]
  for v in cat['releases']:
   for r in load_inventory(v):
    if a.pattern in r['path'] or a.pattern==r['category']: found.append((v,r))
  for v,r in found[:a.limit]: print(v,r['container']+'/'+r['path'],r['type'],r.get('sha256','')[:16])
  print(f'{len(found)} matches; showing {min(a.limit,len(found))}')
 elif a.command=='functions':
  p=BASE/'functions.json'; rows=read(p).get('correspondences',[]) if p.exists() else []
  rows=[r for r in rows if (not a.reviewed or r.get('reviewed')) and (not a.pattern or a.pattern in r.get('feature',''))]
  for r in rows[:a.limit]: print(json.dumps(r,sort_keys=True))
  print(f'{len(rows)} correspondences; showing {min(a.limit,len(rows))}')


def main():
 p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('build',help='Explicitly write catalog/inventories; never extract or audit')
 sub.add_parser('list')
 s=sub.add_parser('show'); s.add_argument('release',choices=RELEASES); s.add_argument('component',nargs='?')
 s=sub.add_parser('changes'); s.add_argument('source',choices=RELEASES); s.add_argument('destination',choices=RELEASES); s.add_argument('--metadata',action='store_true'); s.add_argument('--pattern'); s.add_argument('--limit',type=int,default=20)
 s=sub.add_parser('find'); s.add_argument('pattern'); s.add_argument('--limit',type=int,default=20)
 s=sub.add_parser('functions'); s.add_argument('--pattern'); s.add_argument('--reviewed',action='store_true'); s.add_argument('--limit',type=int,default=20)
 a=p.parse_args()
 if hasattr(a,'limit'): require(0<=a.limit<=1000,'Limit must be 0..1000')
 build() if a.command=='build' else query(a)
if __name__=='__main__': main()
