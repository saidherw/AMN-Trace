"""AMN Trace MVP - local-first inspection traceability prototype.

Run: python amn_trace_mvp.py
Open: http://127.0.0.1:8080
No external packages are required; data is stored in SQLite and images in data/evidence.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from datetime import datetime, timezone
import base64, hashlib, json, mimetypes, os, sqlite3, threading, uuid

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EVIDENCE = DATA / "evidence"
DB_PATH = DATA / "amn_trace.db"
DATA.mkdir(exist_ok=True)
EVIDENCE.mkdir(exist_ok=True)
DB_LOCK = threading.Lock()

HTML = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMN Trace MVP</title>
<style>
:root{--navy:#123047;--teal:#007b83;--ink:#1e2933;--muted:#64717b;--line:#dce5e9;--pale:#eef7f7;--gold:#c69214}*{box-sizing:border-box}body{margin:0;background:#f6f8f9;color:var(--ink);font:15px Arial,sans-serif}header{background:var(--navy);color:#fff;padding:22px 34px;display:flex;justify-content:space-between;align-items:center}header h1{font-size:23px;margin:0}header span{color:#a8e1df;font-size:12px;letter-spacing:.12em}.wrap{max-width:1180px;margin:28px auto;padding:0 22px}.hero{display:flex;justify-content:space-between;gap:22px;align-items:end;margin-bottom:24px}.hero h2{color:var(--navy);font-size:27px;margin:0 0 8px}.hero p{margin:0;color:var(--muted)}.status{padding:10px 14px;border-radius:8px;background:#e7f5ee;color:#176b46;font-size:13px;white-space:nowrap}.grid{display:grid;grid-template-columns:360px 1fr;gap:22px}.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px;box-shadow:0 3px 12px #1230470a}.card h3{margin:0 0 16px;color:var(--navy);font-size:17px}label{display:block;font-size:12px;font-weight:bold;color:var(--muted);margin:12px 0 5px}input,select,textarea{width:100%;border:1px solid #cbd7dc;border-radius:7px;padding:10px;font:inherit;background:#fff}button{border:0;border-radius:7px;padding:11px 15px;font-weight:bold;cursor:pointer}button.primary{background:var(--teal);color:#fff;width:100%;margin-top:17px}button.secondary{background:var(--pale);color:var(--teal)}.filters{display:grid;grid-template-columns:1fr 150px 120px;gap:10px;margin-bottom:14px}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;background:var(--navy);color:#fff;padding:11px 9px}td{border-bottom:1px solid var(--line);padding:11px 9px;vertical-align:top}tr:hover td{background:#f7fbfb}.badge{display:inline-block;border-radius:20px;padding:4px 9px;font-size:11px;font-weight:bold}.OK{background:#def5e7;color:#176b46}.NOK{background:#fde4e2;color:#a62e29}.PENDIENTE{background:#fff1ce;color:#7d5b00}.detail{margin-top:18px;background:var(--pale);border-radius:9px;padding:14px;display:none}.detail img{max-width:210px;max-height:150px;border-radius:6px;border:1px solid var(--line);margin-top:8px}.kv{display:grid;grid-template-columns:145px 1fr;gap:5px;font-size:13px}.kv b{color:var(--muted)}.small{font-size:12px;color:var(--muted);line-height:1.4}.empty{padding:35px;text-align:center;color:var(--muted)}@media(max-width:800px){.grid{grid-template-columns:1fr}.hero{display:block}.status{display:inline-block;margin-top:14px}.filters{grid-template-columns:1fr 1fr}.filters input{grid-column:1/-1}}
</style></head><body><header><h1>AMN Trace <span>MVP</span></h1><span>LOCAL-FIRST · EVIDENCIA DE INSPECCIÓN</span></header>
<main class="wrap"><div class="hero"><div><h2>Registro de trazabilidad</h2><p>Registra cada pieza, incluso las inspecciones OK, con su evidencia visual.</p></div><div class="status" id="status">● Operación local activa</div></div>
<div class="grid"><section class="card"><h3>Nueva inspección</h3><form id="form"><label>ID / número de serie *</label><input id="serial" required placeholder="SN-004928184"><label>Número de parte *</label><input id="part" required placeholder="AMN-TSL-000234"><label>Lote / orden de producción</label><input id="lot" placeholder="LOTE-2026-0903 / OP-4812"><label>Línea / estación</label><input id="station" placeholder="Línea 2 / Estación 4"><label>Operador</label><input id="operator" placeholder="Operador turno B"><label>Resultado *</label><select id="result"><option>OK</option><option>NOK</option><option>PENDIENTE</option></select><label>Motivo / comentario</label><textarea id="note" rows="2" placeholder="Defecto o comentario opcional"></textarea><label>Imagen de evidencia</label><input id="image" type="file" accept="image/*"><p class="small">La imagen se guarda localmente. Si no hay red, el registro queda pendiente de sincronización.</p><button class="primary">Guardar inspección</button></form></section>
<section class="card"><h3>Expedientes recientes</h3><div class="filters"><input id="q" placeholder="Buscar serie, parte, lote u operador"><select id="filter"><option value="">Todos</option><option>OK</option><option>NOK</option><option>PENDIENTE</option></select><button class="secondary" onclick="load()">Actualizar</button></div><div id="table"><div class="empty">Cargando registros...</div></div><div class="detail" id="detail"></div></section></div></main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function load(){const p=new URLSearchParams({q:document.querySelector('#q').value,result:document.querySelector('#filter').value});const r=await fetch('/api/inspections?'+p);const d=await r.json();if(!d.items.length){document.querySelector('#table').innerHTML='<div class="empty">No hay registros que coincidan.</div>';return}document.querySelector('#table').innerHTML='<table><thead><tr><th>Pieza</th><th>Resultado</th><th>Fecha/hora</th><th>Contexto</th></tr></thead><tbody>'+d.items.map(x=>`<tr onclick="show('${x.id}')"><td><b>${esc(x.serial)}</b><br><span class="small">${esc(x.part)}</span></td><td><span class="badge ${esc(x.result)}">${esc(x.result)}</span><br><span class="small">${esc(x.sync_status)}</span></td><td>${esc(x.inspected_at.replace('T',' ').replace('Z',''))}</td><td>${esc(x.station||'-')}<br><span class="small">${esc(x.operator||'-')}</span></td></tr>`).join('')+'</tbody></table>'}
async function show(id){const r=await fetch('/api/inspections/'+id);const x=await r.json();let img=x.image_path?`<img src="/evidence/${encodeURIComponent(x.image_path)}">`:'';const d=document.querySelector('#detail');d.style.display='block';d.innerHTML=`<div class="kv"><b>ID de evento</b><span>${esc(x.id)}</span><b>Hash SHA-256</b><span class="small">${esc(x.image_sha256||'Sin imagen')}</span><b>Lote / orden</b><span>${esc(x.lot||'-')}</span><b>Comentario</b><span>${esc(x.note||'-')}</span><b>Auditoría</b><span>Creado por ${esc(x.created_by)} · ${esc(x.created_at.replace('T',' ').replace('Z',''))}</span></div>${img}`}
document.querySelector('#q').addEventListener('input',load);document.querySelector('#filter').addEventListener('change',load);
document.querySelector('#form').addEventListener('submit',async e=>{e.preventDefault();const f=document.querySelector('#image').files[0];let image_base64=null,image_name=null;if(f){image_base64=await new Promise((ok,no)=>{const r=new FileReader();r.onload=()=>ok(r.result.split(',')[1]);r.onerror=no;r.readAsDataURL(f)});image_name=f.name}const body={serial:serial.value,part:part.value,lot:lot.value,station:station.value,operator:operator.value,result:result.value,note:note.value,image_base64,image_name};const r=await fetch('/api/inspections',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();if(!r.ok){alert(d.error||'No se pudo guardar');return}e.target.reset();document.querySelector('#status').textContent='● Guardado local: '+d.id;load();show(d.id)});load();
</script></body></html>'''

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS inspections(
      id TEXT PRIMARY KEY, serial TEXT NOT NULL, part TEXT NOT NULL, lot TEXT,
      station TEXT, operator TEXT, result TEXT NOT NULL, note TEXT,
      inspected_at TEXT NOT NULL, created_at TEXT NOT NULL, created_by TEXT NOT NULL,
      image_path TEXT, image_sha256 TEXT, sync_status TEXT NOT NULL DEFAULT 'PENDIENTE',
      synced_at TEXT)""")
    conn.commit()
    return conn

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')

