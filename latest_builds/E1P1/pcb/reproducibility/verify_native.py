from pathlib import Path
import subprocess,os,json,hashlib,time
W=Path(__file__).resolve().parent.parent; E=W/'electrical'; V=W/'verification'; V.mkdir(exist_ok=True)
name='Anticipy_R1_E1_PROTOTYPE'; cli='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
env=dict(os.environ,KICAD_CONFIG_HOME=str(W/'kicad-config'),KICAD10_FOOTPRINT_DIR='/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints',KICAD10_SYMBOL_DIR='/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={p.name:sha(p) for p in E.iterdir() if p.suffix in ('.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru','.kicad_sym')}
commands=[('drc_parity',['pcb','drc','--all-track-errors','--schematic-parity','--format','json','--severity-all','--exit-code-violations','-o',str(V/'drc_parity.json'),str(E/(name+'.kicad_pcb'))]),('erc',['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(V/'erc.json'),str(E/(name+'.kicad_sch'))]),('netlist',['sch','export','netlist','--format','kicadxml','-o',str(V/'native_netlist.xml'),str(E/(name+'.kicad_sch'))])]
rows=[]
for tag,args in commands:
 t=time.monotonic(); r=subprocess.run([cli]+args,env=env,capture_output=True,text=True,timeout=50)
 (V/(tag+'.log')).write_text(r.stdout+r.stderr)
 rows.append(dict(task=tag,command=[cli]+args,return_code=r.returncode,elapsed_seconds=round(time.monotonic()-t,3)))
 print(tag,r.returncode,r.stdout.strip(),flush=True)
assert all(sha(E/n)==h for n,h in hashes.items()),'Source mutated during checks'
receipt=dict(kicad_version=subprocess.check_output([cli,'version'],text=True).strip(),source_sha256=hashes,commands=rows,source_unchanged=True,fresh_fill='U4 routing repair filled through native KiCad PCB Editor on isolated board before component metadata update; no copper changes during metadata update.')
(V/'final_native_checks.json').write_text(json.dumps(receipt,indent=2))
assert all(r['return_code']==0 for r in rows),'Native check failed; inspect reports'
