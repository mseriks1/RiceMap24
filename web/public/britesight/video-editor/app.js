const state = {
  projectName: '',
  format: '9:16',
  musicTrack: 'None',
  musicVolume: 55,
  globalFilter: 'None',
  clips: [],
  selectedClipId: null,
  clipboard: null,
  playing: false,
  playMode: 'idle',
  playToken: 0,
  currentClipIndex: -1,
  currentTimelineTime: 0,
  dragClipId: null,
  timeoutId: null,
  importedAudio: [],
  musicClip: null,
  musicClips: [],
  selectedMusicId: null,
  musicDrag: null,
  suppressTimelineAutoScrollUntil: 0,
  previewFastMode: false,
  previewRenderQueued: false,
  deferredRenderTimer: null,
  trimDrag: null,
  trimPreviewThrottleUntil: 0,
  sliderPreviewThrottleUntil: 0,
  previewVideoAltReadyForClipId: null,
  playbackUiRaf: 0,
  currentPlaybackClipId: null,
  transitionRaf: 0,
  lastPlayStatePaintAt: 0,
  lastMusicSyncAt: 0,
  lastMusicVolumeAt: -1,
  lastTransitionCss: '',
  lastTransitionOpacity: -1,
  lastTransitionTransform: '',
  timelineZoom: 120,
  timelineZooming: false,
  timelineRenderRaf: 0,
  musicLibraryUrl: localStorage.getItem('britesightMusicLibraryUrl') || '',
  musicLibraryTracks: [],
  musicLibraryPreviewAudio: null,
  musicLibraryPreviewId: null,
};

const filterPresets = {
  'None': { b: 0, c: 1, s: 1, sepia: 0, hue: 0, grayscale: 0 },
  'Soft Fade': { b: 3, c: 0.92, s: 0.88, sepia: 0.04, hue: 0, grayscale: 0 },
  'Crisp Pop': { b: 2, c: 1.14, s: 1.18, sepia: 0, hue: 0, grayscale: 0 },
  'Warm Social': { b: 5, c: 1.05, s: 1.12, sepia: 0.12, hue: -5, grayscale: 0 },
  'Cool Fresh': { b: 1, c: 1.06, s: 1.08, sepia: 0, hue: 12, grayscale: 0 },
  'Golden Hour': { b: 6, c: 1.08, s: 1.16, sepia: 0.18, hue: -10, grayscale: 0 },
  'Food Pop': { b: 4, c: 1.18, s: 1.24, sepia: 0.04, hue: -3, grayscale: 0 },
  'Moody Contrast': { b: -5, c: 1.24, s: 0.96, sepia: 0.05, hue: 0, grayscale: 0 },
  'Soft Pastel': { b: 7, c: 0.88, s: 1.22, sepia: 0.02, hue: 4, grayscale: 0 },
  'Vintage Warm': { b: 2, c: 0.96, s: 0.86, sepia: 0.26, hue: -8, grayscale: 0 },
  'Clean Mono': { b: 2, c: 1.12, s: 1, sepia: 0, hue: 0, grayscale: 1 },
};

const el = {
  projectName: document.getElementById('projectName'),
  mediaInput: document.getElementById('mediaInput'),
  importProgressBox: document.getElementById('importProgressBox'),
  importProgressPercent: document.getElementById('importProgressPercent'),
  importProgressFill: document.getElementById('importProgressFill'),
  importProgressFile: document.getElementById('importProgressFile'),
  importProgressStatus: document.getElementById('importProgressStatus'),
  exportProjectBtn: document.getElementById('exportProjectBtn'),
  openExportPanelBtn: document.getElementById('openExportPanelBtn'),
  exportPanel: document.getElementById('exportPanel'),
  exportPresetBadge: document.getElementById('exportPresetBadge'),
  exportFormat: document.getElementById('exportFormat'),
  exportQuality: document.getElementById('exportQuality'),
  exportFps: document.getElementById('exportFps'),
  exportSize: document.getElementById('exportSize'),
  exportBitrate: document.getElementById('exportBitrate'),
  exportBitrateLabel: document.getElementById('exportBitrateLabel'),
  renderVideoBtn: document.getElementById('renderVideoBtn'),
  shareVideoBtn: document.getElementById('shareVideoBtn'),
  exportPosterFrameBtn: document.getElementById('exportPosterFrameBtn'),
  exportStatus: document.getElementById('exportStatus'),
  addImageBtn: document.getElementById('addImageBtn'),
  addVideoBtn: document.getElementById('addVideoBtn'),
  addBackgroundBtn: document.getElementById('addBackgroundBtn'),
  addTextBtn: document.getElementById('addTextBtn'),
  addOverlayTextBtn: document.getElementById('addOverlayTextBtn'),
  musicInput: document.getElementById('musicInput'),
  musicTrack: document.getElementById('musicTrack'),
  musicInfo: document.getElementById('musicInfo'),
  musicVolume: document.getElementById('musicVolume'),
  musicVolumeLabel: document.getElementById('musicVolumeLabel'),
  musicFadeIn: document.getElementById('musicFadeIn'),
  musicFadeInLabel: document.getElementById('musicFadeInLabel'),
  musicFadeOut: document.getElementById('musicFadeOut'),
  musicFadeOutLabel: document.getElementById('musicFadeOutLabel'),
  musicStartTime: document.getElementById('musicStartTime'),
  musicTrimStart: document.getElementById('musicTrimStart'),
  musicTrimEnd: document.getElementById('musicTrimEnd'),
  removeMusicBtn: document.getElementById('removeMusicBtn'),
  musicLibraryUrl: document.getElementById('musicLibraryUrl'),
  saveMusicLibraryUrlBtn: document.getElementById('saveMusicLibraryUrlBtn'),
  testMusicLibraryBtn: document.getElementById('testMusicLibraryBtn'),
  clearMusicLibraryBtn: document.getElementById('clearMusicLibraryBtn'),
  musicLibraryStatus: document.getElementById('musicLibraryStatus'),
  musicLibraryBrowser: document.getElementById('musicLibraryBrowser'),
  musicLibrarySearch: document.getElementById('musicLibrarySearch'),
  musicLibraryType: document.getElementById('musicLibraryType'),
  musicLibraryCategory: document.getElementById('musicLibraryCategory'),
  musicLibraryList: document.getElementById('musicLibraryList'),
  globalFilter: document.getElementById('globalFilter'),
  formatBadge: document.getElementById('formatBadge'),
  filterBadge: document.getElementById('filterBadge'),
  playModeBadge: document.getElementById('playModeBadge'),
  libraryList: document.getElementById('libraryList'),
  dropZone: document.getElementById('dropZone'),
  previewFrame: document.getElementById('previewFrame'),
  previewMediaLayer: document.getElementById('previewMediaLayer'),
  previewVideo: document.getElementById('previewVideo'),
  previewImage: document.getElementById('previewImage'),
  previewSynthetic: document.getElementById('previewSynthetic'),
  previewFallback: document.getElementById('previewFallback'),
  previewTextOverlay: document.getElementById('previewTextOverlay'),
  previewTypeLabel: document.getElementById('previewTypeLabel'),
  previewName: document.getElementById('previewName'),
  previewZoom: document.getElementById('previewZoom'),
  previewVolume: document.getElementById('previewVolume'),
  playPauseBtn: document.getElementById('playPauseBtn'),
  playTimelineBtn: document.getElementById('playTimelineBtn'),
  playSelectedBtn: document.getElementById('playSelectedBtn'),
  playPauseBtn2: document.getElementById('playPauseBtn2'),
  prevClipBtn: document.getElementById('prevClipBtn'),
  nextClipBtn: document.getElementById('nextClipBtn'),
  previewStatus: document.getElementById('previewStatus'),
  timecode: document.getElementById('timecode'),
  timelineMeta: document.getElementById('timelineMeta'),
  timelineDropHint: document.getElementById('timelineDropHint'),
  timeRuler: document.getElementById('timeRuler'),
  visualTrack: document.getElementById('visualTrack'),
  musicTrackBar: document.getElementById('musicTrackBar'),
  timelineZoom: document.getElementById('timelineZoom'),
  timelineZoomLabel: document.getElementById('timelineZoomLabel'),
  timelineStage: document.getElementById('timelineStage'),
  timelineScroll: document.getElementById('timelineScroll'),
  timelinePlayhead: document.getElementById('timelinePlayhead'),
  timelineSeek: document.getElementById('timelineSeek'),
  timelineSeekLabel: document.getElementById('timelineSeekLabel'),
  inspectorEmpty: document.getElementById('inspectorEmpty'),
  inspectorContent: document.getElementById('inspectorContent'),
  clipNameLabel: document.getElementById('clipNameLabel'),
  clipDurationLabel: document.getElementById('clipDurationLabel'),
  clipSupportLabel: document.getElementById('clipSupportLabel'),
  cropZoom: document.getElementById('cropZoom'),
  cropZoomValue: document.getElementById('cropZoomValue'),
  cropX: document.getElementById('cropX'),
  cropXValue: document.getElementById('cropXValue'),
  cropY: document.getElementById('cropY'),
  cropYValue: document.getElementById('cropYValue'),
  kenBurnsInspector: document.getElementById('kenBurnsInspector'),
  kenBurnsMotion: document.getElementById('kenBurnsMotion'),
  kenBurnsStrength: document.getElementById('kenBurnsStrength'),
  speedInspector: document.getElementById('speedInspector'),
  clipSpeed: document.getElementById('clipSpeed'),
  speedRamp: document.getElementById('speedRamp'),
  speedRampStrength: document.getElementById('speedRampStrength'),
  speedRampTiming: document.getElementById('speedRampTiming'),
  speedRampCustomControls: document.getElementById('speedRampCustomControls'),
  speedRampStart: document.getElementById('speedRampStart'),
  speedRampEnd: document.getElementById('speedRampEnd'),
  brightness: document.getElementById('brightness'),
  brightnessValue: document.getElementById('brightnessValue'),
  contrast: document.getElementById('contrast'),
  contrastValue: document.getElementById('contrastValue'),
  saturation: document.getElementById('saturation'),
  saturationValue: document.getElementById('saturationValue'),
  volume: document.getElementById('volume'),
  volumeValue: document.getElementById('volumeValue'),
  textBackgroundInspector: document.getElementById('textBackgroundInspector'),
  textInspectorLabel: document.getElementById('textInspectorLabel'),
  clipBgColorWrap: document.getElementById('clipBgColorWrap'),
  textOverlayHint: document.getElementById('textOverlayHint'),
  clipText: document.getElementById('clipText'),
  clipFont: document.getElementById('clipFont'),
  clipTextMotion: document.getElementById('clipTextMotion'),
  clipTextColor: document.getElementById('clipTextColor'),
  clipBgColor: document.getElementById('clipBgColor'),
  clipFontSize: document.getElementById('clipFontSize'),
  trimStart: document.getElementById('trimStart'),
  trimStartValue: document.getElementById('trimStartValue'),
  trimEnd: document.getElementById('trimEnd'),
  trimEndValue: document.getElementById('trimEndValue'),
  transitionInType: document.getElementById('transitionInType'),
  transitionOutType: document.getElementById('transitionOutType'),
  transitionInDuration: document.getElementById('transitionInDuration'),
  transitionOutDuration: document.getElementById('transitionOutDuration'),
  transitionInDurationValue: document.getElementById('transitionInDurationValue'),
  transitionOutDurationValue: document.getElementById('transitionOutDurationValue'),
  transitionOverlay: document.getElementById('transitionOverlay'),
  splitBtn: document.getElementById('splitBtn'),
  copyBtn: document.getElementById('copyBtn'),
  pasteBtn: document.getElementById('pasteBtn'),
  moveLeftBtn: document.getElementById('moveLeftBtn'),
  moveRightBtn: document.getElementById('moveRightBtn'),
  deleteBtn: document.getElementById('deleteBtn'),
};

const musicAudio = new Audio();
musicAudio.loop = true;
musicAudio.preload = 'auto';
const musicAudioPlayers = new Map();

function pxPerSec() {
  const raw = Number(state.timelineZoom);
  return clamp(Number.isFinite(raw) ? raw : 120, 6, 600);
}

function zoomPercent() {
  return Math.round((pxPerSec() / 120) * 100);
}

function requestTimelineRender() {
  if (state.timelineRenderRaf) return;
  state.timelineRenderRaf = requestAnimationFrame(() => {
    state.timelineRenderRaf = 0;
    renderTimeline();
  });
}

function setTimelineZooming(active) {
  state.timelineZooming = !!active;
  document.body.classList.toggle('timeline-zooming', !!active);
}

const previewVideoAlt = document.createElement('video');
previewVideoAlt.className = 'media-el hidden';
previewVideoAlt.playsInline = true;
previewVideoAlt.preload = 'auto';
el.previewMediaLayer.appendChild(previewVideoAlt);
el.previewVideoAlt = previewVideoAlt;
el.previewVideoMain = el.previewVideo;
state.activePreviewVideo = el.previewVideoMain;

const transitionImage = document.createElement('img');
transitionImage.className = 'media-el transition-peer hidden';
transitionImage.alt = 'Transition preview';
el.previewMediaLayer.appendChild(transitionImage);
el.transitionImage = transitionImage;

let previewAudioContext = null;
const previewAudioBundles = new WeakMap();

function ensurePreviewAudioContext() {
  if (previewAudioContext) return previewAudioContext;
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return null;
  try {
    previewAudioContext = new Ctx();
  } catch {
    previewAudioContext = null;
  }
  return previewAudioContext;
}

function getPreviewAudioBundle(videoEl) {
  if (!videoEl) return null;
  if (previewAudioBundles.has(videoEl)) return previewAudioBundles.get(videoEl);
  const ctx = ensurePreviewAudioContext();
  if (!ctx) return null;
  try {
    const source = ctx.createMediaElementSource(videoEl);
    const gain = ctx.createGain();
    gain.gain.value = 1;
    source.connect(gain);
    gain.connect(ctx.destination);
    const bundle = { source, gain };
    previewAudioBundles.set(videoEl, bundle);
    return bundle;
  } catch {
    const bundle = null;
    previewAudioBundles.set(videoEl, bundle);
    return null;
  }
}

function resumePreviewAudioContext() {
  const ctx = ensurePreviewAudioContext();
  if (!ctx) return;
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {});
  }
}

function setPreviewVideoGain(videoEl, scalar) {
  if (!videoEl) return;
  const gainScalar = Math.max(0, Math.min(2, Number(scalar || 0)));
  videoEl.volume = 1;
  const bundle = getPreviewAudioBundle(videoEl);
  if (bundle?.gain) bundle.gain.gain.value = gainScalar;
  else videoEl.volume = Math.max(0, Math.min(1, gainScalar));
}

function allPreviewVideos() {
  return [el.previewVideoMain, el.previewVideoAlt].filter(Boolean);
}

function getActivePreviewVideo() {
  return state.activePreviewVideo || el.previewVideoMain || el.previewVideoAlt;
}

function getInactivePreviewVideo() {
  const active = getActivePreviewVideo();
  return active === el.previewVideoMain ? el.previewVideoAlt : el.previewVideoMain;
}

function showPreviewVideo(videoEl) {
  allPreviewVideos().forEach(v => v.classList.add('hidden'));
  const nextVideo = videoEl || getActivePreviewVideo() || el.previewVideoMain;
  if (nextVideo) nextVideo.classList.remove('hidden');
  state.activePreviewVideo = nextVideo;
}

function refreshPlaybackUi() {
  const activeId = state.selectedClipId;
  const playingIndex = state.currentClipIndex;
  if (el.visualTrack) {
    [...el.visualTrack.querySelectorAll('.clip-card')].forEach((card, index) => {
      const isSelected = card.dataset.clipId === activeId;
      const isPlaying = state.playing && index === playingIndex;
      card.classList.toggle('selected', isSelected);
      card.classList.toggle('playing', isPlaying);
    });
  }
  const clip = getSelectedClip();
  if (clip) {
    el.clipNameLabel.textContent = clip.name;
    el.clipDurationLabel.textContent = `${usableDuration(clip).toFixed(1)}s on timeline`;
    el.clipSupportLabel.textContent = clip.previewSupported === false ? (clip.supportNote || 'This clip is imported, but this browser cannot preview this codec/container.') : (clip.supportNote || 'Preview should work in supported browsers.');
  }
  renderPlayState();
}

function clipVolumeScalar(clip) {
  return Math.max(0, Math.min(2, Number(clip?.volume ?? 100) / 100));
}

function ensureClipTransitionDefaults(clip) {
  if (!clip) return;
  const allowed = new Set(['none', 'fade', 'blur', 'crossfade', 'slide', 'push', 'zoom', 'dip-black', 'dip-white', 'flash']);
  clip.transitionInType = allowed.has(clip.transitionInType) ? clip.transitionInType : 'none';
  clip.transitionOutType = allowed.has(clip.transitionOutType) ? clip.transitionOutType : 'none';
  const maxLen = Math.max(0.1, usableDuration(clip));
  clip.transitionInDuration = clamp(Number(clip.transitionInDuration || 0), 0, Math.min(3, maxLen));
  clip.transitionOutDuration = clamp(Number(clip.transitionOutDuration || 0), 0, Math.min(3, maxLen));
}

function baseMediaFilter(clip, extraBlurPx = 0) {
  const preset = filterPresets[state.globalFilter] || filterPresets['None'];
  const brightness = 1 + (Number(clip.brightness) / 100) + (preset.b / 100);
  const contrast = 1 + (Number(clip.contrast) / 100) + (preset.c - 1);
  const saturation = 1 + (Number(clip.saturation) / 100) + (preset.s - 1);
  const sepia = clamp(Number(preset.sepia || 0), 0, 1);
  const hue = Number(preset.hue || 0);
  const grayscale = clamp(Number(preset.grayscale || 0), 0, 1);
  const blur = Math.max(0, Number(extraBlurPx || 0));
  const neutral = Math.abs(brightness - 1) < 0.0001 && Math.abs(contrast - 1) < 0.0001 && Math.abs(saturation - 1) < 0.0001 && sepia <= 0 && Math.abs(hue) < 0.0001 && grayscale <= 0 && blur <= 0;
  if (neutral) return 'none';
  return `brightness(${brightness.toFixed(3)}) contrast(${contrast.toFixed(3)}) saturate(${saturation.toFixed(3)}) sepia(${sepia.toFixed(3)}) hue-rotate(${hue.toFixed(1)}deg) grayscale(${grayscale.toFixed(3)})${blur > 0 ? ` blur(${blur.toFixed(2)}px)` : ''}`;
}

function smoothTransitionProgress(value) {
  const t = clamp(Number(value || 0), 0, 1);
  return t * t * (3 - (2 * t));
}

function isLinkedTransition(type) {
  return ['crossfade', 'slide', 'push', 'zoom'].includes(type);
}

function applyVisualToNode(node, clip, visual = {}) {
  if (!node || !clip) return;
  node.style.opacity = String(Number(clamp(Number(visual.opacity ?? 1), 0, 1).toFixed(4)));
  node.style.filter = baseMediaFilter(clip, Math.max(0, Number(visual.blur || 0)));
  node.style.transform = mediaTransformForClip(clip, visual, Number(visual.localTime || 0));
}

function hideLinkedTransitionPeer() {
  if (el.transitionImage) {
    el.transitionImage.classList.add('hidden');
    el.transitionImage.style.opacity = '0';
  }
  const active = getActivePreviewVideo();
  allPreviewVideos().forEach(v => {
    if (v && v !== active && !v.dataset.keepVisibleForTransition) {
      v.classList.add('hidden');
      v.style.opacity = '0';
      try { v.pause(); } catch {}
      v.muted = true;
      setPreviewVideoGain(v, 0);
    }
    if (v) v.dataset.keepVisibleForTransition = '';
  });
}

function prepareLinkedTransitionPeer(peerClip, mode) {
  if (!peerClip) return null;
  if (peerClip.type === 'image') {
    if (el.transitionImage.src !== peerClip.objectUrl) el.transitionImage.src = peerClip.objectUrl || '';
    el.transitionImage.classList.remove('hidden');
    return el.transitionImage;
  }
  if (peerClip.type !== 'video' || !peerClip.previewSupported || !peerClip.objectUrl) return null;
  const node = getInactivePreviewVideo();
  if (!node) return null;
  node.dataset.keepVisibleForTransition = '1';
  node.muted = true;
  setPreviewVideoGain(node, 0);
  configurePreviewVideo(node, peerClip);
  if (node.dataset.boundSrc !== peerClip.objectUrl) {
    node.dataset.boundSrc = peerClip.objectUrl;
    node.src = peerClip.objectUrl;
    try { node.load(); } catch {}
  }
  const target = mode === 'prev-end'
    ? Math.max(0, Number(peerClip.trimEnd || peerClip.duration || 0) - 0.06)
    : Math.max(0, Number(peerClip.trimStart || 0));
  try {
    if (Number.isFinite(target) && Math.abs((node.currentTime || 0) - target) > 0.08) node.currentTime = target;
  } catch {}
  node.classList.remove('hidden');
  return node;
}

function linkedTransitionState(clip, localTime) {
  if (!clip || !state.clips.length) return null;
  ensureClipTransitionDefaults(clip);
  const index = state.playing ? state.currentClipIndex : getSelectedIndex();
  if (index < 0 || state.clips[index]?.id !== clip.id) return null;
  const duration = usableDuration(clip);
  const local = clamp(Number(localTime || 0), 0, duration);

  const outDur = Number(clip.transitionOutDuration || 0);
  const outRemaining = duration - local;
  if (isLinkedTransition(clip.transitionOutType) && outDur > 0 && outRemaining <= outDur && state.clips[index + 1]) {
    return {
      type: clip.transitionOutType,
      edge: 'out',
      progress: smoothTransitionProgress(1 - clamp(outRemaining / outDur, 0, 1)),
      currentClip: clip,
      peerClip: state.clips[index + 1],
      peerMode: 'next-start'
    };
  }

  const inDur = Number(clip.transitionInDuration || 0);
  if (isLinkedTransition(clip.transitionInType) && inDur > 0 && local <= inDur && state.clips[index - 1]) {
    return {
      type: clip.transitionInType,
      edge: 'in',
      progress: smoothTransitionProgress(clamp(local / inDur, 0, 1)),
      currentClip: clip,
      peerClip: state.clips[index - 1],
      peerMode: 'prev-end'
    };
  }
  return null;
}