def row_json(row): return dict(row)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send_json(self, payload, status=200):
        data=json.dumps(payload, ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/': return self.send_text(HTML, 'text/html; charset=utf-8')
        if path.startswith('/evidence/'):
            name=Path(path[len('/evidence/'):]).name; f=EVIDENCE/name
            if not f.exists(): return self.send_json({'error':'No encontrado'},404)
            data=f.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(f.name)[0] or 'application/octet-stream'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if path=='/api/health': return self.send_json({'ok':True,'mode':'local-first','database':str(DB_PATH)})
        if path=='/api/inspections':
            qs=parse_qs(urlparse(self.path).query); q=qs.get('q',[''])[0].strip(); result=qs.get('result',[''])[0]
            sql='SELECT * FROM inspections WHERE 1=1'; args=[]
            if q: sql+=' AND (serial LIKE ? OR part LIKE ? OR lot LIKE ? OR operator LIKE ?)'; args += [f'%{q}%']*4
            if result: sql+=' AND result=?'; args.append(result)
            sql+=' ORDER BY inspected_at DESC LIMIT 200'
            with DB_LOCK:
                c=db(); rows=[row_json(x) for x in c.execute(sql,args).fetchall()]; c.close()
            return self.send_json({'items':rows,'count':len(rows)})
        if path.startswith('/api/inspections/'):
            ident=path.rsplit('/',1)[1]
            with DB_LOCK:
                c=db(); row=c.execute('SELECT * FROM inspections WHERE id=?',(ident,)).fetchone(); c.close()
            return self.send_json(row_json(row) if row else {'error':'No encontrado'}, 200 if row else 404)
        return self.send_json({'error':'Ruta no encontrada'},404)
    def send_text(self,text,ctype):
        data=text.encode(); self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_POST(self):
        path=urlparse(self.path).path
        if path!='/api/inspections': return self.send_json({'error':'Ruta no encontrada'},404)
        try: body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
        except Exception: return self.send_json({'error':'JSON inválido'},400)
        if not body.get('serial') or not body.get('part') or body.get('result') not in {'OK','NOK','PENDIENTE'}: return self.send_json({'error':'serial, part y result son obligatorios'},400)
        ident='INSP-'+datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+uuid.uuid4().hex[:10].upper(); image_path=None; image_hash=None
        if body.get('image_base64'):
            try:
                raw=base64.b64decode(body['image_base64'],validate=True); ext=Path(body.get('image_name') or 'evidence.jpg').suffix.lower()
                if ext not in {'.jpg','.jpeg','.png','.webp','.bmp'}: ext='.jpg'
                name=ident+ext; (EVIDENCE/name).write_bytes(raw); image_path=name; image_hash=hashlib.sha256(raw).hexdigest()
            except Exception: return self.send_json({'error':'Imagen inválida'},400)
        ts=now(); values=(ident,body['serial'].strip(),body['part'].strip(),body.get('lot','').strip(),body.get('station','').strip(),body.get('operator','').strip(),body['result'],body.get('note','').strip(),ts,ts,'MVP-LOCAL',image_path,image_hash,'PENDIENTE',None)
        with DB_LOCK:
            c=db(); c.execute('INSERT INTO inspections VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',values); c.commit(); c.close()
        return self.send_json({'ok':True,'id':ident,'sync_status':'PENDIENTE'},201)

if __name__=='__main__':
    with DB_LOCK: db().close()
    print('AMN Trace MVP: http://127.0.0.1:8080')
    ThreadingHTTPServer(('127.0.0.1',8080),Handler).serve_forever()
