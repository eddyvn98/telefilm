import { state, elements } from './state.js';
import { loadMovie } from './player-page.js';

let startX = 0;
let startY = 0;
let isVertical = false;
let isHorizontal = false;
let startVolume = 0;
let startBrightness = 100;
let startSeekTime = 0;
let side = 'none'; // 'left', 'middle', 'right'
let swipeThreshold = 60;

// Ref to dynamically injected elements
let gestureIndicators = {};

export function initPlayerGestures() {
    if (!state.player) return;

    const container = state.player.elements.container;
    if (!container) return;

    // Remove existing if any
    const oldLayer = container.querySelector('.dynamic-gesture-layer');
    if (oldLayer) oldLayer.remove();

    // Create the layer
    const layer = document.createElement('div');
    layer.className = 'dynamic-gesture-layer absolute inset-0 z-[10] touch-none pointer-events-auto';

    layer.innerHTML = `
        <div id="dynamic-brightness-overlay" class="absolute inset-0 bg-black pointer-events-none z-[11]" style="opacity: 0; transition: opacity 0.1s ease;"></div>
        <div class="gesture-indicator-left gesture-indicator left-6 top-1/2 -translate-y-1/2 pointer-events-none">
            <i class="fa-solid fa-sun mb-2"></i>
            <div class="indicator-bar"><div class="indicator-fill"></div></div>
        </div>
        <div class="gesture-indicator-right gesture-indicator right-6 top-1/2 -translate-y-1/2 pointer-events-none">
            <i class="fa-solid fa-volume-high mb-2"></i>
            <div class="indicator-bar"><div class="indicator-fill"></div></div>
        </div>
        <div class="gesture-indicator-center gesture-indicator left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex-col pointer-events-none">
            <div class="switch-icon mb-2 text-2xl"><i class="fa-solid fa-film"></i></div>
            <div class="seek-preview text-lg font-bold">Chuyển phim</div>
            <div class="seek-offset text-xs text-white/60">Vuốt dọc để đổi</div>
        </div>
    `;

    container.appendChild(layer);

    // Store refs
    gestureIndicators = {
        left: layer.querySelector('.gesture-indicator-left'),
        right: layer.querySelector('.gesture-indicator-right'),
        center: layer.querySelector('.gesture-indicator-center'),
        brightness: layer.querySelector('#dynamic-brightness-overlay')
    };

    layer.addEventListener('touchstart', handleTouchStart, { passive: false });
    layer.addEventListener('touchmove', handleTouchMove, { passive: false });
    layer.addEventListener('touchend', handleTouchEnd, { passive: false });
}

function handleTouchStart(e) {
    if (e.touches.length > 1) return;
    const touch = e.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = touch.clientX - rect.left;
    const oneThird = rect.width / 3;

    if (x < oneThird) side = 'left';
    else if (x < oneThird * 2) side = 'middle';
    else side = 'right';

    startVolume = state.softwareVolume || 100;
    startBrightness = state.brightness || 100;
    startSeekTime = state.player ? state.player.currentTime : 0;

    isVertical = false;
    isHorizontal = false;

    if (state.audioContext && state.audioContext.state === 'suspended') {
        state.audioContext.resume();
    }
}

function handleTouchMove(e) {
    if (e.touches.length > 1) return;
    const touch = e.touches[0];
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;

    if (!isVertical && !isHorizontal) {
        if (Math.abs(dy) > Math.abs(dx) && Math.abs(dy) > 10) isVertical = true;
        else if (Math.abs(dx) > 10) isHorizontal = true;
    }

    if (isVertical) {
        e.preventDefault();
        const sensitivity = 0.5;
        const delta = (startY - touch.clientY) * sensitivity;

        if (side === 'left') {
            updateBrightness(Math.max(0, Math.min(100, startBrightness + delta)));
        } else if (side === 'right') {
            // Software Volume logic - higher sensitivity for volume
            const vSensitivity = 0.8;
            const vDelta = (startY - touch.clientY) * vSensitivity;
            let val = Math.max(0, Math.min(150, startVolume + vDelta));
            updateSoftwareVolume(val);
        } else if (side === 'middle') {
            showSwitchPreview(startY - touch.clientY);
        }
    } else if (isHorizontal) {
        e.preventDefault();
        const dx = touch.clientX - startX;
        if (state.player) {
            const seekOffset = dx / 5;
            const newTime = Math.max(0, Math.min(state.player.duration, startSeekTime + seekOffset));
            state.player.currentTime = newTime;
        }
        showSeekPreview(dx);
    }
}