function applyLinkedTransitionVisual(clip, localTime) {
  const linked = linkedTransitionState(clip, localTime);
  if (!linked) {
    hideLinkedTransitionPeer();
    return false;
  }
  const p = linked.progress;
  const currentNode = clip.type === 'image' ? el.previewImage : getActivePreviewVideo();
  const peerNode = prepareLinkedTransitionPeer(linked.peerClip, linked.peerMode);
  if (!currentNode || !peerNode) {
    hideLinkedTransitionPeer();
    return false;
  }

  currentNode.style.zIndex = '1';
  peerNode.style.zIndex = '2';

  let currentVisual = { opacity: 1, scale: 1, translateX: 0, translateY: 0, blur: 0 };
  let peerVisual = { opacity: 1, scale: 1, translateX: 0, translateY: 0, blur: 0 };

  if (linked.type === 'crossfade') {
    currentVisual.opacity = linked.edge === 'out' ? 1 - p : p;
    peerVisual.opacity = linked.edge === 'out' ? p : 1 - p;
  } else if (linked.type === 'slide') {
    if (linked.edge === 'out') {
      peerVisual.translateX = 100 * (1 - p);
    } else {
      currentVisual.translateX = 100 * (1 - p);
    }
  } else if (linked.type === 'push') {
    if (linked.edge === 'out') {
      currentVisual.translateX = -100 * p;
      peerVisual.translateX = 100 * (1 - p);
    } else {
      currentVisual.translateX = 100 * (1 - p);
      peerVisual.translateX = -100 * p;
    }
  } else if (linked.type === 'zoom') {
    currentVisual.opacity = linked.edge === 'out' ? 1 - p : p;
    peerVisual.opacity = linked.edge === 'out' ? p : 1 - p;
    currentVisual.scale = linked.edge === 'out' ? 1 + 0.08 * p : 0.94 + 0.06 * p;
    peerVisual.scale = linked.edge === 'out' ? 0.94 + 0.06 * p : 1 + 0.08 * p;
  }

  applyVisualToNode(currentNode, clip, currentVisual);
  applyVisualToNode(peerNode, linked.peerClip, peerVisual);

  if (el.transitionOverlay) {
    el.transitionOverlay.style.opacity = '0';
    el.transitionOverlay.classList.add('hidden');
  }
  return true;
}

function transitionVisualAt(clip, localTime) {
  ensureClipTransitionDefaults(clip);
  const duration = usableDuration(clip);
  const local = clamp(Number(localTime || 0), 0, duration);
  let opacity = 1;
  let blur = 0;
  let scale = 1;
  let translateX = 0;
  let translateY = 0;
  let overlayOpacity = 0;
  let overlayColor = '#000';
  const maxBlur = 8;
  const moveDistance = 16;
  const maxZoom = 0.065;

  const applyEdge = (type, progress, edge) => {
    const p = smoothTransitionProgress(progress);
    const incoming = edge === 'in';
    const away = incoming ? (1 - p) : p;

    if (type === 'fade' || type === 'crossfade') {
      opacity *= incoming ? p : (1 - p);
    }
    if (type === 'blur') {
      blur = Math.max(blur, away * maxBlur);
      opacity *= incoming ? (0.88 + 0.12 * p) : (0.88 + 0.12 * (1 - p));
    }
    if (type === 'slide') {
      translateX += incoming ? moveDistance * (1 - p) : -moveDistance * p;
      opacity *= incoming ? (0.78 + 0.22 * p) : (1 - 0.18 * p);
    }
    if (type === 'push') {
      translateX += incoming ? moveDistance * (1 - p) : -moveDistance * p;
      scale *= incoming ? (0.985 + 0.015 * p) : (1 - 0.015 * p);
    }
    if (type === 'zoom') {
      scale *= incoming ? (1 + maxZoom * (1 - p)) : (1 + maxZoom * p);
      opacity *= incoming ? (0.84 + 0.16 * p) : (1 - 0.12 * p);
    }
    if (type === 'dip-black' || type === 'dip-white') {
      overlayColor = type === 'dip-white' ? '#fff' : '#000';
      overlayOpacity = Math.max(overlayOpacity, incoming ? (1 - p) : p);
    }
    if (type === 'flash') {
      overlayColor = '#fff';
      const peak = incoming ? (1 - p) : p;
      overlayOpacity = Math.max(overlayOpacity, Math.sin(peak * Math.PI) * 0.72);
    }
  };

  if (clip.transitionInType !== 'none' && clip.transitionInDuration > 0 && local < clip.transitionInDuration) {
    applyEdge(clip.transitionInType, local / clip.transitionInDuration, 'in');
  }
  const outRemaining = duration - local;
  if (clip.transitionOutType !== 'none' && clip.transitionOutDuration > 0 && outRemaining < clip.transitionOutDuration) {
    applyEdge(clip.transitionOutType, 1 - (outRemaining / clip.transitionOutDuration), 'out');
  }
  return {
    opacity: clamp(opacity, 0, 1),
    blur,
    scale: clamp(scale, 0.9, 1.12),
    translateX: clamp(translateX, -25, 25),
    translateY: clamp(translateY, -25, 25),
    overlayOpacity: clamp(overlayOpacity, 0, 1),
    overlayColor
  };
}

function ensureKenBurnsDefaults(clip) {
  if (!clip || (clip.type !== 'image' && clip.type !== 'video')) return;
  if (!clip.kenBurnsMotion) clip.kenBurnsMotion = 'none';
  if (clip.kenBurnsStrength == null) clip.kenBurnsStrength = 35;
}

function kenBurnsVisualAt(clip, localTime = 0) {
  if (!clip || (clip.type !== 'image' && clip.type !== 'video')) return { scale: 1, x: 0, y: 0 };
  ensureKenBurnsDefaults(clip);
  const mode = clip.kenBurnsMotion || 'none';
  if (mode === 'none') return { scale: 1, x: 0, y: 0 };
  const duration = Math.max(0.1, usableDuration(clip));
  const p = clamp(Number(localTime || 0) / duration, 0, 1);
  const strength = clamp(Number(clip.kenBurnsStrength || 35), 0, 100);
  const move = strength * 1.15;
  const zoomDelta = strength / 70;
  const visual = { scale: 1, x: 0, y: 0 };

  if (mode.includes('zoom-in')) visual.scale = 1 + zoomDelta * p;
  if (mode.includes('zoom-out')) visual.scale = 1 + zoomDelta * (1 - p);

  if (mode === 'move-left') visual.x = (move / 2) - (move * p);
  if (mode === 'move-right') visual.x = (-move / 2) + (move * p);
  if (mode === 'move-up') visual.y = (move / 2) - (move * p);
  if (mode === 'move-down') visual.y = (-move / 2) + (move * p);
  if (mode === 'zoom-in-right') visual.x = (-move / 2) + (move * p);
  if (mode === 'zoom-in-left') visual.x = (move / 2) - (move * p);
  if (mode === 'zoom-out-up') visual.y = (move / 2) - (move * p);
  if (mode === 'zoom-out-down') visual.y = (-move / 2) + (move * p);

  if (Math.abs(visual.x) > 0.01 || Math.abs(visual.y) > 0.01 || mode.includes('move')) {
    visual.scale = Math.max(visual.scale, 1 + zoomDelta);
  }

  return visual;
}

function safeCssShiftPercent(shift, zoom) {
  const z = Math.max(1, Number(zoom || 1));
  const maxShift = Math.max(0, ((z - 1) * 50) / z);
  return clamp(Number(shift || 0), -maxShift, maxShift);
}

function mediaTransformForClip(clip, visual = {}, localTime = 0) {
  const kb = kenBurnsVisualAt(clip, localTime);
  const rawX = Number(clip?.cropX || 0) + Number(visual.translateX || 0) + Number(kb.x || 0);
  const rawY = Number(clip?.cropY || 0) + Number(visual.translateY || 0) + Number(kb.y || 0);
  const zoom = Math.max(1, Number(clip?.cropZoom || 1) * Number(visual.scale || 1) * Number(kb.scale || 1));
  const x = safeCssShiftPercent(rawX, zoom);
  const y = safeCssShiftPercent(rawY, zoom);
  return `translate(${x.toFixed(3)}%, ${y.toFixed(3)}%) scale(${zoom.toFixed(4)})`;
}

function applyTransitionVisual(clip, localTime, force = false) {
  if (force && applyLinkedTransitionVisual(clip, localTime)) return;
  const visual = force ? transitionVisualAt(clip, localTime) : { opacity: 1, blur: 0, scale: 1, translateX: 0, translateY: 0, overlayOpacity: 0, overlayColor: '#000' };
  const opacity = Number(visual.opacity.toFixed(4));
  const filter = baseMediaFilter(clip, Number(visual.blur || 0));
  const transform = mediaTransformForClip(clip, visual, localTime);
  const overlayOpacity = Number((visual.overlayOpacity || 0).toFixed(4));
  const overlayColor = visual.overlayColor || '#000';
  if (Math.abs(opacity - state.lastTransitionOpacity) >= 0.002 || filter !== state.lastTransitionCss || transform !== state.lastTransitionTransform) {
    state.lastTransitionOpacity = opacity;
    state.lastTransitionCss = filter;
    state.lastTransitionTransform = transform;
    const currentNode = clip?.type === 'image' ? el.previewImage : getActivePreviewVideo();
    if (currentNode && !currentNode.classList.contains('hidden')) {
      currentNode.style.zIndex = '1';
      currentNode.style.opacity = String(opacity);
      currentNode.style.filter = filter;
      currentNode.style.transform = transform;
    }
  }
  if (el.transitionOverlay) {
    if (overlayOpacity > 0.002) {
      el.transitionOverlay.classList.remove('hidden');
      el.transitionOverlay.style.background = overlayColor;
      el.transitionOverlay.style.opacity = String(overlayOpacity);
    } else if (!el.transitionOverlay.classList.contains('hidden')) {
      el.transitionOverlay.style.opacity = '0';
      el.transitionOverlay.classList.add('hidden');
    }
  }
}

function configurePreviewVideo(videoEl, clip) {
  if (!videoEl || !clip) return;
  videoEl.style.transform = mediaTransformForClip(clip, {}, 0);
  videoEl.style.filter = baseMediaFilter(clip, 0);
  videoEl.style.opacity = '1';
  state.lastTransitionCss = '';
  state.lastTransitionOpacity = -1;
  state.lastTransitionTransform = '';
  setPreviewVideoGain(videoEl, clipVolumeScalar(clip));
}

function syncActiveClipVolume(clip, options = {}) {
  if (!clip || clip.type !== 'video') return;
  const activeVideo = getActivePreviewVideo();
  if (!activeVideo) return;
  const sameClip = activeVideo.dataset.preloadedClipId === clip.id || activeVideo.dataset.boundSrc === clip.objectUrl;
  if (!sameClip) return;
  setPreviewVideoGain(activeVideo, clipVolumeScalar(clip));
  if (options.unmute && state.playing) activeVideo.muted = false;
}

function prewarmUpcomingClip(currentIndex) {
  const nextClip = state.clips[currentIndex + 1];
  const warmVideo = getInactivePreviewVideo();
  if (!nextClip || nextClip.type !== 'video' || !nextClip.previewSupported || !nextClip.objectUrl || !warmVideo) {
    if (warmVideo) {
      warmVideo.dataset.preloadedClipId = '';
      warmVideo.dataset.prewarmedAt = '';
      warmVideo.dataset.prestartedClipId = '';
    }
    state.previewVideoAltReadyForClipId = null;
    return;
  }
  const targetStart = Math.max(0, Number(nextClip.trimStart || 0));
  const alreadyReady = warmVideo.dataset.preloadedClipId === nextClip.id
    && warmVideo.dataset.boundSrc === nextClip.objectUrl
    && Math.abs(Number(warmVideo.dataset.prewarmedAt || -999) - targetStart) < 0.03
    && Number(warmVideo.readyState || 0) >= 2;
  if (alreadyReady) {
    state.previewVideoAltReadyForClipId = nextClip.id;
    return;
  }
  warmVideo.onloadedmetadata = null;
  warmVideo.oncanplay = null;
  warmVideo.onseeked = null;
  warmVideo.ontimeupdate = null;
  warmVideo.onended = null;
  warmVideo.onerror = null;
  warmVideo.pause();
  warmVideo.muted = true;
  setPreviewVideoGain(warmVideo, 0);
  warmVideo.dataset.preloadedClipId = nextClip.id;
  warmVideo.dataset.prewarmedAt = '';
  warmVideo.dataset.prestartedClipId = '';
  warmVideo.dataset.boundSrc = nextClip.objectUrl;
  configurePreviewVideo(warmVideo, nextClip);
  if (nextClip.thumb && nextClip.thumbKind === 'image') { try { warmVideo.poster = nextClip.thumb; } catch {} }
  try {
    warmVideo.src = nextClip.objectUrl;
    warmVideo.load();
    const markReady = () => {
      try {
        warmVideo.currentTime = targetStart;
        warmVideo.dataset.prewarmedAt = String(targetStart);
      } catch {}
      state.previewVideoAltReadyForClipId = nextClip.id;
    };
    warmVideo.onloadedmetadata = markReady;
    warmVideo.oncanplay = markReady;
    warmVideo.onloadeddata = markReady;
    warmVideo.onseeked = () => {
      warmVideo.dataset.prewarmedAt = String(targetStart);
      state.previewVideoAltReadyForClipId = nextClip.id;
    };
  } catch {
    state.previewVideoAltReadyForClipId = null;
  }
}



function prestartUpcomingClip(currentIndex, token) {
  const nextClip = state.clips[currentIndex + 1];
  if (token !== state.playToken || !state.playing) return;
  if (!nextClip || nextClip.type !== 'video' || !nextClip.previewSupported || !nextClip.objectUrl) return;
  const warmVideo = allPreviewVideos().find(v => v.dataset.preloadedClipId === nextClip.id && v.dataset.boundSrc === nextClip.objectUrl) || getInactivePreviewVideo();
  if (!warmVideo || warmVideo === getActivePreviewVideo()) return;
  const targetStart = Math.max(0, Number(nextClip.trimStart || 0));
  const readyEnough = Number(warmVideo.readyState || 0) >= 2;
  if (!readyEnough) return;
  if (warmVideo.dataset.prestartedClipId === nextClip.id) return;
  try {
    warmVideo.muted = true;
    setPreviewVideoGain(warmVideo, 0);
    warmVideo.playsInline = true;
    warmVideo.preload = 'auto';
    if (Math.abs((warmVideo.currentTime || 0) - targetStart) > 0.08) warmVideo.currentTime = targetStart;
    try { warmVideo.playbackRate = speedAtTimelineLocal(nextClip, 0); } catch {}
    const p = warmVideo.play();
    warmVideo.dataset.prestartedClipId = nextClip.id;
    warmVideo.dataset.prewarmedAt = String(targetStart);
    if (p && typeof p.catch === 'function') p.catch(() => { warmVideo.dataset.prestartedClipId = ''; });
  } catch {
    warmVideo.dataset.prestartedClipId = '';
  }
}

function isSyntheticClip(clip) {
  return clip && (clip.type === 'background' || clip.type === 'text');
}

function ensureTextDefaults(clip) {
  if (!clip) return;
  if (!clip.textColor) clip.textColor = '#ffffff';
  if (!clip.fontFamily) clip.fontFamily = 'Inter, Arial, sans-serif';
  if (!clip.fontSize) clip.fontSize = clip.type === 'text' ? 56 : 44;
  if (!clip.textMotion) clip.textMotion = 'none';
  if (clip.type === 'text' && clip.text == null) clip.text = 'Your text here';
  if (clip.type === 'background' && clip.text == null) clip.text = '';
  if ((clip.type === 'image' || clip.type === 'video') && clip.text == null) clip.text = '';
}

function ensureSyntheticDefaults(clip) {
  if (!clip || !isSyntheticClip(clip)) return;
  if (!clip.bgColor) clip.bgColor = clip.type === 'background' ? '#111827' : '#0f172a';
  if (!clip.textColor) clip.textColor = '#ffffff';
  if (!clip.fontFamily) clip.fontFamily = 'Inter, Arial, sans-serif';
  if (!clip.fontSize) clip.fontSize = clip.type === 'text' ? 56 : 44;
  if (!clip.textMotion) clip.textMotion = 'none';
  if (clip.type === 'background' && clip.text == null) clip.text = '';
  if (clip.type === 'text' && clip.text == null) clip.text = 'Your text here';
}

function textMotionVisual(clip, localTime) {
  const duration = usableDuration(clip);
  const t = clamp(Number(localTime || 0) / Math.max(0.1, duration), 0, 1);
  const ease = smoothTransitionProgress(t);
  const visual = { opacity: 1, scale: 1, x: 0, y: 0 };
  const motion = clip?.textMotion || 'none';
  if (motion === 'fade-in') visual.opacity = clamp(t / 0.25, 0, 1);
  if (motion === 'slide-up') { visual.opacity = clamp(t / 0.25, 0, 1); visual.y = (1 - ease) * 28; }
  if (motion === 'slow-zoom') visual.scale = 1 + t * 0.08;
  if (motion === 'drift') { visual.x = Math.sin(t * Math.PI * 2) * 10; visual.y = -t * 18; }
  return visual;
}

