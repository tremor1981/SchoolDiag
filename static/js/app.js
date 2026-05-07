// Score bar live update
document.addEventListener('input', function(e) {
  if (e.target.classList.contains('score-field')) {
    const val = Math.max(0, Math.min(100, parseInt(e.target.value) || 0));
    const wrap = e.target.closest('.score-input-wrap');
    if (wrap) {
      const fill = wrap.querySelector('.score-bar-fill');
      if (fill) {
        fill.style.width = val + '%';
        if (val >= 80) fill.style.background = 'linear-gradient(90deg,#00d4aa,#00ff88)';
        else if (val >= 50) fill.style.background = 'linear-gradient(90deg,#6c63ff,#00d4aa)';
        else fill.style.background = 'linear-gradient(90deg,#ff4f70,#ffb547)';
      }
    }
  }
});

// Modal helpers
function openModal(id) {
  document.getElementById(id).classList.add('open');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// Flash auto-hide
document.querySelectorAll('.alert').forEach(a => {
  setTimeout(() => { a.style.opacity = '0'; a.style.transition = 'opacity 0.5s'; }, 4000);
  setTimeout(() => a.remove(), 4600);
});

// Score field clamp
document.addEventListener('change', function(e) {
  if (e.target.classList.contains('score-field')) {
    let v = parseInt(e.target.value);
    if (isNaN(v)) v = 0;
    e.target.value = Math.max(0, Math.min(100, v));
  }
});
