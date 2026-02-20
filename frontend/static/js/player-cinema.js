import { state, updateState, tg, screens } from './state.js';

// ── Landscape Detection → Fullscreen Cinema ───────────────────────────────

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

export const handleOrientationChange = debounce(() => {
    if (screens.player.classList.contains('hidden')) return;

    // Use a slighly larger threshold or check specific orientation APIs if available
    const isLandscape = window.innerWidth > window.innerHeight;

    if (isLandscape && !state.isCinemaMode) {
        enterCinemaFullscreen();
    } else if (!isLandscape && state.isCinemaMode) {
        exitCinemaMode();
    }
}, 200); // 200ms debounce to wait for rotation animation

// ── Enter Cinema Fullscreen ───────────────────────────────────────────────
// Move Plyr wrapper into #cinema-overlay (body-level div), show it fullscreen.
// This avoids CSS clipping from nested feed structures.
// CSS-Only Approach: Add .cinema-fullscreen class to fixed position the player.
// No DOM moving = No reload/stutter.

export function enterCinemaFullscreen() {
    if (!state.player) return;
    const movie = state.movies[state.currentMovieIndex];
    if (!movie) return;

    // Prevent double entry
    if (state.isCinemaMode) return;

    updateState({ isCinemaMode: true });
    screens.player.classList.add('cinema-mode-active');
    if (tg.setHeaderColor) tg.setHeaderColor('#000000');

    const playerWrapper = state.player.elements.container;
    playerWrapper.classList.add('cinema-fullscreen');

    if (!state.player.playing) state.player.play().catch(() => { });

    // Create close button
    createCinemaCloseBtn();

    if (tg.requestFullscreen) tg.requestFullscreen();

    // Trigger resize to fix layout
    setTimeout(() => window.dispatchEvent(new Event('resize')), 100);

    const icon = document.getElementById('cinema-icon');
    if (icon) icon.className = 'fa-solid fa-compress';
}

function createCinemaCloseBtn() {
    removeCinemaCloseBtn();
    const closeBtn = document.createElement('button');
    closeBtn.id = 'cinema-close-btn';
    closeBtn.className = 'cinema-close-btn';
    closeBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>';
    closeBtn.setAttribute('aria-label', 'Thoát fullscreen');
    closeBtn.addEventListener('click', () => exitCinemaMode());
    document.body.appendChild(closeBtn);
    showCinemaControls();
}

function removeCinemaCloseBtn() {
    document.getElementById('cinema-close-btn')?.remove();
}

// ── Exit Cinema Mode ──────────────────────────────────────────────────────

export function exitCinemaMode() {
    if (!state.isCinemaMode) return;

    updateState({ isCinemaMode: false });
    screens.player.classList.remove('cinema-mode-active');
    if (tg.setHeaderColor) tg.setHeaderColor('bg_color');

    removeCinemaCloseBtn();
    clearTimeout(state.controlsTimeout);

    if (state.player) {
        const playerWrapper = state.player.elements.container;
        playerWrapper.classList.remove('cinema-fullscreen');

        // Re-mute for portrait scroll preview
        state.player.muted = true;
    }

    // Restore button icon
    const icon = document.getElementById('cinema-icon');
    if (icon) icon.className = 'fa-solid fa-expand';

    if (tg.exitFullscreen) tg.exitFullscreen();
    setTimeout(() => window.dispatchEvent(new Event('resize')), 100);
}

// ── Cinema Controls Auto-hide ─────────────────────────────────────────────

export function showCinemaControls() {
    const closeBtn = document.getElementById('cinema-close-btn');
    if (!closeBtn) return;

    closeBtn.classList.add('visible');
    clearTimeout(state.controlsTimeout);

    const timeout = setTimeout(() => {
        closeBtn.classList.remove('visible');
    }, 3000);
    updateState({ controlsTimeout: timeout });
}

// ── Cinema Mode Toggle (manual button) ───────────────────────────────────

// ── Cinema Mode Toggle (manual button or tap) ────────────────────────────

window.toggleCinemaMode = function (targetIdx) {
    if (state.isCinemaMode) {
        exitCinemaMode();
    } else {
        // If a specific index is requested and it's different from current, switch to it first
        // Note: attachPlayerToSlide needs to be imported if we want to switch, 
        // but circular dependency might be an issue. 
        // For now, let's assume UI handles index switching or ignore targetIdx 
        // if it's strictly for cinema toggle.
        // Actually, let's import it dynamically to avoid cycle if possible, or move this back to app/feed.
        // But toggleCinemaMode is called from HTML.

        // Strategy: We'll dispatch a custom event if index change is needed, or just warn.
        // Or better: The HTML calling this usually assumes we are on that slide.

        /* 
           Refactor Note: 
           If targetIdx is passed and != current, we strictly need to switch.
           Since attachPlayerToSlide is in player-feed.js, and that imports exitCinemaMode from here,
           we have a potential circular dependency if we import attachPlayerToSlide here.
           
           Solution: We can assume toggleCinemaMode is called when the user is already on the slide 
           OR we can move this window function to `app.js` or `player-feed.js` where full context is available.
           
           However, for now, let's keep it here but remove the slide switching logic if it causes issues, 
           or use a global helper. 
           
           Actually, let's move `toggleCinemaMode` to `player-feed.js` since it might involve feed navigation.
           Wait, `rotateVideo` is purely visual/cinema.
           
           Let's keep `enter` and `exit` here. `toggle` can be here if we don't switch slides.
           The original code had switching logic.
           
           Let's use a delayed import or global function for the switch if needed.
           But `attachPlayerToSlide` is exported from `player-feed.js`.
           
           Let's move `toggleCinemaMode` to `player-feed.js` because it interacts with the feed (changing slides).
        */
        enterCinemaFullscreen();
    }
};

// ── Manual Rotate Video ───────────────────────────────────────────────────

window.rotateVideo = function () {
    const playerWrapper = state.player?.elements.container;
    const video = playerWrapper?.querySelector('video') || document.getElementById('video-player');
    if (!video) return;

    const rot = (state.currentRotation + 90) % 360;
    updateState({ currentRotation: rot });

    if (rot === 90 || rot === 270) {
        const container = video.closest('.video-container') || video.parentElement;
        const rect = container.getBoundingClientRect();
        const scale = Math.min(rect.width / video.offsetHeight, rect.height / video.offsetWidth);
        video.style.transform = `rotate(${rot}deg) scale(${scale})`;
    } else {
        video.style.transform = `rotate(${rot}deg) scale(1)`;
    }
};