function escapeAttr(value) { return String(value || '').replace(/"/g, '&quot;'); }

function applySyntheticPreview(clip, localTime = 0, applyTransition = false) {
  ensureSyntheticDefaults(clip);
  if (!el.previewSynthetic) return;
  allPreviewVideos().forEach(v => v.classList.add('hidden'));
  el.previewImage.classList.add('hidden');
  if (el.previewSynthetic) el.previewSynthetic.classList.add('hidden');
  el.previewFallback.classList.add('hidden');
  hideLinkedTransitionPeer();
  const transition = applyTransition ? transitionVisualAt(clip, localTime) : { opacity: 1, scale: 1, translateX: 0, translateY: 0, blur: 0, overlayOpacity: 0 };
  const motion = clip.type === 'text' ? textMotionVisual(clip, localTime) : { opacity: 1, scale: 1, x: 0, y: 0 };
  el.previewSynthetic.classList.remove('hidden');
  if (el.previewTextOverlay) el.previewTextOverlay.classList.add('hidden');
  el.previewSynthetic.textContent = clip.type === 'text' ? (clip.text || '') : '';
  el.previewSynthetic.style.background = clip.bgColor || '#111827';
  el.previewSynthetic.style.color = clip.textColor || '#ffffff';
  el.previewSynthetic.style.fontFamily = clip.fontFamily || 'Inter, Arial, sans-serif';
  el.previewSynthetic.style.fontSize = clamp(Number(clip.fontSize || 56), 20, 140) + 'px';
  el.previewSynthetic.style.fontWeight = clip.fontFamily && clip.fontFamily.includes('Impact') ? '800' : '750';
  el.previewSynthetic.style.opacity = String(clamp(Number(transition.opacity || 1) * Number(motion.opacity || 1), 0, 1));
  el.previewSynthetic.style.filter = Number(transition.blur || 0) > 0 ? 'blur(' + Number(transition.blur || 0).toFixed(2) + 'px)' : 'none';
  const tx = Number(transition.translateX || 0) + Number(motion.x || 0);
  const ty = Number(transition.translateY || 0) + Number(motion.y || 0);
  const sc = Number(transition.scale || 1) * Number(motion.scale || 1);
  el.previewSynthetic.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + sc.toFixed(4) + ')';
  if (el.transitionOverlay) {
    const overlayOpacity = Number(transition.overlayOpacity || 0);
    if (overlayOpacity > 0.002) {
      el.transitionOverlay.classList.remove('hidden');
      el.transitionOverlay.style.background = transition.overlayColor || '#000';
      el.transitionOverlay.style.opacity = String(overlayOpacity);
    } else {
      el.transitionOverlay.style.opacity = '0';
      el.transitionOverlay.classList.add('hidden');
    }
  }
}

function renderPreviewTextOverlay(clip, localTime = 0) {
  if (!el.previewTextOverlay) return;
  if (!clip || isSyntheticClip(clip) || !String(clip.text || '').trim()) {
    el.previewTextOverlay.classList.add('hidden');
    el.previewTextOverlay.textContent = '';
    return;
  }
  ensureTextDefaults(clip);
  const motion = textMotionVisual(clip, localTime);
  el.previewTextOverlay.classList.remove('hidden');
  el.previewTextOverlay.textContent = clip.text || '';
  el.previewTextOverlay.style.color = clip.textColor || '#ffffff';
  el.previewTextOverlay.style.fontFamily = clip.fontFamily || 'Inter, Arial, sans-serif';
  el.previewTextOverlay.style.fontSize = clamp(Number(clip.fontSize || 44), 20, 140) + 'px';
  el.previewTextOverlay.style.fontWeight = clip.fontFamily && clip.fontFamily.includes('Impact') ? '800' : '750';
  el.previewTextOverlay.style.opacity = String(clamp(Number(motion.opacity || 1), 0, 1));
  el.previewTextOverlay.style.transform = 'translate(' + Number(motion.x || 0) + 'px,' + Number(motion.y || 0) + 'px) scale(' + Number(motion.scale || 1).toFixed(4) + ')';
}

function wrapTextCanvas(ctx, text, maxWidth) {
  const paragraphs = String(text || '').split(/\n/);
  const lines = [];
  for (const para of paragraphs) {
    const words = para.split(/\s+/).filter(Boolean);
    if (!words.length) { lines.push(''); continue; }
    let line = '';
    for (const word of words) {
      const test = line ? line + ' ' + word : word;
      if (ctx.measureText(test).width > maxWidth && line) { lines.push(line); line = word; }
      else line = test;
    }
    lines.push(line);
  }
  return lines;
}

function drawSyntheticClip(ctx, canvas, clip, localTime = 0) {
  ensureSyntheticDefaults(clip);
  ctx.save();
  ctx.fillStyle = clip.bgColor || '#111827';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  if (clip.type === 'text' && String(clip.text || '').trim()) {
    const motion = textMotionVisual(clip, localTime);
    const fontSize = clamp(Number(clip.fontSize || 56) * (canvas.width / 1080), 18, 180);
    ctx.translate(canvas.width / 2 + Number(motion.x || 0) * (canvas.width / 1080), canvas.height / 2 + Number(motion.y || 0) * (canvas.height / 1080));
    ctx.scale(Number(motion.scale || 1), Number(motion.scale || 1));
    ctx.globalAlpha = clamp(Number(motion.opacity || 1), 0, 1);
    ctx.fillStyle = clip.textColor || '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = '750 ' + fontSize.toFixed(1) + 'px ' + (clip.fontFamily || 'Inter, Arial, sans-serif');
    const maxWidth = canvas.width * 0.82;
    const lines = wrapTextCanvas(ctx, clip.text || '', maxWidth);
    const lineHeight = fontSize * 1.12;
    const startY = -((lines.length - 1) * lineHeight) / 2;
    lines.forEach((line, i) => ctx.fillText(line, 0, startY + i * lineHeight));
  }
  ctx.restore();
}

function drawClipTextOverlay(ctx, canvas, clip, localTime = 0) {
  if (!clip || !String(clip.text || '').trim()) return;
  ensureTextDefaults(clip);
  const motion = textMotionVisual(clip, localTime);
  const fontSize = clamp(Number(clip.fontSize || 44) * (canvas.width / 1080), 18, 180);
  ctx.save();
  ctx.translate(canvas.width / 2 + Number(motion.x || 0) * (canvas.width / 1080), canvas.height / 2 + Number(motion.y || 0) * (canvas.height / 1080));
  ctx.scale(Number(motion.scale || 1), Number(motion.scale || 1));
  ctx.globalAlpha = clamp(Number(motion.opacity || 1), 0, 1);
  ctx.fillStyle = clip.textColor || '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = '750 ' + fontSize.toFixed(1) + 'px ' + (clip.fontFamily || 'Inter, Arial, sans-serif');
  ctx.shadowColor = 'rgba(0,0,0,.38)';
  ctx.shadowBlur = fontSize * 0.32;
  ctx.shadowOffsetY = fontSize * 0.08;
  const maxWidth = canvas.width * 0.82;
  const lines = wrapTextCanvas(ctx, clip.text || '', maxWidth);
  const lineHeight = fontSize * 1.12;
  const startY = -((lines.length - 1) * lineHeight) / 2;
  lines.forEach((line, i) => ctx.fillText(line, 0, startY + i * lineHeight));
  ctx.restore();
}

function makeId() {
  return 'clip-' + Math.random().toString(36).slice(2, 10);
}

function sanitizeFilename(value) {
  return value.toLowerCase().replace(/[^a-z0-9-_]+/g, '-').replace(/^-+|-+$/g, '') || 'project';
}


function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '';
  const units = ['B','KB','MB','GB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) { value /= 1024; unit += 1; }
  return `${value >= 10 || unit === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[unit]}`;
}
let importProgressHideTimer = null;
function setImportProgress({ visible = true, percent = 0, fileName = '', fileSize = '', status = '', done = false, error = false } = {}) {
  if (!el.importProgressBox) return;
  if (importProgressHideTimer) { clearTimeout(importProgressHideTimer); importProgressHideTimer = null; }
  if (!visible) { el.importProgressBox.classList.add('hidden'); return; }
  const safePercent = Math.max(0, Math.min(100, Math.round(percent || 0)));
  el.importProgressBox.classList.remove('hidden', 'done', 'error');
  if (done) el.importProgressBox.classList.add('done');
  if (error) el.importProgressBox.classList.add('error');
  if (el.importProgressPercent) el.importProgressPercent.textContent = `${safePercent}%`;
  if (el.importProgressFill) el.importProgressFill.style.width = `${safePercent}%`;
  if (el.importProgressFile) el.importProgressFile.textContent = fileName ? `${fileName}${fileSize ? ' · ' + fileSize : ''}` : 'Preparing file…';
  if (el.importProgressStatus) el.importProgressStatus.textContent = status || (done ? 'Ready.' : 'Importing…');
}
function finishImportProgress(status = 'Import complete.') {
  setImportProgress({ visible: true, percent: 100, status, done: true });
  importProgressHideTimer = setTimeout(() => {
    if (el.importProgressBox) el.importProgressBox.classList.add('hidden');
  }, 2600);
}
function nextFrame() { return new Promise(resolve => requestAnimationFrame(() => resolve())); }

function extensionOf(fileName = '') {
  const lower = fileName.toLowerCase();
  return lower.includes('.') ? '.' + lower.split('.').pop() : '';
}

function classifyFile(file) {
  const ext = extensionOf(file.name);
  const imageExt = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
  const videoExt = ['.mp4', '.mov', '.m4v', '.webm', '.ogv'];
  const audioExt = ['.mp3', '.wav', '.m4a', '.aac', '.ogg'];
  const type = file.type || '';
  if (type.startsWith('image/') || imageExt.includes(ext)) return 'image';
  if (type.startsWith('video/') || videoExt.includes(ext)) return 'video';
  if (type.startsWith('audio/') || audioExt.includes(ext)) return 'audio';
  return 'unknown';
}

function isSafariBrowser() {
  const ua = navigator.userAgent || '';
  return /Safari/i.test(ua) && !/Chrome|Chromium|CriOS|FxiOS|Edg/i.test(ua);
}

function safariVideoSupportNote(fileName = '') {
  const ext = extensionOf(fileName).toLowerCase();
  if (!isSafariBrowser()) return '';
  if (ext === '.webm' || ext === '.ogv') return 'Safari cannot reliably preview WebM/OGV. Use MP4/MOV encoded as H.264, or continue editing this source in Chrome.';
  return 'Safari preview depends on the source codec. MP4/MOV with H.264 normally works; VP8/VP9/AV1 or unusual phone/screen-recording codecs may not preview.';
}

function defaultGradient(type) {
  if (type === 'image') return 'linear-gradient(135deg,#6a7cff,#7f4fff,#f04ab8)';
  if (type === 'audio') return 'linear-gradient(135deg,#11bf9c,#11c6e6,#3874ff)';
  if (type === 'background') return 'linear-gradient(135deg,#111827,#1f2937)';
  if (type === 'text') return 'linear-gradient(135deg,#0f172a,#4f46e5,#7c3aed)';
  return 'linear-gradient(135deg,#ff8a3d,#ff4f8e,#6e67ff)';
}


function ensureSpeedDefaults(clip) {
  if (!clip || clip.type !== 'video') return;
  const allowedRamps = new Set(['none','normal-slow','slow-normal','normal-fast','fast-normal','fast-slow','slow-fast']);
  const allowedStrengths = new Set(['soft','medium','strong']);
  const allowedTimings = new Set(['full','start','middle','end','custom']);
  clip.clipSpeed = clamp(Number(clip.clipSpeed || 1), 0.25, 4);
  clip.speedRamp = allowedRamps.has(clip.speedRamp) ? clip.speedRamp : 'none';
  clip.speedRampStrength = allowedStrengths.has(clip.speedRampStrength) ? clip.speedRampStrength : 'medium';
  clip.speedRampTiming = allowedTimings.has(clip.speedRampTiming) ? clip.speedRampTiming : 'full';
  clip.speedRampStart = Math.max(0, Number(clip.speedRampStart || 0));
  clip.speedRampEnd = Math.max(0, Number(clip.speedRampEnd || 3));
  if (clip.speedRampEnd <= clip.speedRampStart) clip.speedRampEnd = clip.speedRampStart + 0.1;
}

function baseSpeedForClip(clip) {
  ensureSpeedDefaults(clip);
  return clamp(Number(clip?.clipSpeed || 1), 0.25, 4);
}

function rampSpeedPair(clip) {
  ensureSpeedDefaults(clip);
  const base = baseSpeedForClip(clip);
  if (!clip || clip.speedRamp === 'none') return [base, base];
  const strength = clip.speedRampStrength || 'medium';
  const slowMap = { soft: 0.75, medium: 0.5, strong: 0.33 };
  const fastMap = { soft: 1.35, medium: 1.8, strong: 2.5 };
  const normal = base;
  const slow = clamp(base * (slowMap[strength] || 0.5), 0.25, 4);
  const fast = clamp(base * (fastMap[strength] || 1.8), 0.25, 4);
  switch (clip.speedRamp) {
    case 'normal-slow': return [normal, slow];
    case 'slow-normal': return [slow, normal];
    case 'normal-fast': return [normal, fast];
    case 'fast-normal': return [fast, normal];
    case 'fast-slow': return [fast, slow];
    case 'slow-fast': return [slow, fast];
    default: return [base, base];
  }
}

function averageSpeedForClip(clip) {
  const [a, b] = rampSpeedPair(clip);
  return clamp((a + b) / 2, 0.25, 4);
}

function rawSourceDuration(clip) {
  return Math.max(0.1, Number(clip?.trimEnd || 0) - Number(clip?.trimStart || 0));
}

function speedWindow(clip, timelineDur) {
  const d = Math.max(0.1, Number(timelineDur || 0));
  const mode = clip?.speedRampTiming || 'full';
  if (mode === 'custom') {
    const start = clamp(Number(clip?.speedRampStart || 0), 0, d);
    const end = clamp(Number(clip?.speedRampEnd || d), start + 0.1, d);
    return { a: start, b: end };
  }
  if (mode === 'start') return { a: 0, b: d * 0.45 };
  if (mode === 'middle') return { a: d * 0.275, b: d * 0.725 };
  if (mode === 'end') return { a: d * 0.55, b: d };
  return { a: 0, b: d };
}

function speedAtTimelineLocal(clip, local) {
  ensureSpeedDefaults(clip);
  const [startSpeed, endSpeed] = rampSpeedPair(clip);
  if (!clip || clip.speedRamp === 'none') return startSpeed;
  const d = usableDuration(clip);
  const win = speedWindow(clip, d);
  const span = Math.max(0.001, win.b - win.a);
  const p = smoothTransitionProgress(clamp((Number(local || 0) - win.a) / span, 0, 1));
  return clamp(startSpeed + ((endSpeed - startSpeed) * p), 0.25, 4);
}

function sourceElapsedForTimelineLocal(clip, local) {
  if (!clip || clip.type !== 'video') return Number(local || 0);
  ensureSpeedDefaults(clip);
  const d = usableDuration(clip);
  const raw = rawSourceDuration(clip);
  const t = clamp(Number(local || 0), 0, d);
  if (clip.speedRamp === 'none') return clamp(t * baseSpeedForClip(clip), 0, raw);
  const steps = Math.max(12, Math.min(120, Math.ceil(t * 12)));
  let acc = 0;
  let prev = 0;
  for (let i = 1; i <= steps; i += 1) {
    const cur = (t * i) / steps;
    const mid = (prev + cur) / 2;
    acc += speedAtTimelineLocal(clip, mid) * (cur - prev);
    prev = cur;
  }
  return clamp(acc, 0, raw);
}

function timelineLocalFromSourceElapsed(clip, sourceElapsed) {
  if (!clip || clip.type !== 'video') return Number(sourceElapsed || 0);
  const target = clamp(Number(sourceElapsed || 0), 0, rawSourceDuration(clip));
  const d = usableDuration(clip);
  let lo = 0;
  let hi = d;
  for (let i = 0; i < 24; i += 1) {
    const mid = (lo + hi) / 2;
    if (sourceElapsedForTimelineLocal(clip, mid) < target) lo = mid; else hi = mid;
  }
  return clamp((lo + hi) / 2, 0, d);
}

function videoSourceTimeAtTimelineLocal(clip, local) {
  return Number(clip?.trimStart || 0) + sourceElapsedForTimelineLocal(clip, local);
}


function usableDuration(clip) {
  if (clip && clip.type === 'video') {
    ensureSpeedDefaults(clip);
    return Math.max(0.1, rawSourceDuration(clip) / averageSpeedForClip(clip));
  }
  return Math.max(0.1, Number(clip.trimEnd) - Number(clip.trimStart));
}

function totalDuration() {
  return state.clips.reduce((sum, clip) => sum + usableDuration(clip), 0);
}

function visibleTimelineDuration() {
  return Math.max(totalDuration(), musicEndOnTimeline());
}

function clampTimelineToProjectEnd() {
  const total = totalDuration();
  if (!Number.isFinite(state.currentTimelineTime)) state.currentTimelineTime = 0;
  state.currentTimelineTime = clamp(Number(state.currentTimelineTime || 0), 0, total);
  return total;
}

function getMusicClips() {
  if (!Array.isArray(state.musicClips)) state.musicClips = [];
  if (state.musicClip && !state.musicClips.some(m => m.id === state.musicClip.id)) state.musicClips.unshift(state.musicClip);
  state.musicClips = state.musicClips.slice(0, 5);
  if (!state.selectedMusicId && state.musicClips[0]) state.selectedMusicId = state.musicClips[0].id;
  state.musicClip = state.musicClips.find(m => m.id === state.selectedMusicId) || state.musicClips[0] || null;
  return state.musicClips;
}
function getSelectedMusicClip() { getMusicClips(); return state.musicClip; }
function musicUsableDuration(m = getSelectedMusicClip()) { if (!m) return 0; return Math.max(0.1, Number(m.trimEnd || 0) - Number(m.trimStart || 0)); }
function getSelectedClip() { return state.clips.find(c => c.id === state.selectedClipId) || null; }
function getSelectedIndex() { return state.clips.findIndex(c => c.id === state.selectedClipId); }
function findMusicSource(name) { const match = getMusicClips().find(m => m.name === name); return match || state.importedAudio.find(item => item.name === name) || null; }
function timelineVisualGapPx() { return 0; }
function timelineOffsetForIndex(index) { let sum=0; for (let i=0;i<index;i+=1) sum += usableDuration(state.clips[i]); return sum; }
function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
function musicProjectDuration(m = getSelectedMusicClip()) { if (!m) return 0; return Math.max(0.1, Number(m.duration || 0)); }
function ensureMusicClipDefaults(m = getSelectedMusicClip()) {
  if (!m) return;
  m.startTimeOnTimeline = Number(m.startTimeOnTimeline || 0);
  const projectDuration = musicProjectDuration(m);
  m.trimStart = clamp(Number(m.trimStart || 0), 0, Math.max(0, projectDuration));
  m.trimEnd = clamp(Number(m.trimEnd || projectDuration), m.trimStart + 0.1, Math.max(m.trimStart + 0.1, projectDuration));
  const usable = Math.max(0.1, Number(m.trimEnd || 0) - Number(m.trimStart || 0));
  m.volume = clamp(Number(m.volume ?? state.musicVolume ?? 55), 0, 100);
  m.fadeIn = clamp(Number(m.fadeIn || 0), 0, usable);
  m.fadeOut = clamp(Number(m.fadeOut || 0), 0, usable);
  m.enabled = m.enabled !== false;
}
function musicEndOnTimeline() {
  return getMusicClips().reduce((maxEnd, m) => { ensureMusicClipDefaults(m); return Math.max(maxEnd, Number(m.startTimeOnTimeline || 0) + musicUsableDuration(m)); }, 0);
}
function musicVolumeAtTimelineTime(t, m = getSelectedMusicClip()) {
  if (!m || !m.enabled) return 0;
  const start = Number(m.startTimeOnTimeline || 0), len = musicUsableDuration(m), local = Number(t) - start;
  if (local < 0 || local > len) return 0;
  const base = clamp(Number(m.volume ?? state.musicVolume ?? 55) / 100, 0, 1);
  let scalar = base;
  const fi = Number(m.fadeIn || 0), fo = Number(m.fadeOut || 0);
  if (fi > 0) scalar *= clamp(local / fi, 0, 1);
  if (fo > 0) scalar *= clamp((len - local) / fo, 0, 1);
  return scalar;
}
function getMusicAudioPlayer(m) {
  if (!m || !m.id) return null;
  if (!musicAudioPlayers.has(m.id)) { const audio = new Audio(); audio.loop = false; audio.preload = 'auto'; musicAudioPlayers.set(m.id, audio); }
  return musicAudioPlayers.get(m.id);
}
function pauseAllMusicPlayers(reset = false) {
  try { musicAudio.pause(); if (reset) musicAudio.currentTime = 0; } catch {}
  for (const audio of musicAudioPlayers.values()) {
    try { audio.pause(); } catch {}
    try { audio.volume = 0; } catch {}
    if (reset) { try { audio.currentTime = 0; } catch {} }
  }
}
function syncMusicToTimeline(forceSeek = false) {
  const clips = getMusicClips();
  if (!clips.length) { pauseAllMusicPlayers(); return; }
  const timelineT = Number(state.currentTimelineTime || 0);
  for (const m of clips) {
    ensureMusicClipDefaults(m);
    const audio = getMusicAudioPlayer(m);
    if (!audio || !m.enabled || !m.url) continue;
    if (audio.src !== m.url) audio.src = m.url;
    const start = Number(m.startTimeOnTimeline || 0), len = musicUsableDuration(m);
    if (timelineT < start || timelineT > start + len) { try { audio.pause(); } catch {}; if (audio.volume !== 0) audio.volume = 0; continue; }
    const target = Number(m.trimStart || 0) + (timelineT - start);
    const canSeek = Number.isFinite(audio.duration) && audio.duration > 0;
    const currentAudioTime = Number(audio.currentTime || 0);
    // During normal playback, never seek music backwards at video clip boundaries.
    // Browser video handoff can lag briefly; a backward audio seek here creates
    // the audible repeat/loop between clips.
    if (forceSeek || !canSeek) {
      try { audio.currentTime = clamp(target, 0, Math.max(0, (audio.duration || m.duration || target) - 0.02)); } catch {}
    } else if (state.playing) {
      if (currentAudioTime + 0.75 < target) {
        try { audio.currentTime = clamp(target, 0, Math.max(0, (audio.duration || m.duration || target) - 0.02)); } catch {}
      }
    } else if (Math.abs(currentAudioTime - target) > 0.35) {
      try { audio.currentTime = clamp(target, 0, Math.max(0, (audio.duration || m.duration || target) - 0.02)); } catch {}
    }
    audio.volume = musicVolumeAtTimelineTime(timelineT, m);
    if (state.playing && audio.paused) audio.play().catch(() => {});
  }
}
function syncMusicToTimelineLight() { const now = performance.now(); if (now - Number(state.lastMusicSyncAt || 0) < 180) return; state.lastMusicSyncAt = now; syncMusicToTimeline(false); }
function renderPlayStateLight() { const now = performance.now(); if (now - Number(state.lastPlayStatePaintAt || 0) < 90) return; state.lastPlayStatePaintAt = now; renderPlayState(); }
function updateMusicUi() {
  const clips = getMusicClips(); const m = getSelectedMusicClip();
  if (!m) {
    if (el.musicTrack) el.musicTrack.value = 'None';
    el.musicInfo.textContent = 'Upload up to five music tracks. Select a track here, then drag and trim it in the music rows below.';
    if (el.musicVolume) el.musicVolume.value = state.musicVolume || 55;
    if (el.musicVolumeLabel) el.musicVolumeLabel.textContent = `${state.musicVolume || 55}%`;
    if (el.musicFadeIn) { el.musicFadeIn.max = 5; el.musicFadeIn.value = 0; }
    if (el.musicFadeOut) { el.musicFadeOut.max = 5; el.musicFadeOut.value = 0; }
    if (el.musicFadeInLabel) el.musicFadeInLabel.textContent = '0.0s';
    if (el.musicFadeOutLabel) el.musicFadeOutLabel.textContent = '0.0s';
    if (el.musicStartTime) el.musicStartTime.value = '0.0';
    if (el.musicTrimStart) el.musicTrimStart.value = '0.0';
    if (el.musicTrimEnd) el.musicTrimEnd.value = '0.0';
    return;
  }
  ensureMusicClipDefaults(m);
  state.musicTrack = m.name; state.musicVolume = Number(m.volume ?? state.musicVolume ?? 55);
  if (el.musicTrack && el.musicTrack.value !== m.id) el.musicTrack.value = m.id;
  if (el.musicVolume) el.musicVolume.value = state.musicVolume;
  if (el.musicVolumeLabel) el.musicVolumeLabel.textContent = `${state.musicVolume}%`;
  const usable = musicUsableDuration(m);
  if (el.musicFadeIn) { el.musicFadeIn.max = `${usable}`; el.musicFadeIn.value = m.fadeIn; }
  if (el.musicFadeOut) { el.musicFadeOut.max = `${usable}`; el.musicFadeOut.value = m.fadeOut; }
  if (el.musicFadeInLabel) el.musicFadeInLabel.textContent = `${Number(m.fadeIn).toFixed(1)}s`;
  if (el.musicFadeOutLabel) el.musicFadeOutLabel.textContent = `${Number(m.fadeOut).toFixed(1)}s`;
  if (el.musicStartTime) el.musicStartTime.value = Number(m.startTimeOnTimeline || 0).toFixed(1);
  if (el.musicTrimStart) { el.musicTrimStart.max = Math.max(0, musicProjectDuration(m) - 0.1).toFixed(1); el.musicTrimStart.value = Number(m.trimStart || 0).toFixed(1); }
  if (el.musicTrimEnd) { el.musicTrimEnd.max = musicProjectDuration(m).toFixed(1); el.musicTrimEnd.value = Number(m.trimEnd || musicProjectDuration(m)).toFixed(1); }
  el.musicInfo.textContent = `Track ${clips.findIndex(x => x.id === m.id) + 1}/5: ${m.name} • start ${Number(m.startTimeOnTimeline).toFixed(1)}s • trim ${Number(m.trimStart).toFixed(1)}-${Number(m.trimEnd).toFixed(1)}s • used ${usable.toFixed(1)}s`;
}
function updateMusicBlockVisual() {
  for (const m of getMusicClips()) {
    ensureMusicClipDefaults(m);
    const block = document.getElementById(`musicBlock-${m.id}`);
    if (!block) continue;
    block.style.left = `${Math.max(0, Number(m.startTimeOnTimeline || 0) * pxPerSec())}px`;
    block.style.width = `${Math.max(24, musicUsableDuration(m) * pxPerSec())}px`;
    block.classList.toggle('selected', m.id === state.selectedMusicId);
    const meta = block.querySelector('.meta');
    if (meta) meta.textContent = `${musicUsableDuration(m).toFixed(1)}s • vol ${Number(m.volume).toFixed(0)}% • fades ${Number(m.fadeIn).toFixed(1)}/${Number(m.fadeOut).toFixed(1)}s`;
  }
}
function scheduleMusicTimelineRefresh() { if (state.musicUiRaf) return; state.musicUiRaf = requestAnimationFrame(() => { state.musicUiRaf = null; updateMusicBlockVisual(); }); }
function holdTimelineViewport(ms = 700) {
  state.suppressTimelineAutoScrollUntil = Math.max(state.suppressTimelineAutoScrollUntil || 0, Date.now() + ms);
}
function preserveTimelineViewport(fn, ms = 700) {
  const scrollEl = el.timelineScroll;
  const previousScrollLeft = scrollEl ? Number(scrollEl.scrollLeft || 0) : 0;
  holdTimelineViewport(ms);
  const result = fn ? fn() : undefined;
  if (scrollEl) requestAnimationFrame(() => { scrollEl.scrollLeft = previousScrollLeft; });
  return result;
}
function shouldAutoScrollTimelineToPlayhead() {
  return !state.musicDrag && Date.now() > Number(state.suppressTimelineAutoScrollUntil || 0);
}
function beginMusicDrag(event, mode, musicId = null) {
  if (musicId) state.selectedMusicId = musicId;
  getMusicClips(); const m = getSelectedMusicClip(); if (!m) return;
  event.preventDefault(); event.stopPropagation();
  holdTimelineViewport(1200);
  stopPlayback('');
  const block = document.getElementById(`musicBlock-${m.id}`); if (block) block.classList.add('dragging');
  const stageRect = el.timelineStage.getBoundingClientRect();
  state.musicDrag = { musicId: m.id, mode, startX: event.clientX, stageWidth: stageRect.width || Math.max(720, totalDuration()*pxPerSec()), originalStart: Number(m.startTimeOnTimeline || 0), originalTrimStart: Number(m.trimStart || 0), originalTrimEnd: Number(m.trimEnd || musicProjectDuration(m)) };
  updateMusicUi(); syncMusicOptions();
  const move = (ev) => onMusicDragMove(ev);
  const up = () => {
    window.removeEventListener('pointermove', move);
    const dragBlock = document.getElementById(`musicBlock-${m.id}`); if (dragBlock) dragBlock.classList.remove('dragging');
    state.musicDrag = null; holdTimelineViewport(900); clampTimelineToProjectEnd(); updateMusicUi(); preserveTimelineViewport(() => renderTimeline(), 900); renderPlayState();
  };
  try { block?.setPointerCapture?.(event.pointerId); } catch {}
  window.addEventListener('pointermove', move, { passive: false }); window.addEventListener('pointerup', up, { once: true });
}
function onMusicDragMove(event) {
  const drag = state.musicDrag; const m = drag ? getMusicClips().find(x => x.id === drag.musicId) : null; if (!drag || !m) return;
  state.selectedMusicId = m.id; state.musicClip = m;
  const dxSec = (event.clientX - drag.startX) / pxPerSec();
  if (drag.mode === 'move') m.startTimeOnTimeline = Math.max(0, drag.originalStart + dxSec);
  else if (drag.mode === 'left') {
    const originalRight = Number(drag.originalStart || 0) + Math.max(0.1, Number(drag.originalTrimEnd || 0) - Number(drag.originalTrimStart || 0));
    const minLeft = Math.max(0, originalRight - Math.max(0.1, musicProjectDuration(m)));
    const maxLeft = Math.max(minLeft, originalRight - 0.1);
    const newLeft = clamp(Number(drag.originalStart || 0) + dxSec, minLeft, maxLeft);
    m.startTimeOnTimeline = newLeft;
    m.trimStart = clamp(Number(drag.originalTrimStart || 0) + (newLeft - Number(drag.originalStart || 0)), 0, Number(drag.originalTrimEnd || 0) - 0.1);
  } else if (drag.mode === 'right') m.trimEnd = clamp(drag.originalTrimEnd + dxSec, Number(m.trimStart) + 0.1, musicProjectDuration(m));
  ensureMusicClipDefaults(m); holdTimelineViewport(900); clampTimelineToProjectEnd(); updateMusicUi(); scheduleMusicTimelineRefresh();
}


function probeAudio(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const audio = document.createElement('audio');
    audio.preload = 'metadata';
    let done = false;
    const finish = (duration = 30) => {
      if (done) return;
      done = true;
      resolve({ url, duration: Number.isFinite(duration) && duration > 0 ? duration : 30, previewSupported: true });
    };
    audio.onloadedmetadata = () => finish(audio.duration);
    audio.onerror = () => finish(30);
    audio.src = url;
  });
}

