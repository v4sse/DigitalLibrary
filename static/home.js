function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className   = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
}

function starsHtml(avg, count) {
    if (avg == null) return `<span class="stars-meta">No reviews</span>`;
    const full  = Math.round(avg);
    const stars = '★'.repeat(full) + '☆'.repeat(5 - full);
    return `<span class="stars">${stars}</span> <span class="stars-meta">${avg.toFixed(1)} (${count})</span>`;
}

function renderBooks(list) {
    const el = document.getElementById('booksContainer');
    if (!list.length) {
        el.innerHTML = '<p class="empty">No books found.</p>';
        return;
    }
    el.innerHTML = `<div class="books-grid">${list.map(b => `
        <div class="book-card" onclick="window.location.href='/book/${b._id}'">
            <div class="book-title">${b.name}</div>
            <div class="book-author">${b.author}</div>
            <span class="book-genre">${b.genre}</span>
            <div class="book-meta">
                <span class="${b.available ? 'avail-yes' : 'avail-no'}">
                    ${b.available ? `✓ ${b.left} left` : '✗ Unavailable'}
                </span>
            </div>
            <div>${starsHtml(b.avgRating, b.reviewCount)}</div>
        </div>`).join('')}</div>`;
}

function setHint(text) {
    const el = document.getElementById('indexHint');
    if (text) { el.textContent = text; el.style.display = ''; }
    else       { el.style.display = 'none'; }
}

async function loadBooks(genre) {
    document.getElementById('booksContainer').innerHTML = '<div class="spinner"></div>';
    const url  = genre ? `/books/?genre=${encodeURIComponent(genre)}` : '/books/';
    const data = await (await fetch(url)).json();
    setHint(genre ? `Genre filter: "${genre}" — uses the genre ascending index` : '');
    renderBooks(data);
}

async function searchBooks(query) {
    document.getElementById('booksContainer').innerHTML = '<div class="spinner"></div>';
    const res  = await fetch(`/books/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    setHint(`Full-text search for "${query}" — uses the text index on name, author, genre`);
    if (data.error) { document.getElementById('booksContainer').innerHTML = `<p class="empty">${data.error}</p>`; return; }
    renderBooks(data);
}

document.getElementById('genreFilters').addEventListener('click', e => {
    const chip = e.target.closest('.filter-chip');
    if (!chip) return;
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    document.getElementById('searchInput').value = '';
    document.getElementById('clearBtn').style.display = 'none';
    loadBooks(chip.dataset.genre);
});

document.getElementById('searchBtn').addEventListener('click', () => {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) { loadBooks(''); return; }
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    document.querySelector('.filter-chip[data-genre=""]').classList.add('active');
    document.getElementById('clearBtn').style.display = '';
    searchBooks(q);
});

document.getElementById('searchInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('searchBtn').click();
});

document.getElementById('clearBtn').addEventListener('click', () => {
    document.getElementById('searchInput').value = '';
    document.getElementById('clearBtn').style.display = 'none';
    setHint('');
    loadBooks('');
});

document.getElementById('logoutBtn').addEventListener('click', async () => {
    await fetch('/auth/logout', {method: 'POST'});
    window.location.href = '/login';
});

(async () => {
    const session = await (await fetch('/auth/me')).json();

    if (session.role === 'admin') {
        window.location.href = '/admin-panel';
        return;
    }

    if (session.role === 'user') {
        document.getElementById('userGreeting').textContent = `Hello, ${session.username}`;
        document.getElementById('logoutBtn').style.display    = '';
        document.getElementById('dashboardLink').style.display = '';
    } else {
        document.getElementById('loginLink').style.display = '';
    }

    loadBooks('');
})();
