fetch('/auth/me').then(r => r.json()).then(s => {
    if (s.role === 'admin') window.location.href = '/admin-panel';
    else if (s.role === 'user') window.location.href = '/home';
});

document.getElementById('signupForm').addEventListener('submit', async e => {
    e.preventDefault();

    const username        = document.getElementById('username').value.trim();
    const password        = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorEl         = document.getElementById('error');
    const btn             = e.target.querySelector('button[type=submit]');

    errorEl.textContent = '';

    if (!username) {
        errorEl.textContent = 'Username is required';
        return;
    }
    if (password.length < 4) {
        errorEl.textContent = 'Password must be at least 4 characters';
        return;
    }
    if (password !== confirmPassword) {
        errorEl.textContent = 'Passwords do not match';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Creating account...';

    try {
        const res  = await fetch('/auth/register', {
            method:  'POST',
            headers: {'Content-Type': 'application/json'},
            body:    JSON.stringify({username, password})
        });
        const data = await res.json();

        if (!res.ok) {
            errorEl.textContent = data.error || 'Registration failed';
            return;
        }

        const loginRes = await fetch('/auth/unified-login', {
            method:  'POST',
            headers: {'Content-Type': 'application/json'},
            body:    JSON.stringify({username, password})
        });

        if (loginRes.ok) {
            window.location.href = '/home';
        } else {
            window.location.href = '/login';
        }
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
});