function normalizeMusicLibrary(raw) {
  const rows = Array.isArray(raw) ? raw : Array.isArray(raw?.tracks) ? raw.tracks : [];
  return rows.map((item, index) => {
    const url = item.url || item.src || item.file || item.fullUrl || '';
    const title = item.title || item.name || (url ? decodeURIComponent(url.split('/').pop().replace(/\.[a-z0-9]+$/i, '').replace(/[-_]+/g, ' ')) : `Track ${index + 1}`);
    const type = String(item.type || item.length || item.group || '').toLowerCase().includes('short') ? 'short' : String(item.type || item.length || item.group || '').toLowerCase().includes('long') ? 'long' : (String(item.category || '').toLowerCase().includes('short') ? 'short' : 'long');
    const category = String(item.category || item.folder || item.mood || 'uncategorized').replace(/-/g, '_');
    return { id: String(item.id || `lib-${index}-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`), title, name: title, type, category, mood: item.mood || category, bpm: item.bpm || null, duration: Number(item.duration || 0) || null, url, previewUrl: item.previewUrl || item.preview_url || url };
  }).filter(t => t.url);
}

function setMusicLibraryStatus(message, kind = 'muted') {
  if (!el.musicLibraryStatus) return;
  el.musicLibraryStatus.textContent = message;
  el.musicLibraryStatus.classList.toggle('error-text', kind === 'error');
  el.musicLibraryStatus.classList.toggle('ok-text', kind === 'ok');
}

