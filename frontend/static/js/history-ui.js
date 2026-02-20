/**
 * history-ui.js – Renders "Continue Watching" and "Recommendations" sections.
 */

// ── Templates ─────────────────────────────────────────────────────────────────

function _progressBar(percent) {
    const clamped = Math.min(percent, 100);
    return `
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-black/40">
            <div class="h-full bg-primary transition-all duration-300" style="width:${clamped}%"></div>
        </div>`;
}

function _continueCard(item) {
    const pct = item.progress_percent || 0;
    return `
        <div class="continue-card cursor-pointer group flex-shrink-0 w-28" onclick="playMovie(${item.movie_id})">
            <div class="relative rounded-xl overflow-hidden aspect-[2/3]">
                <img src="${item.poster_url || '/static/img/placeholder.jpg'}"
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                     alt="${item.title}" loading="lazy">
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                ${pct > 0 ? _progressBar(pct) : ''}
                ${pct > 0 ? `<div class="absolute top-2 right-2 bg-black/70 text-[10px] font-bold text-white px-1.5 py-0.5 rounded-md">${Math.round(pct)}%</div>` : ''}
            </div>
            <p class="text-xs font-medium mt-1.5 text-white/70 truncate">${item.title}</p>
        </div>`;
}

function _recommendCard(item) {
    const badge = item.reason === 'unfinished'
        ? `<div class="absolute top-2 left-2 bg-primary/90 text-black text-[9px] font-black px-1.5 py-0.5 rounded-full uppercase">Xem tiếp</div>`
        : '';
    return `
        <div class="cursor-pointer group flex-shrink-0 w-28" onclick="playMovie(${item.movie_id})">
            <div class="relative rounded-xl overflow-hidden aspect-[2/3]">
                <img src="${item.poster_url || '/static/img/placeholder.jpg'}"
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                     alt="${item.title}" loading="lazy">
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                ${badge}
                ${item.progress_percent > 0 ? _progressBar(item.progress_percent) : ''}
            </div>
            <p class="text-xs font-medium mt-1.5 text-white/70 truncate">${item.title}</p>
        </div>`;
}

// ── Section Renderers ─────────────────────────────────────────────────────────

/**
 * Render "Xem tiếp" section (movies with progress > 0 and < 100%).
 * @param {Array} historyItems - items from GET /api/history/list
 */
export function renderContinueWatching(historyItems) {
    const section = document.getElementById('continue-watching-section');
    if (!section) return;

    const inProgress = historyItems.filter(
        item => item.progress_percent > 1 && item.progress_percent < 95
    );

    if (inProgress.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    const grid = section.querySelector('.history-scroll-row');
    if (grid) grid.innerHTML = inProgress.map(_continueCard).join('');
}

/**
 * Render "Gợi ý cho bạn" section.
 * @param {Array} recommendations - items from GET /api/history/recommendations
 */
export function renderRecommendationSection(recommendations) {
    const section = document.getElementById('recommendations-section');
    if (!section) return;

    if (recommendations.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    const grid = section.querySelector('.history-scroll-row');
    if (grid) grid.innerHTML = recommendations.map(_recommendCard).join('');
}
