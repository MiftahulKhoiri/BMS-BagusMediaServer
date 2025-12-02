/* BMS_video_play.js
   Robust player for Mode A (playlist under player).
   - Reads server-injected data-video-id / data-folder-id if present
   - Falls back to URL ?id=...&folder=...
   - If folder missing, fetches /video/library to lookup folder_id
   - Loads playlist and renders scrollable list
   - Clicking playlist item plays video in-place (no page reload)
   - Updates URL (pushState) so share/bookmark works
*/

let PLAYER = null;
let CURRENT_VIDEO_ID = null;
let CURRENT_FOLDER_ID = null;
let PLAYLIST = []; // array of {id, filename, filepath, size, added_at}

// helper: get numeric id or null
function toInt(v){ let n = parseInt(v); return Number.isFinite(n) ? n : null; }

// read data-video-id, data-folder-id from DOM meta (server-injected)
function readMetaIds(){
  const meta = document.getElementById('player-meta');
  if (!meta) return { vid: null, fid: null };
  const vid = meta.dataset.videoId && meta.dataset.videoId.trim() ? meta.dataset.videoId.trim() : null;
  const fid = meta.dataset.folderId && meta.dataset.folderId.trim() ? meta.dataset.folderId.trim() : null;
  return { vid: toInt(vid), fid: toInt(fid) };
}

// fallback read from URL query params: ?id=23&folder=5
function readQueryIds(){
  const qp = new URLSearchParams(location.search);
  return { vid: toInt(qp.get('id')), fid: toInt(qp.get('folder')) };
}

// fallback: if folder missing, find folder by scanning library endpoint
async function resolveFolderIdFromLibrary(videoId){
  try{
    const res = await fetch('/video/library'); // returns array of videos
    if (!res.ok) return null;
    const arr = await res.json();
    const found = arr.find(v => toInt(v.id) === videoId);
    return found ? toInt(found.folder_id || found.folderId || null) : null;
  }catch(e){
    console.warn('resolveFolderIdFromLibrary failed', e);
    return null;
  }
}

// utility: set player src and play
function setPlayerSource(videoId){
  if (!PLAYER) PLAYER = document.getElementById('playerVideo');
  PLAYER.pause();
  PLAYER.src = `/video/play/${videoId}`;
  PLAYER.load();
  // try play (some browsers require user gesture)
  PLAYER.play().catch(()=>{ /* ignore play errors */ });
  // update title
  const item = PLAYLIST.find(v => toInt(v.id) === toInt(videoId));
  document.getElementById('videoTitle').innerText = item ? item.filename : 'Memutar...';
  CURRENT_VIDEO_ID = toInt(videoId);
  highlightPlaying();
  // update URL param without reload
  const url = new URL(window.location);
  url.searchParams.set('id', videoId);
  if (CURRENT_FOLDER_ID) url.searchParams.set('folder', CURRENT_FOLDER_ID);
  history.replaceState({}, '', url.toString());
}

// render playlist items
function renderPlaylist(){
  const box = document.getElementById('playlist');
  box.innerHTML = '';
  if (!Array.isArray(PLAYLIST) || PLAYLIST.length === 0){
    box.innerHTML = '<div style="color:#d6ffd8">Tidak ada video dalam folder ini.</div>';
    return;
  }
  PLAYLIST.forEach(v=>{
    const el = document.createElement('div');
    el.className = 'playlist-item';
    el.setAttribute('role','listitem');
    el.dataset.videoId = v.id;
    el.innerHTML = (toInt(v.id) === toInt(CURRENT_VIDEO_ID)) ? `▶ ${v.filename}` : v.filename;
    el.onclick = (ev) => {
      const vid = toInt(ev.currentTarget.dataset.videoId);
      if (vid && vid !== CURRENT_VIDEO_ID) setPlayerSource(vid);
    };
    box.appendChild(el);
  });
  highlightPlaying();
  // ensure the playing item is visible
  scrollPlayingIntoView();
}

