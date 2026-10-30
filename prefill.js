/* ThunderPrintSG quick-price prefill (OPS site-wide Custom JS).
   Does nothing unless the URL has ?tpq={...} (links from the Quick Price page).
   tpq = JSON {fieldName: value}; a value starting with "~" picks the <select> option whose text starts with it.
   Fields are set one at a time (the OPS calculator re-renders after each change), then a 2nd pass fixes anything a
   re-render reset. Source of truth: Desktop/ClaudeCode/quickprice/prefill.js */
(function () {
  var raw = new URLSearchParams(location.search).get('tpq');
  if (!raw) return;
  var spec;
  try { spec = JSON.parse(raw); } catch (e) { return; }
  var names = Object.keys(spec);
  var fire = function (e) {
    ['input', 'change', 'keyup', 'blur'].forEach(function (t) { e.dispatchEvent(new Event(t, { bubbles: true })); });
  };
  var setOne = function (name) {
    var e = document.querySelector('[name="' + name + '"]');
    if (!e) return false;
    var val = spec[name];
    if (e.tagName === 'SELECT') {
      var want = String(val).charAt(0) === '~' ? String(val).slice(1).toLowerCase() : null;
      var o = null;
      for (var i = 0; i < e.options.length; i++) {
        var opt = e.options[i];
        if (want ? opt.text.trim().toLowerCase().indexOf(want) === 0 : opt.value === String(val)) { o = opt; break; }
      }
      if (!o) return false;
      if (e.value === o.value) return true;
      e.value = o.value;
    } else {
      if (e.value === String(val)) return true;
      e.value = String(val);
    }
    fire(e);
    return true;
  };
  var pass = function (i, done) {
    if (i >= names.length) return done();
    setOne(names[i]);
    setTimeout(function () { pass(i + 1, done); }, 900);
  };
  var banner = function () {
    var b = document.createElement('div');
    b.textContent = 'Your Quick Price choices are filled in. Please check them, then upload your artwork.';
    b.setAttribute('style', 'position:fixed;left:12px;right:12px;bottom:12px;z-index:99999;background:#111841;color:#fff;' +
      'font:600 14px Montserrat,sans-serif;padding:12px 40px 12px 14px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.25)');
    var x = document.createElement('button');
    x.textContent = '×';
    x.setAttribute('aria-label', 'Close');
    x.setAttribute('style', 'position:absolute;right:8px;top:6px;background:none;border:0;color:#fff;font-size:22px;cursor:pointer');
    x.onclick = function () { b.remove(); };
    b.appendChild(x);
    document.body.appendChild(b);
    setTimeout(function () { b.remove(); }, 12000);
  };
  var start = function () {
    if (!document.querySelector('[name^="aoptions["]')) return;
    pass(0, function () { setTimeout(function () { pass(0, banner); }, 1200); });
  };
  if (document.readyState === 'complete') setTimeout(start, 800);
  else window.addEventListener('load', function () { setTimeout(start, 800); });
})();
