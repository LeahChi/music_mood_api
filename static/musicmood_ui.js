// ============================================================
// MusicMood UI — JavaScript
// Connects to the MusicMood FastAPI backend at localhost:8000
// ============================================================

// Base URL for all API calls
// Automatically uses the deployed Railway URL in production,
// falls back to localhost for local development
const API = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
  ? 'http://127.0.0.1:8000'
  : 'https://musicmoodapi-production.up.railway.app/';

// Global state — stored in memory for the session
let token = null;         // JWT token from login
let currentUser = null;   // { username, id } of logged in user
let selectedTrackId = null; // track ID chosen in the log session search

// ============================================================
// EMOTION HELPERS
// Based on Russell's circumplex model of affect:
// valence (positivity) + energy → emotion quadrant
// ============================================================

// Returns CSS variable strings for a given emotion label
function es(e) {
  return ({
    Calm:        { bg:'var(--calm-bg)',    text:'var(--calm-text)',    bar:'var(--calm-bar)' },
    Excited:     { bg:'var(--excited-bg)', text:'var(--excited-text)', bar:'var(--excited-bar)' },
    Melancholic: { bg:'var(--mel-bg)',     text:'var(--mel-text)',     bar:'var(--mel-bar)' },
    Tense:       { bg:'var(--tense-bg)',   text:'var(--tense-text)',   bar:'var(--tense-bar)' }
  }[e]) || { bg:'var(--mel-bg)', text:'var(--mel-text)', bar:'var(--mel-bar)' };
}

// Maps valence + energy values onto the four emotion quadrants
function getEmotion(valence, energy) {
  if (valence >= 0.5 && energy >= 0.5) return 'Excited';     // high positivity + high energy
  if (valence < 0.5  && energy >= 0.5) return 'Tense';       // low positivity + high energy
  if (valence >= 0.5 && energy < 0.5)  return 'Calm';        // high positivity + low energy
  return 'Melancholic';                                        // low positivity + low energy
}

// Capitalises the first letter of a string
function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

// ============================================================
// PAGE & MODAL NAVIGATION
// ============================================================

// Shows a page by adding .active class, hides all others
function showPage(p) {
  document.querySelectorAll('.page').forEach(x => x.classList.remove('active'));
  document.getElementById(p + 'Page').classList.add('active');
}

// Opens a modal (login or register)
function openModal(t) { document.getElementById(t + 'Modal').classList.add('open'); }

// Closes a modal
function closeModal(t) { document.getElementById(t + 'Modal').classList.remove('open'); }

// Toggles the log session panel open/closed
function toggleLogPanel() {
  const p = document.getElementById('logPanel');
  p.style.display = p.style.display === 'none' ? 'block' : 'none';
}

// ============================================================
// AUTHENTICATION
// ============================================================

// Handles login form submission
// Uses OAuth2PasswordRequestForm (form data, not JSON) — required by FastAPI's OAuth2 flow
async function doLogin() {
  const u = document.getElementById('loginUsername').value;
  const p = document.getElementById('loginPassword').value;
  const err = document.getElementById('loginError');
  err.style.display = 'none';

  // OAuth2 login requires form data, not JSON
  const form = new FormData();
  form.append('username', u);
  form.append('password', p);

  try {
    const res = await fetch(`${API}/auth/login`, { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) { err.style.display = 'block'; return; }

    // store the JWT token — used in all subsequent authenticated requests
    token = data.access_token;
    currentUser = { username: u };
    closeModal('login');
    afterLogin(u);
  } catch(e) { err.style.display = 'block'; }
}

// Handles register form submission
async function doRegister() {
  const u = document.getElementById('regUsername').value;
  const e = document.getElementById('regEmail').value;
  const p = document.getElementById('regPassword').value;
  const err = document.getElementById('registerError');
  err.style.display = 'none';

  try {
    // register endpoint expects JSON
    const res = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, email: e, password: p })
    });
    const data = await res.json();
    if (!res.ok) { err.textContent = data.detail || 'Registration failed'; err.style.display = 'block'; return; }

    // auto-login after successful registration
    closeModal('register');
    document.getElementById('loginUsername').value = u;
    document.getElementById('loginPassword').value = p;
    await doLogin();
  } catch(e) { err.textContent = 'Something went wrong'; err.style.display = 'block'; }
}

