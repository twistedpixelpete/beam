import http from 'node:http';
import { readFile, realpath, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const args=process.argv.slice(2), option=(key,fallback)=>args.includes(key)?args[args.indexOf(key)+1]:fallback;
const packageRoot=await realpath(option('--package',path.join(root,'example')));
const port=Number(option('--port','8787'));
const mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.glb':'model/gltf-binary','.png':'image/png','.jpg':'image/jpeg'};
const server=http.createServer(async(req,res)=>{
 try {
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);res.end();return;}
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  let base=root, relative=pathname==='/'?'index.html':pathname.slice(1);
  if(pathname.startsWith('/package/')){base=packageRoot;relative=pathname.slice(9);}
  else if(pathname.startsWith('/vendor/')){base=path.join(root,'node_modules/three');relative=pathname.slice(8);}
  else if(!['index.html','app.js','core.js','style.css'].includes(relative)){res.writeHead(404);res.end();return;}
  const resolved=await realpath(path.resolve(base,relative));base=await realpath(base);
  if(!resolved.startsWith(base+path.sep)||!(await stat(resolved)).isFile()){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':mime[path.extname(resolved)]||'application/octet-stream','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self' blob:; object-src 'none'; frame-ancestors 'none'"});
  res.end(req.method==='HEAD'?undefined:await readFile(resolved));
 }catch{res.writeHead(404);res.end('Not found');}
});
server.listen(port,'127.0.0.1',()=>console.log(`Beam Review: http://127.0.0.1:${port}\nRead-only package: ${packageRoot}\nLocal prototype; no hosted authentication.`));
