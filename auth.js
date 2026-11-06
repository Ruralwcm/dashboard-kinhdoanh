/* Cổng đăng nhập cho các trang dashboard-kinhdoanh (trừ Key Sale KM).
   Lưu ý: GitHub Pages là trang tĩnh — đây là lớp chặn xem thông thường, không phải bảo mật máy chủ. */
(function(){
  var KEY = 'rwcm_auth_v1', H = 'd9aeccd21c1573d604615b01aa83ecaf8d50bc3d50bc097e09cf57ddab00fb4a', TTL = 12 * 3600 * 1000;
  var de = document.documentElement; de.style.visibility = 'hidden';
  function ok(){ try { var t = JSON.parse(localStorage.getItem(KEY) || 'null'); return !!(t && t.h === H && t.exp > Date.now()); } catch(e){ return false; } }
  function sha(s){ return crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)).then(function(b){ return Array.prototype.map.call(new Uint8Array(b), function(x){ return ('0' + x.toString(16)).slice(-2); }).join(''); }); }
  window.rwcmLogout = function(){ try { localStorage.removeItem(KEY); } catch(e){} location.reload(); };
  function logoutBtn(){ var b = document.createElement('button'); b.textContent = '⎋ Đăng xuất'; b.title = 'Đăng xuất';
    b.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:9999;border:1px solid #E4E8EF;background:#fff;border-radius:999px;padding:6px 12px;font:600 12px system-ui,sans-serif;color:#44546A;cursor:pointer;box-shadow:0 4px 14px rgba(16,32,64,.12)';
    b.onclick = window.rwcmLogout; document.body.appendChild(b); }
  if (ok()){ de.style.visibility = 'visible'; document.addEventListener('DOMContentLoaded', logoutBtn); return; }
  function form(){
    var w = document.createElement('div');
    w.style.cssText = 'visibility:visible;position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0F2A4A,#C8102E);font-family:"Be Vietnam Pro",Inter,"Segoe UI",system-ui,sans-serif';
    w.innerHTML = '<form style="background:#fff;border-radius:16px;padding:28px 28px 22px;width:min(340px,90vw);box-shadow:0 20px 50px rgba(0,0,0,.3)">'
      + '<div style="font-size:18px;font-weight:800;color:#0F2A4A;margin-bottom:4px">🔒 Dashboard Kinh doanh</div>'
      + '<div style="font-size:12.5px;color:#44546A;margin-bottom:16px">Win Rural · vui lòng đăng nhập</div>'
      + '<label style="display:block;font-size:12px;font-weight:600;color:#44546A">Tài khoản<input name="u" autocomplete="username" required style="display:block;width:100%;box-sizing:border-box;margin:4px 0 10px;border:1px solid #E4E8EF;border-radius:9px;padding:9px 11px;font-size:14px"></label>'
      + '<label style="display:block;font-size:12px;font-weight:600;color:#44546A">Mật khẩu<input name="p" type="password" autocomplete="current-password" required style="display:block;width:100%;box-sizing:border-box;margin:4px 0 6px;border:1px solid #E4E8EF;border-radius:9px;padding:9px 11px;font-size:14px"></label>'
      + '<div id="rwcmErr" style="min-height:18px;font-size:12px;color:#DC2626;margin-bottom:6px"></div>'
      + '<button style="width:100%;border:0;background:#C8102E;color:#fff;border-radius:10px;padding:10px;font-size:14px;font-weight:700;cursor:pointer">Đăng nhập</button></form>';
    document.body.appendChild(w);
    var f = w.querySelector('form'); f.u.focus();
    f.onsubmit = function(e){ e.preventDefault();
      sha(f.u.value.trim().toLowerCase() + ':' + f.p.value).then(function(h){
        if (h === H){ try { localStorage.setItem(KEY, JSON.stringify({h:h, exp:Date.now() + TTL})); } catch(e){} w.remove(); de.style.visibility = 'visible'; logoutBtn(); }
        else { w.querySelector('#rwcmErr').textContent = 'Sai tài khoản hoặc mật khẩu.'; f.p.value = ''; f.p.focus(); } }); };
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', form); else form();
})();
