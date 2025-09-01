  // Toggle simples do menu mobile
  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('nav-toggle');
    const panel = document.getElementById('mobile-menu');
    if (!btn || !panel) return;

    const toggle = () => {
      const isHidden = panel.classList.contains('hidden');
      panel.classList.toggle('hidden', !isHidden);
      btn.setAttribute('aria-expanded', String(isHidden));
      // troca ícone opcional
      btn.innerHTML = isHidden
        ? '<span class="sr-only">Fechar menu</span><i class="fa-solid fa-xmark text-xl"></i>'
        : '<span class="sr-only">Abrir menu</span><i class="fa-solid fa-bars text-xl"></i>';
    };

    btn.addEventListener('click', toggle);

    // Fecha ao mudar para md (quando o menu desktop aparece)
    const mql = window.matchMedia('(min-width: 768px)');
    const syncWithBreakpoint = () => {
      if (mql.matches) {
        panel.classList.add('hidden');
        btn.setAttribute('aria-expanded', 'false');
        btn.innerHTML = '<span class="sr-only">Abrir menu</span><i class="fa-solid fa-bars text-xl"></i>';
      }
    };
    mql.addEventListener?.('change', syncWithBreakpoint);
    syncWithBreakpoint();
  });