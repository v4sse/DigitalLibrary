function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className   = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
}

async function returnBook(bookId) {
    const res  = await fetch(`/users/return/${bookId}`, {method: 'POST'});
    const data = await res.json();
    showToast(data[res.ok ? 'message' : 'error'], res.ok ? 'success' : 'error');
    if (res.ok) loadDashboard();
}

function fmtDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString();
}

async function loadDashboard() {
    const session = await (await fetch('/auth/me')).json();
    if (session.role !== 'user') { window.location.href = '/login'; return; }

    document.getElementById('userGreeting').textContent = `Hello, ${session.username}`;

    const [meRes, histRes] = await Promise.all([
        fetch('/users/me'),
        fetch('/users/history')
    ]);
    const meData   = await meRes.json();
    const history  = await histRes.json();
    const borrowed = meData.borrowedBooks || [];

    const booksHtml = borrowed.length
        ? `<div class="books-grid">${borrowed.map(b => `
            <div class="book-card">
                <div class="book-title">${b.name}</div>
                <div class="book-author">${b.author}</div>
                <span class="book-genre">${b.genre}</span>
                <div style="margin-top:0.75rem;display:flex;gap:0.5rem">
                    <a href="/book/${b._id}" class="btn btn-secondary btn-sm">View</a>
                    <button class="btn btn-danger btn-sm" onclick="returnBook('${b._id}')">Return</button>
                </div>
            </div>`).join('')}</div>`
        : '<p class="empty">You have no borrowed books.</p>';

    const historyRows = history.map(r => {
        const statusLabel = r.returnedAt
            ? (r.forcedReturn
                ? '<span class="badge badge-danger">Force Returned</span>'
                : '<span class="badge badge-success">Returned</span>')
            : '<span class="badge badge-warning">Active</span>';
        return `
        <tr>
            <td><a href="/book/${r.bookId}">${r.bookName || '—'}</a></td>
            <td>${r.author || '—'}</td>
            <td><span class="book-genre">${r.genre || '—'}</span></td>
            <td>${fmtDate(r.borrowedAt)}</td>
            <td>${fmtDate(r.returnedAt)}</td>
            <td>${statusLabel}</td>
        </tr>`;
    }).join('');

    const historyHtml = history.length
        ? `<table class="table">
            <thead>
                <tr>
                    <th>Book</th><th>Author</th><th>Genre</th>
                    <th>Borrowed At</th><th>Returned At</th><th>Status</th>
                </tr>
            </thead>
            <tbody>${historyRows}</tbody>
           </table>`
        : '<p class="empty">No borrow history yet.</p>';

    document.getElementById('dashContent').innerHTML = `
        <div class="card">
            <p class="section-title">Currently Borrowed &nbsp;<span style="color:var(--muted);font-weight:400">(${borrowed.length})</span></p>
            ${booksHtml}
        </div>
        <div class="card mt-2">
            <p class="section-title">Borrow History &nbsp;<span style="color:var(--muted);font-weight:400">(${history.length})</span></p>
            ${historyHtml}
        </div>`;
}

document.getElementById('logoutBtn').addEventListener('click', async () => {
    await fetch('/auth/logout', {method: 'POST'});
    window.location.href = '/login';
});

loadDashboard();
