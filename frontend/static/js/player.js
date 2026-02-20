import { state, updateState, saveProgress } from './state.js';

// ── Plyr Initialization ────────────────────────────────────────────────────

export function initPlyr() {
    const playerInstance = new Plyr('#video-player', {
        controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'settings'],
        seekTime: 10,
        muted: true,
        settings: ['quality', 'speed', 'loop'],
        speed: { selected: 2, options: [0.5, 0.75, 1, 1.25, 1.5, 2, 4] },
        i18n: {
            play: 'Phát', pause: 'Tạm dừng', speed: 'Tốc độ', normal: 'Bình thường',
            quality: 'Chất lượng', loop: 'Lặp lại', settings: 'Cài đặt'
        }
    });

    // Save progress periodically
    let lastSave = 0;
    playerInstance.on('timeupdate', () => {
        const now = Date.now();
        if (now - lastSave > 3000) { // Save every 3 seconds
            const movieId = state.movies[state.currentMovieIndex]?.id;
            if (movieId) saveProgress(movieId, playerInstance.currentTime);
            lastSave = now;
        }
    });

    playerInstance.on('ended', () => {
        const movieId = state.movies[state.currentMovieIndex]?.id;
        if (movieId) saveProgress(movieId, 0); // Clear progress when finished

        const nextIdx = state.currentMovieIndex + 1;
        if (nextIdx < state.movies.length) {
            const nextMovie = state.movies[nextIdx];
            setTimeout(() => {
                if (window.playMovie) window.playMovie(nextMovie.id);
            }, 2000);
        }
    });

    updateState({ player: playerInstance });
}

export function setupHLS(video, src) {
    if (!window.Hls) return false;

    if (src.includes('.m3u8')) {
        if (Hls.isSupported()) {
            const hls = new Hls();
            hls.loadSource(src);
            hls.attachMedia(video);
            state.hls = hls; // Store in state for cleanup
            return true;
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            // Native HLS support (Safari)
            video.src = src;
            return true;
        }
    }
    return false;
}