// Called after successful login — updates nav, switches to dashboard, loads data
async function afterLogin(username) {
  // update nav to show avatar + username + sign out button
  document.getElementById('navRight').innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;">
      <div class="avatar">${username[0].toUpperCase()}</div>
      <span style="font-size:13px;color:var(--muted)">${username}</span>
      <button class="btn" onclick="doLogout()">Sign out</button>
    </div>`;

  showPage('dash');
  document.getElementById('dashName').textContent = username;

  // call /auth/me to get the user's numeric ID — needed for analytics endpoints
  try {
    const r = await fetch(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
    if (r.ok) {
      const me = await r.json();
      currentUser.id = me.id;
      loadDashboard(me.id);
    } else {
      // fallback to user ID 1 if /auth/me fails
      currentUser.id = 1;
      loadDashboard(1);
    }
  } catch(e) { currentUser.id = 1; loadDashboard(1); }
}

// Clears auth state and returns to homepage
function doLogout() {
  token = null;
  currentUser = null;
  document.getElementById('navRight').innerHTML = `
    <button class="btn" onclick="openModal('login')">Sign in</button>
    <button class="btn btn-primary" onclick="openModal('register')">Get started</button>`;
  showPage('home');
}

// ============================================================
// DASHBOARD — loads all four data sections in parallel
// ============================================================

async function loadDashboard(uid) {
  // Promise.all loads all four sections simultaneously — faster than loading sequentially
  await Promise.all([
    loadMoodTrend(uid),
    loadContextBreakdown(uid),
    loadTopTracks(uid),
    loadAI(uid)
  ]);
}

// ============================================================
// MOOD TREND
// Fetches mood trend data and renders the metric cards + SVG chart
// ============================================================

async function loadMoodTrend(uid) {
  try {
    const res = await fetch(`${API}/analytics/mood-trend/${uid}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) return;

    const trend = data.mood_trend;
    const overall = data.overall_mood_score;

    // use the most recent day's emotion for the dominant emotion card
    const emotion = trend.length ? trend[trend.length - 1].dominant_emotion : 'Calm';
    const col = es(emotion);
    const total = trend.reduce((a, b) => a + b.sessions_count, 0);

    // render the four metric cards
    document.getElementById('metricsGrid').innerHTML = `
      <div class="metric-card fade-in" style="background:var(--brand-light)">
        <p class="metric-label" style="color:var(--brand)">Mood score</p>
        <p class="metric-value" style="color:var(--brand)">${overall.toFixed(2)}</p>
        <p class="metric-sub" style="color:var(--brand)">Overall positivity</p>
      </div>
      <div class="metric-card fade-in" style="background:${col.bg};animation-delay:0.08s">
        <p class="metric-label" style="color:${col.text}">Dominant emotion</p>
        <p class="metric-value" style="color:${col.text}">${emotion}</p>
        <p class="metric-sub" style="color:${col.text}">Valence + energy</p>
      </div>
      <div class="metric-card fade-in" style="background:var(--excited-bg);animation-delay:0.16s">
        <p class="metric-label" style="color:var(--excited-text)">Total sessions</p>
        <p class="metric-value" style="color:var(--excited-text)">${total}</p>
        <p class="metric-sub" style="color:var(--excited-text)">Logged sessions</p>
      </div>
      <div class="metric-card fade-in" style="background:var(--mel-bg);animation-delay:0.24s">
        <p class="metric-label" style="color:var(--mel-text)">Days tracked</p>
        <p class="metric-value" style="color:var(--mel-text)">${trend.length}</p>
        <p class="metric-sub" style="color:var(--mel-text)">Days with sessions</p>
      </div>`;

    if (!trend.length) return;

    // draw the SVG mood chart — maps mood scores to y coordinates
    const vals = trend.map(t => t.mood_score);
    const mn = Math.min(...vals) - 0.05;
    const mx = Math.max(...vals) + 0.05;
    const w = 500, h = 100, pad = 10;

    // x position: spread points evenly across the width
    const px = i => pad + (i / Math.max(vals.length - 1, 1)) * (w - pad * 2);
    // y position: flip so higher mood = higher on chart
    const py = v => h - pad - ((v - mn) / (mx - mn || 1)) * (h - pad * 2);

    const pts = vals.map((v, i) => `${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(' ');
    // area polygon fills the area under the line
    const area = pts + ` ${px(vals.length - 1).toFixed(1)},${h} ${px(0).toFixed(1)},${h}`;

    document.getElementById('moodChart').innerHTML = `
      <defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#0F6E56"/>
        <stop offset="100%" stop-color="#1D9E75"/>
      </linearGradient></defs>
      <polygon points="${area}" fill="#E1F5EE" opacity="0.6"/>
      <polyline points="${pts}" fill="none" stroke="url(#lg)" stroke-width="2.5" stroke-linejoin="round"/>
      <text x="${pad}" y="${h + 14}" font-size="10" fill="#5A7870">${trend[0].date}</text>
      <text x="${w - pad - 42}" y="${h + 14}" font-size="10" fill="#5A7870">${trend[trend.length - 1].date}</text>`;
  } catch(e) { console.error('mood trend error', e); }
}

// ============================================================
// CONTEXT BREAKDOWN
// Fetches how the user listens across different contexts and renders bar chart
// ============================================================

async function loadContextBreakdown(uid) {
  try {
    const res = await fetch(`${API}/analytics/context-breakdown/${uid}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) return;

    // each context gets a distinct colour from this array
    const bars = ['#0F6E56', '#378ADD', '#EF9F27', '#7F77DD', '#D85A30', '#1D9E75', '#888780'];

    document.getElementById('contextBars').innerHTML = data.context_breakdown.map((c, i) => `
      <div class="context-row">
        <div class="context-meta">
          <span class="context-name">${cap(c.context)}</span>
          <span class="context-pct" style="color:${bars[i % bars.length]}">${c.percentage}%</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${c.percentage}%;background:${bars[i % bars.length]}"></div>
        </div>
      </div>`).join('');
  } catch(e) { console.error('context error', e); }
}