// highlight the playing item visually
function highlightPlaying(){
  const items = document.querySelectorAll('.playlist-item');
  items.forEach(i => {
    const vid = toInt(i.dataset.videoId);
    if (vid === CURRENT_VIDEO_ID) {
      i.classList.add('playing');
    } else i.classList.remove('playing');
  });
}

// if playing item out of view, scroll it into view (nice UX)
function scrollPlayingIntoView(){
  const active = document.querySelector('.playlist-item.playing');
  if (active && active.scrollIntoView) {
    // smooth scroll but keep at center-ish
    active.scrollIntoView({behavior:'smooth', block:'center'});
  }
}

// main initializer: read ids, load playlist, set player source
async function initializePlayerFromPage(){
  PLAYER = document.getElementById('playerVideo');

  // 1) try reading server-injected meta
  const meta = readMetaIds();
  let vid = meta.vid;
  let fid = meta.fid;

  // 2) fallback to query params
  if (!vid || !fid){
    const q = readQueryIds();
    // prefer vid from meta if present
    vid = vid || q.vid;
    fid = fid || q.fid;
  }

  // 3) if still missing folder id, try resolve from library endpoint
  if (vid && !fid){
    fid = await resolveFolderIdFromLibrary(vid);
  }

  // Save to current
  CURRENT_VIDEO_ID = toInt(vid);
  CURRENT_FOLDER_ID = toInt(fid);

  if (!CURRENT_VIDEO_ID){
    alert('Tidak ada ID video (gagal menentukan video).');
    return;
  }

  // load playlist for folder (if folder found)
  if (CURRENT_FOLDER_ID){
    try {
      const res = await fetch(`/video/folder/${CURRENT_FOLDER_ID}/videos`);
      if (res.ok) {
        PLAYLIST = await res.json();
      } else {
        PLAYLIST = [];
      }
    } catch(e){
      console.warn('Gagal ambil playlist', e);
      PLAYLIST = [];
    }
  } else {
    // fallback: try /video/library and filter by file path's folder (best effort)
    try {
      const res = await fetch('/video/library');
      const all = await res.json();
      const matched = all.find(v => toInt(v.id) === CURRENT_VIDEO_ID);
      if (matched){
        // try to derive folder by filepath directory
        const fp = matched.filepath || '';
        const dir = fp.replace(/\/[^\/]*$/, '');
        // find folder by folder listing
        const fres = await fetch('/video/folders');
        const folders = await fres.json();
        const found = folders.find(f => f.folder_path === dir || dir.endsWith(f.folder_name));
        if (found) CURRENT_FOLDER_ID = found.id;
      }
    } catch(e){
      // ignore
    }
  }

  // set player to current video id
  setPlayerSource(CURRENT_VIDEO_ID);

  // render playlist (could be empty)
  renderPlaylist();

  // optional: when video ends, auto play next
  PLAYER.addEventListener('ended', () => {
    // find current index
    const idx = PLAYLIST.findIndex(v=> toInt(v.id) === toInt(CURRENT_VIDEO_ID));
    if (idx >= 0 && idx < PLAYLIST.length - 1){
      const next = PLAYLIST[idx+1].id;
      setPlayerSource(next);
    }
  });

  // handle keyboard shortcuts: left/right for prev/next (optional)
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') {
      // next
      const idx = PLAYLIST.findIndex(v=> toInt(v.id) === toInt(CURRENT_VIDEO_ID));
      if (idx >= 0 && idx < PLAYLIST.length - 1) setPlayerSource(PLAYLIST[idx+1].id);
    } else if (e.key === 'ArrowLeft') {
      const idx = PLAYLIST.findIndex(v=> toInt(v.id) === toInt(CURRENT_VIDEO_ID));
      if (idx > 0) setPlayerSource(PLAYLIST[idx-1].id);
    }
  });
}