function updateMusicLibraryUi() {
  if (el.musicLibraryUrl && el.musicLibraryUrl.value !== state.musicLibraryUrl) el.musicLibraryUrl.value = state.musicLibraryUrl || '';
  if (!el.musicLibraryBrowser) return;
  const tracks = state.musicLibraryTracks || [];
  el.musicLibraryBrowser.classList.toggle('hidden', !tracks.length);
  if (!tracks.length) { setMusicLibraryStatus(state.musicLibraryUrl ? 'Library URL saved. Test/load it to show tracks.' : 'Library not connected.'); return; }
  const cats = ['all', ...Array.from(new Set(tracks.map(t => t.category || 'uncategorized'))).sort()];
  if (el.musicLibraryCategory) {
    const current = el.musicLibraryCategory.value || 'all';
    el.musicLibraryCategory.innerHTML = cats.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c === 'all' ? 'All categories' : c.replace(/_/g, ' '))}</option>`).join('');
    el.musicLibraryCategory.value = cats.includes(current) ? current : 'all';
  }
  renderMusicLibraryList();
}

function renderMusicLibraryList() {
  if (!el.musicLibraryList) return;
  const q = String(el.musicLibrarySearch?.value || '').trim().toLowerCase();
  const type = el.musicLibraryType?.value || 'all';
  const cat = el.musicLibraryCategory?.value || 'all';
  const tracks = (state.musicLibraryTracks || []).filter(t => {
    if (type !== 'all' && t.type !== type) return false;
    if (cat !== 'all' && t.category !== cat) return false;
    if (q && !`${t.title} ${t.category} ${t.type} ${t.mood || ''}`.toLowerCase().includes(q)) return false;
    return true;
  }).slice(0, 80);
  if (!tracks.length) { el.musicLibraryList.innerHTML = '<div class="muted small">No matching tracks.</div>'; return; }
  el.musicLibraryList.innerHTML = tracks.map(t => `
    <div class="music-library-item" data-track-id="${escapeHtml(t.id)}">
      <div class="music-library-item-head">
        <div class="music-library-title">${escapeHtml(t.title)}</div>
        <div class="music-library-meta">${escapeHtml(t.type)} · ${escapeHtml((t.category || '').replace(/_/g, ' '))}${t.duration ? ` · ${formatTime(t.duration)}` : ''}</div>
      </div>
      <div class="music-library-actions">
        <button class="btn ghost small" data-action="preview-library-track" data-track-id="${escapeHtml(t.id)}">Preview</button>
        <button class="btn small" data-action="add-library-track" data-track-id="${escapeHtml(t.id)}">Add</button>
      </div>
    </div>`).join('');
  el.musicLibraryList.querySelectorAll('[data-action="preview-library-track"]').forEach(btn => btn.addEventListener('click', () => previewLibraryTrack(btn.dataset.trackId)));
  el.musicLibraryList.querySelectorAll('[data-action="add-library-track"]').forEach(btn => btn.addEventListener('click', () => addLibraryTrackToTimeline(btn.dataset.trackId).catch(err => setMusicLibraryStatus('Could not add track: ' + (err?.message || 'unknown error'), 'error'))));
}

async function loadMusicLibraryFromUrl(url) {
  const cleanUrl = String(url || '').trim();
  if (!cleanUrl) { setMusicLibraryStatus('Paste the public music-library.json URL first.', 'error'); return; }
  state.musicLibraryUrl = cleanUrl;
  if (el.musicLibraryUrl) el.musicLibraryUrl.value = cleanUrl;
  localStorage.setItem('britesightMusicLibraryUrl', cleanUrl);
  setMusicLibraryStatus('Loading music library…');
  const res = await fetch(cleanUrl, { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const raw = await res.json();
  state.musicLibraryTracks = normalizeMusicLibrary(raw);
  setMusicLibraryStatus(`Library connected. ${state.musicLibraryTracks.length} tracks loaded.`, 'ok');
  updateMusicLibraryUi();
}

function previewLibraryTrack(trackId) {
  const track = (state.musicLibraryTracks || []).find(t => t.id === trackId);
  if (!track) return;
  if (!state.musicLibraryPreviewAudio) state.musicLibraryPreviewAudio = new Audio();
  const audio = state.musicLibraryPreviewAudio;
  if (state.musicLibraryPreviewId === trackId && !audio.paused) { audio.pause(); state.musicLibraryPreviewId = null; setMusicLibraryStatus('Preview stopped.'); return; }
  try { audio.pause(); } catch {}
  audio.src = track.previewUrl || track.url;
  audio.currentTime = 0;
  audio.volume = 0.8;
  state.musicLibraryPreviewId = trackId;
  audio.play().then(() => setMusicLibraryStatus(`Previewing: ${track.title}`)).catch(() => setMusicLibraryStatus('Preview blocked by browser or missing CORS/access.', 'error'));
}

function probeAudioUrl(url) {
  return new Promise((resolve) => {
    const audio = document.createElement('audio');
    audio.preload = 'metadata';
    let done = false;
    const finish = (duration = 30) => { if (done) return; done = true; resolve(Number.isFinite(duration) && duration > 0 ? duration : 30); };
    audio.onloadedmetadata = () => finish(audio.duration);
    audio.onerror = () => finish(30);
    audio.src = url;
    setTimeout(() => finish(30), 5000);
  });
}

async function addLibraryTrackToTimeline(trackId) {
  const track = (state.musicLibraryTracks || []).find(t => t.id === trackId);
  if (!track) return;
  if (!Array.isArray(state.musicClips)) state.musicClips = [];
  if (state.musicClips.length >= 5) { alert('You can use up to 5 music tracks. Remove one before adding another.'); return; }
  setMusicLibraryStatus(`Adding: ${track.title}…`);
  const duration = track.duration || await probeAudioUrl(track.url);
  const newMusic = { id: makeId(), name: track.title, url: track.url, duration, startTimeOnTimeline: 0, trimStart: 0, trimEnd: duration, volume: state.musicVolume, fadeIn: 0, fadeOut: 0, enabled: true, type: 'library', libraryId: track.id, category: track.category };
  state.musicClips.push(newMusic);
  state.selectedMusicId = newMusic.id;
  state.musicClip = newMusic;
  state.musicTrack = newMusic.name;
  syncMusicOptions();
  render();
  setMusicLibraryStatus(`Added to timeline: ${track.title}`, 'ok');
}

function formatTime(value) {
  const sec = Math.max(0, Number(value) || 0);
  return `${sec.toFixed(1)}s`;
}

function findClipAtTimelineTime(seconds) {
  let cursor = 0;
  for (let i = 0; i < state.clips.length; i += 1) {
    const clip = state.clips[i];
    const len = usableDuration(clip);
    if (seconds <= cursor + len || i === state.clips.length - 1) {
      return { clip, index: i, offset: cursor, local: Math.max(0, Math.min(len, seconds - cursor)) };
    }
    cursor += len;
  }
  return null;
}

function seekTimeline(seconds) {
  const total = clampTimelineToProjectEnd();
  const target = Math.max(0, Math.min(total, Number(seconds) || 0));
  state.currentTimelineTime = target;
  const hit = findClipAtTimelineTime(target);
  if (!hit) { renderPlayState(); return; }
  state.selectedClipId = hit.clip.id;
  state.currentClipIndex = hit.index;
  setPreviewMedia(hit.clip, { localTime: hit.local, applyTransition: true });
  if (hit.clip.type === 'video' && hit.clip.objectUrl && hit.clip.previewSupported) {
    const absoluteTime = videoSourceTimeAtTimelineLocal(hit.clip, hit.local);
    try {
      const activeVideo = getActivePreviewVideo();
      if (activeVideo.dataset.boundSrc !== hit.clip.objectUrl) {
        activeVideo.dataset.boundSrc = hit.clip.objectUrl;
        activeVideo.src = hit.clip.objectUrl;
      }
      activeVideo.pause();
      const setTime = () => {
        try { activeVideo.currentTime = Math.min(absoluteTime, Math.max(0, (activeVideo.duration || hit.clip.duration) - 0.05)); } catch {}
      };
      if (Number.isFinite(activeVideo.duration) && activeVideo.duration > 0) setTime();
      else {
        activeVideo.onloadedmetadata = setTime;
        try { activeVideo.load(); } catch {}
      }
    } catch {}
  }
  applyTransitionVisual(hit.clip, hit.local, true);
  syncMusicToTimeline(true);
  el.previewStatus.textContent = `At ${formatTime(target)}`;
  renderLibrary();
  renderTimeline();
  renderInspector();
  renderPlayState();
}

function updateClip(id, patch) {
  const clip = state.clips.find(c => c.id === id);
  if (!clip) return;
  Object.assign(clip, patch);
  clip.trimStart = Math.max(0, Number(clip.trimStart || 0));
  clip.trimEnd = Math.min(Number(clip.duration || 0), Number(clip.trimEnd || 0));
  if (clip.trimEnd < clip.trimStart + 0.1) clip.trimEnd = Math.min(clip.duration, clip.trimStart + 0.1);
  updateExportUi();
render();
}

const socialExportPresets = {
  custom: { label: 'Custom', format: null, size: null, fps: '30', quality: 'standard', bitrate: 8 },
  'instagram-reels': { label: 'Instagram Reels', format: '9:16', size: '1080', fps: '30', quality: 'high', bitrate: 10 },
  tiktok: { label: 'TikTok', format: '9:16', size: '1080', fps: '30', quality: 'high', bitrate: 10 },
  'youtube-shorts': { label: 'YouTube Shorts', format: '9:16', size: '1080', fps: '30', quality: 'high', bitrate: 10 },
  'facebook-feed': { label: 'Facebook Feed', format: '4:5', size: '1080', fps: '30', quality: 'standard', bitrate: 8 },
};

function outputSizeFor(format, longSide) {
  const size = Number(longSide || 1080);
  if (format === '16:9') return { width: Math.round(size * 16 / 9), height: size };
  if (format === '1:1') return { width: size, height: size };
  if (format === '4:5') return { width: size, height: Math.round(size * 5 / 4) };
  return { width: size, height: Math.round(size * 16 / 9) };
}

function mimeForExport(choice) {
  const mp4s = ['video/mp4;codecs=h264,aac', 'video/mp4'];
  const webms = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'];
  const candidates = choice === 'mp4' ? mp4s : choice === 'webm' ? webms : [...mp4s, ...webms];
  return candidates.find(type => window.MediaRecorder && MediaRecorder.isTypeSupported(type)) || '';
}

function setExportStatus(text) {
  if (el.exportStatus) el.exportStatus.textContent = text;
}

function waitMs(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function safeFetchArrayBuffer(url) {
  try { const res = await fetch(url); if (!res.ok) return null; return await res.arrayBuffer(); } catch { return null; }
}

async function arrayBufferFromMediaItem(item) {
  if (!item) return null;
  try { if (item.file && typeof item.file.arrayBuffer === 'function') return await item.file.arrayBuffer(); } catch {}
  const src = item.objectUrl || item.url || item.src || '';
  if (!src) return null;
  return await safeFetchArrayBuffer(src);
}

async function buildExportAudioStream(totalSeconds) {
  const Ctx = window.AudioContext || window.webkitAudioContext;
  const OfflineCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
  if (!Ctx || !OfflineCtx) return null;
  const sampleRate = 44100;
  const total = Math.max(0.1, Number(totalSeconds || 0.1));
  const offline = new OfflineCtx(2, Math.ceil(total * sampleRate), sampleRate);
  let included = 0;
  let timelineOffset = 0;

  for (const clip of state.clips) {
    const dur = usableDuration(clip);
    if (clip.type === 'video' && clip.previewSupported !== false) {
      const ab = await arrayBufferFromMediaItem(clip);
      if (ab) {
        try {
          const decoded = await offline.decodeAudioData(ab.slice(0));
          const src = offline.createBufferSource();
          src.buffer = decoded;
          const gain = offline.createGain();
          gain.gain.value = clamp(Number(clip.volume || 100) / 100, 0, 1);
          src.connect(gain).connect(offline.destination);
          const offset = clamp(Number(clip.trimStart || 0), 0, Math.max(0, decoded.duration - 0.01));
          const playDur = Math.max(0.01, Math.min(dur, decoded.duration - offset, total - timelineOffset));
          if (playDur > 0) { src.start(Math.max(0, timelineOffset), offset, playDur); included += 1; }
        } catch {}
      }
    }
    timelineOffset += dur;
  }

  for (const m of getMusicClips()) {
    if (!m || m.enabled === false) continue;
    const ab = await arrayBufferFromMediaItem(m);
    if (ab) {
      try {
        const decoded = await offline.decodeAudioData(ab.slice(0));
        const src = offline.createBufferSource();
        src.buffer = decoded;
        const gain = offline.createGain();
        const start = clamp(Number(m.startTimeOnTimeline || 0), 0, total);
        const trimStart = clamp(Number(m.trimStart || 0), 0, Math.max(0, decoded.duration - 0.01));
        const trimEnd = clamp(Number(m.trimEnd || decoded.duration), trimStart + 0.01, decoded.duration);
        const playDur = Math.max(0.01, Math.min(trimEnd - trimStart, total - start, decoded.duration - trimStart));
        const baseGain = clamp(Number(m.volume ?? state.musicVolume ?? 55) / 100, 0, 1);
        gain.gain.setValueAtTime(baseGain, start);
        const fadeIn = Math.max(0, Math.min(Number(m.fadeIn || 0), playDur / 2));
        const fadeOut = Math.max(0, Math.min(Number(m.fadeOut || 0), playDur / 2));
        if (fadeIn > 0) { gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(baseGain, start + fadeIn); }
        if (fadeOut > 0) { gain.gain.setValueAtTime(baseGain, start + Math.max(0, playDur - fadeOut)); gain.gain.linearRampToValueAtTime(0, start + playDur); }
        src.connect(gain).connect(offline.destination);
        src.start(start, trimStart, playDur);
        included += 1;
      } catch {}
    }
  }

  if (!included) return null;
  try {
    const rendered = await offline.startRendering();
    const liveCtx = new Ctx();
    const destination = liveCtx.createMediaStreamDestination();
    const source = liveCtx.createBufferSource();
    source.buffer = rendered;
    source.connect(destination);
    return { stream: destination.stream, context: liveCtx, source, included };
  } catch { return null; }
}

function updateExportUi() {
  if (el.exportBitrateLabel && el.exportBitrate) el.exportBitrateLabel.textContent = `${el.exportBitrate.value} Mbps`;
}

function applySocialPreset(name) {
  const preset = socialExportPresets[name] || socialExportPresets.custom;
  document.querySelectorAll('.social-preset').forEach(btn => btn.classList.toggle('active', btn.dataset.socialPreset === name));
  if (el.exportPresetBadge) el.exportPresetBadge.textContent = preset.label;
  if (preset.format) {
    state.format = preset.format;
    document.querySelectorAll('.format-btn').forEach(b => b.classList.toggle('active', b.dataset.format === state.format));
  }
  if (preset.size && el.exportSize) el.exportSize.value = preset.size;
  if (preset.fps && el.exportFps) el.exportFps.value = preset.fps;
  if (preset.quality && el.exportQuality) el.exportQuality.value = preset.quality;
  if (preset.bitrate && el.exportBitrate) el.exportBitrate.value = preset.bitrate;
  updateExportUi();
  render();
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function loadExportImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

async function loadExportVideo(src) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.muted = true;
    video.playsInline = true;
    video.preload = 'auto';
    video.onloadedmetadata = () => resolve(video);
    video.onerror = reject;
    video.src = src;
    try { video.load(); } catch {}
  });
}

function seekVideo(video, time) {
  return new Promise(resolve => {
    const target = Math.max(0, Number(time || 0));
    let doneOnce = false;
    const done = () => {
      if (doneOnce) return;
      doneOnce = true;
      video.removeEventListener('seeked', done);
      resolve();
    };
    video.addEventListener('seeked', done, { once: true });
    try { video.currentTime = target; } catch { done(); }
    setTimeout(done, 650);
  });
}

function clipAtTimelineTime(time) {
  let offset = 0;
  for (let i = 0; i < state.clips.length; i += 1) {
    const clip = state.clips[i];
    const dur = usableDuration(clip);
    if (time <= offset + dur || i === state.clips.length - 1) return { clip, index: i, local: Math.max(0, time - offset) };
    offset += dur;
  }
  return null;
}

function drawCover(ctx, source, x, y, w, h, zoom = 1, tx = 0, ty = 0) {
  const sw = source.videoWidth || source.naturalWidth || source.width || 1;
  const sh = source.videoHeight || source.naturalHeight || source.height || 1;
  const baseScale = Math.max(w / sw, h / sh) * Math.max(0.1, zoom);
  const dw = sw * baseScale;
  const dh = sh * baseScale;
  const rawDx = x + (w - dw) / 2 + (Number(tx || 0) / 100) * w;
  const rawDy = y + (h - dh) / 2 + (Number(ty || 0) / 100) * h;
  const minDx = x + w - dw;
  const maxDx = x;
  const minDy = y + h - dh;
  const maxDy = y;
  const dx = dw > w ? clamp(rawDx, minDx, maxDx) : x + (w - dw) / 2;
  const dy = dh > h ? clamp(rawDy, minDy, maxDy) : y + (h - dh) / 2;
  ctx.drawImage(source, dx, dy, dw, dh);
}

function canvasFilterForClip(clip, blurPx = 0) {
  return baseMediaFilter(clip, blurPx);
}

async function makeExportSources() {
  const map = new Map();
  for (const clip of state.clips) {
    if (!clip.objectUrl) continue;
    if (clip.type === 'image') map.set(clip.id, await loadExportImage(clip.objectUrl));
    if (clip.type === 'video' && clip.previewSupported !== false) map.set(clip.id, await loadExportVideo(clip.objectUrl));
  }
  return map;
}

async function drawExportFrame(ctx, canvas, hit, sources, clearFirst = true) {
  if (!hit?.clip) {
    if (clearFirst) { ctx.save(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore(); }
    return false;
  }
  const { clip, local } = hit;
  if (isSyntheticClip(clip)) {
    if (clearFirst) { ctx.save(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore(); }
    const visual = transitionVisualAt(clip, local);
    ctx.save();
    ctx.globalAlpha = visual.opacity;
    ctx.filter = Number(visual.blur || 0) > 0 ? 'blur(' + Number(visual.blur || 0).toFixed(2) + 'px)' : 'none';
    ctx.translate((Number(visual.translateX || 0) / 100) * canvas.width, (Number(visual.translateY || 0) / 100) * canvas.height);
    ctx.scale(Number(visual.scale || 1), Number(visual.scale || 1));
    drawSyntheticClip(ctx, canvas, clip, local);
    ctx.restore();
    if (visual.overlayOpacity > 0) { ctx.save(); ctx.fillStyle = visual.overlayColor || '#000'; ctx.globalAlpha = visual.overlayOpacity; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore(); }
    return true;
  }
  const source = sources.get(clip.id);
  if (!source) return false;

  // Seek before clearing, so MediaRecorder never receives blank/black waiting frames.
  if (clip.type === 'video') await seekVideo(source, videoSourceTimeAtTimelineLocal(clip, local));

  if (clearFirst) { ctx.save(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore(); }
  const visual = transitionVisualAt(clip, local);
  ctx.save();
  ctx.globalAlpha = visual.opacity;
  ctx.filter = canvasFilterForClip(clip, visual.blur) || 'none';
  const kb = kenBurnsVisualAt(clip, local);
  const zoom = Number(clip.cropZoom || 1) * Number(visual.scale || 1) * Number(kb.scale || 1);
  drawCover(ctx, source, 0, 0, canvas.width, canvas.height, zoom, Number(clip.cropX || 0) + Number(visual.translateX || 0) + Number(kb.x || 0), Number(clip.cropY || 0) + Number(visual.translateY || 0) + Number(kb.y || 0));
  ctx.restore();
  drawClipTextOverlay(ctx, canvas, clip, local);
  if (visual.overlayOpacity > 0) { ctx.save(); ctx.fillStyle = visual.overlayColor || '#000'; ctx.globalAlpha = visual.overlayOpacity; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore(); }
  return true;
}

async function prepareRealtimeVideoSource(source, clip, local = 0) {
  if (!source || !clip || clip.type !== 'video') return;
  const target = Math.max(0, videoSourceTimeAtTimelineLocal(clip, Number(local || 0)));
  try { source.pause(); } catch {}
  source.muted = true;
  source.playsInline = true;
  source.preload = 'auto';
  await seekVideo(source, target);
  try { source.currentTime = target; } catch {}
  try {
    const p = source.play();
    if (p && typeof p.then === 'function') await p.catch(() => {});
  } catch {}
}

function pauseRealtimeVideoSources(sources) {
  sources?.forEach(source => {
    if (source && source.tagName === 'VIDEO') {
      try { source.pause(); } catch {}
    }
  });
}

async function drawRealtimeExportFrame(ctx, canvas, hit, sources) {
  if (!hit?.clip) {
    ctx.save(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore();
    return false;
  }
  const { clip, local } = hit;
  if (isSyntheticClip(clip)) {
    ctx.save(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore();
    const visual = transitionVisualAt(clip, local);
    ctx.save();
    ctx.globalAlpha = visual.opacity;
    ctx.filter = Number(visual.blur || 0) > 0 ? 'blur(' + Number(visual.blur || 0).toFixed(2) + 'px)' : 'none';
    ctx.translate((Number(visual.translateX || 0) / 100) * canvas.width, (Number(visual.translateY || 0) / 100) * canvas.height);
    ctx.scale(Number(visual.scale || 1), Number(visual.scale || 1));
    drawSyntheticClip(ctx, canvas, clip, local);
    ctx.restore();
    if (visual.overlayOpacity > 0) { ctx.save(); ctx.fillStyle = visual.overlayColor || '#000'; ctx.globalAlpha = visual.overlayOpacity; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore(); }
    return true;
  }
  const source = sources.get(clip.id);
  if (!source) return false;

  ctx.save(); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore();
  const visual = transitionVisualAt(clip, local);
  ctx.save();
  ctx.globalAlpha = visual.opacity;
  ctx.filter = canvasFilterForClip(clip, visual.blur) || 'none';
  const kb = kenBurnsVisualAt(clip, local);
  const zoom = Number(clip.cropZoom || 1) * Number(visual.scale || 1) * Number(kb.scale || 1);
  drawCover(ctx, source, 0, 0, canvas.width, canvas.height, zoom, Number(clip.cropX || 0) + Number(visual.translateX || 0) + Number(kb.x || 0), Number(clip.cropY || 0) + Number(visual.translateY || 0) + Number(kb.y || 0));
  ctx.restore();
  drawClipTextOverlay(ctx, canvas, clip, local);
  if (visual.overlayOpacity > 0) { ctx.save(); ctx.fillStyle = visual.overlayColor || '#000'; ctx.globalAlpha = visual.overlayOpacity; ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore(); }
  return true;
}

async function exportCurrentFrame() {
  if (!state.clips.length) { setExportStatus('Add at least one visual clip first.'); return; }
  const size = outputSizeFor(state.format, Number(el.exportSize?.value || 1080));
  const canvas = document.createElement('canvas');
  canvas.width = size.width;
  canvas.height = size.height;
  const ctx = canvas.getContext('2d');
  const sources = await makeExportSources();
  await drawExportFrame(ctx, canvas, clipAtTimelineTime(state.currentTimelineTime || 0), sources);
  canvas.toBlob(blob => {
    if (!blob) return setExportStatus('Could not export frame.');
    downloadBlob(blob, `${sanitizeFilename(el.projectName.value || 'britesight-frame')}.jpg`);
    setExportStatus(`Frame exported: ${canvas.width}×${canvas.height} JPG`);
  }, 'image/jpeg', 0.92);
}

async function renderVideoExport({ share = false } = {}) {
  if (!state.clips.length) { setExportStatus('Add at least one visual clip first.'); return; }
  if (!window.MediaRecorder) { setExportStatus('This browser does not support video rendering with MediaRecorder.'); return; }
  const mimeType = mimeForExport(el.exportFormat?.value || 'auto');
  if (!mimeType) { setExportStatus('No supported video export codec found in this browser. Try another browser.'); return; }

  const fps = Number(el.exportFps?.value || 30);
  const bitrate = Number(el.exportBitrate?.value || 8) * 1000 * 1000;
  const size = outputSizeFor(state.format, Number(el.exportSize?.value || 1080));
  const total = Math.max(0.1, totalDuration());
  const frameMs = 1000 / Math.max(1, fps);

  const canvas = document.createElement('canvas');
  canvas.width = size.width; canvas.height = size.height;
  const ctx = canvas.getContext('2d');

  setExportStatus('Preparing realtime renderer...');
  const sources = await makeExportSources();

  const firstHit = clipAtTimelineTime(0);

  const stream = canvas.captureStream(fps);
  setExportStatus('Preparing audio...');
  const audioBundle = await buildExportAudioStream(total);

  // Prepare the first video after audio prep, so the source has not already
  // been playing while export setup is still running. This reduces drift/jitter.
  if (firstHit?.clip?.type === 'video') await prepareRealtimeVideoSource(sources.get(firstHit.clip.id), firstHit.clip, firstHit.local);
  await drawRealtimeExportFrame(ctx, canvas, firstHit, sources);
  if (audioBundle?.stream) audioBundle.stream.getAudioTracks().forEach(track => stream.addTrack(track));

  const chunks = [];
  const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: bitrate });
  recorder.ondataavailable = e => { if (e.data?.size) chunks.push(e.data); };
  const stopped = new Promise(resolve => { recorder.onstop = resolve; });

  if (audioBundle?.context?.state === 'suspended') { try { await audioBundle.context.resume(); } catch {} }
  recorder.start(250);
  try { audioBundle?.source?.start(0); } catch {}

  let activeClipId = firstHit?.clip?.id || null;
  const startedAt = performance.now();
  const endAt = startedAt + total * 1000;
  let lastPercent = -1;
  let lastDrawnFrame = -1;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'medium';
  setExportStatus(`Rendering 0% • smooth realtime • ${size.width}×${size.height}${audioBundle ? ' • audio included' : ' • no audio track found'}`);

  // Use requestAnimationFrame for the export paint loop. The previous setTimeout-based
  // loop produced correct duration, but timer jitter could make exported video look choppy.
  // captureStream(fps) samples the canvas at the chosen frame rate, while RAF keeps the
  // canvas visually updated as smoothly as the browser can manage.
  while (performance.now() < endAt) {
    await new Promise(resolve => requestAnimationFrame(resolve));
    const now = performance.now();
    const timelineTime = Math.min(total - 0.001, Math.max(0, (now - startedAt) / 1000));
    const expectedFrame = Math.floor(timelineTime * Math.max(1, fps));
    if (expectedFrame === lastDrawnFrame) continue;
    lastDrawnFrame = expectedFrame;

    const hit = clipAtTimelineTime(timelineTime);
    if (hit?.clip?.id !== activeClipId) {
      const previous = activeClipId ? sources.get(activeClipId) : null;
      if (previous && previous.tagName === 'VIDEO') { try { previous.pause(); } catch {} }
      activeClipId = hit?.clip?.id || null;
      if (hit?.clip?.type === 'video') await prepareRealtimeVideoSource(sources.get(hit.clip.id), hit.clip, hit.local);
    }

    // Soft sync only. Avoid repeated seeking, because that caused blinking and long exports.
    if (hit?.clip?.type === 'video') {
      const video = sources.get(hit.clip.id);
      const desired = videoSourceTimeAtTimelineLocal(hit.clip, hit.local || 0);
      if (video && Number.isFinite(video.currentTime)) {
        const drift = desired - video.currentTime;
        try { video.playbackRate = speedAtTimelineLocal(hit.clip, hit.local || 0); } catch {}
        if (Math.abs(drift) > 0.75) {
          try { video.currentTime = desired; } catch {}
        }
      }
    }

    await drawRealtimeExportFrame(ctx, canvas, hit, sources);
    const percent = Math.min(99, Math.round((timelineTime / total) * 100));
    if (percent !== lastPercent && percent % 5 === 0) {
      lastPercent = percent;
      setExportStatus(`Rendering ${percent}% • smooth realtime • ${size.width}×${size.height}${audioBundle ? ' • audio included' : ' • no audio track found'}`);
    }
  }

  await drawRealtimeExportFrame(ctx, canvas, clipAtTimelineTime(Math.max(0, total - 0.001)), sources);
  setExportStatus(`Finalizing • smooth realtime • ${size.width}×${size.height}${audioBundle ? ' • audio included' : ' • no audio track found'}`);
  await waitMs(150);
  recorder.stop();
  await stopped;
  pauseRealtimeVideoSources(sources);
  stream.getTracks().forEach(track => track.stop());
  try { audioBundle?.source?.stop(); } catch {}
  try { audioBundle?.context?.close(); } catch {}

  const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
  const blob = new Blob(chunks, { type: mimeType });
  const filename = `${sanitizeFilename(el.projectName.value || 'britesight-video')}-${state.format.replace(':','x')}-${size.height}p.${ext}`;
  if (share && navigator.canShare && navigator.share) {
    const file = new File([blob], filename, { type: blob.type });
    if (navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], title: el.projectName.value || 'BriteSight video' }).catch(() => downloadBlob(blob, filename));
      setExportStatus('Share dialog opened.'); return;
    }
  }
  downloadBlob(blob, filename);
  setExportStatus(`Exported ${filename}${audioBundle ? ' with audio.' : ' without audio: no readable audio track was found.'}`);
}

function exportProject() {
  const serializable = {
    projectName: el.projectName.value,
    format: state.format,
    musicTrack: state.musicTrack,
    musicVolume: state.musicVolume,
    musicClips: getMusicClips().map(({ file, ...rest }) => rest),
    globalFilter: state.globalFilter,
    clips: state.clips.map(({ objectUrl, thumb, file, ...rest }) => rest),
  };
  const blob = new Blob([JSON.stringify(serializable, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = sanitizeFilename(el.projectName.value || 'britesight-video-editor-project') + '.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 500);
}

async function readImageThumb(file) {
  return new Promise(resolve => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => resolve(url);
    img.onerror = () => resolve(null);
    img.src = url;
  });
}

async function captureVideoThumbnail(video, seekTime = 0.1) {
  return new Promise((resolve) => {
    let finished = false;
    const cleanup = () => {
      video.removeEventListener('seeked', onSeeked);
      video.removeEventListener('loadeddata', onLoadedData);
      video.removeEventListener('error', onError);
    };
    const done = (value) => {
      if (finished) return;
      finished = true;
      cleanup();
      resolve(value || null);
    };
    const drawFrame = () => {
      try {
        const w = Math.max(1, video.videoWidth || 0);
        const h = Math.max(1, video.videoHeight || 0);
        if (!w || !h) return done(null);
        const canvas = document.createElement('canvas');
        const maxW = 480;
        const scale = Math.min(1, maxW / w);
        canvas.width = Math.max(1, Math.round(w * scale));
        canvas.height = Math.max(1, Math.round(h * scale));
        const ctx = canvas.getContext('2d');
        if (!ctx) return done(null);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        done(canvas.toDataURL('image/jpeg', 0.82));
      } catch {
        done(null);
      }
    };
    const onSeeked = () => setTimeout(drawFrame, 30);
    const onLoadedData = () => {
      try {
        const duration = Number(video.duration) || 0;
        const target = Math.min(Math.max(0, seekTime), Math.max(0, duration - 0.05));
        if (duration <= 0.12 || Math.abs((video.currentTime || 0) - target) < 0.02) setTimeout(drawFrame, 30);
        else video.currentTime = target;
      } catch { done(null); }
    };
    const onError = () => done(null);
    video.addEventListener('seeked', onSeeked);
    video.addEventListener('loadeddata', onLoadedData, { once: true });
    video.addEventListener('error', onError, { once: true });
    setTimeout(() => done(null), 4500);
    try { video.load(); } catch {}
  });
}

async function probeVideo(file) {
  return new Promise(resolve => {
    const url = URL.createObjectURL(file);
    const video = document.createElement('video');
    video.preload = 'auto';
    video.muted = true;
    video.playsInline = true;
    video.src = url;
    let settled = false;
    const finish = (data) => {
      if (settled) return;
      settled = true;
      try { video.pause(); } catch {}
      resolve({ url, ...data });
    };
    video.onloadedmetadata = async () => {
      const duration = Number.isFinite(video.duration) && video.duration > 0 ? Number(video.duration) : 5;
      const safeTime = Math.min(Math.max(0.04, duration * 0.15), Math.max(0.04, duration - 0.05));
      const thumb = await captureVideoThumbnail(video, safeTime);
      finish({ duration, previewSupported: true, thumb: thumb || url, thumbKind: thumb ? 'image' : 'video', supportNote: safariVideoSupportNote(file.name) });
    };
    video.onerror = () => finish({ duration: 5, previewSupported: false, thumb: null, thumbKind: 'none', supportNote: safariVideoSupportNote(file.name) });
    setTimeout(() => finish({ duration: 5, previewSupported: false, thumb: null, thumbKind: 'none', supportNote: safariVideoSupportNote(file.name) }), isSafariBrowser() ? 8000 : 5000);
    try { video.load(); } catch {}
  });
}

function attachVideoThumb(videoEl, clip) {
  if (!videoEl || !clip?.objectUrl) return;
  videoEl.muted = true;
  videoEl.playsInline = true;
  videoEl.preload = 'metadata';
  if (videoEl.dataset.boundSrc !== clip.objectUrl) {
    videoEl.dataset.boundSrc = clip.objectUrl;
    videoEl.src = clip.objectUrl;
  }
  const showFrame = () => {
    try {
      const t = Math.min(Math.max(0.04, Number(clip.trimStart || 0) + 0.04), Math.max(0.04, Number(clip.duration || 0) - 0.05));
      if (Number.isFinite(videoEl.duration) && videoEl.duration > 0) videoEl.currentTime = Math.min(t, Math.max(0.04, videoEl.duration - 0.05));
    } catch {}
  };
  videoEl.addEventListener('loadedmetadata', showFrame, { once: true });
  videoEl.addEventListener('canplay', showFrame, { once: true });
  try { videoEl.load(); } catch {}
}

function setPlaybackTimelineTime(target, options = {}) {
  const total = totalDuration();
  const next = clamp(Number(target || 0), 0, total);
  if (options.force || !state.playing) {
    state.currentTimelineTime = next;
    return state.currentTimelineTime;
  }
  const current = Number(state.currentTimelineTime || 0);
  const tolerance = Number(options.tolerance ?? 0.025);
  if (next + tolerance < current) {
    state.currentTimelineTime = current;
    return state.currentTimelineTime;
  }
  state.currentTimelineTime = next;
  return state.currentTimelineTime;
}

function stopPlayback(message = 'Stopped') {
  state.playToken += 1;
  state.playing = false;
  state.playMode = 'idle';
  state.currentClipIndex = getSelectedIndex();
  state.currentPlaybackClipId = null;
  if (state.timeoutId) {
    clearTimeout(state.timeoutId);
    state.timeoutId = null;
  }
  if (state.transitionRaf) {
    cancelAnimationFrame(state.transitionRaf);
    state.transitionRaf = 0;
  }
  try {
    allPreviewVideos().forEach(v => {
      v.pause();
      v.ontimeupdate = null;
      v.onended = null;
      v.onerror = null;
      v.onseeked = null;
      v.onloadedmetadata = null;
      v.oncanplay = null;
    });
  } catch {}
  pauseAllMusicPlayers(true);
  if (message) el.previewStatus.textContent = message;
  renderPlayState();
}

function startMusicIfAvailable() {
  if (!state.musicClip || !state.musicClip.url) {
    try { musicAudio.pause(); } catch {}
    return;
  }
  syncMusicToTimeline(true);
}

function setPreviewFastMode(enabled) {
  state.previewFastMode = !!enabled;
  el.previewFrame.classList.toggle('preview-fast', !!enabled);
}

function updateSliderValue(label, value, formatter) {
  if (label) label.textContent = formatter(value);
}

function updateMusicTrackBar() { renderTimeline(); }

function queueDeferredRender(delay = 120) {
  if (state.deferredRenderTimer) clearTimeout(state.deferredRenderTimer);
  state.deferredRenderTimer = setTimeout(() => {
    state.deferredRenderTimer = null;
    render();
  }, delay);
}

function queuePreviewRefresh() {
  if (state.previewRenderQueued) return;
  state.previewRenderQueued = true;
  requestAnimationFrame(() => {
    state.previewRenderQueued = false;
    const clip = getSelectedClip();
    if (!clip || state.playing) return;
    setPreviewMedia(clip);
  });
}

function throttleSliderPreviewRefresh() {
  const now = performance.now();
  if (now < state.sliderPreviewThrottleUntil) return;
  state.sliderPreviewThrottleUntil = now + 85;
  queuePreviewRefresh();
}

function getTimelineCardByClipId(clipId) {
  if (!clipId) return null;
  return el.visualTrack ? el.visualTrack.querySelector(`.clip-card[data-clip-id="${clipId}"]`) : null;
}

function throttleTrimSliderPreviewSeek(clip, edge) {
  const now = performance.now();
  if (now < state.sliderPreviewThrottleUntil) return;
  state.sliderPreviewThrottleUntil = now + 95;
  if (!clip) return;
  setPreviewMedia(clip);
  if (clip.type !== 'video' || !clip.objectUrl || !clip.previewSupported) return;
  const target = edge === 'left'
    ? Number(clip.trimStart || 0)
    : Math.max(Number(clip.trimStart || 0), Number(clip.trimEnd || 0) - 0.05);
  try {
    const activeVideo = getActivePreviewVideo();
    if (activeVideo.dataset.boundSrc !== clip.objectUrl) {
      activeVideo.dataset.boundSrc = clip.objectUrl;
      activeVideo.src = clip.objectUrl;
    }
    activeVideo.pause();
    activeVideo.currentTime = Math.max(0, Math.min(target, Math.max(0, (activeVideo.duration || clip.duration || target) - 0.05)));
  } catch {}
}


function primeSafariPreviewFrame(videoEl, clip, sourceTime = 0) {
  if (!videoEl || !clip || clip.type !== 'video') return;
  if (clip.thumb && clip.thumbKind === 'image') {
    try { videoEl.poster = clip.thumb; } catch {}
    try { el.previewMediaLayer.style.background = `#000 center / cover no-repeat url('${clip.thumb}')`; } catch {}
  }
  const target = Math.max(0, Number(sourceTime || 0));
  const applySeek = () => {
    if (state.playing) return;
    try {
      const maxTime = Math.max(0, Number(videoEl.duration || clip.duration || target) - 0.05);
      const safe = Math.min(target, maxTime);
      if (Number.isFinite(safe) && Math.abs(Number(videoEl.currentTime || 0) - safe) > 0.04) videoEl.currentTime = safe;
    } catch {}
  };
  try {
    if (Number(videoEl.readyState || 0) >= 1) applySeek();
    else videoEl.addEventListener('loadedmetadata', applySeek, { once: true });
    const reveal = () => {
      if (state.playing) return;
      try { videoEl.classList.remove('hidden'); } catch {}
    };
    if (Number(videoEl.readyState || 0) >= 2) reveal();
    else {
      videoEl.addEventListener('loadeddata', reveal, { once: true });
      videoEl.addEventListener('canplay', reveal, { once: true });
    }
    if (typeof videoEl.requestVideoFrameCallback === 'function') {
      try { videoEl.requestVideoFrameCallback(() => reveal()); } catch {}
    }
  } catch {}
}

