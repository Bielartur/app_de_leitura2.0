(function setupBookSearch() {
  // só inicia quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupBookSearch);
    return;
  }

  const input = document.getElementById('pesquisa-autor');
  const box   = document.getElementById('resultado-busca');
  if (!input || !box) return; // evita erro se o bloco ainda não existe

  // Campos do formulário (podem não existir dependendo do modal/tela)
  const fTitulo   = document.getElementById('titulo-livro');
  const fAutor    = document.getElementById('autor-livro');
  const fTotal    = document.getElementById('total-paginas');
  const fIsbn     = document.getElementById('isbn');
  const fCapa     = document.getElementById('capa-url');
  const fGoogleId = document.getElementById('google-id');

  // Helpers de lock
  function lockInput(el) {
    if (!el) return;
    el.readOnly = true;
    el.classList.add('bg-slate-100','text-slate-600','cursor-not-allowed');
    el.classList.remove('focus:ring-2','focus:ring-blue-500','focus:border-blue-500');
  }
  function unlockInput(el) {
    if (!el) return;
    el.readOnly = false;
    el.classList.remove('bg-slate-100','text-slate-600','cursor-not-allowed');
    el.classList.add('focus:ring-2','focus:ring-blue-500','focus:border-blue-500');
  }

  // (novo) estado inicial: já deixa os 3 campos com aparência de readonly
  [fTitulo, fAutor, fTotal].forEach(lockInput);

  // Debounce
  const debounce = (fn, delay = 300) => {
    let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
  };

  let abortController = null;
  let lastResults = [];
  let selectedBook = null;

  // Busca (Google Books)
  async function searchBooks(q, signal) {
    const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(q)}&printType=books&maxResults=8&fields=items(id,volumeInfo/title,volumeInfo/authors,volumeInfo/pageCount,volumeInfo/imageLinks,volumeInfo/industryIdentifiers)`;
    const res = await fetch(url, { signal });
    if (!res.ok) return [];
    const data = await res.json();

    return (data.items || []).map(it => {
      const v = it.volumeInfo || {};
      const img = (v.imageLinks?.thumbnail || v.imageLinks?.smallThumbnail || "").replace(/^http:/, "https:");
      const ids = v.industryIdentifiers || [];
      const isbn13 = ids.find(x => x.type === "ISBN_13")?.identifier;
      const isbn10 = ids.find(x => x.type === "ISBN_10")?.identifier;
      const isbn = isbn13 || isbn10 || null;

      const cover = img || (isbn
        ? `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(isbn)}-M.jpg`
        : `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(v.title || q)}`);

      return {
        title: v.title || "",
        authors: v.authors || [],
        pageCount: v.pageCount,
        isbn,
        cover,
        id: it.id
      };
    });
  }

  function render(items) {
    lastResults = items;
    if (!items.length) {
      box.innerHTML = `<div class="p-3 text-sm text-slate-500">Nenhum resultado</div>`;
      return;
    }
    box.innerHTML = items.map((b, i) => `
      <button type="button" data-index="${i}"
        class="w-full text-left flex items-center gap-3 p-3 hover:bg-slate-50 transition-colors cursor-pointer">
        <img src="${b.cover}" alt="" class="w-10 h-14 object-cover rounded-md border border-slate-200"/>
        <div class="min-w-0">
          <div class="font-medium text-slate-800 truncate">${b.title || 'Sem título'}</div>
          <div class="text-sm text-slate-500 truncate">${(b.authors || []).join(', ') || 'Autor desconhecido'}</div>
          ${Number.isFinite(b.pageCount) ? `<div class="text-xs text-slate-400">${b.pageCount} páginas</div>` : ``}
        </div>
      </button>
    `).join('');
  }

  function fillForm(book) {
    const authorStr = (book.authors && book.authors.length) ? book.authors.join(', ') : "";
    const pageStr   = (Number.isFinite(book.pageCount) && book.pageCount > 0) ? String(book.pageCount) : "";

    if (fTitulo)   fTitulo.value   = book.title || "";
    if (fAutor)    fAutor.value    = authorStr;
    if (fTotal)    fTotal.value    = pageStr;
    if (fIsbn)     fIsbn.value     = book.isbn || "";
    if (fCapa)     fCapa.value     = book.cover || "";
    if (fGoogleId) fGoogleId.value = book.id || "";

    // trava a busca
    input.value = (book.title || "Sem título") + (book.authors?.length ? ` — ${book.authors[0]}` : "");
    lockInput(input);

    // Regra: libera apenas os campos que vierem vazios
    if (fTitulo) { if (!fTitulo.value.trim()) unlockInput(fTitulo); else lockInput(fTitulo); }
    if (fAutor)  { if (!fAutor.value.trim())  unlockInput(fAutor);  else lockInput(fAutor);  }
    if (fTotal)  { if (!fTotal.value.trim())  unlockInput(fTotal);  else lockInput(fTotal);  }
  }

  function showSelectedMessage(book) {
    const authors = (book.authors || []).join(', ') || 'Autor desconhecido';
    const pages = Number.isFinite(book.pageCount) ? `${book.pageCount} páginas` : '';
    box.innerHTML = `
      <div class="p-3 flex items-center gap-3">
        <img src="${book.cover}" alt="" class="w-10 h-14 object-cover rounded-md border border-slate-200"/>
        <div class="min-w-0">
          <div class="font-medium text-slate-800 truncate">"${book.title || 'Sem título'}"</div>
          <div class="text-sm text-slate-500 truncate">${authors}</div>
          ${pages ? `<div class="text-xs text-slate-400">${pages}</div>` : ``}
          <div class="text-xs text-[var(--great-green)] mt-1">Livro selecionado.</div>
        </div>
        <div class="ml-auto">
          <button type="button" data-action="trocar"
            class="px-3 py-1 text-xs rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors cursor-pointer">
            Trocar
          </button>
        </div>
      </div>
    `;
  }

  function clearSelection() {
    selectedBook = null;

    // volta ao padrão visual readonly nos 3 campos
    [fTitulo, fAutor, fTotal].forEach(lockInput);

    // reabilita a busca
    unlockInput(input);
    // input.value = ""; // opcional

    lastResults = [];
    box.innerHTML = `<div class="p-3 text-sm text-slate-500">Nenhum livro foi buscado ainda</div>`;
    input.focus();
  }

  // clique: selecionar livro ou Trocar
  box.addEventListener('click', (ev) => {
    const swapBtn = ev.target.closest('button[data-action="trocar"]');
    if (swapBtn) {
      clearSelection();
      return;
    }
    const btn = ev.target.closest('button[data-index]');
    if (!btn) return;

    const idx = Number(btn.dataset.index);
    const book = lastResults[idx];
    if (!book) return;

    selectedBook = book;
    fillForm(book);
    showSelectedMessage(book);
  });

  // Busca com debounce — começa com 1 caractere
  const MIN_CHARS = 1;
  const onInput = debounce(async (e) => {
    if (selectedBook) return;

    const q = e.target.value.trim();
    if (q.length < MIN_CHARS) {
      box.innerHTML = `<div class="p-3 text-sm text-slate-500">Digite pelo menos ${MIN_CHARS} caractere${MIN_CHARS>1?'s':''}…</div>`;
      lastResults = [];
      return;
    }

    if (abortController) abortController.abort();
    abortController = new AbortController();

    box.innerHTML = `<div class="p-3 text-sm text-slate-500">Buscando…</div>`;

    try {
      const items = await searchBooks(q, abortController.signal);
      render(items);
    } catch (err) {
      if (err.name === 'AbortError') return;
      box.innerHTML = `<div class="p-3 text-sm text-red-600">Erro ao buscar</div>`;
    }
  }, 300);

  input.addEventListener('input', onInput);

  // manter box visível; apenas mensagem padrão quando clicar fora sem seleção
  document.addEventListener('click', (ev) => {
    if (selectedBook) return;
    if (!ev.target.closest('#resultado-busca') && !ev.target.closest('#pesquisa-autor')) {
      if (!lastResults.length) {
        box.innerHTML = `<div class="p-3 text-sm text-slate-500">Nenhum livro foi buscado ainda</div>`;
      }
    }
  });
})();
