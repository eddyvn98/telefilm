import { tg } from './state.js';

export async function login() {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Telegram-Init-Data': tg.initData
        },
        body: JSON.stringify({ init_data: tg.initData })
    });

    if (!response.ok) {
        const err = new Error("Login failed");
        err.status = response.status;
        throw err;
    }
}

export async function fetchMovies() {
    // Fetch all movies for client-side pagination & sorting
    const response = await fetch('/api/catalog/movies?limit=10000', {
        headers: {
            'X-Telegram-Init-Data': tg.initData
        }
    });

    if (response.ok) {
        return await response.json();
    } else if (response.status === 403) {
        throw response;
    }
    return [];
}