function setPreviewMedia(clip, options = {}) {
  allPreviewVideos().forEach(v => v.classList.add('hidden'));
  el.previewImage.classList.add('hidden');
  if (el.previewSynthetic) el.previewSynthetic.classList.add('hidden');
  el.previewFallback.classList.add('hidden');
  hideLinkedTransitionPeer();
  el.previewMediaLayer.style.background = '#000';

  el.previewName.textContent = clip.name;
  el.previewTypeLabel.textContent = clip.type === 'video' ? 'Video clip' : 'Image clip';
  el.previewZoom.textContent = `Zoom ${Number(clip.cropZoom).toFixed(2)}x`;
  el.previewVolume.textContent = `Vol ${clip.volume}%`;
  if (state.previewFastMode) {
    el.previewStatus.textContent = 'Fast preview while dragging';
  }

  if (isSyntheticClip(clip)) {
    el.previewTypeLabel.textContent = clip.type === 'text' ? 'Text slide' : 'Background';
    el.previewZoom.textContent = 'Text/background';
    el.previewVolume.textContent = 'Vol 0%';
    applySyntheticPreview(clip, Number(options.localTime || 0), !!options.applyTransition);
    return;
  }

  const filter = baseMediaFilter(clip, 0);
  const transform = mediaTransformForClip(clip, {}, Number(options.localTime || 0));

  if (clip.type === 'image' && clip.objectUrl) {
    el.previewImage.src = clip.objectUrl;
    el.previewImage.style.transform = transform;
    el.previewImage.style.filter = filter;
    el.previewImage.style.opacity = '1';
    el.previewImage.classList.remove('hidden');
    applyTransitionVisual(clip, Number(options.localTime || 0), !!options.applyTransition);
    renderPreviewTextOverlay(clip, Number(options.localTime || 0));
    return;
  }

  if (clip.type === 'video') {
    if (clip.thumb && clip.thumbKind === 'image') el.previewMediaLayer.style.background = `#000 center / cover no-repeat url('${clip.thumb}')`;
    if (!clip.previewSupported || !clip.objectUrl) {
      const sub = el.previewFallback?.querySelector('.fallback-sub');
      if (sub) sub.textContent = clip.supportNote || 'This browser cannot decode this video for live preview.';
      el.previewFallback.classList.remove('hidden');
      return;
    }
    const targetVideo = options.targetVideo || getActivePreviewVideo() || el.previewVideoMain;
    configurePreviewVideo(targetVideo, clip);
    targetVideo.preload = 'auto';
    if (clip.thumb && clip.thumbKind === 'image') {
      try { targetVideo.poster = clip.thumb; } catch {}
    }
    if (targetVideo.dataset.boundSrc !== clip.objectUrl) {
      targetVideo.dataset.boundSrc = clip.objectUrl;
      targetVideo.src = clip.objectUrl;
      try { targetVideo.load(); } catch {}
    }
    showPreviewVideo(targetVideo);
    const previewLocal = Number(options.localTime || 0);
    const previewSourceTime = videoSourceTimeAtTimelineLocal(clip, previewLocal);
    primeSafariPreviewFrame(targetVideo, clip, previewSourceTime);
    applyTransitionVisual(clip, previewLocal, !!options.applyTransition);
    renderPreviewTextOverlay(clip, Number(options.localTime || 0));
  }
}

async function playClipIndex(index, token, resumeLocalOffset = 0) {
  if (token !== state.playToken) return;
  const clip = state.clips[index];
  if (!clip) {
    stopPlayback('Reached end of timeline');
    return;
  }

  state.currentClipIndex = index;
  state.currentPlaybackClipId = clip.id;
  state.selectedClipId = clip.id;

  let playbackVideo = el.previewVideo;
  let wasPrewarmedForClip = false;
  let wasPrestartedForClip = false;
  if (clip.type === 'video' && clip.previewSupported && clip.objectUrl) {
    const candidate = allPreviewVideos().find(v => v.dataset.preloadedClipId === clip.id || v.dataset.boundSrc === clip.objectUrl) || getInactivePreviewVideo() || el.previewVideo;
    playbackVideo = candidate;
    wasPrewarmedForClip = playbackVideo.dataset.preloadedClipId === clip.id && playbackVideo.dataset.boundSrc === clip.objectUrl;
    wasPrestartedForClip = playbackVideo.dataset.prestartedClipId === clip.id && playbackVideo.dataset.boundSrc === clip.objectUrl;
    configurePreviewVideo(playbackVideo, clip);
    showPreviewVideo(playbackVideo);
    el.previewName.textContent = clip.name;
    el.previewTypeLabel.textContent = 'Video clip';
    el.previewZoom.textContent = `Zoom ${Number(clip.cropZoom).toFixed(2)}x`;
    el.previewVolume.textContent = `Vol ${clip.volume}%`;
  } else {
    setPreviewMedia(clip);
  }
  refreshPlaybackUi();

  const clipOffset = timelineOffsetForIndex(index);
  const duration = usableDuration(clip);
  const initialTimelineLocal = clamp(Number(resumeLocalOffset || 0), 0, duration);
  setPlaybackTimelineTime(Math.min(totalDuration(), clipOffset + initialTimelineLocal), { force: true });
  renderPlayStateLight();

  if (clip.type === 'image' || isSyntheticClip(clip)) {
    if (isSyntheticClip(clip)) applySyntheticPreview(clip, initialTimelineLocal, true); else { applyTransitionVisual(clip, initialTimelineLocal, true); renderPreviewTextOverlay(clip, initialTimelineLocal); }
    el.previewStatus.textContent = `Showing image ${index + 1}/${state.clips.length}`;
    const startedAt = performance.now() - (initialTimelineLocal * 1000);
    const tick = () => {
      if (token !== state.playToken || !state.playing) return;
      const elapsed = (performance.now() - startedAt) / 1000;
      const local = Math.min(duration, elapsed);
      setPlaybackTimelineTime(Math.min(totalDuration(), clipOffset + local));
      if (isSyntheticClip(clip)) applySyntheticPreview(clip, local, true); else { applyTransitionVisual(clip, local, true); renderPreviewTextOverlay(clip, local); }
      syncMusicToTimelineLight();
      renderPlayStateLight();
      if (elapsed >= duration) {
        playClipIndex(index + 1, token);
      } else {
        state.transitionRaf = requestAnimationFrame(tick);
      }
    };
    tick();
    return;
  }

  if (!clip.previewSupported || !clip.objectUrl) {
    el.previewStatus.textContent = `Skipping unsupported preview: ${clip.name}`;
    setPlaybackTimelineTime(Math.min(totalDuration(), clipOffset + duration), { force: true });
    renderPlayState();
    state.timeoutId = setTimeout(() => playClipIndex(index + 1, token), 120);
    return;
  }

  prewarmUpcomingClip(index);

  const start = Number(clip.trimStart || 0);
  const end = Number(clip.trimEnd || clip.duration || 0);
  ensureSpeedDefaults(clip);
  const requestedStart = clamp(videoSourceTimeAtTimelineLocal(clip, Number(resumeLocalOffset || 0)), start, Math.max(start, end - 0.05));
  const safeStart = Math.max(0, Math.min(requestedStart, Math.max(0, (clip.duration || requestedStart) - 0.05)));
  const targetVolume = clipVolumeScalar(clip);
  const isPrewarmed = wasPrewarmedForClip
    && playbackVideo.dataset.boundSrc === clip.objectUrl
    && Math.abs(Number(playbackVideo.dataset.prewarmedAt || -999) - safeStart) < 0.05
    && Number(playbackVideo.readyState || 0) >= 2;
  const isPrestarted = wasPrestartedForClip
    && playbackVideo.dataset.boundSrc === clip.objectUrl
    && Number(playbackVideo.readyState || 0) >= 2;
  playbackVideo.dataset.preloadedClipId = '';
  let handedOff = false;
  let timelineArmed = false;

  const handoffToNext = () => {
    if (handedOff || token !== state.playToken) return;
    handedOff = true;
    setPlaybackTimelineTime(Math.min(totalDuration(), clipOffset + duration), { force: true });

    const cleanupOldVideo = () => {
      try {
        playbackVideo.ontimeupdate = null;
        playbackVideo.onended = null;
        playbackVideo.onerror = null;
        playbackVideo.onseeked = null;
        playbackVideo.onloadedmetadata = null;
        playbackVideo.oncanplay = null;
        playbackVideo.pause();
        playbackVideo.muted = true;
        setPreviewVideoGain(playbackVideo, 0);
      } catch {}
    };

    if (state.transitionRaf) {
      cancelAnimationFrame(state.transitionRaf);
      state.transitionRaf = 0;
    }
    renderPlayStateLight();

    if (state.playMode === 'selected') {
      cleanupOldVideo();
      stopPlayback(`Selected clip finished: `);
      return;
    }

    // Safari can show a small frozen frame if the outgoing video is paused
    // before the prestarted incoming video is made visible. Start/swap first,
    // then clean up the old element on the next task.
    const nextClip = state.clips[index + 1];
    const nextIsPrestartedVideo = nextClip?.type === 'video'
      && allPreviewVideos().some(v => v !== playbackVideo
        && v.dataset.prestartedClipId === nextClip.id
        && v.dataset.boundSrc === nextClip.objectUrl
        && Number(v.readyState || 0) >= 2);

    playClipIndex(index + 1, token);
    // Keep the outgoing frame alive briefly when the next video still has to seek/play.
    // Safari is more likely than Chromium to display a black/frozen beat if we pause
    // the old element before the incoming element has painted its first frame.
    if (nextIsPrestartedVideo) setTimeout(cleanupOldVideo, 0);
    else setTimeout(cleanupOldVideo, isSafariBrowser() ? 180 : 80);
  };


  const localUpdate = () => {
    if (handedOff || token !== state.playToken || !state.playing || !timelineArmed) return;
    syncActiveClipVolume(clip, { unmute: true });
    const local = timelineLocalFromSourceElapsed(clip, Math.max(0, playbackVideo.currentTime - start));
    setPlaybackTimelineTime(clipOffset + local);
    try { playbackVideo.playbackRate = speedAtTimelineLocal(clip, local); } catch {}
    syncMusicToTimelineLight();
    renderPlayStateLight();
    const remaining = Math.max(0, end - playbackVideo.currentTime);
    if (remaining <= 1.15) prestartUpcomingClip(index, token);
    const threshold = Math.max(start, end - 0.075);
    if (playbackVideo.currentTime >= threshold) handoffToNext();
  };

  const visualLoop = () => {
    if (token !== state.playToken || !state.playing || handedOff) return;
    const local = timelineLocalFromSourceElapsed(clip, Math.max(0, playbackVideo.currentTime - start));
    setPlaybackTimelineTime(clipOffset + local);
    try { playbackVideo.playbackRate = speedAtTimelineLocal(clip, local); } catch {}
    applyTransitionVisual(clip, local, true);
    renderPreviewTextOverlay(clip, local);
    renderPlayStateLight();
    const remaining = Math.max(0, end - playbackVideo.currentTime);
    if (remaining <= 1.15) prestartUpcomingClip(index, token);
    const threshold = Math.max(start, end - 0.075);
    if (playbackVideo.currentTime >= threshold) {
      handoffToNext();
      return;
    }
    state.transitionRaf = requestAnimationFrame(visualLoop);
  };

  const onEnded = () => {
    if (token !== state.playToken) return;
    handoffToNext();
  };

  if (!isPrestarted) playbackVideo.pause();
  playbackVideo.muted = true;
  setPreviewVideoGain(playbackVideo, 0);
  playbackVideo.ontimeupdate = localUpdate;
  playbackVideo.onended = onEnded;
  playbackVideo.onerror = () => {
    if (token !== state.playToken) return;
    handoffToNext();
  };

  const rampUpVolume = () => {
    let step = 0;
    const maxSteps = 5;
    const tick = () => {
      if (token !== state.playToken || !state.playing || handedOff) return;
      step += 1;
      if (step === 1) playbackVideo.muted = false;
      setPreviewVideoGain(playbackVideo, targetVolume * (step / maxSteps));
      if (step < maxSteps) setTimeout(tick, 16);
    };
    tick();
  };

  const startPlaybackAtTrimPoint = () => {
    if (token !== state.playToken || !state.playing) return;
    playbackVideo.onseeked = null;
    playbackVideo.onloadedmetadata = null;
    playbackVideo.oncanplay = null;
    setPreviewVideoGain(playbackVideo, 0);
    playbackVideo.muted = true;
    const initialLocal = timelineLocalFromSourceElapsed(clip, Math.max(0, (playbackVideo.currentTime || safeStart) - start));
    try { playbackVideo.playbackRate = speedAtTimelineLocal(clip, initialLocal); } catch {}
    applyTransitionVisual(clip, initialLocal, true);
    const armVisuals = () => {
      if (token !== state.playToken || !state.playing || handedOff) return;
      timelineArmed = true;
      playbackVideo.dataset.prestartedClipId = '';
      rampUpVolume();
      if (state.transitionRaf) cancelAnimationFrame(state.transitionRaf);
      state.transitionRaf = requestAnimationFrame(visualLoop);
      el.previewStatus.textContent = `${state.playMode === 'timeline' ? 'Timeline' : 'Selected clip'} playing: ${clip.name}`;
    };
    if (isPrestarted && !playbackVideo.paused) {
      armVisuals();
      return;
    }
    playbackVideo.play().then(() => {
      if (Math.abs((playbackVideo.currentTime || 0) - safeStart) > 0.05) {
        try { playbackVideo.currentTime = safeStart; } catch {}
      }
      requestAnimationFrame(armVisuals);
    }).catch(() => {
      el.previewStatus.textContent = 'Playback blocked by browser';
      stopPlayback('Playback blocked by browser');
    });
  };

  const seekToTrimStart = () => {
    try {
      playbackVideo.muted = true;
      setPreviewVideoGain(playbackVideo, 0);
      if (Math.abs((playbackVideo.currentTime || 0) - safeStart) < 0.03) {
        playbackVideo.dataset.prewarmedAt = String(safeStart);
        startPlaybackAtTrimPoint();
        return;
      }
      playbackVideo.onseeked = () => {
        playbackVideo.dataset.prewarmedAt = String(safeStart);
        startPlaybackAtTrimPoint();
      };
      playbackVideo.currentTime = safeStart;
    } catch {
      startPlaybackAtTrimPoint();
    }
  };

  try {
    const alreadyBound = playbackVideo.dataset.boundSrc === clip.objectUrl;
    if (isPrestarted) {
      startPlaybackAtTrimPoint();
    } else if (isPrewarmed) {
      startPlaybackAtTrimPoint();
    } else if (!alreadyBound) {
      playbackVideo.dataset.boundSrc = clip.objectUrl;
      playbackVideo.dataset.prewarmedAt = '';
      playbackVideo.src = clip.objectUrl;
      playbackVideo.onloadedmetadata = seekToTrimStart;
      playbackVideo.oncanplay = seekToTrimStart;
      playbackVideo.load();
    } else if (Number.isFinite(playbackVideo.duration) && playbackVideo.duration > 0) {
      seekToTrimStart();
    } else {
      playbackVideo.onloadedmetadata = seekToTrimStart;
      playbackVideo.oncanplay = seekToTrimStart;
      playbackVideo.load();
    }
  } catch {
    handoffToNext();
  }
}

function playTimeline() {
  if (!state.clips.length) return;
  stopPlayback('');
  state.playToken += 1;
  state.playing = true;
  state.playMode = 'timeline';
  state.currentTimelineTime = 0;
  state.currentClipIndex = 0;
  state.selectedClipId = state.clips[0].id;
  startMusicIfAvailable();
  renderPlayState();
  playClipIndex(0, state.playToken);
}

function playFromCurrentPosition() {
  if (!state.clips.length) return;
  const total = clampTimelineToProjectEnd();
  const target = clamp(Number(state.currentTimelineTime || 0), 0, total);
  const hit = findClipAtTimelineTime(target) || { index: 0, clip: state.clips[0], local: 0 };
  stopPlayback('');
  state.playToken += 1;
  state.playing = true;
  state.playMode = 'timeline';
  state.currentTimelineTime = target;
  state.currentClipIndex = hit.index;
  state.selectedClipId = hit.clip.id;
  startMusicIfAvailable();
  renderPlayState();
  playClipIndex(hit.index, state.playToken, hit.local || 0);
}

function playSelected() {
  const index = getSelectedIndex();
  if (index === -1) return;
  stopPlayback('');
  state.playToken += 1;
  state.playing = true;
  state.playMode = 'selected';
  state.currentTimelineTime = timelineOffsetForIndex(index);
  startMusicIfAvailable();
  renderPlayState();
  playClipIndex(index, state.playToken, 0);
}

function pausePlayback() {
  stopPlayback('Paused');
}

function syncMusicOptions() {
  const clips = getMusicClips();
  const options = ['<option value="None">None</option>'].concat(
    clips.map((m, index) => `<option value="${escapeHtml(m.id)}">Track ${index + 1}: ${escapeHtml(m.name)}</option>`)
  );
  el.musicTrack.innerHTML = options.join('');
  const currentId = state.selectedMusicId && clips.some(m => m.id === state.selectedMusicId) ? state.selectedMusicId : (clips[0]?.id || 'None');
  el.musicTrack.value = currentId;
  state.selectedMusicId = currentId === 'None' ? null : currentId;
  state.musicClip = clips.find(m => m.id === state.selectedMusicId) || null;
  state.musicTrack = state.musicClip ? state.musicClip.name : 'None';
  updateMusicUi();
}


async function importFiles(fileList) {
  const files = [...fileList];
  if (!files.length) return;
  let importedCount = 0;
  const total = files.length;
  setImportProgress({ visible: true, percent: 1, fileName: `${total} file${total === 1 ? '' : 's'} selected`, status: 'Starting import…' });
  await nextFrame();

  for (let i = 0; i < files.length; i += 1) {
    const file = files[i];
    const kind = classifyFile(file);
    const basePct = Math.round((i / total) * 100);
    const fileSize = formatFileSize(file.size);
    if (kind === 'unknown') { setImportProgress({ visible: true, percent: basePct, fileName: file.name, fileSize, status: 'Skipped unsupported file type.' }); await nextFrame(); continue; }
    try {
      setImportProgress({ visible: true, percent: Math.max(2, basePct + 2), fileName: file.name, fileSize, status: kind === 'video' ? 'Loading video file in browser…' : kind === 'image' ? 'Loading image file in browser…' : 'Loading audio file in browser…' });
      await nextFrame();
      if (kind === 'audio') {
        if (!Array.isArray(state.musicClips)) state.musicClips = [];
        if (state.musicClips.length >= 5) { setImportProgress({ visible: true, percent: Math.min(95, basePct + 8), fileName: file.name, fileSize, status: 'Skipped: maximum 5 music tracks.' }); alert('You can use up to 5 music tracks. Remove one before uploading another.'); continue; }
        setImportProgress({ visible: true, percent: Math.min(95, basePct + 25), fileName: file.name, fileSize, status: 'Reading audio metadata…' }); await nextFrame();
        const probe = await probeAudio(file);
        const newMusic = { id: makeId(), name: file.name, url: probe.url, file, duration: probe.duration, startTimeOnTimeline: 0, trimStart: 0, trimEnd: probe.duration, volume: state.musicVolume, fadeIn: 0, fadeOut: 0, enabled: true, type: 'uploaded' };
        state.importedAudio.push(newMusic); state.musicClips.push(newMusic); state.selectedMusicId = newMusic.id; state.musicClip = newMusic; state.musicTrack = file.name; syncMusicOptions(); importedCount += 1;
        setImportProgress({ visible: true, percent: Math.min(99, Math.round(((i + 1) / total) * 100)), fileName: file.name, fileSize, status: 'Music track ready.' }); await nextFrame(); continue;
      }
      const base = { id: makeId(), name: file.name, type: kind, duration: kind === 'image' ? 3 : 5, trimStart: 0, trimEnd: kind === 'image' ? 3 : 5, cropZoom: 1, cropX: 0, cropY: 0, kenBurnsMotion: 'none', kenBurnsStrength: 35, clipSpeed: 1, speedRamp: 'none', speedRampStrength: 'medium', speedRampTiming: 'full', speedRampStart: 0, speedRampEnd: 3, brightness: 0, contrast: 0, saturation: 0, volume: kind === 'video' ? 100 : 0, transitionInType: 'none', transitionOutType: 'none', transitionInDuration: 0, transitionOutDuration: 0, objectUrl: null, thumb: null, thumbKind: 'none', previewSupported: true, file, gradient: defaultGradient(kind) };
      if (kind === 'image') {
        setImportProgress({ visible: true, percent: Math.min(95, basePct + 35), fileName: file.name, fileSize, status: 'Creating image thumbnail…' }); await nextFrame();
        const url = URL.createObjectURL(file); const thumb = await readImageThumb(file); base.objectUrl = url; base.thumb = thumb || url; base.thumbKind = 'image'; state.clips.push(base); state.selectedClipId = base.id; importedCount += 1;
        setImportProgress({ visible: true, percent: Math.min(99, Math.round(((i + 1) / total) * 100)), fileName: file.name, fileSize, status: 'Image ready.' }); await nextFrame(); continue;
      }
      if (kind === 'video') {
        setImportProgress({ visible: true, percent: Math.min(95, basePct + 30), fileName: file.name, fileSize, status: 'Loading video metadata…' }); await nextFrame();
        const probe = await probeVideo(file);
        setImportProgress({ visible: true, percent: Math.min(95, basePct + 75), fileName: file.name, fileSize, status: 'Creating video thumbnail…' }); await nextFrame();
        base.objectUrl = probe.url; base.duration = probe.duration; base.trimEnd = probe.duration; base.previewSupported = probe.previewSupported; base.thumb = probe.thumb || null; base.thumbKind = probe.thumbKind || (probe.thumb ? 'image' : 'none'); base.supportNote = probe.supportNote || ''; state.clips.push(base); state.selectedClipId = base.id; importedCount += 1;
        setImportProgress({ visible: true, percent: Math.min(99, Math.round(((i + 1) / total) * 100)), fileName: file.name, fileSize, status: 'Video ready.' }); await nextFrame(); continue;
      }
    } catch (err) { console.error(err); setImportProgress({ visible: true, percent: Math.max(5, basePct), fileName: file.name, fileSize, status: 'Import failed for this file.', error: true }); await nextFrame(); }
  }
  render();
  finishImportProgress(importedCount ? `Import complete. ${importedCount} file${importedCount === 1 ? '' : 's'} ready.` : 'No files imported.');
}


function beginTrimDrag(event, clipId, edge, card) {
  event.preventDefault();
  event.stopPropagation();
  const clip = state.clips.find(c => c.id === clipId);
  if (!clip) return;
  stopPlayback('');
  state.selectedClipId = clipId;
  renderPreview();
  setPreviewFastMode(true);
  const startX = event.clientX;
  const originalStart = Number(clip.trimStart || 0);
  const originalEnd = Number(clip.trimEnd || clip.duration || 0);
  const originalWidth = Math.max(110, usableDuration(clip) * pxPerSec());
  state.trimDrag = { clipId, edge, card, startX, originalStart, originalEnd, originalWidth, startedAt: performance.now() };
  const move = (ev) => onTrimDragMove(ev);
  const up = (ev) => endTrimDrag(ev, move, up);
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up, { once: true });
}

