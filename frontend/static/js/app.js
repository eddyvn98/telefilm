const BOT_API = "";
const tg = window.Telegram.WebApp;

// Components
const screens = {
    loading: document.getElementById('loading'),
    home: document.getElementById('home'),
    player: document.getElementById('player-screen')
};

const elements = {
    movieRow: document.getElementById('latest-movies'),
    featuredHero: document.getElementById('featured-hero'),
    videoPlayer: document.getElementById('video-player'),
    playerTitle: document.getElementById('player-title'),
    playerDesc: document.getElementById('player-desc'),
    userProfile: document.getElementById('user-profile'),
    searchInput: document.getElementById('search-input'),
    searchResults: document.getElementById('search-results'),
    searchGrid: document.getElementById('search-grid')
};

// State
let movies = [];

async function init() {
    tg.ready();
    tg.expand();

    // Sync Theme
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.backgroundColor);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.textColor);

    try {
        renderUser();
        await loadMovies();

        // Show Home Screen after logic is ready
        setTimeout(() => {
            screens.loading.classList.add('opacity-0');
            setTimeout(() => {
                screens.loading.classList.add('hidden');
                screens.home.classList.remove('hidden');
                screens.home.classList.add('block');
            }, 500);
        }, 800);

    } catch (error) {
        console.error("Init Error:", error);
        // Fallback or show error
    }
}

function renderUser() {
    const user = tg.initDataUnsafe?.user;
    if (user) {
        elements.userProfile.innerHTML = `
            <span class="text-sm font-medium text-white/80">${user.first_name}</span>
            <div class="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-xs border border-primary/30">
                ${user.first_name.charAt(0)}
            </div>
        `;
    } else {
        elements.userProfile.innerHTML = `<span class="text-sm font-medium text-white/40">Guest</span>`;
    }
}

async function loadMovies() {
    try {
        const response = await fetch('/api/catalog/movies');
        if (response.ok) {
            movies = await response.json();
        }
    } catch (e) {
        console.warn("Could not fetch movies from API, using premium placeholders.");
    }

    // Default premium content for demonstration if API is empty
    if (!movies || movies.length === 0) {
        movies = [
            {
                id: 1,
                title: "Interstellar",
                poster_url: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlSaba7.jpg",
                backdrop_url: "https://image.tmdb.org/t/p/original/rAiXKRqEn9nSop8f6DR9Yv1v9Sj.jpg",
                description: "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
                release_year: 2014,
                rating: 8.7
            },
            {
                id: 2,
                title: "The Dark Knight",
                poster_url: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDr9p1v3hvZBn0zSSTg.jpg",
                backdrop_url: "https://image.tmdb.org/t/p/original/nMKdUUtnkbvMDy9O9O3YDSAgSXC.jpg",
                description: "Batman raises the stakes in his war on crime with the help of Lt. Jim Gordon and District Attorney Harvey Dent.",
                release_year: 2008,
                rating: 9.0
            },
            {
                id: 3,
                title: "Inception",
                poster_url: "https://image.tmdb.org/t/p/w500/9gk7Fn9sVAsS9Te69sb0gEJAO3n.jpg",
                backdrop_url: "https://image.tmdb.org/t/p/original/s3TqrSfyRImEJv78ol6t3ulvSrm.jpg",
                description: "A thief who steals corporate secrets through the use of dream-sharing technology...",
                release_year: 2010,
                rating: 8.8
            }
        ];
    }

    renderHero(movies[0]);
    renderMovieList(movies, elements.movieRow);
}

function renderHero(movie) {
    if (!movie) return;
    const heroImg = movie.backdrop_url || movie.poster_url || "https://image.tmdb.org/t/p/original/rAiXKRqEn9nSop8f6DR9Yv1v9Sj.jpg";
    elements.featuredHero.innerHTML = `
        <div class="relative h-[180px] sm:h-[220px] rounded-3xl overflow-hidden glass group cursor-pointer" onclick="playMovie(${movie.id})">
            <img src="${heroImg}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" alt="${movie.title}">
            <div class="absolute inset-0 bg-gradient-to-t from-[#0f0f0f] via-black/20 to-transparent"></div>
            <div class="absolute bottom-0 p-6 w-full">
                <span class="inline-block px-2 py-0.5 rounded-full bg-primary text-[8px] font-bold uppercase tracking-widest mb-2">Featured</span>
                <h1 class="text-xl sm:text-2xl font-bold text-white mb-1 leading-tight">${movie.title}</h1>
                <p class="text-white/60 text-[10px] sm:text-xs line-clamp-1 max-w-sm">${movie.description || 'No description available.'}</p>
            </div>
        </div>
    `;
}

function renderMovieList(movieList, container) {
    container.innerHTML = movieList.map(movie => {
        const poster = movie.poster_url || "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlSaba7.jpg";
        return `
        <div class="movie-card group cursor-pointer w-full" onclick="playMovie(${movie.id})">
            <div class="relative aspect-[2/3] rounded-2xl overflow-hidden mb-2 ring-1 ring-white/10 group-hover:ring-primary/50 transition-all duration-300">
                <img src="${poster}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" alt="${movie.title}" loading="lazy">
                <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center scale-75 group-hover:scale-100 transition-transform">
                        <svg class="w-5 h-5 text-white fill-current" viewBox="0 0 20 20"><path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.841z"></path></svg>
                    </div>
                </div>
            </div>
            <h4 class="text-[11px] sm:text-xs font-semibold truncate group-hover:text-primary transition-colors">${movie.title}</h4>
            <p class="text-[9px] text-white/40 uppercase tracking-wider mt-0.5">${movie.release_year || '2024'} • ${movie.rating || 'N/A'}★</p>
        </div>
        `;
    }).join('');
}

window.playMovie = function (id) {
    const movie = movies.find(m => m.id === id);
    if (!movie) return;

    elements.playerTitle.innerText = movie.title;
    elements.playerDesc.innerText = movie.description;

    screens.player.classList.remove('hidden');
    screens.player.classList.add('flex');

    const video = elements.videoPlayer;
    // Real streaming from our backend
    video.src = `/api/stream/${movie.id}`;
    video.play();
};

window.closePlayer = function () {
    elements.videoPlayer.pause();
    screens.player.classList.add('hidden');
    screens.player.classList.remove('flex');
};

// Search Logic
elements.searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    if (query.length < 2) {
        elements.searchResults.classList.add('hidden');
        return;
    }

    const filtered = movies.filter(m =>
        m.title.toLowerCase().includes(query) ||
        (m.description && m.description.toLowerCase().includes(query))
    );

    if (filtered.length > 0) {
        elements.searchResults.classList.remove('hidden');
        elements.searchResults.style.display = 'block';
        renderMovieList(filtered, elements.searchGrid);
    }
});

// Initialize
init();