// ============================================================
// TOP TRACKS
// Fetches the user's most-played tracks and renders them as a list
// ============================================================

async function loadTopTracks(uid) {
  try {
    const res = await fetch(`${API}/analytics/top-tracks/${uid}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) return;

    document.getElementById('topTracks').innerHTML = data.top_tracks.slice(0, 5).map((t, i) => {
      const col = es(t.dominant_emotion);
      return `
        <div class="track-row fade-in" style="animation-delay:${i * 0.07}s">
          <div class="track-left">
            <div class="track-num">${i + 1}</div>
            <div>
              <div class="track-title">${t.title}</div>
              <div class="track-artist">${t.artist} · ${t.play_count} play${t.play_count !== 1 ? 's' : ''}</div>
            </div>
          </div>
          <span class="emotion-tag" style="background:${col.bg};color:${col.text}">${t.dominant_emotion}</span>
        </div>`;
    }).join('');
  } catch(e) { console.error('top tracks error', e); }
}

// ============================================================
// AI INTERPRETATION
// Calls the AI endpoint which queries our analytics then sends them to Llama 3
// The AI speaks directly to the user using "you" — personalised by username
// ============================================================

async function loadAI(uid) {
  try {
    const res = await fetch(`${API}/ai/interpret/${uid}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) return;

    // hide loading text, show the AI interpretation
    document.getElementById('aiLoading').style.display = 'none';
    const el = document.getElementById('aiText');
    el.style.display = 'block';
    el.textContent = data.ai_interpretation;
  } catch(e) {
    document.getElementById('aiLoading').textContent = 'AI interpretation unavailable right now.';
  }
}

// ============================================================
// TRACK SEARCH
// Uses the /tracks/search endpoint which does a database-wide
// case-insensitive search — much better than filtering 100 tracks client-side
// ============================================================

