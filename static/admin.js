function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className   = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
}

function q(v) {
    return JSON.stringify(v).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}

function starsAvg(avg) {
    if (avg == null) return '—';
    const full = Math.round(avg);
    return `<span class="stars">${'★'.repeat(full)}${'☆'.repeat(5-full)}</span> ${avg.toFixed(1)}`;
}

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const panel = document.getElementById(btn.dataset.tab);
        panel.classList.add('active');
        if (panel.querySelector('.spinner')) loadTab(btn.dataset.tab);
    });
});

async function loadTab(tab) {
    if (tab === 'stats')   loadStats();
    if (tab === 'books')   loadBooks();
    if (tab === 'users')   loadUsers();
    if (tab === 'borrows') loadBorrows();
}

async function loadStats() {
    const panel = document.getElementById('stats');
    const {byGenre, topBooks} = await (await fetch('/admin/stats')).json();

    const totalBooks    = byGenre.reduce((s, g) => s + g.totalBooks, 0);
    const totalBorrowed = byGenre.reduce((s, g) => s + (g.totalBorrowed || 0), 0);

    const genreRows = byGenre.map(g => `
        <tr>
            <td>${g._id}</td>
            <td>${g.totalBooks}</td>
            <td>${g.totalBorrowed || 0}</td>
            <td>${g.avgRating != null ? g.avgRating.toFixed(2) : '—'}</td>
        </tr>`).join('');

    const topRows = topBooks.map((b, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${b.name}</td>
            <td>${b.author}</td>
            <td><span class="book-genre">${b.genre}</span></td>
            <td>${b.borrowed}</td>
            <td>${b.left} / ${b.copies}</td>
        </tr>`).join('');

    panel.innerHTML = `
        <div class="stats-row">
            <div class="stat-card"><div class="stat-value">${totalBooks}</div><div class="stat-label">Total Books</div></div>
            <div class="stat-card"><div class="stat-value">${totalBorrowed}</div><div class="stat-label">Currently Borrowed</div></div>
            <div class="stat-card"><div class="stat-value">${byGenre.length}</div><div class="stat-label">Genres</div></div>
        </div>

        <div class="card">
            <p class="section-title">By Genre
                <span style="font-weight:400;color:var(--muted);font-size:0.8rem"> — $group aggregation</span>
            </p>
            <table class="table">
                <thead><tr><th>Genre</th><th>Books</th><th>Borrowed</th><th>Avg Rating</th></tr></thead>
                <tbody>${genreRows}</tbody>
            </table>
        </div>

        <div class="card mt-2">
            <p class="section-title">Top 10 Most Borrowed
                <span style="font-weight:400;color:var(--muted);font-size:0.8rem"> — sorted aggregation</span>
            </p>
            <table class="table">
                <thead><tr><th>#</th><th>Title</th><th>Author</th><th>Genre</th><th>Borrowed</th><th>Available</th></tr></thead>
                <tbody>${topRows}</tbody>
            </table>
        </div>`;
}

async function loadBooks() {
    const panel = document.getElementById('books');
    const data  = await (await fetch('/admin/books')).json();

    const rows = data.map(b => `
        <tr>
            <td>${b.name}</td>
            <td>${b.author}</td>
            <td><span class="book-genre">${b.genre}</span></td>
            <td>${b.totalCopies ?? '—'}</td>
            <td>${b.borrowed ?? 0} borrowed / ${b.left ?? '—'} left</td>
            <td>${b.avgRating != null ? starsAvg(b.avgRating) : '—'} &nbsp;<span style="color:var(--muted);font-size:0.8rem">(${b.reviewCount || 0})</span></td>
            <td>
                <button class="btn btn-secondary btn-sm"
                    onclick="editCopies('${b._id}', ${b.totalCopies ?? 0})">Edit Copies</button>
                <button class="btn btn-danger btn-sm"
                    onclick="deleteBook('${b._id}', ${q(b.name)})">Delete</button>
            </td>
        </tr>`).join('');

    panel.innerHTML = `
        <div class="card">
            <p class="section-title">Add New Book</p>
            <form id="addBookForm">
                <div class="add-book-grid">
                    <div class="form-group" style="margin:0">
                        <label>Title</label>
                        <input id="newTitle" placeholder="Book title" required>
                    </div>
                    <div class="form-group" style="margin:0">
                        <label>Author</label>
                        <input id="newAuthor" placeholder="Author name" required>
                    </div>
                    <div class="form-group" style="margin:0">
                        <label>Genre</label>
                        <input id="newGenre" placeholder="Genre" required>
                    </div>
                    <div class="form-group" style="margin:0">
                        <label>Copies</label>
                        <input id="newCopies" type="number" min="1" value="1" required>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary" style="margin-top:0.75rem">Add Book</button>
            </form>
        </div>

        <div class="card mt-2">
            <p class="section-title">All Books (${data.length})</p>
            <table class="table">
                <thead><tr><th>Title</th><th>Author</th><th>Genre</th><th>Copies</th><th>Status</th><th>Rating</th><th>Actions</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;

    document.getElementById('addBookForm').addEventListener('submit', async e => {
        e.preventDefault();
        const res  = await fetch('/admin/books', {
            method:  'POST',
            headers: {'Content-Type': 'application/json'},
            body:    JSON.stringify({
                name:   document.getElementById('newTitle').value.trim(),
                author: document.getElementById('newAuthor').value.trim(),
                genre:  document.getElementById('newGenre').value.trim(),
                copies: document.getElementById('newCopies').value
            })
        });
        const data = await res.json();
        if (res.ok) { showToast('Book added', 'success'); loadBooks(); }
        else          showToast(data.error, 'error');
    });
}

async function loadUsers() {
    const panel = document.getElementById('users');
    const data  = await (await fetch('/admin/users')).json();

    const rows = data.map(u => {
        const blacklisted = u.blacklisted === true;
        const bookCells = (u.borrowedBooks || []).map(b => `
            <span class="book-tag">
                ${b.name}
                <button class="btn btn-danger btn-sm"
                    onclick="forceReturn('${u._id}', '${b._id}', ${q(b.name)}, ${q(u.username)})">
                    Force Return
                </button>
            </span>`).join('');

        return `
        <tr class="${blacklisted ? 'row-blacklisted' : ''}">
            <td>
                ${u.username}
                ${blacklisted ? '<span class="badge badge-danger">Blacklisted</span>' : ''}
            </td>
            <td>${(u.borrowedBooks || []).length}</td>
            <td>${bookCells || '<span style="color:var(--muted)">—</span>'}</td>
            <td>
                ${blacklisted
                    ? `<button class="btn btn-success btn-sm" onclick="whitelistUser('${u._id}', ${q(u.username)})">Whitelist</button>`
                    : `<button class="btn btn-danger btn-sm" onclick="blacklistUser('${u._id}', ${q(u.username)})">Blacklist</button>`
                }
            </td>
        </tr>`;
    }).join('');

    panel.innerHTML = `
        <div class="card">
            <p class="section-title">All Users (${data.length})</p>
            <table class="table">
                <thead><tr><th>Username</th><th>Borrowed</th><th>Books</th><th>Actions</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

async function loadBorrows() {
    const panel = document.getElementById('borrows');
    const data  = await (await fetch('/admin/borrows')).json();

    const rows = data.map(b => {
        const borrowedAt  = new Date(b.borrowedAt).toLocaleString();
        const returnedAt  = b.returnedAt ? new Date(b.returnedAt).toLocaleString() : '—';
        const statusLabel = b.returnedAt
            ? (b.forcedReturn
                ? '<span class="badge badge-danger">Force Returned</span>'
                : '<span class="badge badge-success">Returned</span>')
            : '<span class="badge badge-warning">Active</span>';
        return `
        <tr>
            <td>${b.username || '—'}</td>
            <td>${b.bookName || '—'}</td>
            <td>${b.author || '—'}</td>
            <td>${borrowedAt}</td>
            <td>${returnedAt}</td>
            <td>${statusLabel}</td>
        </tr>`;
    }).join('');

    panel.innerHTML = `
        <div class="card">
            <p class="section-title">Borrow History (${data.length})</p>
            <table class="table">
                <thead>
                    <tr>
                        <th>User</th><th>Book</th><th>Author</th>
                        <th>Borrowed At</th><th>Returned At</th><th>Status</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

async function editCopies(bookId, current) {
    const n = prompt(`Current total copies: ${current}\nNew total:`, current);
    if (n === null) return;
    const res  = await fetch(`/admin/books/${bookId}/copies`, {
        method:  'PUT',
        headers: {'Content-Type': 'application/json'},
        body:    JSON.stringify({copies: parseInt(n)})
    });
    const data = await res.json();
    if (res.ok) { showToast(data.message, 'success'); loadBooks(); }
    else          showToast(data.error, 'error');
}

async function deleteBook(bookId, name) {
    if (!confirm(`Delete "${name}"?\nThis cannot be undone.`)) return;
    const res  = await fetch(`/admin/books/${bookId}`, {method: 'DELETE'});
    const data = await res.json();
    if (res.ok) { showToast('Book deleted', 'success'); loadBooks(); }
    else          showToast(data.error, 'error');
}

async function forceReturn(userId, bookId, bookName, username) {
    if (!confirm(`Force-return "${bookName}" from ${username}?`)) return;
    const res  = await fetch(`/admin/users/${userId}/force-return/${bookId}`, {method: 'POST'});
    const data = await res.json();
    if (res.ok) { showToast(data.message, 'success'); loadUsers(); }
    else          showToast(data.error, 'error');
}

async function blacklistUser(userId, username) {
    if (!confirm(`Blacklist user "${username}"? They will no longer be able to borrow books.`)) return;
    const res  = await fetch(`/admin/users/${userId}/blacklist`, {method: 'POST'});
    const data = await res.json();
    if (res.ok) { showToast(data.message, 'success'); loadUsers(); }
    else          showToast(data.error, 'error');
}

async function whitelistUser(userId, username) {
    if (!confirm(`Whitelist user "${username}"? They will be able to borrow books again.`)) return;
    const res  = await fetch(`/admin/users/${userId}/unblacklist`, {method: 'POST'});
    const data = await res.json();
    if (res.ok) { showToast(data.message, 'success'); loadUsers(); }
    else          showToast(data.error, 'error');
}

(async () => {
    const session = await (await fetch('/auth/me')).json();
    if (session.role !== 'admin') { window.location.href = '/login'; return; }

    document.getElementById('userGreeting').textContent = `Admin: ${session.username}`;

    document.getElementById('logoutBtn').addEventListener('click', async () => {
        await fetch('/auth/logout', {method: 'POST'});
        window.location.href = '/login';
    });

    loadStats();
})();
