"""Export paste only for Machine_Assembly_BOM.csv; never edit electrical source."""
from pathlib import Path
import pcbnew as p,csv,json,hashlib,subprocess,os,tempfile,re,shutil
W=Path(__file__).resolve().parent.parent;EL=W/'electrical';M=W/'manufacturing';V=W/'verification';source=EL/'Anticipy_R1_E1_PROTOTYPE.kicad_pcb';before=hashlib.sha256(source.read_bytes()).hexdigest();b=p.LoadBoard(str(source));fit={r['Reference']for r in csv.DictReader((M/'Machine_Assembly_BOM.csv').open())};assert len(fit)==47
removed=[];retained=[]
for f in b.GetFootprints():
 if f.GetReference()not in fit:
  changed=False
  for pad in f.Pads():
   layers=pad.GetLayerSet()
   if pad.IsOnLayer(p.F_Paste)or pad.IsOnLayer(p.B_Paste):changed=True
   layers.RemoveLayer(p.F_Paste);layers.RemoveLayer(p.B_Paste);pad.SetLayerSet(layers)
  if changed:removed.append(f.GetReference())
 else:retained.append(f.GetReference())
assert set(retained)==fit
out=M/'assembly_stencil_nominal';out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='anticipy_stencil_')as td:
 temp=Path(td)/source.name;p.SaveBoard(str(temp),b)
 env=dict(os.environ,KICAD_CONFIG_HOME=str(W/'kicad-config'))
 args=['/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','export','gerbers','--layers','F.Paste,B.Paste','-o',str(out)+'/',str(temp)];r=subprocess.run(args,capture_output=True,text=True,env=env,timeout=40);(V/'fitted_stencil.log').write_text(r.stdout+r.stderr);assert r.returncode==0
seen=set()
for f in out.glob('*.g*'):
 if f.suffix in ['.gtp','.gbp']:seen.update(re.findall(r'%TO.C,([^*]+)\*%',f.read_text()))
assert seen==fit,dict(extra=sorted(seen-fit),missing=sorted(fit-seen));assert hashlib.sha256(source.read_bytes()).hexdigest()==before
receipt={'source_sha256':before,'source_unchanged':True,'intended_fitted_count':len(fit),'fitted_references':sorted(fit),'references_removed_from_paste':sorted(removed),'actual_paste_references':sorted(seen),'all_paste_references_fitted':seen==fit,'scope':'Released nominal aperture geometry for exactly 47 fitted parts. Use 80 um laser-cut electropolished stencil and Type 5 SAC305 paste as the first-article process specification; do not blanket-resize apertures. U2 exposed-pad paste coverage is 62.86%. Assembler establishes its profiled reflow and SPI acceptance on first articles; geometry checks are not measured production yield.'};(V/'fitted_stencil_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

# Primary manufacturing Gerbers use fitted paste; archive only genuinely unfiltered native plots.
archive=V/'native_paste_reference_NOT_FOR_STENCIL';archive.mkdir(exist_ok=True)
for suffix in ['-F_Paste.gtp','-B_Paste.gbp']:
 name='Anticipy_R1_E1_PROTOTYPE'+suffix;dest=M/'gerbers'/name
 if dest.exists():
  refs=set(re.findall(r'%TO.C,([^*]+)\*%',dest.read_text()))
  if refs-fit:shutil.copyfile(dest,archive/name)
  shutil.copyfile(out/name,dest)
