// ── Telegram WebApp ───────────────────────────────────────────────────────
export const tg = window.Telegram.WebApp;

// ── DOM Screens ───────────────────────────────────────────────────────────
export const screens = {
    loading: document.getElementById('loading'),
    home: document.getElementById('home'),
    player: document.getElementById('player-screen'),
};

// ── DOM Elements ──────────────────────────────────────────────────────────
export const elements = {
    userProfile: document.getElementById('user-profile'),
    featuredHero: document.getElementById('featured-hero'),
    latestMovies: document.getElementById('latest-movies'),
    playerFeed: document.getElementById('player-feed'),
    sharedPlayerContainer: document.getElementById('shared-player-container'),
    mainVideoMount: document.getElementById('main-video-mount'),
    playerTitle: document.getElementById('player-movie-title'),
    playerViews: document.getElementById('player-movie-views'),
    playerDate: document.getElementById('player-movie-date'),
    playerDescription: document.getElementById('player-movie-description'),
    playerRecommendations: document.getElementById('player-recommendations'),
    searchInput: document.getElementById('search-input'),
    searchResults: document.getElementById('search-results'),
    searchGrid: document.getElementById('search-grid'),
    sharedPlayerContainer: document.getElementById('shared-player-container'),
    brightnessOverlay: document.getElementById('brightness-overlay')
};

// ── Reactive State ────────────────────────────────────────────────────────
export let state = {
    user: null,
    movies: [],
    currentSort: 'newest',
    currentMovieIndex: 0,
    currentSrc: null,
    isCinemaMode: false,
    player: null,
    controlsTimeout: null,
    currentRotation: 0,
    feedObserver: null,
    brightness: 100,
    audioContext: null,
    gainNode: null,
    audioSource: null,
    softwareVolume: 100, // 0-100 or 0.0-2.0
};

export function updateState(patch) {
    Object.assign(state, patch);
}

// ── Persistence Utilities ────────────────────────────────────────────────
const STORAGE_PREFIX = 'tg_film_progress_';

export function saveProgress(movieId, time) {
    if (!movieId) return;
    localStorage.setItem(`${STORAGE_PREFIX}${movieId}`, time.toString());
}

export function getProgress(movieId) {
    if (!movieId) return 0;
    const saved = localStorage.getItem(`${STORAGE_PREFIX}${movieId}`);
    return saved ? parseFloat(saved) : 0;
}
