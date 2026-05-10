function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className   = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
}

function stars(n) { return '★'.repeat(n) + '☆'.repeat(5 - n); }

function starsAvg(avg) {
    if (avg == null) return '<span style="color:var(--muted)">No reviews</span>';
    return `<span class="stars">${stars(Math.round(avg))}</span> ${avg.toFixed(1)}`;
}

async function loadPage(session) {
    const [bookRes, revRes] = await Promise.all([
        fetch(`/books/${BOOK_ID}`),
        fetch(`/reviews/${BOOK_ID}`)
    ]);

    if (!bookRes.ok) {
        const err = await bookRes.json();
        document.getElementById('bookContent').innerHTML =
            `<p class="empty" style="color:var(--danger)">${err.error}</p>`;
        return;
    }

    const {book, copies, similarBooks} = await bookRes.json();
    const {summary, reviews}           = await revRes.json();

    let userBorrowed    = false;
    let alreadyReviewed = false;

    if (session.role === 'user') {
        const me = await (await fetch('/users/me')).json();
        userBorrowed    = (me.borrowedBooks || []).some(b => b._id === BOOK_ID);
        alreadyReviewed = reviews.some(r => r.username === session.username);
    }

    const total    = summary.reviewCount || 0;
    const copyLeft = copies ? copies.left : 0;

    const starKeys = {5:'fiveStars', 4:'fourStars', 3:'threeStars', 2:'twoStars', 1:'oneStar'};
    const ratingBarsHtml = total > 0
        ? [5,4,3,2,1].map(n => {
            const cnt = summary[starKeys[n]] || 0;
            const pct = Math.round(cnt / total * 100);
            return `<div class="rating-row">
                <span class="rlabel">${n} ★</span>
                <div class="rating-bar-track"><div class="rating-bar-fill" style="width:${pct}%"></div></div>
                <span class="rcount">${cnt}</span>
            </div>`;
          }).join('')
        : '<p style="color:var(--muted);font-size:0.9rem">No ratings yet.</p>';

    const reviewsHtml = reviews.length
        ? reviews.map(r => `
            <div class="review-item">
                <div class="review-header">
                    <span class="review-user">${r.username || 'User'}</span>
                    <span class="stars">${stars(r.rating)}</span>
                </div>
                <p class="review-comment">${r.comment || ''}</p>
            </div>`).join('')
        : '<p style="color:var(--muted);font-size:0.9rem">No reviews yet. Be the first!</p>';

    const similarHtml = similarBooks.length
        ? `<div class="books-grid" style="grid-template-columns:repeat(auto-fill,minmax(148px,1fr))">
            ${similarBooks.map(b => `
                <div class="book-card" onclick="window.location.href='/book/${b._id}'">
                    <div class="book-title" style="font-size:0.88rem">${b.name}</div>
                    <div class="book-author">${b.author}</div>
                    <span class="book-genre">${b.genre}</span>
                    <div style="margin-top:0.4rem">${starsAvg(b.avgRating)}</div>
                </div>`).join('')}
           </div>`
        : '<p style="color:var(--muted);font-size:0.9rem">No similar books found.</p>';

    let borrowBtn = '';
    if (session.role === 'user') {
        if (userBorrowed) {
            borrowBtn = `<button id="actionBtn" class="btn btn-danger">Return Book</button>`;
        } else if (copyLeft > 0) {
            borrowBtn = `<button id="actionBtn" class="btn btn-success">Borrow Book</button>`;
        } else {
            borrowBtn = `<button class="btn btn-secondary" disabled>Unavailable</button>`;
        }
    }

    let reviewFormHtml = '';
    if (session.role === 'user' && !alreadyReviewed) {
        reviewFormHtml = `
        <div class="card mt-2">
            <p class="section-title">Write a Review</p>
            <form id="reviewForm">
                <div class="form-group">
                    <label>Rating</label>
                    <select id="ratingInput">
                        <option value="5">★★★★★ — Excellent</option>
                        <option value="4">★★★★☆ — Good</option>
                        <option value="3">★★★☆☆ — Average</option>
                        <option value="2">★★☆☆☆ — Poor</option>
                        <option value="1">★☆☆☆☆ — Terrible</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Comment <span style="color:var(--muted);font-weight:400">(optional)</span></label>
                    <textarea id="commentInput" rows="3" placeholder="Share your thoughts..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Submit Review</button>
            </form>
        </div>`;
    } else if (session.role === 'user' && alreadyReviewed) {
        reviewFormHtml = `<p style="color:var(--muted);font-size:0.88rem;margin-top:1rem">✓ You have already reviewed this book.</p>`;
    }

    document.getElementById('bookContent').innerHTML = `
        <div class="two-col">
            <div>
                <div class="card">
                    <h1 style="font-size:1.45rem;margin-bottom:0.4rem">${book.name}</h1>
                    <p style="color:var(--muted);margin-bottom:0.75rem">by <strong>${book.author}</strong></p>
                    <span class="book-genre">${book.genre}</span>
                    <div style="margin-top:1.25rem;display:flex;align-items:center;gap:1rem;flex-wrap:wrap">
                        <span class="${copyLeft > 0 ? 'avail-yes' : 'avail-no'}" style="font-size:0.9rem">
                            ${copies ? `${copyLeft} of ${copies.copies} copies available` : 'N/A'}
                        </span>
                        ${borrowBtn}
                    </div>
                </div>

                <div class="card mt-2">
                    <p class="section-title">
                        Reviews
                        ${total > 0
                            ? `<span style="font-weight:400;color:var(--muted);font-size:0.88rem">
                                &nbsp;${starsAvg(summary.avgRating)}&nbsp;·&nbsp;${total} review${total !== 1 ? 's' : ''}</span>`
                            : ''}
                    </p>
                    <div class="rating-bars">${ratingBarsHtml}</div>
                    <div style="margin-top:1.4rem">${reviewsHtml}</div>
                </div>

                ${reviewFormHtml}
            </div>

            <div>
                <div class="card">
                    <p class="section-title">Similar Books</p>
                    <p style="color:var(--muted);font-size:0.78rem;margin-bottom:1rem">
                        Same author (2 pts) or genre (1 pt), ranked by rating — aggregation pipeline
                    </p>
                    ${similarHtml}
                </div>
            </div>
        </div>`;

    document.getElementById('actionBtn')?.addEventListener('click', async () => {
        const url  = userBorrowed ? `/users/return/${BOOK_ID}` : `/users/borrow/${BOOK_ID}`;
        const res  = await fetch(url, {method: 'POST'});
        const data = await res.json();
        showToast(data[res.ok ? 'message' : 'error'], res.ok ? 'success' : 'error');
        if (res.ok) loadPage(session);
    });

    document.getElementById('reviewForm')?.addEventListener('submit', async e => {
        e.preventDefault();
        const res  = await fetch(`/reviews/${BOOK_ID}`, {
            method:  'POST',
            headers: {'Content-Type': 'application/json'},
            body:    JSON.stringify({
                rating:  parseInt(document.getElementById('ratingInput').value),
                comment: document.getElementById('commentInput').value
            })
        });
        const data = await res.json();
        showToast(data[res.ok ? 'message' : 'error'], res.ok ? 'success' : 'error');
        if (res.ok) loadPage(session);
    });
}

(async () => {
    const session = await (await fetch('/auth/me')).json();

    if (session.role) {
        document.getElementById('userGreeting').textContent = `Hello, ${session.username}`;
        document.getElementById('logoutBtn').style.display  = '';
        if (session.role === 'user')
            document.getElementById('dashboardLink').style.display = '';
    }

    document.getElementById('logoutBtn').addEventListener('click', async () => {
        await fetch('/auth/logout', {method: 'POST'});
        window.location.href = '/login';
    });

    loadPage(session);
})();