function updateDraggingCardVisual(card, clip) {
  if (!card || !clip) return;
  card.style.width = Math.max(110, usableDuration(clip) * pxPerSec()) + 'px';
  const sub = card.querySelector('.clip-sub');
  if (sub) sub.innerHTML = `<span>${usableDuration(clip).toFixed(1)}s</span><span>${clip.volume}%</span>`;
}

function trimPreviewSeek(clip, edge) {
  const now = performance.now();
  if (now < state.trimPreviewThrottleUntil) return;
  state.trimPreviewThrottleUntil = now + 90;
  if (!clip) return;
  setPreviewMedia(clip);
  if (clip.type !== 'video' || !clip.objectUrl || !clip.previewSupported) return;
  const target = edge === 'left' ? Number(clip.trimStart || 0) : Math.max(Number(clip.trimStart || 0), Number(clip.trimEnd || 0) - 0.05);
  try {
    const activeVideo = getActivePreviewVideo();
    if (activeVideo.dataset.boundSrc !== clip.objectUrl) {
      activeVideo.dataset.boundSrc = clip.objectUrl;
      activeVideo.src = clip.objectUrl;
    }
    activeVideo.pause();
    const apply = () => {
      try { activeVideo.currentTime = Math.max(0, Math.min(target, Math.max(0, (activeVideo.duration || clip.duration || target) - 0.05))); } catch {}
    };
    if (Number.isFinite(activeVideo.duration) && activeVideo.duration > 0) apply();
    else {
      activeVideo.onloadedmetadata = apply;
      try { activeVideo.load(); } catch {}
    }
  } catch {}
}

function onTrimDragMove(event) {
  const drag = state.trimDrag;
  if (!drag) return;
  const clip = state.clips.find(c => c.id === drag.clipId);
  if (!clip) return;
  const dx = event.clientX - drag.startX;
  const deltaSec = dx / pxPerSec();
  if (drag.edge === 'left') {
    clip.trimStart = Math.max(0, Math.min(drag.originalStart + deltaSec, clip.trimEnd - 0.1));
  } else {
    if (isSyntheticClip(clip)) {
      clip.trimEnd = Math.max(drag.originalEnd + deltaSec, clip.trimStart + 0.1);
      clip.duration = Math.max(Number(clip.duration || 0), clip.trimEnd);
    } else {
      clip.trimEnd = Math.min(Number(clip.duration || 0), Math.max(drag.originalEnd + deltaSec, clip.trimStart + 0.1));
    }
  }
  updateDraggingCardVisual(drag.card, clip);
  trimPreviewSeek(clip, drag.edge);
}

function endTrimDrag(event, move, up) {
  const drag = state.trimDrag;
  window.removeEventListener('pointermove', move);
  if (!drag) return;
  state.trimDrag = null;
  setPreviewFastMode(false);
  state.trimPreviewThrottleUntil = 0;
  render();
}

function renderLibrary() {
  if (!state.clips.length) {
    el.libraryList.innerHTML = '<div class="library-item"><div class="library-meta">Imported clips appear here.</div></div>';
    return;
  }
  el.libraryList.innerHTML = state.clips.map((clip, i) => `
    <div class="library-item">
      <div class="library-name">${i + 1}. ${escapeHtml(clip.name)}</div>
      <div class="library-meta">${clip.type} • ${usableDuration(clip).toFixed(1)}s${clip.previewSupported === false ? ' • preview limited' : (clip.thumb ? ' • thumbnail ready' : '')}</div>
    </div>
  `).join('');
}

function transitionSummary(clip) {
  ensureClipTransitionDefaults(clip);
  const labels = [];
  if (clip.transitionInType !== 'none' && clip.transitionInDuration > 0) labels.push(`${clip.transitionInType} in`);
  if (clip.transitionOutType !== 'none' && clip.transitionOutDuration > 0) labels.push(`${clip.transitionOutType} out`);
  return labels.length ? labels.join(' / ') : `${clip.volume}%`;
}

function renderTimeline() {
  const duration = clampTimelineToProjectEnd();
  const musicEnd = musicEndOnTimeline();
  const visibleDuration = visibleTimelineDuration();
  const musicUsed = musicUsableDuration();
  el.timelineMeta.textContent = `Video: ${duration.toFixed(1)}s • Music used: ${musicUsed.toFixed(1)}s • Music end: ${musicEnd.toFixed(1)}s • Project end: ${duration.toFixed(1)}s (video)`; 
  const stageWidth = Math.max(720, visibleDuration * pxPerSec());
  el.timelineStage.style.width = stageWidth + 'px';
  el.timeRuler.style.setProperty('--tick-width', `${pxPerSec()}px`);
  const ticks = Math.max(6, Math.ceil(visibleDuration) + 1);
  el.timeRuler.innerHTML = Array.from({ length: ticks }, (_, i) => `<div class="ruler-tick">${i}s</div>`).join('');
  el.visualTrack.innerHTML = '';

  const lowQualityTimeline = !!state.timelineZooming;

  state.clips.forEach((clip, index) => {
    const width = Math.max(40, usableDuration(clip) * pxPerSec());
    const card = document.createElement('div');
    const isPlaying = state.playing && index === state.currentClipIndex;
    card.className = 'clip-card' + (clip.id === state.selectedClipId ? ' selected' : '') + (isPlaying ? ' playing' : '');
    card.style.width = width + 'px';
    card.draggable = true;
    card.dataset.clipId = clip.id;
    card.innerHTML = `
      <div class="clip-bg" style="background:${clip.gradient}${!lowQualityTimeline && clip.thumb && clip.thumbKind === 'image' ? `;background-image:url('${clip.thumb}');background-size:cover;background-position:center` : ''}"></div>
      ${!lowQualityTimeline && clip.thumb && clip.thumbKind === 'image' ? `<img class="clip-thumb" src="${clip.thumb}" alt="">` : ''}
      ${!lowQualityTimeline && clip.type === 'video' && clip.objectUrl ? `<video class="clip-thumb-video" muted playsinline preload="metadata"></video>` : ''}
      <div class="clip-shade"></div>
      <div class="clip-trim-handle left"></div>
      <div class="clip-trim-handle right"></div>
      <div class="clip-top">
        <span class="mini-badge">${clip.type === 'video' ? 'Video' : (clip.type === 'text' ? 'Text' : (clip.type === 'background' ? 'Background' : 'Image'))}</span>
        ${clip.previewSupported === false ? '<span class="mini-badge">Preview limited</span>' : ''}
      </div>
      <div class="clip-bottom">
        <div class="clip-title">${escapeHtml(clip.name)}</div>
        <div class="clip-sub"><span>${usableDuration(clip).toFixed(1)}s</span><span>${transitionSummary(clip)}</span></div>
      </div>
    `;

    card.addEventListener('click', (event) => {
      event.stopPropagation();
      if (state.trimDrag) return;
      state.selectedClipId = clip.id;
      render();
    });
    const leftHandle = card.querySelector('.clip-trim-handle.left');
    const rightHandle = card.querySelector('.clip-trim-handle.right');
    if (leftHandle) leftHandle.addEventListener('pointerdown', (event) => beginTrimDrag(event, clip.id, 'left', card));
    if (rightHandle) rightHandle.addEventListener('pointerdown', (event) => beginTrimDrag(event, clip.id, 'right', card));
    card.addEventListener('dragstart', () => {
      state.dragClipId = clip.id;
      card.classList.add('dragging');
      el.timelineDropHint.classList.remove('hidden');
    });
    card.addEventListener('dragend', () => {
      state.dragClipId = null;
      card.classList.remove('dragging');
      [...document.querySelectorAll('.clip-card')].forEach(x => x.classList.remove('drop-target'));
      el.timelineDropHint.classList.add('hidden');
    });
    card.addEventListener('dragover', (e) => {
      e.preventDefault();
      card.classList.add('drop-target');
    });
    card.addEventListener('dragleave', () => card.classList.remove('drop-target'));
    card.addEventListener('drop', (e) => {
      e.preventDefault();
      card.classList.remove('drop-target');
      reorderClip(state.dragClipId, clip.id);
    });

    el.visualTrack.appendChild(card);
    if (clip.type === 'video' && clip.objectUrl) attachVideoThumb(card.querySelector('.clip-thumb-video'), clip);
  });

  const musicClips = getMusicClips();
  if (!musicClips.length) {
    el.musicTrackBar.innerHTML = '<div class="music-placeholder">No music track yet. Upload up to 5 audio files.</div>';
  } else {
    el.musicTrackBar.innerHTML = musicClips.map((m, index) => {
      ensureMusicClipDefaults(m);
      const left = Math.max(0, Number(m.startTimeOnTimeline || 0) * pxPerSec());
      const width = Math.max(24, musicUsableDuration(m) * pxPerSec());
      const top = index * 68;
      return `
      <div class="music-block ${m.id === state.selectedMusicId ? 'selected' : ''}" id="musicBlock-${m.id}" data-music-id="${escapeHtml(m.id)}" style="left:${left}px;width:${width}px;top:${top}px">
        <div class="music-handle left"></div>
        <div class="music-handle right"></div>
        <div class="content">
          <div class="title">Track ${index + 1}: ${escapeHtml(m.name)}</div>
          <div class="meta">${musicUsableDuration(m).toFixed(1)}s • vol ${Number(m.volume).toFixed(0)}% • fades ${Number(m.fadeIn).toFixed(1)}/${Number(m.fadeOut).toFixed(1)}s</div>
        </div>
      </div>`;
    }).join('');
    musicClips.forEach((m) => {
      const block = document.getElementById(`musicBlock-${m.id}`);
      if (block) {
        block.addEventListener('pointerdown', (e) => { if (!e.target.closest('.music-handle')) beginMusicDrag(e, 'move', m.id); });
        block.addEventListener('click', () => { holdTimelineViewport(700); state.selectedMusicId = m.id; state.musicClip = m; syncMusicOptions(); updateMusicUi(); preserveTimelineViewport(() => renderTimeline(), 700); });
        const lh = block.querySelector('.music-handle.left');
        const rh = block.querySelector('.music-handle.right');
        if (lh) lh.addEventListener('pointerdown', (e) => { e.stopPropagation(); beginMusicDrag(e, 'left', m.id); });
        if (rh) rh.addEventListener('pointerdown', (e) => { e.stopPropagation(); beginMusicDrag(e, 'right', m.id); });
      }
    });
  }

  renderPlayState();
}

function renderPreview() {
  el.formatBadge.textContent = state.format;
  el.filterBadge.textContent = state.globalFilter;
  el.previewFrame.className = `preview-frame ratio-${state.format.replace(':','-')}`;

  const clip = getSelectedClip();
  if (!clip) {
    el.previewName.textContent = 'No clip selected';
    el.previewTypeLabel.textContent = 'No clip';
    el.previewZoom.textContent = 'Zoom 1.00x';
    el.previewVolume.textContent = 'Vol 0%';
    el.previewMediaLayer.style.background = '#000';
    allPreviewVideos().forEach(v => v.classList.add('hidden'));
    el.previewImage.classList.add('hidden');
    if (el.previewSynthetic) el.previewSynthetic.classList.add('hidden');
    if (el.previewTextOverlay) el.previewTextOverlay.classList.add('hidden');
    el.previewFallback.classList.add('hidden');
    return;
  }

  if (!state.playing) setPreviewMedia(clip);
}

function renderInspector() {
  const clip = getSelectedClip();
  if (!clip) {
    el.inspectorEmpty.classList.remove('hidden');
    el.inspectorContent.classList.add('hidden');
    if (el.textBackgroundInspector) el.textBackgroundInspector.classList.add('hidden');
    return;
  }
  el.inspectorEmpty.classList.add('hidden');
  el.inspectorContent.classList.remove('hidden');
  ensureSyntheticDefaults(clip);
  el.clipNameLabel.textContent = clip.name;
  el.clipDurationLabel.textContent = `${usableDuration(clip).toFixed(1)}s on timeline`;
  el.clipSupportLabel.textContent = isSyntheticClip(clip) ? 'Generated in the app. Exports without extra source files.' : (clip.previewSupported === false ? (clip.supportNote || 'This clip is imported, but this browser cannot preview this codec/container.') : (clip.supportNote || 'Preview should work in supported browsers.'));
  if (el.textBackgroundInspector) el.textBackgroundInspector.classList.remove('hidden');
  ensureTextDefaults(clip);
  if (el.textInspectorLabel) el.textInspectorLabel.textContent = isSyntheticClip(clip) ? 'Text & background' : 'Text on image/video';
  if (el.clipBgColorWrap) el.clipBgColorWrap.style.display = isSyntheticClip(clip) ? '' : 'none';
  if (el.textOverlayHint) el.textOverlayHint.textContent = isSyntheticClip(clip) ? 'This text belongs to the generated background/text slide.' : 'This text is placed on top of the selected image/video for its full clip duration.';
  {
    if (el.clipText) { el.clipText.value = clip.text || ''; el.clipText.disabled = clip.type === 'background'; }
    if (el.clipFont) el.clipFont.value = clip.fontFamily || 'Inter, Arial, sans-serif';
    if (el.clipTextMotion) el.clipTextMotion.value = clip.textMotion || 'none';
    if (el.clipTextColor) el.clipTextColor.value = clip.textColor || '#ffffff';
    if (el.clipBgColor) el.clipBgColor.value = clip.bgColor || '#111827';
    if (el.clipFontSize) el.clipFontSize.value = clip.fontSize || 56;
  }
  bindRange(el.cropZoom, el.cropZoomValue, clip.cropZoom, v => `${Number(v).toFixed(2)}x`);
  bindRange(el.cropX, el.cropXValue, clip.cropX, v => `${v}`);
  bindRange(el.cropY, el.cropYValue, clip.cropY, v => `${v}`);

  if (el.kenBurnsInspector) {
    const showKb = clip.type === 'image' || clip.type === 'video';
    el.kenBurnsInspector.classList.toggle('hidden', !showKb);
    if (showKb) {
      ensureKenBurnsDefaults(clip);
      if (el.kenBurnsMotion) el.kenBurnsMotion.value = clip.kenBurnsMotion || 'none';
      if (el.kenBurnsStrength) el.kenBurnsStrength.value = String(clip.kenBurnsStrength ?? 35);
    }
  }
  if (el.speedInspector) {
    const showSpeed = clip.type === 'video';
    el.speedInspector.classList.toggle('hidden', !showSpeed);
    if (showSpeed) {
      ensureSpeedDefaults(clip);
      if (el.clipSpeed) el.clipSpeed.value = String(clip.clipSpeed || 1);
      if (el.speedRamp) el.speedRamp.value = clip.speedRamp || 'none';
      if (el.speedRampStrength) el.speedRampStrength.value = clip.speedRampStrength || 'medium';
      if (el.speedRampTiming) el.speedRampTiming.value = clip.speedRampTiming || 'full';
      const isCustomRamp = (clip.speedRampTiming || 'full') === 'custom';
      if (el.speedRampCustomControls) el.speedRampCustomControls.classList.toggle('hidden', !isCustomRamp);
      if (el.speedRampStart) el.speedRampStart.value = String(Number(clip.speedRampStart || 0).toFixed(1));
      if (el.speedRampEnd) el.speedRampEnd.value = String(Number(clip.speedRampEnd || 3).toFixed(1));
    }
  }

  bindRange(el.brightness, el.brightnessValue, clip.brightness, v => `${v}`);
  bindRange(el.contrast, el.contrastValue, clip.contrast, v => `${v}`);
  bindRange(el.saturation, el.saturationValue, clip.saturation, v => `${v}`);
  bindRange(el.volume, el.volumeValue, clip.volume, v => `${v}%`);
  ensureClipTransitionDefaults(clip);
  if (el.transitionInType) el.transitionInType.value = clip.transitionInType;
  if (el.transitionOutType) el.transitionOutType.value = clip.transitionOutType;
  if (el.transitionInDuration) {
    el.transitionInDuration.max = Math.min(3, usableDuration(clip)).toFixed(1);
    bindRange(el.transitionInDuration, el.transitionInDurationValue, clip.transitionInDuration, v => `${Number(v).toFixed(1)}s`);
  }
  if (el.transitionOutDuration) {
    el.transitionOutDuration.max = Math.min(3, usableDuration(clip)).toFixed(1);
    bindRange(el.transitionOutDuration, el.transitionOutDurationValue, clip.transitionOutDuration, v => `${Number(v).toFixed(1)}s`);
  }
  el.trimStart.max = isSyntheticClip(clip) ? 0 : Math.max(0, Number(clip.duration) - 0.1);
  el.trimEnd.max = isSyntheticClip(clip) ? 60 : Math.max(0.2, Number(clip.duration));
  bindRange(el.trimStart, el.trimStartValue, clip.trimStart, v => `${Number(v).toFixed(1)}s`);
  bindRange(el.trimEnd, el.trimEndValue, clip.trimEnd, v => `${Number(v).toFixed(1)}s`);
}

function renderPlayState() {
  if (state.playbackUiRaf) return;
  state.playbackUiRaf = requestAnimationFrame(() => {
    state.playbackUiRaf = 0;
    el.playPauseBtn.textContent = state.playing ? '❚❚' : '▶';
    el.playPauseBtn2.textContent = state.playing ? 'Pause' : 'Play';
    el.playModeBadge.textContent = state.playing ? (state.playMode === 'timeline' ? 'Timeline play' : 'Clip play') : 'Idle';
    const total = clampTimelineToProjectEnd();
    el.timecode.textContent = `${state.currentTimelineTime.toFixed(1)}s / ${total.toFixed(1)}s`;
    el.timelineSeek.max = total.toFixed(2);
    el.timelineSeek.value = Math.max(0, Math.min(total, state.currentTimelineTime)).toFixed(2);
    el.timelineSeekLabel.textContent = formatTime(state.currentTimelineTime);
    const visible = visibleTimelineDuration();
    const stageWidth = Math.max(720, visible * pxPerSec());
    const left = clamp(Number(state.currentTimelineTime || 0) * pxPerSec(), 0, stageWidth);
    if (el.timelinePlayhead) el.timelinePlayhead.style.left = `${left}px`;
    if (el.timelineScroll && el.timelineStage) {
      const viewportLeft = Number(el.timelineScroll.scrollLeft || 0);
      const viewportRight = viewportLeft + Number(el.timelineScroll.clientWidth || 0);
      const margin = 96;
      let targetScroll = null;
      if (left < viewportLeft + margin) targetScroll = Math.max(0, left - margin);
      else if (left > viewportRight - margin) targetScroll = Math.max(0, left - (Number(el.timelineScroll.clientWidth || 0) * 0.5));
      if (targetScroll !== null && shouldAutoScrollTimelineToPlayhead()) {
        const maxScroll = Math.max(0, Number(el.timelineStage.scrollWidth || 0) - Number(el.timelineScroll.clientWidth || 0));
        el.timelineScroll.scrollLeft = clamp(targetScroll, 0, maxScroll);
      }
    }
  });
}


function render() {
  state.projectName = el.projectName.value;
  if (el.musicTrack.value && el.musicTrack.value !== 'None') state.selectedMusicId = el.musicTrack.value;
  state.musicClip = getSelectedMusicClip();
  state.musicTrack = state.musicClip ? state.musicClip.name : 'None';
  state.musicVolume = Number(el.musicVolume.value);
  state.globalFilter = el.globalFilter.value;
  el.musicVolumeLabel.textContent = `${state.musicVolume}%`;
  updateMusicUi();
  renderLibrary();
  renderTimeline();
  renderPreview();
  renderInspector();
  renderPlayState();
}

