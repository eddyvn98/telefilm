import { tg, screens, elements, state, updateState } from './state.js';
import { login, fetchMovies } from './api.js';
import { renderUser, renderHero, applySortAndRender, showAccessDenied, renderSkeletons } from './ui.js';
import { exitCinemaMode, showCinemaControls, handleOrientationChange } from './player-cinema.js';
import './player-page.js'; // Registers window.playMovie

async function init() {
    tg.ready();
    tg.expand();

    // Sync Theme
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.backgroundColor);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.textColor);

    try {
        await login();
        renderUser();

        renderSkeletons(elements.latestMovies, 10);
        const movies = await fetchMovies();
        updateState({ movies: movies.length > 0 ? movies : getMockMovies() });

        renderHero(state.movies[0]);
        applySortAndRender(); // This will also init the feed via ui.js

        initGestures();
        initFullscreenListeners();

        // Reveal Home
        setTimeout(() => {
            screens.loading.classList.add('opacity-0');
            setTimeout(() => {
                screens.loading.classList.add('hidden');
                screens.home.classList.remove('hidden');
            }, 500);
        }, 800);

    } catch (error) {
        console.error('Init Error:', error);
        if (error.status === 403) showAccessDenied();
    }
}

function getMockMovies() {
    return [
        { id: 1, title: 'Interstellar', poster_url: 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlSaba7.jpg', description: 'Explorers travel through a wormhole...' },
        { id: 2, title: 'The Dark Knight', poster_url: 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDr9p1v3hvZBn0zSSTg.jpg', description: 'Batman vs Joker...' }
    ];
}

function initFullscreenListeners() {
    tg.onEvent('fullscreenChanged', () => {
        if (!tg.isFullscreen && state.isCinemaMode) exitCinemaMode();
    });
}

// ── UI Handlers (Global Scope for HTML) ───────────────────────────────────

window.toggleSortMenu = (show) => {
    const menu = document.getElementById('sort-menu');
    const overlay = document.getElementById('sort-overlay');
    if (show) { menu.classList.add('active'); overlay.classList.add('active'); }
    else { menu.classList.remove('active'); overlay.classList.remove('active'); }
};

window.selectSort = (val) => {
    updateState({ currentSort: val });
    document.querySelectorAll('.sort-item').forEach(item => {
        item.classList.toggle('selected', item.getAttribute('data-sort') === val);
    });
    window.toggleSortMenu(false);
    applySortAndRender();
};

window.closePlayer = () => {
    if (state.player) state.player.pause();
    exitCinemaMode();
    screens.player.classList.add('hidden');
    screens.player.classList.remove('flex');
};

// ── Gestures & Search ─────────────────────────────────────────────────────

function initGestures() {
    const showControls = () => { if (state.isCinemaMode) showCinemaControls(); };

    screens.player.addEventListener('touchstart', showControls, { passive: true });
    screens.player.addEventListener('mousemove', showControls);

    // Also catch taps on the cinema overlay itself
    const overlay = document.getElementById('cinema-overlay');
    if (overlay) {
        overlay.addEventListener('touchstart', showControls, { passive: true });
        overlay.addEventListener('click', showControls);
    }
}

elements.searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    if (q.length < 2) {
        elements.searchResults.classList.add('hidden');
        return;
    }
    const filtered = state.movies.filter(m => m.title.toLowerCase().includes(q));
    if (filtered.length > 0) {
        elements.searchResults.classList.remove('hidden');
        import('./ui.js').then(m => m.renderMovieList(filtered, elements.searchGrid));
    }
});

init();
