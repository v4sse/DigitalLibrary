fetch('/auth/me').then(r => r.json()).then(s => {
    if (s.role === 'admin') window.location.href = '/admin-panel';
    else if (s.role === 'user') window.location.href = '/home';
});

document.getElementById('loginForm').addEventListener('submit', async e => {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorEl  = document.getElementById('error');
    const btn      = e.target.querySelector('button[type=submit]');

    errorEl.textContent = '';
    btn.disabled = true;
    btn.textContent = 'Signing in...';

    try {
        const res  = await fetch('/auth/unified-login', {
            method:  'POST',
            headers: {'Content-Type': 'application/json'},
            body:    JSON.stringify({username, password})
        });
        const data = await res.json();

        if (!res.ok) {
            errorEl.textContent = data.error || 'Invalid credentials';
            return;
        }

        window.location.href = data.role === 'admin' ? '/admin-panel' : '/home';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
    }
});