async function searchTracks(query) {
  const dd = document.getElementById('searchDropdown');

  // don't search until at least 1 character is typed
  if (query.length < 1) { dd.classList.remove('open'); return; }

  try {
    // /tracks/search?q= searches title AND artist across the full 5000 track database
    const res = await fetch(`${API}/tracks/search?q=${encodeURIComponent(query)}&limit=8`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    const tracks = await res.json();

    if (!tracks.length) { dd.classList.remove('open'); return; }

    // render each result with its emotion tag
    dd.innerHTML = tracks.map(t => {
      const em = getEmotion(t.valence || 0.5, t.energy || 0.5);
      const col = es(em);
      return `
        <div class="search-item" onclick="selectTrack(${t.id}, \`${t.title.replace(/`/g, '\\`')}\`)">
          <div class="search-item-info">
            <span class="search-item-title">${t.title}</span>
            <span class="search-item-artist">${t.artist}</span>
          </div>
          <span class="emotion-tag" style="background:${col.bg};color:${col.text}">${em}</span>
        </div>`;
    }).join('');
    dd.classList.add('open');
  } catch(e) { console.error('search error', e); }
}

// Called when user clicks a track in the dropdown
function selectTrack(id, title) {
  selectedTrackId = id;  // store the ID for when they click Log session
  document.getElementById('trackSearch').value = title;
  document.getElementById('searchDropdown').classList.remove('open');
}

// ============================================================
// LOG SESSION
// Posts a new listening session to the API for the current user
// ============================================================

async function logSession() {
  if (!selectedTrackId) { alert('Please select a track first'); return; }
  const context = document.getElementById('contextSelect').value;

  try {
    const res = await fetch(`${API}/sessions/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ track_id: selectedTrackId, context })
    });

    if (res.ok) {
      // show success message, reset form, reload dashboard after 2 seconds
      const s = document.getElementById('logSuccess');
      s.style.display = 'block';
      document.getElementById('trackSearch').value = '';
      selectedTrackId = null;
      setTimeout(() => {
        s.style.display = 'none';
        if (currentUser?.id) loadDashboard(currentUser.id); // refresh dashboard data
      }, 2000);
    }
  } catch(e) { alert('Failed to log session'); }
}

// ============================================================
// HOMEPAGE — loads genre emotion map and stats without auth
// ============================================================

async function loadHomepage() {
  try {
    // genre-emotion-map is a public endpoint — no auth required
    const res = await fetch(`${API}/analytics/genre-emotion-map`);
    const data = await res.json();
    if (!res.ok) throw new Error();

    const genres = data.genre_emotion_map.slice(0, 6);

    // update stats bar
    document.getElementById('statGenres').textContent = data.total_genres;
    document.getElementById('statTopGenre').textContent = genres[0]?.genre ? cap(genres[0].genre) : '—';

    // render genre cards with emotion colours
    document.getElementById('genreGrid').innerHTML = genres.map((g, i) => {
      const col = es(g.dominant_emotion);
      return `
        <div class="genre-card fade-in" style="background:${col.bg};border-color:${col.bar}30;animation-delay:${i * 0.07}s">
          <div class="genre-name" style="color:${col.text}">${cap(g.genre)}</div>
          <div class="genre-emotion" style="color:${col.text}">${g.dominant_emotion} · ${g.avg_valence.toFixed(2)} valence</div>
        </div>`;
    }).join('');
  } catch(e) {
    // show helpful message if API isn't running
    document.getElementById('genreGrid').innerHTML = `
      <p style="color:var(--muted);font-size:13px;grid-column:1/-1;padding:1rem 0">
        Make sure the API is running at ${API}
      </p>`;
  }
}

// ============================================================
// GLOBAL EVENT LISTENERS
// ============================================================

// Close search dropdown when clicking anywhere outside the search box
document.addEventListener('click', e => {
  if (!e.target.closest('.search-wrap')) {
    document.getElementById('searchDropdown').classList.remove('open');
  }
});

// Allow pressing Enter to submit login/register forms
document.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    if (document.getElementById('loginModal').classList.contains('open')) doLogin();
    if (document.getElementById('registerModal').classList.contains('open')) doRegister();
  }
});

// ============================================================
// INIT — load homepage data when the page first loads
// ============================================================
loadHomepage();
