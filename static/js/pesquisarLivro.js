const input = document.getElementById('pesquisa-autor');
const box = document.getElementById('resultado-busca');

// Campos do formulário
const fTitulo = document.getElementById('titulo-livro');
const fAutor = document.getElementById('autor-livro');
const fTotal = document.getElementById('total-paginas');
const fAtual = document.getElementById('pagina-atual');
const fData = document.getElementById('data-inicio');
const fIsbn = document.getElementById('isbn');
const fCapa = document.getElementById('capa-url');
const fGoogleId = document.getElementById('google-id');

// Debounce genérico (300ms)
const debounce = (fn, delay = 300) => {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
};

let abortController = null;
let lastResults = []; // guarda a lista exibida no dropdown

// Busca normalizada (Google Books + fallback de capa)
async function searchBooks(q, signal) {
  const url = `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(q)}&printType=books&maxResults=8&fields=items(id,volumeInfo/title,volumeInfo/authors,volumeInfo/pageCount,volumeInfo/imageLinks,volumeInfo/industryIdentifiers)`;
  const res = await fetch(url, { signal });
  if (!res.ok) return [];
  const data = await res.json();

  const items = (data.items || []).map(it => {
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
      title: v.title || "Sem título",
      authors: v.authors || [],
      pageCount: v.pageCount,
      isbn,
      cover,
      id: it.id
    };
  });

  return items;
}

function render(items) {
  lastResults = items; // guarda para recuperar no clique
  if (!items.length) {
    box.innerHTML = `<div class="p-3 text-sm text-slate-500">Nenhum resultado</div>`;
    box.classList.remove('hidden');
    return;
  }
  box.innerHTML = items.map((b, i) => `
    <button type="button" data-index="${i}"
      class="w-full text-left flex items-center gap-3 p-3 hover:bg-slate-50 transition-colors">
      <img src="${b.cover}" alt="" class="w-10 h-14 object-cover rounded-md border border-slate-200"/>
      <div class="min-w-0">
        <div class="font-medium text-slate-800 truncate">${b.title}</div>
        <div class="text-sm text-slate-500 truncate">${(b.authors || []).join(', ') || 'Autor desconhecido'}</div>
        ${b.pageCount ? `<div class="text-xs text-slate-400">${b.pageCount} páginas</div>` : ``}
      </div>
    </button>
  `).join('');
  box.classList.remove('hidden');
}

function lockInput(el) {
  el.disabled = true;
  el.classList.add(
    'bg-slate-100',        // fundo mais escuro
    'text-slate-600',      // texto mais “apagado”
    'cursor-not-allowed'   // cursor de desabilitado
  );
  // remove estados de foco azuis para não confundir o usuário
  el.classList.remove('focus:ring-2', 'focus:ring-blue-500', 'focus:border-blue-500');
}

function unlockInput(el) {
  el.disabled = false;
  el.classList.remove('bg-slate-100', 'text-slate-600', 'cursor-not-allowed');
  // restaura foco padrão (ajuste conforme seu design)
  el.classList.add('focus:ring-2', 'focus:ring-blue-500', 'focus:border-blue-500');
}

function fillForm(book) {
  // Preenche valores
  fTitulo.value = book.title || "";
  fAutor.value = (book.authors && book.authors.length) ? book.authors.join(', ') : "";
  fTotal.value = (book.pageCount && Number.isFinite(book.pageCount)) ? book.pageCount : "";

  // Metadados úteis
  fIsbn.value = book.isbn || "";
  fCapa.value = book.cover || "";
  fGoogleId.value = book.id || "";

  // Mostra escolha no campo de busca
  input.value = book.title + (book.authors?.length ? ` — ${book.authors[0]}` : "");

  // Desabilita e escurece os campos que não devem ser editados
  lockInput(fTitulo);
  lockInput(fAutor);
  if (book.pageCount) lockInput(fTotal); // se quiser sempre travar, remova o "if"

  // Opcional: espelhar valores em inputs hidden para enviar no POST mesmo desabilitados
  // (crie no HTML: <input type="hidden" id="titulo-livro-hidden"> etc.)
  const hTitulo = document.getElementById('titulo-livro-hidden');
  const hAutor  = document.getElementById('autor-livro-hidden');
  const hTotal  = document.getElementById('total-paginas-hidden');
  if (hTitulo) hTitulo.value = fTitulo.value;
  if (hAutor)  hAutor.value  = fAutor.value;
  if (hTotal)  hTotal.value  = fTotal.value;
}


// Evento de clique nos resultados (event delegation)
box.addEventListener('click', (ev) => {
  const btn = ev.target.closest('button[data-index]');
  if (!btn) return;
  const idx = Number(btn.dataset.index);
  const book = lastResults[idx];
  if (!book) return;

  fillForm(book);
  // fecha dropdown
  box.classList.add('hidden');
});

// Busca com debounce
const onInput = debounce(async (e) => {
  const q = e.target.value.trim();
  if (q.length < 2) {
    box.classList.add('hidden');
    box.innerHTML = "";
    lastResults = [];
    return;
  }

  if (abortController) abortController.abort();
  abortController = new AbortController();

  box.innerHTML = `<div class="p-3 text-sm text-slate-500">Buscando…</div>`;
  box.classList.remove('hidden');

  try {
    const items = await searchBooks(q, abortController.signal);
    render(items);
  } catch (err) {
    if (err.name === 'AbortError') return;
    box.innerHTML = `<div class="p-3 text-sm text-red-600">Erro ao buscar</div>`;
    box.classList.remove('hidden');
  }
}, 300);

input.addEventListener('input', onInput);

// Fecha dropdown ao clicar fora
document.addEventListener('click', (ev) => {
  if (!ev.target.closest('#resultado-busca') && !ev.target.closest('#pesquisa-autor')) {
    box.classList.add('hidden');
  }
});