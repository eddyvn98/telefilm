/**
 * history-ui.js – Renders "Continue Watching", "Watch History", "Recommendations" sections.
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

function _historyCard(item) {
    const pct = item.progress_percent || 0;
    const isCompleted = pct >= 95;
    const completedBadge = isCompleted
        ? `<div class="absolute top-2 left-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
               <i class="fa-solid fa-check text-black text-[8px]"></i>
           </div>`
        : '';
    const timeAgo = _relativeTime(item.last_watched_at);
    return `
        <div class="cursor-pointer group flex-shrink-0 w-28" onclick="playMovie(${item.movie_id})">
            <div class="relative rounded-xl overflow-hidden aspect-[2/3]">
                <img src="${item.poster_url || '/static/img/placeholder.jpg'}"
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                     alt="${item.title}" loading="lazy">
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                ${completedBadge}
                ${!isCompleted && pct > 0 ? _progressBar(pct) : ''}
                ${!isCompleted && pct > 0
            ? `<div class="absolute bottom-2 right-2 bg-black/70 text-[10px] font-bold text-white px-1.5 py-0.5 rounded-md">${Math.round(pct)}%</div>`
            : ''}
            </div>
            <p class="text-xs font-medium mt-1.5 text-white/80 truncate">${item.title}</p>
            <div class="flex items-center justify-between mt-0.5">
                <p class="text-[10px] text-white/30 truncate">${timeAgo}</p>
                <div class="flex items-center gap-1 text-[10px] text-white/40">
                    <i class="fa-solid fa-eye text-[8px]"></i>
                    <span>${(item.global_views || 0).toLocaleString()}</span>
                </div>
            </div>
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
            <div class="flex items-center gap-1 text-[9px] text-white/30 mt-0.5">
                <i class="fa-solid fa-eye text-[8px]"></i>
                <span>${(item.global_views || 0).toLocaleString()} lượt xem</span>
            </div>
        </div>`;
}

function _relativeTime(isoString) {
    if (!isoString) return '';
    const diff = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Vừa xem';
    if (mins < 60) return `${mins} phút trước`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} giờ trước`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} ngày trước`;
    return new Date(isoString).toLocaleDateString('vi-VN');
}

// ── Section Renderers ─────────────────────────────────────────────────────────

/** "Xem tiếp" – phim đang dở (1% < progress < 95%) */
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

/** "Lịch sử xem" – TẤT CẢ phim đã xem, kể cả xem xong, mới nhất trước */
export function renderWatchHistorySection(historyItems) {
    const section = document.getElementById('watch-history-section');
    if (!section) return;

    if (historyItems.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    const grid = section.querySelector('.history-scroll-row');
    if (grid) grid.innerHTML = historyItems.map(_historyCard).join('');
}

/** "Gợi ý cho bạn" – phim chưa xem + xem chưa xong */
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
