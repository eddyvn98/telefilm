import { state, elements, tg, updateState, screens, getProgress } from './state.js';
import { initPlyr, setupHLS } from './player.js';
import { exitCinemaMode, handleOrientationChange } from './player-cinema.js';
import { renderMovieList, showResumeBanner } from './ui.js';
import { initPlayerGestures } from './player-gestures.js';
import { startTracking, stopTracking, flushNow } from './history.js';

function initSoftwareVolume() {
    if (!state.player) return;
    const video = state.player.elements.viewer || state.player.elements.video;
    if (!video) return;

    try {
        if (!state.audioContext) {
            state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            state.gainNode = state.audioContext.createGain();
            state.gainNode.gain.value = (state.softwareVolume || 100) / 100;
            state.gainNode.connect(state.audioContext.destination);
        }

        // Avoid InvalidStateError by checking existing connections
        if (!state.audioSource || state.audioSource.mediaElement !== video) {
            if (state.audioSource) state.audioSource.disconnect();
            state.audioSource = state.audioContext.createMediaElementSource(video);
            state.audioSource.connect(state.gainNode);
        }

        // Force player to full volume & unmuted internally for GainNode to have full signal
        state.player.volume = 1;
        state.player.muted = false;

        if (state.audioContext.state === 'suspended') {
            state.audioContext.resume();
        }
    } catch (err) {
        console.warn('Software Volume Init:', err.message);
    }
}

export function loadMovie(id) {
    const movie = state.movies.find(m => m.id === id);
    if (!movie) return;

    updateState({ currentMovieIndex: state.movies.indexOf(movie) });

    // Fill UI
    elements.playerTitle.textContent = movie.title;
    elements.playerViews.innerHTML = `<i class="fa-solid fa-eye mr-1"></i>${(movie.views || 0).toLocaleString()} lượt xem`;
    elements.playerDate.innerHTML = `<i class="fa-solid fa-calendar mr-1"></i>${new Date(movie.created_at || Date.now()).toLocaleDateString('vi-VN')}`;
    elements.playerDescription.textContent = movie.description || 'Không có mô tả.';

    // Render recommendations (excluding current movie)
    const otherMovies = state.movies.filter(m => m.id !== id);
    const shuffled = [...otherMovies].sort(() => Math.random() - 0.5);
    renderMovieList(shuffled.slice(0, 6), elements.playerRecommendations);

    // Stop previous tracking before starting new one
    stopTracking();

    // Prepare Player
    if (!state.player) {
        initPlyr();
        initPlayerGestures();
    }

    // If we were in cinema mode, exit or re-init carefully
    if (state.isCinemaMode) exitCinemaMode();

    const mountPoint = elements.mainVideoMount;
    const playerWrapper = state.player.elements.container;

    if (playerWrapper.parentElement !== mountPoint) {
        mountPoint.appendChild(playerWrapper);
    }
    elements.sharedPlayerContainer.classList.remove('hidden');
    playerWrapper.classList.remove('hidden');

    // Initialize Software Volume (GainNode) for iOS/Mobile support
    initSoftwareVolume();

    const newSrc = `/api/stream/${movie.id}?init_data=${encodeURIComponent(tg.initData)}`;

    if (state.currentSrc !== newSrc) {
        updateState({ currentSrc: newSrc });

        const video = state.player.elements.video;
        // Cleanup old HLS
        if (state.hls) {
            state.hls.destroy();
            state.hls = null;
        }

        const isHLS = setupHLS(video, newSrc);
        if (!isHLS) {
            state.player.source = {
                type: 'video',
                title: movie.title,
                sources: [{ src: newSrc, type: 'video/mp4' }]
            };
        }

        // Resume Progress Logic
        const savedProgress = getProgress(movie.id);
        if (savedProgress > 10) {
            showResumeBanner(savedProgress, () => {
                state.player.currentTime = savedProgress;
                state.player.play().catch(() => { });
            });
        }

        state.player.play().catch(() => { });

        // Start history tracking for new source
        startTracking(id, () => state.player);
    }

    // Scroll to top of player screen
    screens.player.scrollTo(0, 0);

    // Listen for rotation
    window.addEventListener('resize', handleOrientationChange);
    window.addEventListener('orientationchange', handleOrientationChange);

    // MiniPlayer Intersection Observer
    if (state.miniPlayerObserver) state.miniPlayerObserver.disconnect();

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const playerWrapper = state.player.elements.container;
            if (!entry.isIntersecting && state.player.playing && !state.isCinemaMode) {
                playerWrapper.classList.add('mini-player');
            } else {
                playerWrapper.classList.remove('mini-player');
            }
        });
    }, { threshold: 0.1 });

    observer.observe(mountPoint);
    updateState({ miniPlayerObserver: observer });
}

// Attach to window for HTML calls
window.playMovie = function (id) {
    screens.player.classList.remove('hidden');
    screens.player.classList.add('flex');
    loadMovie(id);
};

window.shufflePlay = function () {
    if (!state.movies || !state.movies.length) return;
    const randomIndex = Math.floor(Math.random() * state.movies.length);
    const randomMovie = state.movies[randomIndex];
    window.playMovie(randomMovie.id);
};
