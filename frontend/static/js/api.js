import { tg } from './state.js';

let reauthPromise = null;

export async function login() {
    if (!tg.initData) {
        const err = new Error('Telegram initData is unavailable');
        err.status = 401;
        throw err;
    }

    const response = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: tg.initData })
    });
    if (!response.ok) {
        const err = new Error('Login failed');
        err.status = response.status;
        throw err;
    }
    return await response.json();
}

async function apiFetch(url, options = {}, retry = true) {
    const response = await fetch(url, {
        ...options,
        credentials: 'same-origin',
        headers: { ...(options.headers || {}) }
    });
    if (response.status === 401 && retry && tg.initData) {
        if (!reauthPromise) {
            reauthPromise = login().finally(() => { reauthPromise = null; });
        }
        await reauthPromise;
        return apiFetch(url, options, false);
    }
    return response;
}

export async function fetchMovies() {
    const response = await apiFetch('/api/catalog/movies?limit=10000');
    if (response.ok) return await response.json();
    if (response.status === 401 || response.status === 403) throw response;
    return [];
}

export async function postWatchHistory(movieId, progressSeconds, durationSeconds) {
    try {
        await apiFetch('/api/history/record', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                movie_id: movieId,
                progress_seconds: progressSeconds,
                duration_seconds: durationSeconds
            })
        });
    } catch (_) {
        // History is non-critical.
    }
}

export async function getWatchHistory() {
    const response = await apiFetch('/api/history/list?limit=20');
    return response.ok ? await response.json() : [];
}

export async function getRecommendations() {
    const response = await apiFetch('/api/history/recommendations?limit=10');
    return response.ok ? await response.json() : [];
}

export async function incrementMovieView(movieId) {
    try {
        const response = await apiFetch(`/api/catalog/movies/${movieId}/view`, { method: 'POST' });
        if (response.ok) return await response.json();
    } catch (_) {
        // Non-critical.
    }
    return null;
}

export async function getStreamToken(movieId) {
    const response = await apiFetch(`/api/stream/${movieId}/token`);
    if (!response.ok) throw new Error('Unable to authorize playback');
    return await response.json();
}
