/**
 * history.js – Watch history tracking service
 * Records progress every RECORD_INTERVAL seconds (debounced, non-blocking).
 */
import { postWatchHistory } from './api.js';

const RECORD_INTERVAL = 10; // seconds between API calls

let _intervalId = null;
let _currentMovieId = null;
let _getPlayerRef = null; // () => plyr instance

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Start recording watch progress for a movie.
 * @param {number} movieId
 * @param {Function} getPlayer - returns current Plyr instance
 */
export function startTracking(movieId, getPlayer) {
    stopTracking();
    _currentMovieId = movieId;
    _getPlayerRef = getPlayer;

    _intervalId = setInterval(_flush, RECORD_INTERVAL * 1000);
}

/** Stop recording (call on movie close / unmount). */
export function stopTracking() {
    if (_intervalId) {
        clearInterval(_intervalId);
        _intervalId = null;
    }
    _currentMovieId = null;
    _getPlayerRef = null;
}

/**
 * Manually flush current progress to API (e.g. on page unload).
 */
export async function flushNow() {
    await _flush();
}

// ── Internal ──────────────────────────────────────────────────────────────────

async function _flush() {
    if (!_currentMovieId || !_getPlayerRef) return;

    const player = _getPlayerRef();
    if (!player) return;

    const progress = player.currentTime || 0;
    const duration = player.duration || 0;

    // Skip if not meaningfully started
    if (progress < 1) return;

    await postWatchHistory(_currentMovieId, progress, duration);
}
