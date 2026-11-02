/* common.js — helper dùng chung cho các trang báo cáo */
const CH = {};
const PAL = ['#3b82f6','#10b981','#f59e0b','#8b5cf6','#ec4899','#06b6d4','#84cc16','#f97316'];

function fmtB(v){ return v==null||isNaN(v) ? '—' : (v/1000).toFixed(1)+' tỷ'; }
function fmtN(v,d=0){ return v==null||isNaN(v) ? '—' : Number(v).toLocaleString('vi-VN',{minimumFractionDigits:d,maximumFractionDigits:d}); }
function fmtPct(v,d=1){ return v==null||isNaN(v) ? '—' : (v>0?'+':'')+Number(v).toFixed(d)+'%'; }
function cls(v,inv=false){ if(v==null||isNaN(v))return ''; const n=inv? -v : v; return n<0?'neg':'pos'; }

function mk(id,type,data,options){
  if(CH[id]) CH[id].destroy();
  const el=document.getElementById(id); if(!el) return;
  CH[id]=new Chart(el.getContext('2d'),{type,data,
    options:Object.assign({responsive:true,maintainAspectRatio:false},options||{})});
}

function toggleTheme(){
  const h=document.documentElement;
  const t=h.getAttribute('data-theme')==='dark'?'light':'dark';
  h.setAttribute('data-theme',t);
  try{ localStorage.setItem('mst-theme',t);}catch(e){}
}
(function(){ try{ const t=localStorage.getItem('mst-theme'); if(t) document.documentElement.setAttribute('data-theme',t);}catch(e){} })();

/* Bảng có sort + phân trang client-side */
function DataTable(opts){
  const {tableId, cols, data, pageSize=100, onRowClick} = opts;
  let sortKey=opts.sortKey||null, sortDir=opts.sortDir||-1, page=0, view=data;
  const tbl=document.getElementById(tableId);
  const thead=tbl.querySelector('thead'), tbody=tbl.querySelector('tbody');

  thead.innerHTML='<tr>'+cols.map(c=>
    `<th data-k="${c.k}" class="${c.num?'num':''}">${c.t}<span class="ar">${sortKey===c.k?(sortDir<0?'▼':'▲'):''}</span></th>`
  ).join('')+'</tr>';
  thead.querySelectorAll('th').forEach(th=>{
    th.onclick=()=>{ const k=th.dataset.k;
      if(sortKey===k) sortDir=-sortDir; else {sortKey=k; sortDir=-1;}
      applySort(); page=0; render(); };
  });

  function applySort(){
    if(!sortKey) return;
    view=[...view].sort((a,b)=>{
      let x=a[sortKey], y=b[sortKey];
      if(x==null) return 1; if(y==null) return -1;
      if(typeof x==='number'&&typeof y==='number') return (x-y)*sortDir;
      return String(x).localeCompare(String(y),'vi')*sortDir;
    });
  }

  function render(){
    const total=view.length, pages=Math.max(1,Math.ceil(total/pageSize));
    if(page>=pages) page=pages-1;
    const slice=view.slice(page*pageSize,(page+1)*pageSize);
    tbody.innerHTML=slice.map(r=>'<tr>'+cols.map(c=>{
      let v=r[c.k];
      let txt = c.fmt ? c.fmt(v,r) : (v==null?'—':v);
      const k = c.clsFn ? c.clsFn(v,r) : (c.num&&c.sign? cls(v) : '');
      return `<td class="${c.num?'num':''} ${k}">${txt}</td>`;
    }).join('')+'</tr>').join('');
    if(onRowClick) tbody.querySelectorAll('tr').forEach((tr,i)=>tr.onclick=()=>onRowClick(slice[i]));
    const cnt=document.getElementById('cnt');
    if(cnt) cnt.textContent = `${fmtN(total)} dòng`;
    const pg=document.getElementById('pager');
    if(pg){ pg.innerHTML = pages>1 ?
      `<button ${page===0?'disabled':''} onclick="__pg(-1)">‹ Trước</button>
       <span>Trang ${page+1}/${pages}</span>
       <button ${page>=pages-1?'disabled':''} onclick="__pg(1)">Sau ›</button>` : ''; }
  }
  window.__pg=(d)=>{ page+=d; render(); };
  window.__setData=(nd)=>{ view=nd; applySort(); page=0; render(); };
  applySort(); render();
  return { setData:(nd)=>{ view=nd; applySort(); page=0; render(); }, render };
}

function exportCsv(filename, cols, rows){
  const head=cols.map(c=>c.t).join(',');
  const body=rows.map(r=>cols.map(c=>{
    let v=r[c.k]; if(v==null) v='';
    v=String(v).replace(/"/g,'""');
    return '"'+v+'"';
  }).join(',')).join('\n');
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob(['\ufeff'+head+'\n'+body],{type:'text/csv;charset=utf-8'}));
  a.download=filename; a.click();
}

function buildNav(active){
  const items=[['index.html','📊 Tổng quan'],['dailysale.html','🛒 DailySale'],
    ['competitor.html','⚔️ Competitor'],['shrinkloss.html','💸 Shrinkage & Loss']];
  document.getElementById('nav').innerHTML=items.map(([h,t])=>
    `<a href="${h}" class="${h===active?'on':''}">${t}</a>`).join('');
}
