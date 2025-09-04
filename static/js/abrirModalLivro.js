const openBtn   = document.getElementById('openModalBtn');
const openBtn2   = document.getElementById('openModalBtn2');
const modalRoot = document.getElementById('modalRoot');
const overlay   = document.getElementById('modalOverlay');
const panel     = document.getElementById('modalPanel');
const cancelBtn = document.getElementById('cancelBtn');
const cancelBtn2 = document.getElementById('cancelBtn2');

  let lastFocus = null;

  function openModal() {
    lastFocus = document.activeElement;
    modalRoot.classList.remove('hidden');
    modalRoot.setAttribute('aria-hidden', 'false');

    // enter transition
    requestAnimationFrame(() => {
      overlay.classList.remove('opacity-0');
      panel.classList.remove('opacity-0','scale-95','translate-y-2');
      // foco inicial dentro do modal
      cancelBtn.focus();
    });

    // fecha com ESC
    document.addEventListener('keydown', onEsc);
  }

  function closeModal() {
    // leave transition
    overlay.classList.add('opacity-0');
    panel.classList.add('opacity-0','scale-95','translate-y-2');

    // aguarda fim da animação
    setTimeout(() => {
      modalRoot.classList.add('hidden');
      modalRoot.setAttribute('aria-hidden', 'true');
      // retorna foco
      if (lastFocus) lastFocus.focus();
    }, 200);

    document.removeEventListener('keydown', onEsc);
  }

  function onEsc(e) {
    if (e.key === 'Escape') closeModal();
  }

  // abrir
  openBtn.addEventListener('click', openModal);
  openBtn2.addEventListener('click', openModal)
  // fechar por botões/overlay
  cancelBtn.addEventListener('click', closeModal);
  cancelBtn2.addEventListener('click', closeModal);
  overlay.addEventListener('click', closeModal);