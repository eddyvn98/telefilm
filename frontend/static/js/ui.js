import { state, elements, screens, tg } from './state.js';
// ── User Profile ──────────────────────────────────────────────────────────

export function renderUser() {
    const user = tg.initDataUnsafe?.user;
    if (!user) return;
    elements.userProfile.innerHTML = `
        <span class="text-sm font-semibold text-white/80">${user.first_name}</span>
        ${user.photo_url
            ? `<img src="${user.photo_url}" class="w-8 h-8 rounded-full object-cover ring-2 ring-primary/30" alt="avatar">`
            : `<div class="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs font-bold">${user.first_name[0]}</div>`
        }
    `;
}

// ── Hero Card ─────────────────────────────────────────────────────────────

export function renderHero(movie) {
    if (!movie) return;
    elements.featuredHero.innerHTML = `
        <div class="relative rounded-3xl overflow-hidden aspect-[16/9] cursor-pointer group" onclick="playMovie(${movie.id})">
            <img src="${movie.poster_url || '/static/img/placeholder.jpg'}"
                 class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                 alt="${movie.title}" loading="lazy">
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>
            <div class="absolute bottom-0 left-0 right-0 p-6">
                <div class="inline-flex items-center gap-1.5 bg-primary/20 backdrop-blur-sm border border-primary/30 rounded-full px-3 py-1 mb-3">
                    <i class="fa-solid fa-fire text-primary text-xs"></i>
                    <span class="text-primary text-xs font-bold uppercase tracking-wider">Featured</span>
                </div>
                <h2 class="text-2xl font-bold tracking-tight mb-1">${movie.title}</h2>
                <p class="text-white/60 text-sm line-clamp-2">${movie.description || ''}</p>
                <div class="mt-4 flex gap-3">
                    <button onclick="event.stopPropagation(); playMovie(${movie.id})"
                        class="flex items-center gap-2 bg-primary text-black font-bold px-6 py-2.5 rounded-full text-sm hover:bg-primary/90 transition-all">
                        <i class="fa-solid fa-play text-xs"></i> Xem Ngay
                    </button>
                    <button class="flex items-center gap-2 glass px-4 py-2.5 rounded-full text-sm hover:bg-white/10 transition-all">
                        <i class="fa-solid fa-circle-info text-xs"></i> Chi Tiết
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ── Movie Grid List (for search) ──────────────────────────────────────────

export function renderMovieList(movies, container) {
    if (!container) return;
    container.innerHTML = movies.map(m => `
        <div class="movie-card cursor-pointer group" onclick="playMovie(${m.id})">
            <div class="relative rounded-2xl overflow-hidden aspect-[2/3]">
                <img src="${m.poster_url || '/static/img/placeholder.jpg'}"
                     class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                     alt="${m.title}" loading="lazy">
                <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-3">
                    <span class="text-xs font-semibold truncate">${m.title}</span>
                </div>
            </div>
            <p class="text-xs font-medium mt-2 text-white/70 truncate">${m.title}</p>
        </div>
    `).join('');
}

// ── Sort & Render ─────────────────────────────────────────────────────────

export function applySortAndRender() {
    const sorted = [...state.movies].sort((a, b) => {
        switch (state.currentSort) {
            case 'title': return a.title.localeCompare(b.title);
            case 'views_desc': return (b.views || 0) - (a.views || 0);
            case 'duration_desc': return (b.duration || 0) - (a.duration || 0);
            case 'size_desc': return (b.file_size || 0) - (a.file_size || 0);
            case 'size_asc': return (a.file_size || 0) - (b.file_size || 0);
            default: return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        }
    });

    // Render grid in #latest-movies (home screen)
    renderMovieList(sorted, elements.latestMovies);
}

// ── Access Denied ─────────────────────────────────────────────────────────

export function showAccessDenied() {
    screens.loading.innerHTML = `
        <div class="text-center px-8">
            <div class="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
                <i class="fa-solid fa-lock text-red-400 text-xl"></i>
            </div>
            <h2 class="text-xl font-bold mb-2">Truy Cập Bị Từ Chối</h2>
            <p class="text-white/50 text-sm">Bạn không có quyền truy cập vào ứng dụng này.</p>
        </div>
    `;
    screens.loading.classList.remove('opacity-0', 'hidden');
}

// ── Resume Banner ─────────────────────────────────────────────────────────

export function showResumeBanner(time, onConfirm) {
    // Remove existing if any
    document.getElementById('resume-banner')?.remove();

    const formatTime = (s) => {
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = Math.floor(s % 60);
        return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}` : `${m}:${String(sec).padStart(2, '0')}`;
    };

    const banner = document.createElement('div');
    banner.id = 'resume-banner';
    banner.className = 'fixed bottom-24 left-4 right-4 z-[110] glass rounded-2xl p-4 flex items-center justify-between animate-in fade-in slide-in-from-bottom-5 duration-500';
    banner.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                <i class="fa-solid fa-clock-rotate-left"></i>
            </div>
            <div>
                <div class="text-xs font-bold text-white/40 uppercase tracking-wider">Xem tiếp?</div>
                <div class="text-sm font-semibold">Tiếp tục từ ${formatTime(time)}</div>
            </div>
        </div>
        <div class="flex gap-2">
            <button id="resume-cancel" class="px-3 py-2 text-xs font-bold text-white/40 hover:text-white transition-all">Bỏ qua</button>
            <button id="resume-confirm" class="bg-primary text-black px-4 py-2 rounded-xl text-xs font-bold hover:bg-primary/90 transition-all">Xem ngay</button>
        </div>
    `;

    document.body.appendChild(banner);

    const close = () => {
        banner.classList.add('animate-out', 'fade-out', 'slide-out-to-bottom-5');
        setTimeout(() => banner.remove(), 500);
    };

    banner.querySelector('#resume-confirm').onclick = () => { onConfirm(); close(); };
    banner.querySelector('#resume-cancel').onclick = close;

    // Auto hide after 8 seconds
    setTimeout(() => { if (document.getElementById('resume-banner')) close(); }, 8000);
}

// ── Skeletons ─────────────────────────────────────────────────────────────

export function renderSkeletons(container, count = 6) {
    if (!container) return;
    container.innerHTML = Array(count).fill(0).map(() => `
        <div class="skeleton-item mb-4">
            <div class="skeleton-card skeleton-shimmer"></div>
            <div class="skeleton-text skeleton-shimmer w-3/4"></div>
            <div class="skeleton-text skeleton-shimmer w-1/2"></div>
        </div>
    `).join('');
}