function bindRange(input, label, value, formatter) {
  input.value = value;
  label.textContent = formatter(value);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function reorderClip(sourceId, targetId) {
  if (!sourceId || !targetId || sourceId === targetId) return;
  const from = state.clips.findIndex(c => c.id === sourceId);
  const to = state.clips.findIndex(c => c.id === targetId);
  if (from === -1 || to === -1) return;
  const [item] = state.clips.splice(from, 1);
  state.clips.splice(to, 0, item);
  render();
}

function splitSelected() {
  const clip = getSelectedClip();
  if (!clip) return;
  const span = usableDuration(clip);
  if (span < 1) return;
  const mid = Number(clip.trimStart) + span / 2;
  const index = state.clips.findIndex(c => c.id === clip.id);
  const first = { ...clip, id: makeId(), trimEnd: mid, name: clip.name + ' A' };
  const second = { ...clip, id: makeId(), trimStart: mid, name: clip.name + ' B' };
  state.clips.splice(index, 1, first, second);
  state.selectedClipId = first.id;
  render();
}

function copySelected() {
  const clip = getSelectedClip();
  if (!clip) return;
  state.clipboard = { ...clip, id: null };
}

function pasteSelected() {
  if (!state.clipboard) return;
  const copy = { ...state.clipboard, id: makeId(), name: state.clipboard.name + ' Copy' };
  const index = state.selectedClipId ? state.clips.findIndex(c => c.id === state.selectedClipId) : state.clips.length - 1;
  state.clips.splice(index + 1, 0, copy);
  state.selectedClipId = copy.id;
  render();
}

function moveSelected(direction) {
  const index = getSelectedIndex();
  if (index === -1) return;
  const target = index + direction;
  if (target < 0 || target >= state.clips.length) return;
  [state.clips[index], state.clips[target]] = [state.clips[target], state.clips[index]];
  render();
}

function deleteSelected() {
  const index = getSelectedIndex();
  if (index === -1) return;
  const [removed] = state.clips.splice(index, 1);
  if (removed?.objectUrl) {
    try { URL.revokeObjectURL(removed.objectUrl); } catch {}
  }
  state.selectedClipId = state.clips[index]?.id || state.clips[index - 1]?.id || null;
  stopPlayback('Clip removed');
  render();
}


function addTextToSelectedClip() {
  const clip = getSelectedClip();
  if (!clip || isSyntheticClip(clip)) {
    addGeneratedClip('text');
    return;
  }
  ensureTextDefaults(clip);
  if (!String(clip.text || '').trim()) clip.text = 'Your text here';
  if (!clip.textMotion || clip.textMotion === 'none') clip.textMotion = 'fade-in';
  render();
  setPreviewMedia(clip);
}

function addGeneratedClip(type) {
  const isText = type === 'text';
  const clip = {
    id: makeId(),
    name: isText ? ('Text slide ' + (state.clips.length + 1)) : ('Blank background ' + (state.clips.length + 1)),
    type,
    duration: 4,
    trimStart: 0,
    trimEnd: 4,
    cropZoom: 1,
    cropX: 0,
    cropY: 0,
    kenBurnsMotion: 'none',
    kenBurnsStrength: 35,
    brightness: 0,
    contrast: 0,
    saturation: 0,
    volume: 0,
    transitionInType: isText ? 'fade' : 'none',
    transitionOutType: 'none',
    transitionInDuration: isText ? 0.4 : 0,
    transitionOutDuration: 0,
    objectUrl: null,
    thumb: null,
    thumbKind: 'none',
    previewSupported: true,
    gradient: defaultGradient(type),
    bgColor: isText ? '#0f172a' : '#111827',
    text: isText ? 'Your text here' : '',
    textColor: '#ffffff',
    fontFamily: 'Inter, Arial, sans-serif',
    fontSize: isText ? 56 : 44,
    textMotion: isText ? 'fade-in' : 'none',
  };
  ensureSyntheticDefaults(clip);
  state.clips.push(clip);
  state.selectedClipId = clip.id;
  stopPlayback('Generated clip added');
  render();
}

function addPlaceholder(type) {
  const clip = {
    id: makeId(),
    name: type === 'video' ? `Video ${state.clips.length + 1}.mp4` : `Image ${state.clips.length + 1}.jpg`,
    type,
    duration: type === 'video' ? 5 : 3,
    trimStart: 0,
    trimEnd: type === 'video' ? 5 : 3,
    cropZoom: 1,
    cropX: 0,
    cropY: 0,
    kenBurnsMotion: 'none',
    kenBurnsStrength: 35,
    brightness: 0,
    contrast: 0,
    saturation: 0,
    volume: type === 'video' ? 100 : 0,
    transitionInType: 'none',
    transitionOutType: 'none',
    transitionInDuration: 0,
    transitionOutDuration: 0,
    objectUrl: null,
    thumb: null,
    previewSupported: false,
    gradient: defaultGradient(type),
  };
  state.clips.push(clip);
  state.selectedClipId = clip.id;
  render();
}

function selectRelativeClip(step) {
  const index = getSelectedIndex();
  if (index === -1) return;
  const target = Math.max(0, Math.min(state.clips.length - 1, index + step));
  state.selectedClipId = state.clips[target].id;
  state.currentClipIndex = target;
  render();
}

function setupEvents() {
  document.querySelectorAll('.format-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      state.format = btn.dataset.format;
      document.querySelectorAll('.format-btn').forEach(b => b.classList.toggle('active', b === btn));
      render();
    });
  });

  el.projectName.addEventListener('input', render);
  el.musicTrack.addEventListener('change', () => { state.selectedMusicId = el.musicTrack.value === 'None' ? null : el.musicTrack.value; state.musicClip = getSelectedMusicClip(); updateMusicUi(); renderTimeline(); syncMusicToTimeline(true); });
  if (el.timelineZoom) {
    el.timelineZoom.value = String(state.timelineZoom);
    if (el.timelineZoomLabel) el.timelineZoomLabel.textContent = `${zoomPercent()}%`;
    let zoomIdle = 0;
    const finishZoom = () => {
      if (zoomIdle) { clearTimeout(zoomIdle); zoomIdle = 0; }
      setTimelineZooming(false);
      renderTimeline();
    };
    el.timelineZoom.addEventListener('input', () => {
      state.timelineZoom = Number(el.timelineZoom.value) || 120;
      if (el.timelineZoomLabel) el.timelineZoomLabel.textContent = `${zoomPercent()}%`;
      setTimelineZooming(true);
      requestTimelineRender();
      if (zoomIdle) clearTimeout(zoomIdle);
      zoomIdle = setTimeout(finishZoom, 120);
    });
    el.timelineZoom.addEventListener('change', finishZoom);
    el.timelineZoom.addEventListener('pointerup', finishZoom);
  }
  if (el.musicInput) el.musicInput.addEventListener('change', async (e) => { await importFiles(e.target.files || []); e.target.value=''; });
  el.musicVolume.addEventListener('input', () => {
    state.musicVolume = Number(el.musicVolume.value);
    const m = getSelectedMusicClip();
    if (m) m.volume = state.musicVolume;
    el.musicVolumeLabel.textContent = `${state.musicVolume}%`;
    syncMusicToTimeline(false);
    updateMusicUi();
    scheduleMusicTimelineRefresh();
  });
  el.musicVolume.addEventListener('change', () => preserveTimelineViewport(() => renderTimeline(), 700));
  if (el.musicFadeIn) el.musicFadeIn.addEventListener('input', () => { const m = getSelectedMusicClip(); if (!m) return; m.fadeIn = Number(el.musicFadeIn.value); updateMusicUi(); syncMusicToTimeline(false); scheduleMusicTimelineRefresh(); });
  if (el.musicFadeIn) el.musicFadeIn.addEventListener('change', () => preserveTimelineViewport(() => renderTimeline(), 700));
  if (el.musicFadeOut) el.musicFadeOut.addEventListener('input', () => { const m = getSelectedMusicClip(); if (!m) return; m.fadeOut = Number(el.musicFadeOut.value); updateMusicUi(); syncMusicToTimeline(false); scheduleMusicTimelineRefresh(); });
  if (el.musicFadeOut) el.musicFadeOut.addEventListener('change', () => preserveTimelineViewport(() => renderTimeline(), 700));

  const applyMusicTimingFields = () => {
    const m = getSelectedMusicClip(); if (!m) return;
    const projectDur = musicProjectDuration(m);
    m.startTimeOnTimeline = Math.max(0, Number(el.musicStartTime?.value || 0));
    m.trimStart = clamp(Number(el.musicTrimStart?.value || 0), 0, Math.max(0, projectDur - 0.1));
    m.trimEnd = clamp(Number(el.musicTrimEnd?.value || projectDur), Number(m.trimStart || 0) + 0.1, projectDur);
    ensureMusicClipDefaults(m); updateMusicUi(); preserveTimelineViewport(() => renderTimeline(), 700); syncMusicToTimeline(true);
  };
  ['musicStartTime','musicTrimStart','musicTrimEnd'].forEach(key => {
    if (el[key]) {
      el[key].addEventListener('input', () => {
        const m = getSelectedMusicClip(); if (!m) return;
        holdTimelineViewport(700);
        const projectDur = musicProjectDuration(m);
        if (key === 'musicStartTime') m.startTimeOnTimeline = Math.max(0, Number(el[key].value || 0));
        if (key === 'musicTrimStart') m.trimStart = clamp(Number(el[key].value || 0), 0, Math.max(0, projectDur - 0.1));
        if (key === 'musicTrimEnd') m.trimEnd = clamp(Number(el[key].value || projectDur), Number(m.trimStart || 0) + 0.1, projectDur);
        ensureMusicClipDefaults(m); updateMusicUi(); scheduleMusicTimelineRefresh();
      });
      el[key].addEventListener('change', applyMusicTimingFields);
    }
  });
  if (el.removeMusicBtn) el.removeMusicBtn.addEventListener('click', () => { const m = getSelectedMusicClip(); if (m) { state.musicClips = getMusicClips().filter(x => x.id !== m.id); state.importedAudio = state.importedAudio.filter(x => x.id !== m.id); const audio = musicAudioPlayers.get(m.id); try { audio?.pause(); } catch {} musicAudioPlayers.delete(m.id); } state.selectedMusicId = state.musicClips[0]?.id || null; state.musicClip = null; state.musicTrack = 'None'; syncMusicOptions(); render(); });

  if (el.musicLibraryUrl) el.musicLibraryUrl.value = state.musicLibraryUrl || '';
  if (el.saveMusicLibraryUrlBtn) el.saveMusicLibraryUrlBtn.addEventListener('click', () => { state.musicLibraryUrl = String(el.musicLibraryUrl?.value || '').trim(); localStorage.setItem('britesightMusicLibraryUrl', state.musicLibraryUrl); updateMusicLibraryUi(); });
  if (el.testMusicLibraryBtn) el.testMusicLibraryBtn.addEventListener('click', () => loadMusicLibraryFromUrl(el.musicLibraryUrl?.value || state.musicLibraryUrl).catch(err => setMusicLibraryStatus('Could not load library. Check URL, CORS and that music-library.json is public. ' + (err?.message || ''), 'error')));
  if (el.clearMusicLibraryBtn) el.clearMusicLibraryBtn.addEventListener('click', () => { try { state.musicLibraryPreviewAudio?.pause(); } catch {} state.musicLibraryUrl = ''; state.musicLibraryTracks = []; localStorage.removeItem('britesightMusicLibraryUrl'); if (el.musicLibraryUrl) el.musicLibraryUrl.value = ''; updateMusicLibraryUi(); });
  if (el.musicLibrarySearch) el.musicLibrarySearch.addEventListener('input', renderMusicLibraryList);
  if (el.musicLibraryType) el.musicLibraryType.addEventListener('change', renderMusicLibraryList);
  if (el.musicLibraryCategory) el.musicLibraryCategory.addEventListener('change', renderMusicLibraryList);
  updateMusicLibraryUi();
  el.globalFilter.addEventListener('change', render);

  el.mediaInput.addEventListener('change', async (e) => {
    await importFiles(e.target.files || []);
    el.mediaInput.value = '';
  });

  ['dragenter', 'dragover'].forEach(evt => {
    el.dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      el.dropZone.classList.add('drag-over');
    });
  });
  ['dragleave', 'drop'].forEach(evt => {
    el.dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      el.dropZone.classList.remove('drag-over');
    });
  });
  el.dropZone.addEventListener('drop', async (e) => {
    const files = e.dataTransfer?.files;
    if (files?.length) await importFiles(files);
  });

  el.exportProjectBtn.addEventListener('click', exportProject);
  if (el.openExportPanelBtn && el.exportPanel) el.openExportPanelBtn.addEventListener('click', () => el.exportPanel.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  document.querySelectorAll('.social-preset').forEach(btn => btn.addEventListener('click', () => applySocialPreset(btn.dataset.socialPreset || 'custom')));
  if (el.exportBitrate) el.exportBitrate.addEventListener('input', updateExportUi);
  if (el.exportQuality) el.exportQuality.addEventListener('change', () => {
    const map = { draft: 4, standard: 8, high: 12, max: 18 };
    if (el.exportBitrate) el.exportBitrate.value = map[el.exportQuality.value] || 8;
    updateExportUi();
  });
  if (el.renderVideoBtn) el.renderVideoBtn.addEventListener('click', () => renderVideoExport({ share: false }).catch(err => setExportStatus('Export failed: ' + (err?.message || 'unknown error'))));
  if (el.shareVideoBtn) el.shareVideoBtn.addEventListener('click', () => renderVideoExport({ share: true }).catch(err => setExportStatus('Share/export failed: ' + (err?.message || 'unknown error'))));
  if (el.exportPosterFrameBtn) el.exportPosterFrameBtn.addEventListener('click', () => exportCurrentFrame().catch(err => setExportStatus('Frame export failed: ' + (err?.message || 'unknown error'))));
  if (el.addVideoBtn) el.addVideoBtn.addEventListener('click', () => addPlaceholder('video'));
  if (el.addImageBtn) el.addImageBtn.addEventListener('click', () => addPlaceholder('image'));
  if (el.addBackgroundBtn) el.addBackgroundBtn.addEventListener('click', () => addGeneratedClip('background'));
  if (el.addTextBtn) el.addTextBtn.addEventListener('click', () => addGeneratedClip('text'));
  if (el.addOverlayTextBtn) el.addOverlayTextBtn.addEventListener('click', () => addTextToSelectedClip());

  const updateSyntheticField = (key, value) => {
    const clip = getSelectedClip();
    if (!clip) return;
    if (key === 'bgColor' && !isSyntheticClip(clip)) return;
    clip[key] = value;
    if (isSyntheticClip(clip)) ensureSyntheticDefaults(clip); else ensureTextDefaults(clip);
    if (key === 'bgColor') clip.gradient = 'linear-gradient(135deg,' + value + ',#000000)';
    setPreviewMedia(clip);
    renderTimeline();
    renderLibrary();
  };
  if (el.clipText) el.clipText.addEventListener('input', () => updateSyntheticField('text', el.clipText.value));
  if (el.clipFont) el.clipFont.addEventListener('change', () => updateSyntheticField('fontFamily', el.clipFont.value));
  if (el.clipTextMotion) el.clipTextMotion.addEventListener('change', () => updateSyntheticField('textMotion', el.clipTextMotion.value));
  if (el.clipTextColor) el.clipTextColor.addEventListener('input', () => updateSyntheticField('textColor', el.clipTextColor.value));
  if (el.clipBgColor) el.clipBgColor.addEventListener('input', () => updateSyntheticField('bgColor', el.clipBgColor.value));
  if (el.clipFontSize) el.clipFontSize.addEventListener('input', () => updateSyntheticField('fontSize', Number(el.clipFontSize.value || 56)));
  const updateKenBurnsField = (key, value) => {
    const clip = getSelectedClip();
    if (!clip || (clip.type !== 'image' && clip.type !== 'video')) return;
    ensureKenBurnsDefaults(clip);
    clip[key] = key === 'kenBurnsStrength' ? Number(value || 35) : value;
    setPreviewMedia(clip, { localTime: 0 });
    renderTimeline();
  };
  if (el.kenBurnsMotion) el.kenBurnsMotion.addEventListener('change', () => updateKenBurnsField('kenBurnsMotion', el.kenBurnsMotion.value));
  if (el.kenBurnsStrength) el.kenBurnsStrength.addEventListener('input', () => updateKenBurnsField('kenBurnsStrength', el.kenBurnsStrength.value));


  const updateSpeedField = (key, value) => {
    const clip = getSelectedClip();
    if (!clip || clip.type !== 'video') return;
    ensureSpeedDefaults(clip);
    if (key === 'clipSpeed' || key === 'speedRampStart' || key === 'speedRampEnd') clip[key] = Number(value || 0);
    else clip[key] = value;
    ensureSpeedDefaults(clip);
    const d = usableDuration(clip);
    if (key === 'speedRampStart') clip.speedRampStart = clamp(Number(clip.speedRampStart || 0), 0, Math.max(0, d - 0.1));
    if (key === 'speedRampEnd') clip.speedRampEnd = clamp(Number(clip.speedRampEnd || 0), Number(clip.speedRampStart || 0) + 0.1, d);
    ensureSpeedDefaults(clip);
    renderInspector();
    renderTimeline();
    renderLibrary();
    setPreviewMedia(clip, { localTime: 0 });
  };
  if (el.clipSpeed) el.clipSpeed.addEventListener('change', () => updateSpeedField('clipSpeed', el.clipSpeed.value));
  if (el.speedRamp) el.speedRamp.addEventListener('change', () => updateSpeedField('speedRamp', el.speedRamp.value));
  if (el.speedRampStrength) el.speedRampStrength.addEventListener('change', () => updateSpeedField('speedRampStrength', el.speedRampStrength.value));
  if (el.speedRampTiming) el.speedRampTiming.addEventListener('change', () => updateSpeedField('speedRampTiming', el.speedRampTiming.value));
  if (el.speedRampStart) el.speedRampStart.addEventListener('input', () => updateSpeedField('speedRampStart', el.speedRampStart.value));
  if (el.speedRampEnd) el.speedRampEnd.addEventListener('input', () => updateSpeedField('speedRampEnd', el.speedRampEnd.value));

  el.splitBtn.addEventListener('click', splitSelected);
  el.copyBtn.addEventListener('click', copySelected);
  el.pasteBtn.addEventListener('click', pasteSelected);
  el.moveLeftBtn.addEventListener('click', () => moveSelected(-1));
  el.moveRightBtn.addEventListener('click', () => moveSelected(1));
  el.deleteBtn.addEventListener('click', deleteSelected);

  el.playTimelineBtn.addEventListener('click', playTimeline);
  el.playSelectedBtn.addEventListener('click', playSelected);
  el.playPauseBtn.addEventListener('click', () => state.playing ? pausePlayback() : playFromCurrentPosition());
  el.playPauseBtn2.addEventListener('click', () => state.playing ? pausePlayback() : playFromCurrentPosition());
  el.prevClipBtn.addEventListener('click', () => selectRelativeClip(-1));
  el.nextClipBtn.addEventListener('click', () => selectRelativeClip(1));
  el.timelineSeek.addEventListener('input', () => seekTimeline(el.timelineSeek.value));
  el.timelineStage.addEventListener('click', (e) => {
    if (e.target.closest('.clip-trim-handle')) return;
    const rect = el.timelineStage.getBoundingClientRect();
    const total = clampTimelineToProjectEnd();
    if (!total || !rect.width) return;
    const scrollLeft = Number(el.timelineScroll?.scrollLeft || 0);
    const x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const timelineX = scrollLeft + x;
    seekTimeline(timelineX / pxPerSec());
  });

  const fastSliderConfigs = [
    [el.cropZoom, el.cropZoomValue, 'cropZoom', (v) => `${Number(v).toFixed(2)}x`],
    [el.cropX, el.cropXValue, 'cropX', (v) => `${v}`],
    [el.cropY, el.cropYValue, 'cropY', (v) => `${v}`],
    [el.brightness, el.brightnessValue, 'brightness', (v) => `${v}`],
    [el.contrast, el.contrastValue, 'contrast', (v) => `${v}`],
    [el.saturation, el.saturationValue, 'saturation', (v) => `${v}`],
    [el.volume, el.volumeValue, 'volume', (v) => `${v}%`],
  ];

  fastSliderConfigs.forEach(([input, label, key, formatter]) => {
    const startFast = () => setPreviewFastMode(true);
    const stopFast = () => {
      state.sliderPreviewThrottleUntil = 0;
      setPreviewFastMode(false);
      queueDeferredRender(40);
    };
    input.addEventListener('pointerdown', startFast);
    input.addEventListener('mousedown', startFast);
    input.addEventListener('touchstart', startFast, { passive: true });
    input.addEventListener('input', () => {
      const clip = getSelectedClip();
      if (!clip) return;
      clip[key] = Number(input.value);
      updateSliderValue(label, clip[key], formatter);
      if (key === 'cropZoom') el.previewZoom.textContent = `Zoom ${Number(clip.cropZoom).toFixed(2)}x`;
      if (key === 'volume') {
        el.previewVolume.textContent = `Vol ${clip.volume}%`;
        try {
          if (state.playing && state.currentPlaybackClipId === clip.id) syncActiveClipVolume(clip, { unmute: true });
          else allPreviewVideos().forEach(v => { setPreviewVideoGain(v, clipVolumeScalar(clip)); });
        } catch {}
        return;
      }
      throttleSliderPreviewRefresh();
    });
    input.addEventListener('change', stopFast);
    input.addEventListener('pointerup', stopFast);
    input.addEventListener('mouseup', stopFast);
    input.addEventListener('touchend', stopFast, { passive: true });
  });

  const startTrimSliderFast = () => setPreviewFastMode(true);
  const stopTrimSliderFast = () => {
    state.sliderPreviewThrottleUntil = 0;
    setPreviewFastMode(false);
    queueDeferredRender(25);
  };
  const onTrimSliderInput = (edge) => {
    const clip = getSelectedClip();
    if (!clip) return;
    if (edge === 'left') {
      const value = Math.min(Number(el.trimStart.value), Number(clip.trimEnd) - 0.1);
      clip.trimStart = Math.max(0, value);
      updateSliderValue(el.trimStartValue, clip.trimStart, v => `${Number(v).toFixed(1)}s`);
    } else {
      const value = Math.max(Number(el.trimEnd.value), Number(clip.trimStart) + 0.1);
      if (isSyntheticClip(clip)) {
        clip.trimEnd = value;
        clip.duration = Math.max(Number(clip.duration || 0), clip.trimEnd);
      } else {
        clip.trimEnd = Math.min(Number(clip.duration || 0), value);
      }
      updateSliderValue(el.trimEndValue, clip.trimEnd, v => `${Number(v).toFixed(1)}s`);
    }
    const card = getTimelineCardByClipId(clip.id);
    updateDraggingCardVisual(card, clip);
    throttleTrimSliderPreviewSeek(clip, edge);
  };
  ['pointerdown', 'mousedown'].forEach(evt => {
    el.trimStart.addEventListener(evt, startTrimSliderFast);
    el.trimEnd.addEventListener(evt, startTrimSliderFast);
  });
  ['touchstart'].forEach(evt => {
    el.trimStart.addEventListener(evt, startTrimSliderFast, { passive: true });
    el.trimEnd.addEventListener(evt, startTrimSliderFast, { passive: true });
  });
  el.trimStart.addEventListener('input', () => onTrimSliderInput('left'));
  el.trimEnd.addEventListener('input', () => onTrimSliderInput('right'));
  ['change', 'pointerup', 'mouseup'].forEach(evt => {
    el.trimStart.addEventListener(evt, stopTrimSliderFast);
    el.trimEnd.addEventListener(evt, stopTrimSliderFast);
  });
  ['touchend'].forEach(evt => {
    el.trimStart.addEventListener(evt, stopTrimSliderFast, { passive: true });
    el.trimEnd.addEventListener(evt, stopTrimSliderFast, { passive: true });
  });


  const transitionSelectHandler = () => {
    const clip = getSelectedClip();
    if (!clip) return;
    clip.transitionInType = el.transitionInType?.value || 'none';
    clip.transitionOutType = el.transitionOutType?.value || 'none';
    ensureClipTransitionDefaults(clip);
    render();
  };
  if (el.transitionInType) el.transitionInType.addEventListener('change', transitionSelectHandler);
  if (el.transitionOutType) el.transitionOutType.addEventListener('change', transitionSelectHandler);
  if (el.transitionInDuration) el.transitionInDuration.addEventListener('input', () => {
    const clip = getSelectedClip();
    if (!clip) return;
    clip.transitionInDuration = Number(el.transitionInDuration.value || 0);
    ensureClipTransitionDefaults(clip);
    if (el.transitionInDurationValue) el.transitionInDurationValue.textContent = clip.transitionInDuration.toFixed(1) + 's';
    renderTimeline();
  });
  if (el.transitionOutDuration) el.transitionOutDuration.addEventListener('input', () => {
    const clip = getSelectedClip();
    if (!clip) return;
    clip.transitionOutDuration = Number(el.transitionOutDuration.value || 0);
    ensureClipTransitionDefaults(clip);
    if (el.transitionOutDurationValue) el.transitionOutDurationValue.textContent = clip.transitionOutDuration.toFixed(1) + 's';
    renderTimeline();
  });
  if (el.transitionInDuration) el.transitionInDuration.addEventListener('change', render);
  if (el.transitionOutDuration) el.transitionOutDuration.addEventListener('change', render);
}

setupEvents();
syncMusicOptions();
render();
window.addEventListener('load', () => requestAnimationFrame(() => renderPreview()));


['pointerdown','mousedown','touchstart','keydown'].forEach(evt => {
  window.addEventListener(evt, resumePreviewAudioContext, { passive: true });
});
