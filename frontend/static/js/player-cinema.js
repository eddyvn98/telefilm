import { state, updateState, tg, screens } from './state.js';

// ── Cinema Mode (Manual Toggle Only) ─────────────────────────────────────
// NOTE: Automatic fullscreen on landscape rotation is handled purely by CSS
// @media (orientation: landscape) in cinema.css — no JS needed, no flash.

// ── Enter Cinema Fullscreen (manual button) ───────────────────────────────

export function enterCinemaFullscreen() {
    if (!state.player || state.isCinemaMode) return;

    updateState({ isCinemaMode: true });
    screens.player.classList.add('cinema-mode-active');

    const playerWrapper = state.player.elements.container;
    playerWrapper.classList.add('cinema-fullscreen');

    if (!state.player.playing) state.player.play().catch(() => { });

    createCinemaCloseBtn();

    if (tg.requestFullscreen) tg.requestFullscreen();
    if (tg.setHeaderColor) tg.setHeaderColor('#000000');

    const icon = document.getElementById('cinema-icon');
    if (icon) icon.className = 'fa-solid fa-compress';
}

// ── Exit Cinema Mode (manual button or portrait rotation) ─────────────────

export function exitCinemaMode() {
    if (!state.isCinemaMode) return;

    updateState({ isCinemaMode: false });
    screens.player.classList.remove('cinema-mode-active');

    removeCinemaCloseBtn();
    clearTimeout(state.controlsTimeout);

    if (state.player) {
        const playerWrapper = state.player.elements.container;
        playerWrapper.classList.remove('cinema-fullscreen');
        state.player.muted = true;
    }

    const icon = document.getElementById('cinema-icon');
    if (icon) icon.className = 'fa-solid fa-expand';

    if (tg.exitFullscreen) tg.exitFullscreen();
    if (tg.setHeaderColor) tg.setHeaderColor('bg_color');
}

// ── Orientation watcher for close button + Telegram expand API ────────────
// Uses a matchMedia listener — fires in sync with CSS @media queries,
// avoiding the double-reflow that debounced resize/orientationchange caused.

const landscapeQuery = window.matchMedia('(orientation: landscape)');

function onOrientationChange(e) {
    if (screens.player.classList.contains('hidden')) return;

    if (e.matches) {
        // Landscape: show close button, expand Telegram
        document.body.classList.add('in-player-landscape');
        createCinemaCloseBtn();
        if (tg.requestFullscreen) tg.requestFullscreen();
        if (tg.setHeaderColor) tg.setHeaderColor('#000000');
        if (state.player && !state.player.playing) state.player.play().catch(() => { });
    } else {
        // Portrait: remove close button, restore Telegram header
        document.body.classList.remove('in-player-landscape');
        // Only remove the close btn if not in manual cinema mode
        if (!state.isCinemaMode) {
            removeCinemaCloseBtn();
            if (tg.exitFullscreen) tg.exitFullscreen();
            if (tg.setHeaderColor) tg.setHeaderColor('bg_color');
        }
    }
}

landscapeQuery.addEventListener('change', onOrientationChange);

// ── Close Button ──────────────────────────────────────────────────────────

function createCinemaCloseBtn() {
    if (document.getElementById('cinema-close-btn')) return; // Already exists
    const closeBtn = document.createElement('button');
    closeBtn.id = 'cinema-close-btn';
    closeBtn.className = 'cinema-close-btn visible';
    closeBtn.innerHTML = '<i class="fa-solid fa-arrow-left"></i>';
    closeBtn.setAttribute('aria-label', 'Thoát fullscreen');
    closeBtn.addEventListener('click', () => {
        if (state.isCinemaMode) {
            exitCinemaMode();
        } else {
            // Landscape auto-mode: just trigger exit via orientation (user rotates back)
            // or provide a simple visual feedback — do nothing (user rotates back)
        }
    });
    document.body.appendChild(closeBtn);
}

function removeCinemaCloseBtn() {
    document.getElementById('cinema-close-btn')?.remove();
}

// ── Cinema Controls Auto-hide ─────────────────────────────────────────────

export function showCinemaControls() {
    const closeBtn = document.getElementById('cinema-close-btn');
    if (!closeBtn) return;

    closeBtn.classList.add('visible');
    clearTimeout(state.controlsTimeout);

    const timeout = setTimeout(() => {
        // Only hide if NOT in manual isCinemaMode (landscape auto shows it via CSS)
        if (!state.isCinemaMode) return;
        closeBtn.classList.remove('visible');
    }, 3000);
    updateState({ controlsTimeout: timeout });
}

// ── Cinema Mode Toggle (manual button) ────────────────────────────────────

window.toggleCinemaMode = function () {
    if (state.isCinemaMode) {
        exitCinemaMode();
    } else {
        enterCinemaFullscreen();
    }
};

// ── handleOrientationChange: exported as no-op for backwards compatibility ─
// (player-page.js imports this — keep export to avoid import errors)
export const handleOrientationChange = () => { };

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