function handleTouchEnd(e) {
    hideIndicators();
    if (!e.changedTouches[0]) return;

    const dx = e.changedTouches[0].clientX - startX;
    const dy = e.changedTouches[0].clientY - startY;

    // Tap to pause
    if (!isVertical && !isHorizontal && Math.abs(dx) < 15 && Math.abs(dy) < 15) {
        if (state.player) {
            if (state.player.playing) state.player.pause();
            else state.player.play();
        }
    }

    // Switch Movie execution
    if (isVertical && side === 'middle') {
        const vDelta = startY - e.changedTouches[0].clientY;
        if (Math.abs(vDelta) > swipeThreshold) {
            const direction = vDelta > 0 ? 1 : -1;
            const newIndex = state.currentMovieIndex + direction;
            if (newIndex >= 0 && newIndex < state.movies.length) {
                loadMovie(state.movies[newIndex].id);
            }
        }
    }

    // Seek execution (Already handled in real-time in touchmove)
    if (isHorizontal) {
        // Just clean up state
    }

    isVertical = false;
    isHorizontal = false;
}

function updateBrightness(val) {
    state.brightness = val;
    const opacity = (100 - val) / 100 * 0.8;
    if (gestureIndicators.brightness) gestureIndicators.brightness.style.opacity = opacity;
    updateIndicator(gestureIndicators.left, val);
}

function updateSoftwareVolume(val) {
    state.softwareVolume = val;
    if (state.gainNode) {
        state.gainNode.gain.setTargetAtTime(val / 100, state.audioContext.currentTime, 0.01);
    }
    // Also ensure Plyr is unmuted for web audio to work well
    if (state.player && state.player.muted && val > 0) {
        state.player.muted = false;
        state.player.volume = 1;
    }
    // Indicator: 100% volume = full bar. > 100% still stays full or changes color?
    // Let's just scale it to 100 for visual simplicity.
    updateIndicator(gestureIndicators.right, Math.min(100, val));
}

function updateIndicator(el, val) {
    if (!el) return;
    el.classList.add('active');
    const fill = el.querySelector('.indicator-fill');
    if (fill) fill.style.height = `${val}%`;
}

function showSwitchPreview(vDelta) {
    const el = gestureIndicators.center;
    if (!el) return;
    el.classList.add('active');
    const preview = el.querySelector('.seek-preview');
    const offset = el.querySelector('.seek-offset');
    const iconEl = el.querySelector('.switch-icon i');

    if (Math.abs(vDelta) < swipeThreshold) {
        preview.textContent = 'Đổi phim';
        offset.textContent = vDelta > 0 ? '↑ Vuốt lên: Tiếp' : '↓ Vuốt xuống: Trước';
        if (iconEl) iconEl.className = 'fa-solid fa-film';
    } else {
        const direction = vDelta > 0 ? 1 : -1;
        const nextIdx = state.currentMovieIndex + direction;
        if (nextIdx < 0 || nextIdx >= state.movies.length) {
            preview.textContent = 'Hết danh sách';
            offset.textContent = '';
            if (iconEl) iconEl.className = 'fa-solid fa-ban text-red-500';
        } else {
            preview.textContent = vDelta > 0 ? 'Phim tiếp theo' : 'Phim trước đó';
            offset.textContent = state.movies[nextIdx].title;
            if (iconEl) iconEl.className = vDelta > 0 ? 'fa-solid fa-chevron-up text-primary' : 'fa-solid fa-chevron-down text-primary';
        }
    }
}

function showSeekPreview(dx) {
    const el = gestureIndicators.center;
    if (!el) return;
    el.classList.add('active');
    const preview = el.querySelector('.seek-preview');
    const offset = el.querySelector('.seek-offset');
    const iconEl = el.querySelector('.switch-icon i');

    const seconds = Math.round(dx / 5);
    const prefix = seconds > 0 ? '+' : '';
    preview.textContent = `${prefix}${seconds}s`;
    offset.textContent = seconds > 0 ? 'Tua nhanh' : 'Tua lại';
    if (iconEl) iconEl.className = seconds > 0 ? 'fa-solid fa-forward' : 'fa-solid fa-backward';
}

function hideIndicators() {
    Object.values(gestureIndicators).forEach(el => {
        if (el && el.classList) el.classList.remove('active');
    });
}
