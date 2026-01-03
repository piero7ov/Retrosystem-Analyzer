// ======= Config =======
const REFRESH_MS = 5000;
const DEFAULT_TAB = 'hourly';
const TOAST_TIMEOUT = 8000; // 8 s visible

// ======= Utils =======
const $ = sel => document.querySelector(sel);
const $all = sel => Array.from(document.querySelectorAll(sel));

// ======= Navegación =======
function setActiveTab(type){
  $all('.sidebar a').forEach(a=>{
    a.classList.toggle('active', a.dataset.type === type);
  });
  ['hourly','alertas','comparativa','reportes'].forEach(t=>{
    const v = $('#view-'+t);
    if (v) v.style.display = (t===type)?'grid':'none';
  });
}
function getRouteType(){
  const h = (location.hash || '').replace('#','').trim().toLowerCase();
  return ['hourly','alertas','comparativa','reportes'].includes(h) ? h : DEFAULT_TAB;
}
function initNav(){
  const type = getRouteType();
  setActiveTab(type);
  $all('.sidebar a').forEach(a=>{
    a.addEventListener('click', ()=>{
      const t = a.dataset.type;
      location.hash = '#'+t;
      setActiveTab(t);
    });
  });
  window.addEventListener('hashchange', ()=>{
    setActiveTab(getRouteType());
  });
}

// ======= Modal =======
function openModal(src){
  const m = $('#myModal'), img = $('#modalImage');
  if(!m || !img) return;
  img.src = src + '?t=' + Date.now();
  m.style.display = 'flex'; // centrado via CSS
}
function closeModal(){ const m = $('#myModal'); if(m) m.style.display = 'none'; }
window.openModal = openModal;
window.closeModal = closeModal;

// ======= Refresco de PNGs =======
function refreshImages(){
  ['cpu','mem','disk','net'].forEach(id=>{
    const img = document.querySelector(`#view-hourly img[src^="plots/${id}"]`);
    if(img) img.src = `plots/${id}.png?t=${Date.now()}`;
  });
}

// ======= Descargas =======
function downloadIfExists(path){
  const a = document.createElement('a');
  a.href = path + '?t=' + Date.now();
  a.download = '';
  document.body.appendChild(a); a.click(); a.remove();
}
window.downloadIfExists = downloadIfExists;

// ======= Toast de alertas (con ✕ y autocierre) =======
let toastTimeout = null;
function createToast(message){
  let toast = $('#alertToast');
  if(!toast){
    toast = document.createElement('div');
    toast.id = 'alertToast';
    toast.className = 'alert-toast';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `
    <span>${message}</span>
    <button id="toastCloseBtn" title="Cerrar">✕</button>
  `;
  toast.style.display = 'flex';

  // Cierre manual
  $('#toastCloseBtn').addEventListener('click', ()=>{
    toast.style.display = 'none';
    if(toastTimeout) clearTimeout(toastTimeout);
  });

  // Cierre automático
  if(toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(()=>{ toast.style.display = 'none'; }, TOAST_TIMEOUT);
}
async function maybeShowAlerts(){
  try{
    const res = await fetch('data/alertas.json?t=' + Date.now());
    if(!res.ok) return;
    const alerts = await res.json();
    const now = Date.now()/1000;
    const recent = alerts.filter(a => (now - a.ts) <= 10*60); // últimos 10 min
    if(recent.length > 0){
      const last = recent[recent.length-1];
      createToast(`⚠️ ${last.message}`);
      // Pintar lista en la vista Alertas (últimas 5)
      const ul = $('#alertasList');
      if(ul){
        ul.innerHTML = recent.slice(-5).map(a =>
          `<li>[${a.time}] ${a.type}: ${a.value} (umbral ${a.threshold})</li>`
        ).join('');
      }
    }
  }catch(e){
    // sin archivo o error: no mostramos nada
  }
}

// ======= Estadísticas de última hora =======
async function renderHourlyStats(){
  try{
    const res = await fetch('data/stats_summary.json?t=' + Date.now());
    if(!res.ok) return;
    const s = await res.json();
    if(!s.ok) return;

    const ul = $('#estadisticasList');
    if(!ul) return;

    const fmt = (n, d=1)=> (n!==undefined && !isNaN(n) ? Number(n).toFixed(d) : '—');

    ul.innerHTML = `
      <li>Muestras analizadas: <strong>${s.samples}</strong></li>
      <li>CPU — Último: <strong>${fmt(s.last.cpu_percent)}%</strong> • Promedio: <strong>${fmt(s.avg.cpu_percent)}%</strong></li>
      <li>RAM — Último: <strong>${fmt(s.last.mem_percent)}%</strong> • Promedio: <strong>${fmt(s.avg.mem_percent)}%</strong></li>
      <li>Disco — Último: <strong>${fmt(s.last.disk_percent)}%</strong></li>
      <li>Red — Último: <strong>${fmt(s.last.net_kb_s)} KB/s</strong> • Promedio: <strong>${fmt(s.avg.net_kb_s)} KB/s</strong></li>
      <li>Actualizado: <code>${s.last_time}</code></li>
    `;
  }catch(e){
    // si no existe aún, no rompemos nada
  }
}

// ======= Init =======
document.addEventListener('DOMContentLoaded', ()=>{
  initNav();
  refreshImages();
  maybeShowAlerts();
  renderHourlyStats();

  setInterval(refreshImages, REFRESH_MS);
  setInterval(maybeShowAlerts, 60000);   // cada 1 min
  setInterval(renderHourlyStats, 60000); // cada 1 min
});



