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
    const response = await fetch('/api/catalog/movies?limit=10000', {
        headers: { 'X-Telegram-Init-Data': tg.initData }
    });

    if (response.ok) return await response.json();
    else if (response.status === 403) throw response;
    return [];
}

export async function postWatchHistory(movieId, progressSeconds, durationSeconds) {
    try {
        await fetch('/api/history/record', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': tg.initData
            },
            body: JSON.stringify({
                movie_id: movieId,
                progress_seconds: progressSeconds,
                duration_seconds: durationSeconds
            })
        });
    } catch (e) {
        // Silent fail – history is non-critical
    }
}

export async function getWatchHistory() {
    const response = await fetch('/api/history/list?limit=20', {
        headers: { 'X-Telegram-Init-Data': tg.initData }
    });
    if (response.ok) return await response.json();
    return [];
}

export async function getRecommendations() {
    const response = await fetch('/api/history/recommendations?limit=10', {
        headers: { 'X-Telegram-Init-Data': tg.initData }
    });
    if (response.ok) return await response.json();
    return [];
}
