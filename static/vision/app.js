const $=id=>document.getElementById(id);
let stream=null, running=false, generation=0, starting=false;
let pending=null, loopTimer=null, overlayTimer=null;
const interval=100;
const video=$('video'), canvas=$('capture'), ctx=canvas.getContext('2d');
const overlay=$('overlay'), ink=overlay.getContext('2d');
const edges=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],[5,9],[9,10],[10,11],[11,12],[9,13],[13,14],[14,15],[15,16],[13,17],[0,17],[17,18],[18,19],[19,20]];
function clearOverlay(){ink.clearRect(0,0,overlay.width,overlay.height);}
function drawHands(hands){
 clearTimeout(overlayTimer);clearOverlay();
 ink.strokeStyle='#28d2dc';ink.fillStyle='#b4f5d4';ink.lineWidth=2;
 for(const hand of hands){
  const points=hand.landmarks||[];if(points.length!==21)continue;
  for(const [a,b] of edges){ink.beginPath();ink.moveTo(points[a][0]*overlay.width,points[a][1]*overlay.height);ink.lineTo(points[b][0]*overlay.width,points[b][1]*overlay.height);ink.stroke();}
  for(const [x,y] of points){ink.beginPath();ink.arc(x*overlay.width,y*overlay.height,4,0,Math.PI*2);ink.fill();}
 }
 // Do not leave stale landmarks floating over live video on a stalled request.
 overlayTimer=setTimeout(clearOverlay,300);
}
const csrf=()=>document.cookie.split('; ').find(c=>c.startsWith('csrftoken='))?.split('=')[1] || '';
function message(text){$('message').textContent=text;}
function reset(){ $('total').textContent='0'; $('hands').textContent='0'; $('meter').style.width='0%'; $('gesture').textContent='Esperando tus manos'; $('fps').textContent='— FPS'; }
function stop(){running=false;generation++;clearTimeout(loopTimer);clearTimeout(overlayTimer);pending?.abort();pending=null;if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;video.srcObject=null;video.hidden=true;overlay.hidden=true;clearOverlay();$('start').disabled=starting;$('stop').disabled=true;$('status').textContent='● Cámara apagada';$('placeholder').hidden=false;reset();}
$('stop').onclick=()=>{stop();message('Cámara detenida. Tu historial se conserva en esta sesión.');};
$('start').onclick=async()=>{
 if(running||starting)return;
 starting=true;$('start').disabled=true;$('stop').disabled=false;const token=++generation;
 try{
  if(!navigator.mediaDevices?.getUserMedia)throw new Error('Abre la app en http://127.0.0.1:8000 o mediante HTTPS para acceder a la cámara.');
  const acquired=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:480},frameRate:{ideal:30,max:30}},audio:false});
  if(token!==generation){acquired.getTracks().forEach(t=>t.stop());return;}
  stream=acquired;video.srcObject=stream;await video.play();
  if(token!==generation)return;
  canvas.width=overlay.width=640;canvas.height=overlay.height=Math.round(video.videoHeight*640/video.videoWidth)||480;
  video.parentElement.style.aspectRatio=`${canvas.width} / ${canvas.height}`;
  video.hidden=false;overlay.hidden=false;$('placeholder').hidden=true;
  stream.getVideoTracks().forEach(track=>track.addEventListener('ended',()=>{if(token===generation){stop();message('La cámara se desconectó. Vuelve a iniciar.');}}));
  running=true;$('stop').disabled=false;$('status').textContent='● Cámara activa';message('Preparando detector… El primer fotograma puede tardar unos segundos.');loop(token);
 }catch(e){if(token!==generation)return;stop();message(e.name==='NotAllowedError'?'Permiso denegado. Habilita la cámara en tu navegador e inténtalo otra vez.':e.name==='NotFoundError'?'No se encontró una cámara conectada.':e.message);}
 finally{starting=false;$('start').disabled=running;}
};
async function loop(token){
 if(!running||token!==generation)return;
 const began=performance.now();
 try{
  // Mirror before processing so the annotated result matches the user's movement.
  ctx.setTransform(-1,0,0,1,640,0);ctx.drawImage(video,0,0,canvas.width,canvas.height);ctx.setTransform(1,0,0,1,0,0);
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.75));
  if(!blob)throw new Error('No se pudo capturar un fotograma.');
  if(!running||token!==generation)return;
  const controller=new AbortController();pending=controller;
  const timeout=setTimeout(()=>controller.abort(),30000);
  let response;
  try{response=await fetch('/api/frame/',{method:'POST',headers:{'Content-Type':'image/jpeg','X-CSRFToken':csrf()},body:blob,signal:controller.signal});}
  finally{clearTimeout(timeout);if(pending===controller)pending=null;}
  if(token!==generation)return;
  if(response.status===429){loopTimer=setTimeout(()=>loop(token),interval);return;}
  if(!response.ok){let data=await response.json().catch(()=>({}));throw new Error(data.error||`Error del servidor (${response.status}). Revisa la terminal.`);}
  const data=await response.json();if(token!==generation)return;
  drawHands(data.hands);
  $('total').textContent=data.total;$('hands').textContent=data.hands.length;$('meter').style.width=(data.total*10)+'%';
  $('gesture').textContent=data.hands.map(h=>h.gesture).join(' + ')||'Sin manos visibles';
  message(data.warning||(data.saved?'✓ Gesto registrado en el historial.':'Mantén el gesto estable. Se guardan cambios, no cada fotograma.'));
  if(data.saved)refresh();
  const elapsed=performance.now()-began;$('fps').textContent=(1000/Math.max(interval,elapsed)).toFixed(1)+' análisis/s · '+Math.round(elapsed)+' ms';
  loopTimer=setTimeout(()=>loop(token),Math.max(0,interval-elapsed));
 }catch(e){if(token!==generation)return;stop();message(e.name==='AbortError'?'El detector tardó demasiado. Revisa el servidor y vuelve a iniciar.':e.message);}
}
async function refresh(){
 try{
  const r=await fetch('/api/history/');if(!r.ok)throw new Error('No se pudo cargar el historial. Revisa la base de datos.');const data=await r.json();
  $('event-count').textContent=data.count;$('rows').replaceChildren();
  if(!data.events.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=4;td.textContent='Aún no hay eventos. Inicia la cámara para comenzar.';tr.append(td);$('rows').append(tr);}
  for(const event of data.events){const tr=document.createElement('tr');for(const value of [event.time,event.gesture,event.fingers,event.hands]){const td=document.createElement('td');td.textContent=value;tr.append(td);}$('rows').append(tr);}
  $('top').replaceChildren();if(!data.top.length)$('top').textContent='Tus estadísticas aparecerán aquí.';
  for(const item of data.top){const row=document.createElement('div');row.className='stat-row';const label=document.createElement('span'),n=document.createElement('b');label.textContent=item.gesture;n.textContent=item.count;row.append(label,n);$('top').append(row);}
 }catch(e){message(e.message);}
}
window.addEventListener('pagehide',stop);
document.addEventListener('visibilitychange',()=>{if(document.hidden&&(running||starting)){stop();message('Cámara detenida al cambiar de pestaña.');}});
refresh();
