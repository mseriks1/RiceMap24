const MAX_COLLAGE_IMAGES = 40;
const state = {images:[],selectedImage:0,texts:[],selectedText:-1,decos:[],selectedDeco:-1,dragging:false,dragType:null,dragStart:{x:0,y:0},startOffsets:{x:0,y:0},layoutShuffleSeed:1,swapHoverIndex:-1,dragOriginIndex:-1,thumbDragIndex:-1,thumbDropIndex:-1,history:[],redoStack:[],historySuspended:false,pendingDragHistory:false,adjustImageMode:false,customSplitRooms:null,customSplitGuide:null,snapDrawPolygons:null,snapDrawGuide:null};
const els = {
  files:document.getElementById('files'), filesButton:document.getElementById('filesButton'), filesLabel:document.getElementById('filesLabel'), thumbs:document.getElementById('thumbs'),
  imageCount:document.getElementById('imageCount'), layoutStyle:document.getElementById('layoutStyle'), customSplitSection:document.getElementById('customSplitSection'), customSplitDrawMode:document.getElementById('customSplitDrawMode'), customSplitReset:document.getElementById('customSplitReset'), snapDrawSection:document.getElementById('snapDrawSection'), snapDrawMode:document.getElementById('snapDrawMode'), snapDrawReset:document.getElementById('snapDrawReset'),
  oneClickTemplate:document.getElementById('oneClickTemplate'), applyOneClick:document.getElementById('applyOneClick'), shuffleLayout:document.getElementById('shuffleLayout'),
  outW:document.getElementById('outW'), outH:document.getElementById('outH'), gap:document.getElementById('gap'), cornerRadius:document.getElementById('cornerRadius'), shapeInnerSize:document.getElementById('shapeInnerSize'),
  backgroundMode:document.getElementById('backgroundMode'),
  bg:document.getElementById('bg'), bgPreview:document.getElementById('bgPreview'), bgPalette:document.getElementById('bgPalette'),
  bg2:document.getElementById('bg2'), bg2None:document.getElementById('bg2None'), bg2Preview:document.getElementById('bg2Preview'), bg2Palette:document.getElementById('bg2Palette'),
  fitMode:document.getElementById('fitMode'),
  frameColor:document.getElementById('frameColor'), frameColorNone:document.getElementById('frameColorNone'), frameColorPreview:document.getElementById('frameColorPreview'), frameColorPalette:document.getElementById('frameColorPalette'),
  frameWidth:document.getElementById('frameWidth'), themePack:document.getElementById('themePack'), applyThemePack:document.getElementById('applyThemePack'),
  shadowStrength:document.getElementById('shadowStrength'), paperGrain:document.getElementById('paperGrain'),
  zoom:document.getElementById('zoom'), offsetX:document.getElementById('offsetX'), offsetY:document.getElementById('offsetY'), rotation:document.getElementById('rotation'), opacity:document.getElementById('opacity'),
  bringFront:document.getElementById('bringFront'), sendBack:document.getElementById('sendBack'), resetImage:document.getElementById('resetImage'), resetAll:document.getElementById('resetAll'),
  addText:document.getElementById('addText'), removeText:document.getElementById('removeText'), textList:document.getElementById('textList'),
  textPreset:document.getElementById('textPreset'), textContent:document.getElementById('textContent'), fontFamily:document.getElementById('fontFamily'), fontSize:document.getElementById('fontSize'),
  textColor:document.getElementById('textColor'), textColorPreview:document.getElementById('textColorPreview'), textColorPalette:document.getElementById('textColorPalette'),
  textAlign:document.getElementById('textAlign'), textOpacity:document.getElementById('textOpacity'), textX:document.getElementById('textX'), textY:document.getElementById('textY'), textRotation:document.getElementById('textRotation'),
  textShadow:document.getElementById('textShadow'), strokeColor:document.getElementById('strokeColor'), strokeColorNone:document.getElementById('strokeColorNone'), strokeColorPreview:document.getElementById('strokeColorPreview'), strokeColorPalette:document.getElementById('strokeColorPalette'),
  strokeWidth:document.getElementById('strokeWidth'), boldToggle:document.getElementById('boldToggle'), italicToggle:document.getElementById('italicToggle'),
  addTape:document.getElementById('addTape'), addHeart:document.getElementById('addHeart'), addStar:document.getElementById('addStar'), addCircle:document.getElementById('addCircle'),
  removeDeco:document.getElementById('removeDeco'), decoList:document.getElementById('decoList'),
  decoColor:document.getElementById('decoColor'), decoColorNone:document.getElementById('decoColorNone'), decoColorPreview:document.getElementById('decoColorPreview'), decoColorPalette:document.getElementById('decoColorPalette'),
  decoOpacity:document.getElementById('decoOpacity'), decoX:document.getElementById('decoX'), decoY:document.getElementById('decoY'),
  decoW:document.getElementById('decoW'), decoH:document.getElementById('decoH'), decoRotation:document.getElementById('decoRotation'), decoStroke:document.getElementById('decoStroke'),
  applyLayoutDefaults:document.getElementById('applyLayoutDefaults'), renderBtn:document.getElementById('renderBtn'), undoBtn:document.getElementById('undoBtn'), redoBtn:document.getElementById('redoBtn'), downloadBtn:document.getElementById('downloadBtn'), saveProjectBtn:document.getElementById('saveProjectBtn'), openProjectBtn:document.getElementById('openProjectBtn'), openProjectInput:document.getElementById('openProjectInput'),
  previewMode:document.getElementById('previewMode'), previewZoom:document.getElementById('previewZoom'), canvasWrap:document.getElementById('canvasWrap'), canvasScaler:document.getElementById('canvasScaler'),
  canvas:document.getElementById('canvas'), swapOnDrag:document.getElementById('swapOnDrag'), nudgeStep:document.getElementById('nudgeStep'), moveUp:document.getElementById('moveUp'), moveLeft:document.getElementById('moveLeft'), moveRight:document.getElementById('moveRight'), moveDown:document.getElementById('moveDown'), zoomOutBtn:document.getElementById('zoomOutBtn'), zoomInBtn:document.getElementById('zoomInBtn'), centerImageBtn:document.getElementById('centerImageBtn'), adjustImageModeBtn:document.getElementById('adjustImageModeBtn')
};
const ctx = els.canvas.getContext('2d');

const PALETTES = {
  warm: ['#fff7ed','#ffedd5','#fed7aa','#fdba74','#fb923c','#ea580c'],
  soft: ['#fdf2f8','#fce7f3','#f5d0fe','#e9d5ff','#ddd6fe','#ede9fe'],
  neutral: ['#ffffff','#f8fafc','#e5e7eb','#d1d5db','#6b7280','#111827'],
  deep: ['#0f172a','#1d4ed8','#7c3aed','#db2777','#ea580c','#16a34a'],
  pastel: ['#fecdd3','#fde68a','#bbf7d0','#bfdbfe','#ddd6fe','#fbcfe8'],
  text: ['#ffffff','#f8fafc','#111827','#1f2937','#374151','#000000']
};

function roundRectPath(ctx,x,y,w,h,r){const rr=Math.max(0,Math.min(r,Math.min(w,h)/2));ctx.beginPath();ctx.moveTo(x+rr,y);ctx.arcTo(x+w,y,x+w,y+h,rr);ctx.arcTo(x+w,y+h,x,y+h,rr);ctx.arcTo(x,y+h,x,y,rr);ctx.arcTo(x,y,x+w,y,rr);ctx.closePath();}


function pathCircle(ctx,cx,cy,r){ctx.beginPath();ctx.arc(cx,cy,Math.max(0,r),0,Math.PI*2);ctx.closePath();}
function pathPolygon(ctx,points){
  if(!points || !points.length) return;
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for(let i=1;i<points.length;i++) ctx.lineTo(points[i].x, points[i].y);
  ctx.closePath();
}
function pathSector(ctx,cx,cy,r,startAngle,endAngle){
  ctx.beginPath();
  ctx.moveTo(cx,cy);
  ctx.arc(cx,cy,Math.max(0,r),startAngle,endAngle);
  ctx.closePath();
}
function pathRingSector(ctx,cx,cy,rOuter,rInner,startAngle,endAngle){
  const outer=Math.max(0,rOuter);
  const inner=Math.max(0,Math.min(rInner, outer));
  ctx.beginPath();
  ctx.arc(cx,cy,outer,startAngle,endAngle);
  ctx.arc(cx,cy,inner,endAngle,startAngle,true);
  ctx.closePath();
}
function pathRing(ctx,cx,cy,rOuter,rInner){
  const outer=Math.max(0,rOuter);
  const inner=Math.max(0,Math.min(rInner, outer));
  ctx.beginPath();
  ctx.arc(cx,cy,outer,0,Math.PI*2);
  ctx.arc(cx,cy,inner,Math.PI*2,0,true);
  ctx.closePath();
}
function pathForSlot(ctx, slot){
  if(!slot) return;
  if(slot.shape==='circle'){ pathCircle(ctx, slot.cx, slot.cy, slot.r); return; }
  if(slot.shape==='sector'){ pathSector(ctx, slot.cx, slot.cy, slot.r, slot.startAngle, slot.endAngle); return; }
  if(slot.shape==='ringSector'){ pathRingSector(ctx, slot.cx, slot.cy, slot.rOuter, slot.rInner, slot.startAngle, slot.endAngle); return; }
  if(slot.shape==='ring'){ pathRing(ctx, slot.cx, slot.cy, slot.rOuter, slot.rInner); return; }
  if(slot.shape==='polygon'){ pathPolygon(ctx, slot.points); return; }
  roundRectPath(ctx, slot.x, slot.y, slot.w, slot.h, parseInt(els.cornerRadius.value||0,10));
}
function getSlotBounds(slot){
  if(!slot) return {x:0,y:0,w:0,h:0};
  if(slot.shape==='circle') return {x:slot.cx-slot.r, y:slot.cy-slot.r, w:slot.r*2, h:slot.r*2};
  if(slot.shape==='sector') return {x:slot.cx-slot.r, y:slot.cy-slot.r, w:slot.r*2, h:slot.r*2};
  if(slot.shape==='ringSector') return {x:slot.cx-slot.rOuter, y:slot.cy-slot.rOuter, w:slot.rOuter*2, h:slot.rOuter*2};
  if(slot.shape==='ring') return {x:slot.cx-slot.rOuter, y:slot.cy-slot.rOuter, w:slot.rOuter*2, h:slot.rOuter*2};
  if(slot.shape==='polygon'){
    const xs=slot.points.map(p=>p.x), ys=slot.points.map(p=>p.y);
    const minX=Math.min(...xs), maxX=Math.max(...xs), minY=Math.min(...ys), maxY=Math.max(...ys);
    return {x:minX,y:minY,w:maxX-minX,h:maxY-minY};
  }
  return {x:slot.x,y:slot.y,w:slot.w,h:slot.h};
}
function isShapeLayoutStyle(style){
  return ['circleSplit','circleInCircle','triangleSplit3','triangleMosaic','triangleInTriangle','hexagonInHexagon'].includes(style);
}
function getGlobalShapeForStyle(style,w,h,gap){
  const pad=Math.max(18, gap);
  if(style==='circleSplit' || style==='circleInCircle'){
    const r=Math.max(40, Math.min(w,h)/2 - pad);
    return {shape:'circle', cx:w/2, cy:h/2, r};
  }
  if(style==='triangleSplit3' || style==='triangleMosaic' || style==='triangleInTriangle'){
    const points=[
      {x:w/2, y:pad},
      {x:w-pad, y:h-pad},
      {x:pad, y:h-pad}
    ];
    return {shape:'polygon', points};
  }
  if(style==='hexagonInHexagon'){
    const r=Math.max(80, Math.min(w,h)/2 - pad);
    return {shape:'polygon', points:regularPolygonPoints(w/2,h/2,r,6,-Math.PI/2)};
  }
  return null;
}
function clipToGlobalShape(style,w,h,gap){
  const shape=getGlobalShapeForStyle(style,w,h,gap);
  if(!shape) return false;
  ctx.save();
  pathForSlot(ctx, shape);
  ctx.clip();
  return true;
}
function restoreGlobalShapeClip(clipped){
  if(clipped) ctx.restore();
}
function pointInPolygon(pt, points){
  let inside=false;
  for(let i=0,j=points.length-1;i<points.length;j=i++){
    const xi=points[i].x, yi=points[i].y, xj=points[j].x, yj=points[j].y;
    const intersect=((yi>pt.y)!==(yj>pt.y)) && (pt.x < (xj-xi)*(pt.y-yi)/((yj-yi)||1e-9)+xi);
    if(intersect) inside=!inside;
  }
  return inside;
}
function pointInSlot(pt, slot){
  if(!slot) return false;
  if(slot.shape==='circle'){
    const dx=pt.x-slot.cx, dy=pt.y-slot.cy;
    return dx*dx+dy*dy <= slot.r*slot.r;
  }
  if(slot.shape==='sector'){
    const dx=pt.x-slot.cx, dy=pt.y-slot.cy;
    const dist=Math.sqrt(dx*dx+dy*dy);
    if(dist>slot.r) return false;
    let ang=Math.atan2(dy,dx);
    const start=slot.startAngle, end=slot.endAngle;
    if(ang<start) ang+=Math.PI*2;
    let adjEnd=end;
    if(adjEnd<start) adjEnd+=Math.PI*2;
    return ang>=start && ang<=adjEnd;
  }
  if(slot.shape==='ring'){
    const dx=pt.x-slot.cx, dy=pt.y-slot.cy;
    const dist=Math.sqrt(dx*dx+dy*dy);
    return dist<=slot.rOuter && dist>=slot.rInner;
  }
  if(slot.shape==='ringSector'){
    const dx=pt.x-slot.cx, dy=pt.y-slot.cy;
    const dist=Math.sqrt(dx*dx+dy*dy);
    if(dist>slot.rOuter || dist<slot.rInner) return false;
    let ang=Math.atan2(dy,dx);
    const start=slot.startAngle, end=slot.endAngle;
    if(ang<start) ang+=Math.PI*2;
    let adjEnd=end;
    if(adjEnd<start) adjEnd+=Math.PI*2;
    return ang>=start && ang<=adjEnd;
  }
  if(slot.shape==='polygon') return pointInPolygon(pt, slot.points);
  return pt.x>=slot.x&&pt.x<=slot.x+slot.w&&pt.y>=slot.y&&pt.y<=slot.y+slot.h;
}



function serializeImageForHistory(item){
  return {
    name: item.file?.name || 'image',
    type: item.file?.type || 'image/png',
    url: item.url,
    zoom: Number.isFinite(item.zoom) ? item.zoom : 1,
    offsetX: Number.isFinite(item.offsetX) ? item.offsetX : 0,
    offsetY: Number.isFinite(item.offsetY) ? item.offsetY : 0,
    rotation: Number.isFinite(item.rotation) ? item.rotation : 0,
    opacity: Number.isFinite(item.opacity) ? item.opacity : 1,
    freeSlot: item.freeSlot ? {...item.freeSlot} : null
  };
}

function makeHistorySnapshot(){
  return {
    layoutShuffleSeed: state.layoutShuffleSeed,
    selectedImage: state.selectedImage,
    selectedText: state.selectedText,
    selectedDeco: state.selectedDeco,
    settings: getProjectSettings(),
    images: state.images.map(serializeImageForHistory),
    texts: state.texts.map(t=>({...t})),
    decos: state.decos.map(d=>({...d})),
    customSplitRooms: Array.isArray(state.customSplitRooms) ? state.customSplitRooms.map(r=>({...r})) : null,
    snapDrawPolygons: Array.isArray(state.snapDrawPolygons) ? state.snapDrawPolygons.map(poly=>({points:(poly.points||[]).map(pt=>({...pt}))})) : null
  };
}

function getHistorySignature(snapshot){
  return JSON.stringify({
    layoutShuffleSeed: snapshot.layoutShuffleSeed,
    selectedImage: snapshot.selectedImage,
    selectedText: snapshot.selectedText,
    selectedDeco: snapshot.selectedDeco,
    settings: snapshot.settings,
    images: snapshot.images,
    texts: snapshot.texts,
    decos: snapshot.decos,
    customSplitRooms: snapshot.customSplitRooms,
    snapDrawPolygons: snapshot.snapDrawPolygons
  });
}

function refreshUndoRedoButtons(){
  if(els.undoBtn) els.undoBtn.disabled = state.history.length <= 1;
  if(els.redoBtn) els.redoBtn.disabled = state.redoStack.length === 0;
}

function restoreSnapshot(snapshot){
  if(!snapshot) return;
  state.historySuspended = true;
  state.layoutShuffleSeed = Number.isFinite(snapshot.layoutShuffleSeed) ? snapshot.layoutShuffleSeed : 1;
  applyProjectSettings(snapshot.settings || {});
  state.images = (snapshot.images || []).map(rec=>{
    const img = new Image();
    img.src = rec.url || '';
    return {
      file: {name: rec.name || 'image', type: rec.type || 'image/png'},
      url: rec.url,
      img,
      zoom: Number.isFinite(rec.zoom) ? rec.zoom : 1,
      offsetX: Number.isFinite(rec.offsetX) ? rec.offsetX : 0,
      offsetY: Number.isFinite(rec.offsetY) ? rec.offsetY : 0,
      rotation: Number.isFinite(rec.rotation) ? rec.rotation : 0,
      opacity: Number.isFinite(rec.opacity) ? rec.opacity : 1,
      freeSlot: rec.freeSlot ? {...rec.freeSlot} : {x:80,y:80,w:420,h:300,freeform:true}
    };
  });
  state.texts = (snapshot.texts || []).map(t=>({...t}));
  state.decos = (snapshot.decos || []).map(d=>({...d}));
  state.customSplitRooms = Array.isArray(snapshot.customSplitRooms) ? snapshot.customSplitRooms.map(r=>({...r})) : null;
  state.snapDrawPolygons = Array.isArray(snapshot.snapDrawPolygons) ? snapshot.snapDrawPolygons.map(poly=>({points:(poly.points||[]).map(pt=>({...pt}))})) : null;
  state.selectedImage = Math.max(0, Math.min(snapshot.selectedImage || 0, Math.max(state.images.length - 1, 0)));
  state.selectedText = Math.min(Math.max(snapshot.selectedText ?? -1, -1), state.texts.length - 1);
  state.selectedDeco = Math.min(Math.max(snapshot.selectedDeco ?? -1, -1), state.decos.length - 1);
  renderThumbs();
  renderTextList();
  renderDecoList();
  syncImageControls();
  syncTextControls();
  syncDecoControls();
  state.historySuspended = false;
  draw();
}

function commitHistory(clearRedo=true){
  if(state.historySuspended) return;
  const snapshot = makeHistorySnapshot();
  const signature = getHistorySignature(snapshot);
  const last = state.history[state.history.length - 1];
  if(last && last.signature === signature){
    refreshUndoRedoButtons();
    return;
  }
  state.history.push({signature, snapshot});
  if(state.history.length > 80) state.history.shift();
  if(clearRedo) state.redoStack = [];
  refreshUndoRedoButtons();
}

function undoHistory(){
  if(state.history.length <= 1) return;
  const current = state.history.pop();
  state.redoStack.push(current);
  const previous = state.history[state.history.length - 1];
  restoreSnapshot(previous.snapshot);
  refreshUndoRedoButtons();
}

function redoHistory(){
  if(!state.redoStack.length) return;
  const next = state.redoStack.pop();
  state.history.push(next);
  restoreSnapshot(next.snapshot);
  refreshUndoRedoButtons();
}

function commitAfterUiSync(){
  renderThumbs();
  renderTextList();
  renderDecoList();
  syncImageControls();
  syncTextControls();
  syncDecoControls();
  draw();
  commitHistory();
}

function getSelectedNudgeStep(multiplier=1){
  const base = Math.max(1, parseFloat(els.nudgeStep?.value || 10) || 10);
  return base * multiplier;
}

function nudgeSelectedImage(dx, dy){
  const item = state.images[state.selectedImage];
  if(!item) return;
  if(els.layoutStyle.value === 'freeform'){
    item.freeSlot.x += dx;
    item.freeSlot.y += dy;
  } else {
    item.offsetX += dx;
    item.offsetY += dy;
  }
  syncImageControls();
  renderThumbs();
  draw();
  commitHistory();
}

function zoomSelectedImage(delta){
  const item = state.images[state.selectedImage];
  if(!item) return;
  item.zoom = Math.max(0.2, Math.min(4, Math.round((item.zoom + delta) * 100) / 100));
  syncImageControls();
  renderThumbs();
  draw();
  commitHistory();
}

function centerSelectedImage(){
  const item = state.images[state.selectedImage];
  if(!item) return;
  if(els.layoutStyle.value === 'freeform'){
    const w = parseInt(els.outW.value || 1800, 10);
    const h = parseInt(els.outH.value || 1200, 10);
    item.freeSlot.x = Math.round((w - item.freeSlot.w) / 2);
    item.freeSlot.y = Math.round((h - item.freeSlot.h) / 2);
  } else {
    item.offsetX = 0;
    item.offsetY = 0;
  }
  syncImageControls();
  renderThumbs();
  draw();
  commitHistory();
}



function updateAdjustModeUi(){
  if(els.adjustImageModeBtn){
    els.adjustImageModeBtn.textContent = `Adjust image: ${state.adjustImageMode ? 'On' : 'Off'}`;
    els.adjustImageModeBtn.classList.toggle('adjust-on', !!state.adjustImageMode);
  }
  if(els.canvas){
    els.canvas.classList.toggle('adjust-mode', !!state.adjustImageMode);
  }
}

function setAdjustImageMode(on){
  state.adjustImageMode = !!on;
  updateAdjustModeUi();
  draw();
}

function toggleAdjustImageMode(){
  setAdjustImageMode(!state.adjustImageMode);
}

function getProjectSettings(){
  return {
    imageCount: els.imageCount.value,
    layoutStyle: els.layoutStyle.value,
    oneClickTemplate: els.oneClickTemplate.value,
    outW: els.outW.value,
    outH: els.outH.value,
    gap: els.gap.value,
    cornerRadius: els.cornerRadius.value,
    shapeInnerSize: els.shapeInnerSize ? els.shapeInnerSize.value : '0',
    backgroundMode: els.backgroundMode.value,
    bg: els.bg.value,
    bg2: els.bg2.value,
    bg2None: !!(els.bg2None && els.bg2None.checked),
    fitMode: els.fitMode.value,
    frameColor: els.frameColor.value,
    frameColorNone: !!(els.frameColorNone && els.frameColorNone.checked),
    frameWidth: els.frameWidth.value,
    themePack: els.themePack.value,
    shadowStrength: els.shadowStrength.value,
    paperGrain: els.paperGrain.value,
    swapOnDrag: !!(els.swapOnDrag && els.swapOnDrag.checked),
    previewMode: els.previewMode.value,
    previewZoom: els.previewZoom.value,
    adjustImageMode: !!state.adjustImageMode,
    textPreset: els.textPreset.value,
    textColor: els.textColor.value,
    strokeColor: els.strokeColor.value,
    strokeColorNone: !!(els.strokeColorNone && els.strokeColorNone.checked),
    decoColor: els.decoColor.value,
    decoColorNone: !!(els.decoColorNone && els.decoColorNone.checked),
    customSplitDrawMode: !!(els.customSplitDrawMode && els.customSplitDrawMode.checked),
    snapDrawMode: !!(els.snapDrawMode && els.snapDrawMode.checked)
  };
}

function applyProjectSettings(settings={}){
  if(settings.layoutStyle==='centerCircleRing' || settings.layoutStyle==='circleSplit4' || settings.layoutStyle==='circleSplit6') settings.layoutStyle='circleSplit';
  if(settings.layoutStyle==='freeform') settings.layoutStyle='collage';
  const keys = ['imageCount','layoutStyle','oneClickTemplate','outW','outH','gap','cornerRadius','shapeInnerSize','backgroundMode','bg','bg2','fitMode','frameColor','frameWidth','themePack','shadowStrength','paperGrain','previewMode','previewZoom','textPreset','textColor','strokeColor','decoColor'];
  keys.forEach(key=>{ if(settings[key] != null && els[key]) els[key].value = settings[key]; });
  if(els.bg2None) els.bg2None.checked = !!settings.bg2None;
  if(els.frameColorNone) els.frameColorNone.checked = !!settings.frameColorNone;
  if(els.strokeColorNone) els.strokeColorNone.checked = !!settings.strokeColorNone;
  if(els.decoColorNone) els.decoColorNone.checked = !!settings.decoColorNone;
  if(els.swapOnDrag) els.swapOnDrag.checked = settings.swapOnDrag !== false;
  if(els.customSplitDrawMode) els.customSplitDrawMode.checked = !!settings.customSplitDrawMode;
  if(els.snapDrawMode) els.snapDrawMode.checked = !!settings.snapDrawMode;
  setAdjustImageMode(!!settings.adjustImageMode);
  updateCustomSplitUi();
  updateSnapDrawUi();
  updateColorPreviews();
  updatePreviewScale();
}

async function imageUrlToDataUrl(url){
  if(!url) return null;
  if(/^data:/i.test(url)) return url;
  const response = await fetch(url);
  const blob = await response.blob();
  return await new Promise((resolve, reject)=>{
    const reader = new FileReader();
    reader.onload = ()=> resolve(reader.result);
    reader.onerror = ()=> reject(new Error('Could not read image data.'));
    reader.readAsDataURL(blob);
  });
}

async function serializeImageItem(item){
  return {
    name: item.file?.name || 'image',
    type: item.file?.type || 'image/png',
    url: await imageUrlToDataUrl(item.url),
    zoom: item.zoom,
    offsetX: item.offsetX,
    offsetY: item.offsetY,
    rotation: item.rotation,
    opacity: item.opacity,
    freeSlot: item.freeSlot ? {...item.freeSlot} : null
  };
}

async function serializeProject(){
  return {
    app: 'Collage Maker Pro',
    version: 37,
    exportedAt: new Date().toISOString(),
    layoutShuffleSeed: state.layoutShuffleSeed,
    selectedImage: state.selectedImage,
    selectedText: state.selectedText,
    selectedDeco: state.selectedDeco,
    settings: getProjectSettings(),
    images: await Promise.all(state.images.map(serializeImageItem)),
    texts: state.texts.map(t=>({...t})),
    decos: state.decos.map(d=>({...d})),
    customSplitRooms: Array.isArray(state.customSplitRooms) ? state.customSplitRooms.map(r=>({...r})) : null,
    snapDrawPolygons: Array.isArray(state.snapDrawPolygons) ? state.snapDrawPolygons.map(poly=>({points:(poly.points||[]).map(pt=>({...pt}))})) : null
  };
}

function downloadTextFile(filename, text, mime='application/json'){
  const blob = new Blob([text], {type: mime});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(()=>URL.revokeObjectURL(url), 2000);
}

async function saveProject(){
  try {
    if(els.saveProjectBtn) {
      els.saveProjectBtn.disabled = true;
      els.saveProjectBtn.textContent = 'Saving...';
    }
    const project = await serializeProject();
    const safeStyle = (els.layoutStyle.value || 'collage').replace(/[^a-z0-9_-]+/gi,'-').toLowerCase();
    downloadTextFile(`collage-project-${safeStyle}.collage`, JSON.stringify(project, null, 2), 'application/json');
  } catch(err) {
    console.error(err);
    alert('The project could not be saved.');
  } finally {
    if(els.saveProjectBtn) {
      els.saveProjectBtn.disabled = false;
      els.saveProjectBtn.textContent = 'Save project';
    }
  }
}

function loadImageRecord(record){
  return new Promise((resolve, reject)=>{
    const img = new Image();
    img.onload = ()=> resolve({
      file: {name: record.name || 'image', type: record.type || 'image/png'},
      url: record.url,
      img,
      zoom: Number.isFinite(record.zoom) ? record.zoom : 1,
      offsetX: Number.isFinite(record.offsetX) ? record.offsetX : 0,
      offsetY: Number.isFinite(record.offsetY) ? record.offsetY : 0,
      rotation: Number.isFinite(record.rotation) ? record.rotation : 0,
      opacity: Number.isFinite(record.opacity) ? record.opacity : 1,
      freeSlot: record.freeSlot ? {...record.freeSlot} : {x:80,y:80,w:420,h:300,freeform:true}
    });
    img.onerror = ()=> reject(new Error(`Could not load image: ${record.name || 'image'}`));
    img.src = record.url || record.dataUrl || '';
  });
}

async function openProjectFile(file){
  if(!file) return;
  const text = await file.text();
  let project;
  try { project = JSON.parse(text); }
  catch(err){ alert('This project file could not be opened.'); return; }
  if(!project || !Array.isArray(project.images)) { alert('This file is not a valid collage project.'); return; }

  const loadedImages = [];
  for(const rec of project.images){
    try { loadedImages.push(await loadImageRecord(rec)); }
    catch(err){ console.error(err); }
  }
  if(!loadedImages.length && project.images.length){
    alert('The project opened, but the images could not be restored.');
  }

  state.images = loadedImages;
  state.texts = Array.isArray(project.texts) ? project.texts.map(t=>({...t})) : [];
  state.decos = Array.isArray(project.decos) ? project.decos.map(d=>({...d})) : [];
  state.layoutShuffleSeed = Number.isFinite(project.layoutShuffleSeed) ? project.layoutShuffleSeed : 1;
  state.customSplitRooms = Array.isArray(project.customSplitRooms) ? project.customSplitRooms.map(r=>({...r})) : null;
  state.snapDrawPolygons = Array.isArray(project.snapDrawPolygons) ? project.snapDrawPolygons.map(poly=>({points:(poly.points||[]).map(pt=>({...pt}))})) : null;
  state.selectedImage = Math.max(0, Math.min(project.selectedImage || 0, Math.max(loadedImages.length - 1, 0)));
  state.selectedText = Math.min(Math.max(project.selectedText ?? -1, -1), state.texts.length - 1);
  state.selectedDeco = Math.min(Math.max(project.selectedDeco ?? -1, -1), state.decos.length - 1);

  applyProjectSettings(project.settings || {});
  renderThumbs();
  renderTextList();
  renderDecoList();
  syncImageControls();
  syncTextControls();
  syncDecoControls();
  if(els.filesLabel) els.filesLabel.textContent = loadedImages.length ? `${loadedImages.length} project image${loadedImages.length===1?'':'s'} loaded` : 'Project opened';
  draw();
  state.history = [];
  state.redoStack = [];
  commitHistory(false);
}

function getMaybeColor(inputEl, noneEl){
  return (noneEl && noneEl.checked) ? 'transparent' : inputEl.value;
}

function renderPalette(container,inputEl,colors,noneEl){
  if(!container||!inputEl) return; 
  container.innerHTML='';

  if(noneEl){
    const noneBtn=document.createElement('button');
    noneBtn.type='button';
    noneBtn.className='swatch none-swatch' + (noneEl.checked ? ' active' : '');
    noneBtn.title='No color';
    noneBtn.addEventListener('click',()=>{
      noneEl.checked = true;
      updateColorPreviews();
      if(inputEl===els.strokeColor){updateSelectedTextFromControls();}
      else if(inputEl===els.decoColor){updateSelectedDecoFromControls();}
      else {draw();}
    });
    container.appendChild(noneBtn);
  }

  colors.forEach(color=>{
    const btn=document.createElement('button');
    btn.type='button';
    const active = (!noneEl || !noneEl.checked) && inputEl.value.toLowerCase()===color.toLowerCase();
    btn.className='swatch'+(active?' active':'');
    btn.style.background=color; 
    btn.title=color;
    btn.addEventListener('click',()=>{
      if(noneEl) noneEl.checked = false;
      inputEl.value=color; 
      updateColorPreviews();
      if(inputEl===els.textColor||inputEl===els.strokeColor){updateSelectedTextFromControls();}
      else if(inputEl===els.decoColor){updateSelectedDecoFromControls();}
      else {draw();}
    }); 
    container.appendChild(btn);
  });
}
function updateColorPreviews(){
  els.bgPreview.style.background=els.bg.value; 
  els.bg2Preview.style.background=getMaybeColor(els.bg2, els.bg2None);
  els.frameColorPreview.style.background=getMaybeColor(els.frameColor, els.frameColorNone);
  els.textColorPreview.style.background=els.textColor.value; 
  els.strokeColorPreview.style.background=getMaybeColor(els.strokeColor, els.strokeColorNone); 
  els.decoColorPreview.style.background=getMaybeColor(els.decoColor, els.decoColorNone);

  renderPalette(els.bgPalette,els.bg,PALETTES.warm.concat(PALETTES.soft.slice(0,2)));
  renderPalette(els.bg2Palette,els.bg2,PALETTES.soft.concat(PALETTES.pastel.slice(0,2)), els.bg2None);
  renderPalette(els.frameColorPalette,els.frameColor,PALETTES.neutral, els.frameColorNone);
  renderPalette(els.textColorPalette,els.textColor,PALETTES.text);
  renderPalette(els.strokeColorPalette,els.strokeColor,PALETTES.text, els.strokeColorNone);
  renderPalette(els.decoColorPalette,els.decoColor,PALETTES.pastel.concat(PALETTES.deep.slice(1,3)), els.decoColorNone);
}

function applyThemePack(){
  const t = els.themePack.value;
  if(t==='warmMemory'){els.backgroundMode.value='gradient';els.bg.value='#fff7ed';els.bg2.value='#f5e9ff';els.frameColor.value='#fffaf5';els.frameWidth.value=10;els.shadowStrength.value=18;els.paperGrain.value=10;els.decoColor.value='#f9a8d4';els.textColor.value='#ffffff';els.strokeColor.value='#7c2d12';}
  else if(t==='cleanModern'){els.backgroundMode.value='solid';els.bg.value='#f8fafc';els.bg2.value='#e2e8f0';els.frameColor.value='#ffffff';els.frameWidth.value=6;els.shadowStrength.value=10;els.paperGrain.value=0;els.decoColor.value='#93c5fd';els.textColor.value='#111827';els.strokeColor.value='#ffffff';}
  else if(t==='romantic'){els.backgroundMode.value='gradient';els.bg.value='#fdf2f8';els.bg2.value='#f5d0fe';els.frameColor.value='#fff1f2';els.frameWidth.value=10;els.shadowStrength.value=16;els.paperGrain.value=6;els.decoColor.value='#fb7185';els.textColor.value='#ffffff';els.strokeColor.value='#881337';}
  else if(t==='vintageScrapbook'){els.backgroundMode.value='paper';els.bg.value='#f5efe1';els.bg2.value='#e7dcc5';els.frameColor.value='#fffaf0';els.frameWidth.value=12;els.shadowStrength.value=20;els.paperGrain.value=28;els.decoColor.value='#d97706';els.textColor.value='#3f2f1d';els.strokeColor.value='#fffaf0';}
  else if(t==='minimalBW'){els.backgroundMode.value='solid';els.bg.value='#ffffff';els.bg2.value='#f3f4f6';els.frameColor.value='#111827';els.frameWidth.value=4;els.shadowStrength.value=8;els.paperGrain.value=0;els.decoColor.value='#111827';els.textColor.value='#111827';els.strokeColor.value='#ffffff';}
  if(els.bg2None) els.bg2None.checked = false;
  if(els.frameColorNone) els.frameColorNone.checked = false;
  if(els.strokeColorNone) els.strokeColorNone.checked = false;
  if(els.decoColorNone) els.decoColorNone.checked = false;
  if(els.bg2None) els.bg2None.checked = false;
  if(els.frameColorNone) els.frameColorNone.checked = false;
  if(els.strokeColorNone) els.strokeColorNone.checked = false;
  if(els.decoColorNone) els.decoColorNone.checked = false;
  updateColorPreviews(); draw();
}

function applyOneClickTemplate(){
  const t = els.oneClickTemplate.value;
  if(t==='memoryBook'){els.layoutStyle.value='scrapbook'; els.imageCount.value=4; els.outW.value=1800; els.outH.value=1250; els.gap.value=24; els.cornerRadius.value=18; els.themePack.value='warmMemory'; applyThemePack();}
  else if(t==='socialStory'){els.layoutStyle.value='heroTopSmall'; els.imageCount.value=3; els.outW.value=1080; els.outH.value=1920; els.gap.value=18; els.cornerRadius.value=26; els.themePack.value='cleanModern'; applyThemePack();}
  else if(t==='romanticBoard'){els.layoutStyle.value='polaroid'; els.imageCount.value=5; els.outW.value=1800; els.outH.value=1300; els.gap.value=22; els.cornerRadius.value=16; els.themePack.value='romantic'; applyThemePack();}
  else if(t==='cleanShowcase'){els.layoutStyle.value='pairFocus'; els.imageCount.value=6; els.outW.value=1800; els.outH.value=1200; els.gap.value=24; els.cornerRadius.value=20; els.themePack.value='cleanModern'; applyThemePack();}
  else if(t==='vintageAlbum'){els.layoutStyle.value='scrapbook'; els.imageCount.value=7; els.outW.value=1900; els.outH.value=1350; els.gap.value=22; els.cornerRadius.value=16; els.themePack.value='vintageScrapbook'; applyThemePack();}
  draw();
}


function createSeededRng(seed){
  let t = (seed >>> 0) || 1;
  return function(){
    t += 0x6D2B79F5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}
function randRange(rng,min,max){ return min + (max-min) * rng(); }
function randInt(rng,min,max){ return Math.floor(randRange(rng,min,max+1)); }
function shuffleArray(arr,rng){
  const copy = arr.slice();
  for(let i=copy.length-1;i>0;i--){
    const j=Math.floor(rng()*(i+1));
    [copy[i],copy[j]]=[copy[j],copy[i]];
  }
  return copy;
}
function getLayoutRng(extra=0){ return createSeededRng((state.layoutShuffleSeed + extra) >>> 0); }
function shuffleLayoutVariant(){
  state.layoutShuffleSeed = ((Date.now() & 0xffffffff) ^ ((Math.random()*0xffffffff)>>>0)) >>> 0;
  if(els.layoutStyle.value==='freeform'){
    const active=Math.min(activeImageCount(), state.images.length);
    const w=parseInt(els.outW.value||1800,10), h=parseInt(els.outH.value||1200,10);
    const rng=getLayoutRng(active);
    for(let i=0;i<active;i++){
      const item=state.images[i];
      if(!item) continue;
      const ww=Math.round(randRange(rng, Math.max(180, w*0.18), Math.max(260, w*0.34)));
      const aspect=(item.img && item.img.naturalWidth && item.img.naturalHeight) ? (item.img.naturalHeight/item.img.naturalWidth) : randRange(rng,0.7,1.3);
      const hh=Math.round(Math.max(150, ww*aspect));
      const x=Math.round(randRange(rng, 40, Math.max(41, w-ww-40)));
      const y=Math.round(randRange(rng, 40, Math.max(41, h-hh-40)));
      item.freeSlot={x,y,w:ww,h:Math.min(hh,h-80),freeform:true};
      item.rotation = Math.round(randRange(rng,-10,10)*10)/10;
    }
    syncImageControls();
  }
  draw();
}
function applyLayoutDefaults(){
  const count = parseInt(els.imageCount.value||6,10);
  const style = els.layoutStyle.value;
  if(style === 'heroTopSmall'){ els.outW.value=1800; els.outH.value=1350; }
  else if(style === 'featured'){ els.outW.value=1800; els.outH.value=1200; }
  else if(style === 'twoLargeSmall' || style === 'pairFocus' || style === 'sideRail' || style === 'centerHero' || style === 'magazine'){ els.outW.value=1800; els.outH.value=1250; }
  else if(style === 'triptych' || style === 'filmstrip' || style === 'panoramaBands' || style === 'contactSheet'){ els.outW.value=1800; els.outH.value=1200; }
  else if(style === 'staggered' || style === 'scattered' || style === 'galleryWall' || style === 'cascade'){ els.outW.value=1800; els.outH.value=1350; }
  else if(style === 'offsetColumns' || style === 'splitEditorial'){ els.outW.value=1800; els.outH.value=1250; }
  else if(style === 'cornerFocus'){ els.outW.value=1800; els.outH.value=1300; }
  else if(style === 'circleSplit' || style === 'circleInCircle'){ els.outW.value=1600; els.outH.value=1600; }
  else if(style === 'triangleSplit3' || style === 'triangleMosaic'){ els.outW.value=1600; els.outH.value=1500; }
  else if(count<=3){els.outW.value=1800; els.outH.value=1200;}
  else if(count<=6){els.outW.value=1800; els.outH.value=1250;}
  else if(count<=9){els.outW.value=1800; els.outH.value=1400;}
  else {els.outW.value=1900; els.outH.value=1500;}
  draw();
}

function activeImageCount(){ return Math.max(1, Math.min(parseInt(els.imageCount.value||1,10), state.images.length||1, MAX_COLLAGE_IMAGES)); }


function generateGridSlots(w,h,gap,count){
  const rng=getLayoutRng(count*17 + Math.round(w+h+gap));
  const ideal=Math.sqrt(count*(w/h));
  const candidates=[];
  for(let cols=Math.max(1,Math.floor(ideal)-1); cols<=Math.max(1,Math.ceil(ideal)+1); cols++){
    const rows=Math.ceil(count/cols);
    candidates.push({cols,rows,score:Math.abs((cols/rows)-(w/h)) + Math.abs(cols*rows-count)*0.35});
  }
  candidates.sort((a,b)=>a.score-b.score);
  const pick=candidates[Math.min(candidates.length-1, randInt(rng,0,Math.min(2,candidates.length-1)))];
  const cols=pick.cols, rows=pick.rows;
  const sw=(w-gap*(cols-1))/cols;
  const sh=(h-gap*(rows-1))/rows;
  const slots=[];
  const snake=rng()>0.5;
  const flipX=rng()>0.5;
  const flipY=rng()>0.5;
  for(let i=0;i<count;i++){
    const r=Math.floor(i/cols);
    let c=i%cols;
    if(snake && (r%2===1)) c=cols-1-c;
    if(flipX) c=cols-1-c;
    const rr=flipY ? rows-1-r : r;
    slots.push({x:c*(sw+gap), y:rr*(sh+gap), w:sw, h:sh});
  }
  return slots;
}
function generateEqualGridSlots(w,h,gap,count){
  return generateGridSlots(w,h,gap,count);
}
function generateStripSlots(w,h,gap,count){
  const rng=getLayoutRng(count*23 + Math.round(w*2+h));
  const horizontal = rng()>0.5 ? w>=h : w<h;
  const slots=[];
  const weights=Array.from({length:count},()=>0.85+rng()*0.45);
  const total=weights.reduce((a,b)=>a+b,0);
  if(horizontal){
    const usable=w-gap*(count-1); let x=0;
    weights.forEach((wt,i)=>{ const sw=usable*(wt/total); slots.push({x,y:0,w:sw,h}); x+=sw+gap; });
  } else {
    const usable=h-gap*(count-1); let y=0;
    weights.forEach((wt,i)=>{ const sh=usable*(wt/total); slots.push({x:0,y,w,h:sh}); y+=sh+gap; });
  }
  return shuffleArray(slots,rng);
}
function generateStoryboardSlots(w,h,gap,count){
  const rng=getLayoutRng(count*29 + Math.round(w+h));
  const cols=Math.min(count, Math.max(2, Math.min(4, randInt(rng,2,3) + (count>8?1:0))));
  const rows=Math.ceil(count/cols);
  const sw=(w-gap*(cols-1))/cols, sh=(h-gap*(rows-1))/rows;
  const slots=[];
  for(let i=0;i<count;i++){ const r=Math.floor(i/cols), c=i%cols; slots.push({x:c*(sw+gap), y:r*(sh+gap), w:sw, h:sh}); }
  return (rng()>0.5) ? shuffleArray(slots,rng) : slots;
}
function generateFeaturedSlots(w,h,gap,count){
  const rng=getLayoutRng(count*31 + Math.round(w*3+h));
  if(count===1) return [{x:0,y:0,w,h}];
  if(count===2){
    const split=(w>h)? randRange(rng,0.45,0.58) : randRange(rng,0.42,0.55);
    if(w>=h){
      const leftW=(w-gap)*split, rightW=w-gap-leftW;
      return rng()>0.5 ? [{x:0,y:0,w:leftW,h},{x:leftW+gap,y:0,w:rightW,h}] : [{x:0,y:0,w:rightW,h},{x:rightW+gap,y:0,w:leftW,h}];
    }
    const topH=(h-gap)*split, bottomH=h-gap-topH;
    return rng()>0.5 ? [{x:0,y:0,w,h:topH},{x:0,y:topH+gap,w,h:bottomH}] : [{x:0,y:0,w,h:bottomH},{x:0,y:bottomH+gap,w,h:topH}];
  }
  const heroLeft = rng()>0.5;
  const heroW = w*randRange(rng,0.54,0.66);
  const sideW = w-heroW-gap;
  const slots=[];
  if(heroLeft) slots.push({x:0,y:0,w:heroW,h});
  const rest=count-1, weights=Array.from({length:rest},()=>0.8+rng()*0.5), total=weights.reduce((a,b)=>a+b,0);
  let y=0;
  weights.forEach((wt)=>{ const sh=(h-gap*(rest-1))*(wt/total); slots.push({x:heroLeft?heroW+gap:0,y,w:sideW,h:sh}); y+=sh+gap; });
  if(!heroLeft){
    slots.unshift({x:sideW+gap,y:0,w:heroW,h});
    return [slots.pop(), ...slots].slice(0,count);
  }
  return slots.slice(0,count);
}
function generateHeroTopSmallSlots(w,h,gap,count){
  const rng=getLayoutRng(count*37 + Math.round(w+h*2));
  if(count===1) return [{x:0,y:0,w,h}];
  const heroOnTop = rng()>0.35;
  const heroRatio=randRange(rng,0.5,0.66);
  const heroH=(h-gap)*heroRatio;
  const stripH=h-gap-heroH;
  const slots=[];
  const rest=count-1;
  const weights=Array.from({length:rest},()=>0.85+rng()*0.5);
  const total=weights.reduce((a,b)=>a+b,0);
  if(heroOnTop){
    slots.push({x:0,y:0,w,h:heroH});
    let x=0;
    weights.forEach((wt)=>{ const bw=(w-gap*(rest-1))*(wt/total); slots.push({x,y:heroH+gap,w:bw,h:stripH}); x+=bw+gap; });
  } else {
    let x=0;
    weights.forEach((wt)=>{ const bw=(w-gap*(rest-1))*(wt/total); slots.push({x,y:0,w:bw,h:stripH}); x+=bw+gap; });
    slots.push({x:0,y:stripH+gap,w,h:heroH});
  }
  return slots.slice(0,count);
}
function generateTwoLargeSmallSlots(w,h,gap,count){
  const rng=getLayoutRng(count*41 + Math.round(w+h));
  if(count<=2){
    const split=randRange(rng,0.45,0.55);
    const sw=(w-gap)*split, sw2=w-gap-sw;
    return [{x:0,y:0,w:sw,h},{x:sw+gap,y:0,w:sw2,h}].slice(0,count);
  }
  const largeOnTop = rng()>0.4;
  const topH=(h-gap)*randRange(rng,0.5,0.64);
  const bottomH=h-gap-topH;
  const largeW=(w-gap)/2;
  const slots=[];
  if(largeOnTop){
    slots.push({x:0,y:0,w:largeW,h:topH},{x:largeW+gap,y:0,w:largeW,h:topH});
    const rest=count-2, weights=Array.from({length:rest},()=>0.85+rng()*0.45), total=weights.reduce((a,b)=>a+b,0);
    let x=0;
    weights.forEach((wt)=>{ const sw=(w-gap*(rest-1))*(wt/total); slots.push({x,y:topH+gap,w:sw,h:bottomH}); x+=sw+gap; });
  } else {
    const rest=count-2, weights=Array.from({length:rest},()=>0.85+rng()*0.45), total=weights.reduce((a,b)=>a+b,0);
    let x=0;
    weights.forEach((wt)=>{ const sw=(w-gap*(rest-1))*(wt/total); slots.push({x,y:0,w:sw,h:bottomH}); x+=sw+gap; });
    slots.push({x:0,y:bottomH+gap,w:largeW,h:topH},{x:largeW+gap,y:bottomH+gap,w:largeW,h:topH});
  }
  return slots.slice(0,count);
}
function generatePairFocusSlots(w,h,gap,count){
  const rng=getLayoutRng(count*43 + Math.round(w+h));
  if(count<=2){
    return generateFeaturedSlots(w,h,gap,count);
  }
  const focusOnTop = rng()>0.35;
  const focusH=(h-gap)*randRange(rng,0.55,0.72);
  const supportH=h-gap-focusH;
  const leftW=(w-gap)/2;
  const slots=[];
  if(focusOnTop){
    slots.push({x:0,y:0,w:leftW,h:focusH},{x:leftW+gap,y:0,w:leftW,h:focusH});
    const rest=count-2, weights=Array.from({length:rest},()=>0.85+rng()*0.45), total=weights.reduce((a,b)=>a+b,0);
    let x=0;
    weights.forEach((wt)=>{ const sw=(w-gap*(rest-1))*(wt/total); slots.push({x,y:focusH+gap,w:sw,h:supportH}); x+=sw+gap; });
  } else {
    const rest=count-2, weights=Array.from({length:rest},()=>0.85+rng()*0.45), total=weights.reduce((a,b)=>a+b,0);
    let x=0;
    weights.forEach((wt)=>{ const sw=(w-gap*(rest-1))*(wt/total); slots.push({x,y:0,w:sw,h:supportH}); x+=sw+gap; });
    slots.push({x:0,y:supportH+gap,w:leftW,h:focusH},{x:leftW+gap,y:supportH+gap,w:leftW,h:focusH});
  }
  return slots.slice(0,count);
}
function generateMosaicSlots(w,h,gap,count){
  const rng=getLayoutRng(count*47 + Math.round(w+h));
  if(count<=4) return generateFeaturedSlots(w,h,gap,count);
  const topCount=Math.max(1, Math.min(count-1, Math.ceil(count/2) + randInt(rng,-1,1)));
  const bottomCount=Math.max(1, count-topCount);
  const topH=(h-gap)*randRange(rng,0.46,0.6);
  const bottomH=h-gap-topH;
  const topSlots=generateStripSlots(w, topH, gap, topCount).map(s=>({...s}));
  const bottomSlots=generateStripSlots(w, bottomH, gap, bottomCount).map(s=>({...s, y:s.y+topH+gap}));
  return (rng()>0.5 ? topSlots.concat(bottomSlots) : bottomSlots.concat(topSlots)).slice(0,count).map((s,idx)=> idx<topCount || s.y>0 ? s : s);
}
function generatePolaroidSlots(w,h,gap,count){
  const rng=getLayoutRng(count*53 + Math.round(w+h));
  const base = generateGridSlots(w,h,gap,count);
  return base.map((s,i)=>({...s, card:true, tape:true, angle:Math.round(randRange(rng,-10,10))}));
}
function generateScrapbookSlots(w,h,gap,count){
  const rng=getLayoutRng(count*59 + Math.round(w+h));
  const base = generateGridSlots(w*0.88,h*0.82,gap,count);
  return shuffleArray(base,rng).map((s,i)=>({
    x:s.x + randRange(rng,-16,26) + 40,
    y:s.y + randRange(rng,-14,32) + 30,
    w:s.w*randRange(rng,0.84,0.96),
    h:s.h*randRange(rng,0.82,0.94),
    card:true,
    tape:true,
    angle:Math.round(randRange(rng,-9,9))
  }));
}

function generateSideRailSlots(w,h,gap,count){
  const rng=getLayoutRng(count*61 + Math.round(w+h*1.7));
  if(count<=2) return generateFeaturedSlots(w,h,gap,count);
  const railLeft = rng()>0.5;
  const railW = w*randRange(rng,0.24,0.34);
  const mainW = w-gap-railW;
  const mainCount = Math.max(1, count-2);
  const mainTopH = (count>4 ? (h-gap)*randRange(rng,0.54,0.68) : h);
  const slots=[];
  const mainX = railLeft ? railW+gap : 0;
  slots.push({x:mainX,y:0,w:mainW,h:mainTopH});
  if(mainCount>1){
    const remainH = h-gap-mainTopH;
    if(remainH>90){
      const bottomCount = mainCount-1;
      const weights=Array.from({length:bottomCount},()=>0.85+rng()*0.5);
      const total=weights.reduce((a,b)=>a+b,0);
      let x=mainX;
      weights.forEach((wt)=>{ const sw=(mainW-gap*(bottomCount-1))*(wt/total); slots.push({x,y:mainTopH+gap,w:sw,h:remainH}); x+=sw+gap; });
    }
  }
  const railCount = count - slots.length;
  const weights=Array.from({length:railCount},()=>0.8+rng()*0.55);
  const total=weights.reduce((a,b)=>a+b,0) || 1;
  let y=0;
  weights.forEach((wt)=>{ const sh=(h-gap*(railCount-1))*(wt/total); slots.push({x:railLeft?0:mainW+gap,y,w:railW,h:sh}); y+=sh+gap; });
  return slots.slice(0,count);
}
function generateCenterHeroSlots(w,h,gap,count){
  const rng=getLayoutRng(count*67 + Math.round(w*1.2+h));
  if(count<=3) return generateFeaturedSlots(w,h,gap,count);
  const heroW=w*randRange(rng,0.42,0.56), heroH=h*randRange(rng,0.42,0.58);
  const heroX=(w-heroW)/2, heroY=(h-heroH)/2;
  const slots=[{x:heroX,y:heroY,w:heroW,h:heroH}];
  const rest=count-1;
  const sideCols = rest>=6 ? 2 : 1;
  const leftCount=Math.ceil(rest/2), rightCount=rest-leftCount;
  const railW=Math.max(120,(w-heroW-gap*2)/2);
  const leftX=Math.max(0, heroX-gap-railW), rightX=Math.min(w-railW, heroX+heroW+gap);
  const buildRail=(x,n)=>{
    if(n<=0) return [];
    const weights=Array.from({length:n},()=>0.8+rng()*0.6), total=weights.reduce((a,b)=>a+b,0);
    let y=0; const out=[];
    weights.forEach((wt,idx)=>{ const sh=(h-gap*(n-1))*(wt/total); out.push({x,y,w:railW,h:sh}); y+=sh+gap; });
    return out;
  };
  return slots.concat(buildRail(leftX,leftCount), buildRail(rightX,rightCount)).slice(0,count);
}
function generateTriptychSlots(w,h,gap,count){
  const rng=getLayoutRng(count*71 + Math.round(w+h));
  if(count<=3){
    const cols=count, sw=(w-gap*(cols-1))/cols;
    return Array.from({length:count},(_,i)=>({x:i*(sw+gap),y:0,w:sw,h}));
  }
  const thirds=[randRange(rng,0.28,0.36), randRange(rng,0.28,0.42)];
  const leftW=w*thirds[0], centerW=w*thirds[1], rightW=w-gap*2-leftW-centerW;
  const rails=[{x:0,w:leftW},{x:leftW+gap,w:centerW},{x:leftW+gap+centerW+gap,w:rightW}];
  const alloc=[Math.ceil(count/3), Math.floor(count/3), count-Math.ceil(count/3)-Math.floor(count/3)];
  const slots=[];
  rails.forEach((rail,ri)=>{
    const n=Math.max(1,alloc[ri]);
    const weights=Array.from({length:n},()=>0.85+rng()*0.5), total=weights.reduce((a,b)=>a+b,0);
    let y=0;
    weights.forEach((wt)=>{ const sh=(h-gap*(n-1))*(wt/total); slots.push({x:rail.x,y,w:rail.w,h:sh}); y+=sh+gap; });
  });
  return shuffleArray(slots,rng).slice(0,count);
}
function generateStaggeredSlots(w,h,gap,count){
  const rng=getLayoutRng(count*73 + Math.round(w+h));
  const cols=Math.min(4, Math.max(2, Math.round(Math.sqrt(count))));
  const baseW=(w-gap*(cols-1))/cols;
  const slots=[];
  let yOffsets=Array.from({length:cols},()=>randRange(rng,0,40));
  for(let i=0;i<count;i++){
    const col=i%cols;
    const row=Math.floor(i/cols);
    const x=col*(baseW+gap);
    const hh=Math.max(140, h/(Math.ceil(count/cols)+0.5)*randRange(rng,0.9,1.22));
    const y=yOffsets[col];
    slots.push({x,y,w:baseW,h:Math.min(hh,h-y)});
    yOffsets[col]+=hh+gap;
  }
  return slots.map((s,idx)=>({...s,y:Math.min(s.y,h-s.h)}));
}
function generateMagazineSlots(w,h,gap,count){
  const rng=getLayoutRng(count*79 + Math.round(w*2+h));
  if(count<=2) return generateFeaturedSlots(w,h,gap,count);
  const topHero = rng()>0.5;
  const heroH=(h-gap)*randRange(rng,0.38,0.52);
  const lowerH=h-gap-heroH;
  const slots=[];
  if(topHero){
    slots.push({x:0,y:0,w,h:heroH});
    const lowerCount=count-1;
    const cols=Math.min(3, Math.max(2, lowerCount>4?3:2));
    const rows=Math.ceil(lowerCount/cols);
    const sw=(w-gap*(cols-1))/cols, sh=(lowerH-gap*(rows-1))/rows;
    for(let i=0;i<lowerCount;i++){ const r=Math.floor(i/cols), c=i%cols; slots.push({x:c*(sw+gap), y:heroH+gap+r*(sh+gap), w:sw, h:sh}); }
  } else {
    const sideW=(w-gap)*randRange(rng,0.34,0.46);
    slots.push({x:0,y:0,w:sideW,h});
    const rightCount=count-1;
    const cols=1 + (rightCount>3?1:0);
    const rows=Math.ceil(rightCount/cols);
    const sw=(w-gap-sideW-gap*(cols-1))/cols, sh=(h-gap*(rows-1))/rows;
    for(let i=0;i<rightCount;i++){ const r=Math.floor(i/cols), c=i%cols; slots.push({x:sideW+gap+c*(sw+gap), y:r*(sh+gap), w:sw, h:sh}); }
  }
  return slots.slice(0,count);
}
function generateFilmstripSlots(w,h,gap,count){
  const rng=getLayoutRng(count*83 + Math.round(w+h));
  const horizontal = w>=h;
  const slots=[];
  if(horizontal){
    const frameW=(w-gap*(count+1))/count;
    const y=gap;
    for(let i=0;i<count;i++) slots.push({x:gap+i*(frameW+gap),y,w:frameW,h:h-gap*2,card:true,angle:0});
  } else {
    const frameH=(h-gap*(count+1))/count;
    const x=gap;
    for(let i=0;i<count;i++) slots.push({x,y:gap+i*(frameH+gap),w:w-gap*2,h:frameH,card:true,angle:0});
  }
  return rng()>0.5 ? slots : slots.reverse();
}
function generateScatteredSlots(w,h,gap,count){
  const rng=getLayoutRng(count*89 + Math.round(w+h));
  const slots=[];
  for(let i=0;i<count;i++){
    const ww=Math.round(randRange(rng,w*0.22,w*0.42));
    const hh=Math.round(randRange(rng,h*0.2,h*0.38));
    const x=Math.round(randRange(rng,20,Math.max(21,w-ww-20)));
    const y=Math.round(randRange(rng,20,Math.max(21,h-hh-20)));
    slots.push({x,y,w:ww,h:hh,card:true,tape:rng()>0.25,angle:Math.round(randRange(rng,-18,18))});
  }
  return slots;
}

function generatePanoramaBandSlots(w,h,gap,count){
  const rng=getLayoutRng(count*97 + Math.round(w*1.4+h));
  if(count<=2) return generateStripSlots(w,h,gap,count);
  const heroBandOnTop = rng()>0.5;
  const heroH=(h-gap)*randRange(rng,0.44,0.58);
  const stripH=h-gap-heroH;
  const stripCount=count-1;
  const stripRows = stripCount>4 ? 2 : 1;
  const slots=[];
  if(heroBandOnTop){
    slots.push({x:0,y:0,w,h:heroH});
    if(stripRows===1){
      const row=generateStripSlots(w,stripH,gap,stripCount).map(s=>({...s,y:s.y+heroH+gap}));
      return slots.concat(row).slice(0,count);
    }
    const topCount=Math.ceil(stripCount/2), bottomCount=stripCount-topCount;
    const rowH=(stripH-gap)/2;
    const row1=generateStripSlots(w,rowH,gap,topCount).map(s=>({...s,y:heroH+gap}));
    const row2=generateStripSlots(w,rowH,gap,bottomCount).map(s=>({...s,y:heroH+gap+rowH+gap}));
    return slots.concat(row1,row2).slice(0,count);
  }
  const topCount=Math.ceil(stripCount/2), bottomCount=stripCount-topCount;
  const rowH=stripRows===1?stripH:(stripH-gap)/2;
  const row1=generateStripSlots(w,rowH,gap,topCount).map(s=>({...s,y:0}));
  const row2=stripRows===1?[]:generateStripSlots(w,rowH,gap,bottomCount).map(s=>({...s,y:rowH+gap}));
  const heroY=stripRows===1?stripH+gap:(rowH*2+gap*2);
  slots.push({x:0,y:heroY,w,h:heroH});
  return row1.concat(row2,slots).slice(0,count);
}
function generateOffsetColumnsSlots(w,h,gap,count){
  const rng=getLayoutRng(count*101 + Math.round(w+h*1.3));
  const cols = count>=8 ? 4 : 3;
  const colW=(w-gap*(cols-1))/cols;
  const offsets=Array.from({length:cols},()=>randRange(rng,0,Math.max(20,h*0.08)));
  const slots=[];
  const colCounts=Array.from({length:cols},()=>0);
  for(let i=0;i<count;i++) colCounts[i%cols]++;
  for(let c=0;c<cols;c++){
    const n=colCounts[c];
    const usableH=h-offsets[c]-gap*(n-1);
    const weights=Array.from({length:n},()=>0.85+rng()*0.55);
    const total=weights.reduce((a,b)=>a+b,0) || 1;
    let y=offsets[c];
    for(let j=0;j<n;j++){
      const sh=Math.max(120, usableH*(weights[j]/total));
      slots.push({x:c*(colW+gap),y:Math.min(y,h-sh),w:colW,h:sh});
      y+=sh+gap;
    }
  }
  return shuffleArray(slots,rng).slice(0,count);
}
function generateCornerFocusSlots(w,h,gap,count){
  const rng=getLayoutRng(count*103 + Math.round(w+h));
  if(count<=3) return generateFeaturedSlots(w,h,gap,count);
  const heroCorner=randInt(rng,0,3);
  const heroW=w*randRange(rng,0.52,0.66);
  const heroH=h*randRange(rng,0.5,0.64);
  let heroX=0, heroY=0;
  if(heroCorner===1 || heroCorner===3) heroX=w-heroW;
  if(heroCorner===2 || heroCorner===3) heroY=h-heroH;
  const slots=[{x:heroX,y:heroY,w:heroW,h:heroH}];
  const rest=count-1;
  const verticalRail=(heroCorner===0 || heroCorner===2);
  if(verticalRail){
    const railX=heroCorner===0 || heroCorner===2 ? 0 : w-heroW;
    const sideX=heroX===0 ? heroW+gap : 0;
    const sideW=w-heroW-gap;
    const side=generateStripSlots(sideW,h,gap,Math.max(1,Math.ceil(rest/2))).map(s=>({...s,x:sideX}));
    slots.push(...side);
    const remaining=rest-side.length;
    if(remaining>0){
      const footerY=heroY===0 ? heroH+gap : 0;
      const footer=generateStripSlots(heroW,h-heroH-gap,gap,remaining).map(s=>({...s,x:heroX,y:s.y+footerY}));
      slots.push(...footer);
    }
  } else {
    const footerY=heroY===0 ? heroH+gap : 0;
    const footerH=h-heroH-gap;
    const row=generateStripSlots(w,footerH,gap,rest).map(s=>({...s,y:s.y+footerY}));
    slots.push(...row);
  }
  return slots.slice(0,count);
}
function generateSplitEditorialSlots(w,h,gap,count){
  const rng=getLayoutRng(count*107 + Math.round(w*1.1+h));
  if(count<=2) return generateFeaturedSlots(w,h,gap,count);
  const verticalSplit = rng()>0.5;
  const slots=[];
  if(verticalSplit){
    const leadW=(w-gap)*randRange(rng,0.44,0.58);
    const otherW=w-gap-leadW;
    slots.push({x:0,y:0,w:leadW,h});
    const rest=count-1;
    const topCount=Math.ceil(rest/2), bottomCount=rest-topCount;
    const topH=(h-gap)*randRange(rng,0.42,0.58);
    const bottomH=h-gap-topH;
    const top=generateStripSlots(otherW,topH,gap,topCount).map(s=>({...s,x:leadW+gap}));
    const bottom=generateStripSlots(otherW,bottomH,gap,bottomCount).map(s=>({...s,x:leadW+gap,y:topH+gap}));
    return slots.concat(top,bottom).slice(0,count);
  }
  const leadH=(h-gap)*randRange(rng,0.42,0.56);
  const lowerH=h-gap-leadH;
  slots.push({x:0,y:0,w,h:leadH});
  const rest=count-1;
  const cols=Math.min(3, Math.max(2, rest>4?3:2));
  const rows=Math.ceil(rest/cols);
  const sw=(w-gap*(cols-1))/cols, sh=(lowerH-gap*(rows-1))/rows;
  for(let i=0;i<rest;i++){
    const r=Math.floor(i/cols), c=i%cols;
    slots.push({x:c*(sw+gap), y:leadH+gap+r*(sh+gap), w:sw, h:sh});
  }
  return slots.slice(0,count);
}
function generateGalleryWallSlots(w,h,gap,count){
  const rng=getLayoutRng(count*109 + Math.round(w+h));
  const cols=count>=8?4:3;
  const slots=[];
  let remaining=count, y=0;
  while(remaining>0){
    const take=Math.min(cols, remaining);
    const rh=Math.max(150, h/Math.ceil(count/cols)*randRange(rng,0.84,1.18));
    const weights=Array.from({length:take},()=>0.82+rng()*0.48);
    const total=weights.reduce((a,b)=>a+b,0) || 1;
    let x=0;
    for(let i=0;i<take;i++){
      const sw=(w-gap*(take-1))*(weights[i]/total);
      slots.push({x,y,w:sw,h:Math.min(rh,h-y)});
      x+=sw+gap;
    }
    y+=rh+gap;
    remaining-=take;
  }
  return slots.slice(0,count);
}
function generateContactSheetSlots(w,h,gap,count){
  const rng=getLayoutRng(count*113 + Math.round(w+h));
  const cols=Math.min(5, Math.max(3, Math.ceil(Math.sqrt(count))));
  const rows=Math.ceil(count/cols);
  const cellW=(w-gap*(cols+1))/cols;
  const cellH=(h-gap*(rows+1))/rows;
  const inset=Math.max(6, Math.round(Math.min(cellW,cellH)*0.08));
  const slots=[];
  for(let r=0;r<rows;r++){
    for(let c=0;c<cols;c++){
      const i=r*cols+c; if(i>=count) break;
      slots.push({x:gap+c*(cellW+gap)+inset, y:gap+r*(cellH+gap)+inset, w:cellW-inset*2, h:cellH-inset*2, card:true, angle:0});
    }
  }
  return rng()>0.5?slots:shuffleArray(slots,rng);
}
function generateCascadeSlots(w,h,gap,count){
  const rng=getLayoutRng(count*127 + Math.round(w+h));
  const slots=[];
  const stepX=Math.max(70, w/(count+2));
  const stepY=Math.max(45, h/(count+3));
  let cardW=Math.min(w*0.56, 760), cardH=Math.min(h*0.42, 520);
  for(let i=0;i<count;i++){
    const x=Math.min(w-cardW-20, 30+i*stepX + randRange(rng,-18,18));
    const y=Math.min(h-cardH-20, 24+i*stepY + randRange(rng,-16,16));
    slots.push({x,y,w:cardW,h:cardH,card:true,tape:i%3===0,angle:Math.round(randRange(rng,-8,8))});
    cardW=Math.max(w*0.28, cardW*0.9);
    cardH=Math.max(h*0.22, cardH*0.9);
  }
  return slots;
}


function generateCircleSplitSlots(w,h,gap,count){
  const total=Math.max(1,count);
  const r=Math.max(80, Math.min(w,h)/2 - Math.max(18,gap));
  const cx=w/2, cy=h/2;
  const startOffset=-Math.PI/2;
  const slots=[];
  for(let i=0;i<total;i++){
    const start=startOffset + i*(Math.PI*2/total);
    const end=startOffset + (i+1)*(Math.PI*2/total);
    slots.push({shape:'sector', cx, cy, r, startAngle:start, endAngle:end});
  }
  return slots.slice(0,count);
}
function generateCircleInCircleSlots(w,h,gap,count){
  const total=Math.max(1,count);
  const r=Math.max(86, Math.min(w,h)/2 - Math.max(18,gap));
  const cx=w/2, cy=h/2;
  if(total===1) return [{shape:'circle', cx, cy, r}];
  const band=r/total;
  const slots=[];
  for(let i=0;i<total-1;i++){
    const rOuter=r - i*band;
    const rInner=Math.max(0, r - (i+1)*band);
    slots.push({shape:'ring', cx, cy, rOuter, rInner});
  }
  slots.push({shape:'circle', cx, cy, r:band});
  return slots.slice(0,count);
}
function generateTriangleSplit3Slots(w,h,gap,count){
  const pad=Math.max(18,gap);
  const A={x:w/2,y:pad}, B={x:w-pad,y:h-pad}, C={x:pad,y:h-pad};
  const G={x:(A.x+B.x+C.x)/3,y:(A.y+B.y+C.y)/3};
  const slots=[
    {shape:'polygon', points:[A,B,G]},
    {shape:'polygon', points:[B,C,G]},
    {shape:'polygon', points:[C,A,G]}
  ];
  return slots.slice(0,count);
}
function midpoint(p1,p2){ return {x:(p1.x+p2.x)/2, y:(p1.y+p2.y)/2}; }

function getShapeInnerScale(){
  if(!els.shapeInnerSize) return 0;
  const raw=parseFloat(els.shapeInnerSize.value||0);
  return Math.max(0, Math.min(0.9, raw/100));
}

function generateNestedPolygonToCenterSlots(outerPoints, cx, cy, sides, count, innerScale){
  const total=Math.max(1,count);
  if(total===1) return [{shape:'polygon', points:outerPoints}];
  const rings=Math.max(1, Math.ceil(total / sides));
  const minScale=Math.max(0, Math.min(0.9, innerScale));
  const boundaries=[];
  for(let i=0;i<=rings;i++){
    const t=i/rings;
    boundaries.push(1 - (1 - minScale)*t);
  }
  const slots=[];
  for(let ring=0; ring<rings; ring++){
    const outerScale=boundaries[ring];
    const innerScaleRing=boundaries[ring+1];
    const outerRing=outerScale===1 ? outerPoints : scalePolygonTowardsCenter(outerPoints,cx,cy,outerScale);
    if(innerScaleRing <= 0.0001){
      const center={x:cx,y:cy};
      for(let i=0;i<sides;i++){
        const ni=(i+1)%sides;
        slots.push({shape:'polygon', points:[outerRing[i], outerRing[ni], center]});
      }
    } else {
      const innerRing=scalePolygonTowardsCenter(outerPoints,cx,cy,innerScaleRing);
      for(let i=0;i<sides;i++){
        const ni=(i+1)%sides;
        slots.push({shape:'polygon', points:[outerRing[i], outerRing[ni], innerRing[ni], innerRing[i]]});
      }
    }
  }
  return slots.slice(0,count);
}
function polygonPoint(cx,cy,r,angle){ return {x:cx+Math.cos(angle)*r, y:cy+Math.sin(angle)*r}; }
function regularPolygonPoints(cx,cy,r,sides,startAngle=-Math.PI/2){
  const pts=[];
  for(let i=0;i<sides;i++) pts.push(polygonPoint(cx,cy,r,startAngle + i*(Math.PI*2/sides)));
  return pts;
}
function scalePolygonTowardsCenter(points,cx,cy,scale){
  return points.map(p=>({x:cx + (p.x-cx)*scale, y:cy + (p.y-cy)*scale}));
}
function generateTriangleInTriangleSlots(w,h,gap,count){
  const pad=Math.max(18,gap);
  const cx=w/2;
  const outerTop=pad;
  const outerBottom=h-pad;
  const triHeight=Math.max(120, outerBottom-outerTop);
  const side=(2*triHeight)/Math.sqrt(3);
  const halfBase=side/2;
  const cy=(outerTop+outerBottom)/2 + triHeight/6;
  const A={x:cx,y:cy-2*triHeight/3};
  const B={x:cx+halfBase,y:cy+triHeight/3};
  const C={x:cx-halfBase,y:cy+triHeight/3};
  return generateNestedPolygonToCenterSlots([A,B,C], cx, cy, 3, count, getShapeInnerScale());
}
function generateHexagonInHexagonSlots(w,h,gap,count){
  const pad=Math.max(18,gap);
  const r=Math.max(80, Math.min(w,h)/2 - pad);
  const cx=w/2, cy=h/2;
  const outer=regularPolygonPoints(cx,cy,r,6,-Math.PI/2);
  return generateNestedPolygonToCenterSlots(outer, cx, cy, 6, count, getShapeInnerScale());
}

function generateTriangleMosaicSlots(w,h,gap,count){
  const pad=Math.max(18,gap);
  const A={x:w/2,y:pad}, B={x:w-pad,y:h-pad}, C={x:pad,y:h-pad};
  const AB=midpoint(A,B), BC=midpoint(B,C), CA=midpoint(C,A);
  const G={x:(A.x+B.x+C.x)/3,y:(A.y+B.y+C.y)/3};
  const slots=[
    {shape:'polygon', points:[A,AB,G]},
    {shape:'polygon', points:[AB,B,G]},
    {shape:'polygon', points:[B,BC,G]},
    {shape:'polygon', points:[BC,C,G]},
    {shape:'polygon', points:[C,CA,G]},
    {shape:'polygon', points:[CA,A,G]}
  ];
  return slots.slice(0,count);
}

function generateFreeformSlots(count){
  return Array.from({length:count},(_,i)=>state.images[i]?.freeSlot || {x:80+i*35,y:80+i*28,w:420,h:300,freeform:true});
}

function getCustomSplitBounds(w,h,gap){
  const pad=Math.max(18, gap);
  return {x:pad, y:pad, w:Math.max(120, w-pad*2), h:Math.max(120, h-pad*2)};
}
function ensureCustomSplitRooms(){
  if(Array.isArray(state.customSplitRooms) && state.customSplitRooms.length) return;
  state.customSplitRooms=[{x:0,y:0,w:1,h:1}];
}
function getCustomSplitSlots(w,h,gap,count){
  ensureCustomSplitRooms();
  const bounds=getCustomSplitBounds(w,h,gap);
  const rooms=state.customSplitRooms.slice(0, Math.max(1,count));
  return rooms.map(room=>({x:bounds.x + room.x*bounds.w, y:bounds.y + room.y*bounds.h, w:room.w*bounds.w, h:room.h*bounds.h, customSplit:true}));
}
function findCustomSplitRoomIndex(pt,w,h,gap){
  ensureCustomSplitRooms();
  const slots=getCustomSplitSlots(w,h,gap,state.customSplitRooms.length);
  for(let i=slots.length-1;i>=0;i--){ if(pointInSlot(pt, slots[i])) return i; }
  return -1;
}
function splitCustomRoomAt(roomIndex, orientation, valueAbs, w, h, gap){
  ensureCustomSplitRooms();
  const bounds=getCustomSplitBounds(w,h,gap);
  const room=state.customSplitRooms[roomIndex];
  if(!room) return false;
  const minRatio=0.08;
  if(orientation==='vertical'){
    const local=(valueAbs - bounds.x)/bounds.w;
    const rel=(local - room.x)/room.w;
    if(rel<=minRatio || rel>=1-minRatio) return false;
    const left={x:room.x, y:room.y, w:room.w*rel, h:room.h};
    const right={x:room.x+room.w*rel, y:room.y, w:room.w*(1-rel), h:room.h};
    state.customSplitRooms.splice(roomIndex,1,left,right);
  } else {
    const local=(valueAbs - bounds.y)/bounds.h;
    const rel=(local - room.y)/room.h;
    if(rel<=minRatio || rel>=1-minRatio) return false;
    const top={x:room.x, y:room.y, w:room.w, h:room.h*rel};
    const bottom={x:room.x, y:room.y+room.h*rel, w:room.w, h:room.h*(1-rel)};
    state.customSplitRooms.splice(roomIndex,1,top,bottom);
  }
  els.imageCount.value = Math.max(1, Math.min(MAX_COLLAGE_IMAGES, state.customSplitRooms.length));
  return true;
}
function resetCustomSplitRooms(){
  state.customSplitRooms=[{x:0,y:0,w:1,h:1}];
  if(els.imageCount) els.imageCount.value=Math.max(1, Math.min(MAX_COLLAGE_IMAGES, state.images.length || 1));
}
function updateCustomSplitUi(){
  const active=els.layoutStyle && els.layoutStyle.value==='customSplit';
  if(els.customSplitSection) els.customSplitSection.classList.toggle('is-visible', !!active);
  if(els.canvas) els.canvas.classList.toggle('custom-split-draw', !!(active && els.customSplitDrawMode && els.customSplitDrawMode.checked));
  if(active){ ensureCustomSplitRooms(); if(els.imageCount) els.imageCount.value=Math.max(1, Math.min(MAX_COLLAGE_IMAGES, state.customSplitRooms.length)); }
}
function drawCustomSplitOverlay(w,h,gap){
  if(els.layoutStyle.value!=='customSplit') return;
  const slots=getCustomSplitSlots(w,h,gap,Math.max(1,state.customSplitRooms?.length||1));
  ctx.save();
  ctx.strokeStyle='rgba(255,255,255,0.98)';
  ctx.lineWidth=Math.max(2, Math.min(8, gap*0.38));
  for(const slot of slots){ ctx.strokeRect(slot.x, slot.y, slot.w, slot.h); }
  ctx.strokeStyle='rgba(17,24,39,0.24)';
  ctx.lineWidth=1;
  for(const slot of slots){ ctx.strokeRect(slot.x, slot.y, slot.w, slot.h); }
  if(state.customSplitGuide){
    const g=state.customSplitGuide;
    ctx.strokeStyle='rgba(37,99,235,0.98)';
    ctx.lineWidth=4;
    ctx.setLineDash([12,10]);
    ctx.beginPath();
    if(g.orientation==='vertical'){
      ctx.moveTo(g.x, g.slot.y);
      ctx.lineTo(g.x, g.slot.y + g.slot.h);
    } else {
      ctx.moveTo(g.slot.x, g.y);
      ctx.lineTo(g.slot.x + g.slot.w, g.y);
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }
  ctx.restore();
}


function clonePoints(points){ return (points||[]).map(pt=>({x:pt.x,y:pt.y})); }
function getSnapDrawBounds(w,h,gap){
  const pad=Math.max(18, gap);
  return {x:pad, y:pad, w:Math.max(120, w-pad*2), h:Math.max(120, h-pad*2)};
}
function ensureSnapDrawPolygons(){
  if(Array.isArray(state.snapDrawPolygons) && state.snapDrawPolygons.length) return;
  state.snapDrawPolygons=[{points:[{x:0,y:0},{x:1,y:0},{x:1,y:1},{x:0,y:1}]}];
}
function getSnapDrawSlots(w,h,gap,count){
  ensureSnapDrawPolygons();
  const bounds=getSnapDrawBounds(w,h,gap);
  const polys=state.snapDrawPolygons.slice(0, Math.max(1,count));
  return polys.map(poly=>({shape:'polygon', snapDraw:true, points:(poly.points||[]).map(pt=>({x:bounds.x+pt.x*bounds.w,y:bounds.y+pt.y*bounds.h}))}));
}
function resetSnapDrawPolygons(){
  state.snapDrawPolygons=[{points:[{x:0,y:0},{x:1,y:0},{x:1,y:1},{x:0,y:1}]}];
  if(els.imageCount) els.imageCount.value=Math.max(1, Math.min(MAX_COLLAGE_IMAGES, state.images.length || 1));
}
function updateSnapDrawUi(){
  const active=els.layoutStyle && els.layoutStyle.value==='snapDraw';
  if(els.snapDrawSection) els.snapDrawSection.classList.toggle('is-visible', !!active);
  if(els.canvas) els.canvas.classList.toggle('snap-draw-mode', !!(active && els.snapDrawMode && els.snapDrawMode.checked));
  if(active){ ensureSnapDrawPolygons(); if(els.imageCount) els.imageCount.value=Math.max(1, Math.min(MAX_COLLAGE_IMAGES, state.snapDrawPolygons.length)); }
}
function findSnapDrawPolygonIndex(pt,w,h,gap){
  const slots=getSnapDrawSlots(w,h,gap,Math.max(1,state.snapDrawPolygons?.length||1));
  for(let i=slots.length-1;i>=0;i--){ if(pointInSlot(pt, slots[i])) return i; }
  return -1;
}
function dist2(a,b){ const dx=a.x-b.x, dy=a.y-b.y; return dx*dx+dy*dy; }
function nearestPointOnSegment(pt,a,b){
  const abx=b.x-a.x, aby=b.y-a.y;
  const denom=abx*abx + aby*aby || 1e-9;
  const t=Math.max(0, Math.min(1, ((pt.x-a.x)*abx + (pt.y-a.y)*aby)/denom));
  return {x:a.x+abx*t,y:a.y+aby*t,t};
}
function getSnapPointForPolygon(pt, polyAbs, snapPx=18){
  const pts=polyAbs.points||[];
  let best=null;
  for(let i=0;i<pts.length;i++){
    const v=pts[i];
    const d=dist2(pt,v);
    if(!best || d<best.d) best={kind:'vertex', edgeIndex:i, point:{x:v.x,y:v.y}, d};
  }
  const edgeMin=(snapPx*snapPx)*4;
  for(let i=0;i<pts.length;i++){
    const a=pts[i], b=pts[(i+1)%pts.length];
    const np=nearestPointOnSegment(pt,a,b);
    const d=dist2(pt,np);
    if((!best || d<best.d) && d<=edgeMin){
      if(np.t<=0.04) best={kind:'vertex', edgeIndex:i, point:{x:a.x,y:a.y}, d};
      else if(np.t>=0.96) best={kind:'vertex', edgeIndex:(i+1)%pts.length, point:{x:b.x,y:b.y}, d};
      else best={kind:'edge', edgeIndex:i, t:np.t, point:{x:np.x,y:np.y}, d};
    }
  }
  return best;
}
function normalizePointToBounds(pt,bounds){ return {x:(pt.x-bounds.x)/bounds.w, y:(pt.y-bounds.y)/bounds.h}; }
function absPointFromNorm(pt,bounds){ return {x:bounds.x+pt.x*bounds.w, y:bounds.y+pt.y*bounds.h}; }
function almostSamePoint(a,b,eps=0.0005){ return Math.abs(a.x-b.x)<=eps && Math.abs(a.y-b.y)<=eps; }
function buildSplitPaths(polyNorm, startInfo, endInfo){
  const pts=clonePoints(polyNorm.points||[]);
  const n=pts.length;
  if(n<3) return null;
  const s=startInfo.normPoint, e=endInfo.normPoint;
  const sequence=[];
  for(let i=0;i<n;i++){
    sequence.push({type:'vertex', point:pts[i], sourceIndex:i});
    if(startInfo.kind==='edge' && startInfo.edgeIndex===i) sequence.push({type:'start', point:s, sourceIndex:i});
    if(endInfo.kind==='edge' && endInfo.edgeIndex===i) sequence.push({type:'end', point:e, sourceIndex:i});
  }
  if(startInfo.kind==='vertex') sequence.splice(startInfo.edgeIndex,0,{type:'start', point:s, sourceIndex:startInfo.edgeIndex});
  if(endInfo.kind==='vertex') {
    const idx=sequence.findIndex(item=>item.type==='vertex' && item.sourceIndex===endInfo.edgeIndex);
    sequence.splice(Math.max(0,idx),0,{type:'end', point:e, sourceIndex:endInfo.edgeIndex});
  }
  let si=sequence.findIndex(item=>item.type==='start');
  let ei=sequence.findIndex(item=>item.type==='end');
  if(si<0 || ei<0 || si===ei) return null;
  const forward=[sequence[si].point];
  let i=si;
  while(i!==ei){ i=(i+1)%sequence.length; forward.push(sequence[i].point); if(forward.length>sequence.length+3) break; }
  const backward=[sequence[ei].point];
  i=ei;
  while(i!==si){ i=(i+1)%sequence.length; backward.push(sequence[i].point); if(backward.length>sequence.length+3) break; }
  const polyA=forward;
  const polyB=backward;
  if(polyA.length<3 || polyB.length<3) return null;
  return [polyA, polyB];
}
function cleanPolygon(points){
  const out=[];
  for(const p of points||[]){ if(!out.length || !almostSamePoint(p,out[out.length-1])) out.push({x:p.x,y:p.y}); }
  if(out.length>1 && almostSamePoint(out[0], out[out.length-1])) out.pop();
  return out;
}
function polygonArea(points){
  let area=0;
  for(let i=0;i<points.length;i++){ const a=points[i], b=points[(i+1)%points.length]; area += a.x*b.y - b.x*a.y; }
  return area/2;
}
function splitSnapPolygonAt(polyIndex, startInfoAbs, endInfoAbs, w, h, gap){
  ensureSnapDrawPolygons();
  const bounds=getSnapDrawBounds(w,h,gap);
  const poly=state.snapDrawPolygons[polyIndex];
  if(!poly) return false;
  const startInfo={...startInfoAbs, normPoint:normalizePointToBounds(startInfoAbs.point,bounds)};
  const endInfo={...endInfoAbs, normPoint:normalizePointToBounds(endInfoAbs.point,bounds)};
  if(almostSamePoint(startInfo.normPoint, endInfo.normPoint, 0.003)) return false;
  const built=buildSplitPaths(poly, startInfo, endInfo);
  if(!built) return false;
  let [a,b]=built.map(cleanPolygon);
  if(a.length<3 || b.length<3) return false;
  if(Math.abs(polygonArea(a))<0.0008 || Math.abs(polygonArea(b))<0.0008) return false;
  state.snapDrawPolygons.splice(polyIndex,1,{points:a},{points:b});
  if(els.imageCount) els.imageCount.value=Math.max(1, Math.min(MAX_COLLAGE_IMAGES, state.snapDrawPolygons.length));
  return true;
}
function drawSnapDrawOverlay(w,h,gap){
  if(els.layoutStyle.value!=='snapDraw') return;
  const slots=getSnapDrawSlots(w,h,gap,Math.max(1,state.snapDrawPolygons?.length||1));
  ctx.save();
  ctx.strokeStyle='rgba(255,255,255,0.98)';
  ctx.lineWidth=Math.max(2, Math.min(8, gap*0.38));
  for(const slot of slots){ pathPolygon(ctx, slot.points); ctx.stroke(); }
  ctx.strokeStyle='rgba(17,24,39,0.24)';
  ctx.lineWidth=1;
  for(const slot of slots){ pathPolygon(ctx, slot.points); ctx.stroke(); }
  if(els.snapDrawMode && els.snapDrawMode.checked){
    for(const slot of slots){
      for(const p of slot.points){ ctx.beginPath(); ctx.fillStyle='rgba(17,24,39,0.55)'; ctx.arc(p.x,p.y,3.5,0,Math.PI*2); ctx.fill(); }
    }
  }
  if(state.snapDrawGuide){
    const g=state.snapDrawGuide;
    ctx.strokeStyle='rgba(37,99,235,0.98)';
    ctx.lineWidth=4;
    ctx.setLineDash([12,10]);
    ctx.beginPath();
    ctx.moveTo(g.start.point.x, g.start.point.y);
    ctx.lineTo(g.current.point.x, g.current.point.y);
    ctx.stroke();
    ctx.setLineDash([]);
    for(const p of [g.start.point, g.current.point]){ ctx.beginPath(); ctx.fillStyle='rgba(37,99,235,0.98)'; ctx.arc(p.x,p.y,5,0,Math.PI*2); ctx.fill(); }
  }
  ctx.restore();
}

function getSlots(w,h,gap,count){
  const style = els.layoutStyle.value;
  if(style==='gridEqual') return generateEqualGridSlots(w,h,gap,count);
  if(style==='grid') return generateGridSlots(w,h,gap,count);
  if(style==='mosaic') return generateMosaicSlots(w,h,gap,count);
  if(style==='storyboard') return generateStoryboardSlots(w,h,gap,count);
  if(style==='strips') return generateStripSlots(w,h,gap,count);
  if(style==='polaroid') return generatePolaroidSlots(w,h,gap,count);
  if(style==='scrapbook') return generateScrapbookSlots(w,h,gap,count);
  if(style==='featured') return generateFeaturedSlots(w,h,gap,count);
  if(style==='heroTopSmall') return generateHeroTopSmallSlots(w,h,gap,count);
  if(style==='twoLargeSmall') return generateTwoLargeSmallSlots(w,h,gap,count);
  if(style==='pairFocus') return generatePairFocusSlots(w,h,gap,count);
  if(style==='sideRail') return generateSideRailSlots(w,h,gap,count);
  if(style==='centerHero') return generateCenterHeroSlots(w,h,gap,count);
  if(style==='triptych') return generateTriptychSlots(w,h,gap,count);
  if(style==='staggered') return generateStaggeredSlots(w,h,gap,count);
  if(style==='magazine') return generateMagazineSlots(w,h,gap,count);
  if(style==='filmstrip') return generateFilmstripSlots(w,h,gap,count);
  if(style==='scattered') return generateScatteredSlots(w,h,gap,count);
  if(style==='panoramaBands') return generatePanoramaBandSlots(w,h,gap,count);
  if(style==='offsetColumns') return generateOffsetColumnsSlots(w,h,gap,count);
  if(style==='cornerFocus') return generateCornerFocusSlots(w,h,gap,count);
  if(style==='splitEditorial') return generateSplitEditorialSlots(w,h,gap,count);
  if(style==='galleryWall') return generateGalleryWallSlots(w,h,gap,count);
  if(style==='contactSheet') return generateContactSheetSlots(w,h,gap,count);
  if(style==='cascade') return generateCascadeSlots(w,h,gap,count);
  if(style==='circleSplit') return generateCircleSplitSlots(w,h,gap,count);
  if(style==='circleInCircle') return generateCircleInCircleSlots(w,h,gap,count);
  if(style==='triangleSplit3') return generateTriangleSplit3Slots(w,h,gap,count);
  if(style==='triangleMosaic') return generateTriangleMosaicSlots(w,h,gap,count);
  if(style==='triangleInTriangle') return generateTriangleInTriangleSlots(w,h,gap,count);
  if(style==='hexagonInHexagon') return generateHexagonInHexagonSlots(w,h,gap,count);
  if(style==='freeform') return generateFreeformSlots(count);
  if(style==='customSplit') return getCustomSplitSlots(w,h,gap,count);
  if(style==='snapDraw') return getSnapDrawSlots(w,h,gap,count);
  return generateGridSlots(w,h,gap,count);
}


function updateThumbDragClasses(){
  const nodes=els.thumbs.querySelectorAll('.thumb');
  nodes.forEach((node,i)=>{
    node.classList.toggle('drag-source', i===state.thumbDragIndex);
    node.classList.toggle('drop-target', i===state.thumbDropIndex && state.thumbDragIndex>=0 && i!==state.thumbDragIndex);
    node.classList.toggle('active', i===state.selectedImage);
  });
}

function renderThumbs(){
  els.thumbs.innerHTML='';
  state.images.forEach((item,idx)=>{
    const div=document.createElement('div');
    div.className='thumb'+(idx===state.selectedImage?' active':'');
    div.draggable=true;
    div.dataset.index=String(idx);
    div.innerHTML=`<img src="${item.url}" alt=""><div class="meta"><strong>Image ${idx+1}</strong><div class="small">${item.file.name}</div><div><span class="badge">zoom ${item.zoom.toFixed(2)}</span><span class="badge">rot ${item.rotation.toFixed(1)}°</span></div></div>`;
    div.onclick=()=>{state.selectedImage=idx; syncImageControls(); updateThumbDragClasses(); draw();};
    div.ondragstart=(e)=>{
      state.thumbDragIndex=idx;
      state.thumbDropIndex=idx;
      state.selectedImage=idx;
      if(e.dataTransfer){
        e.dataTransfer.effectAllowed='move';
        try{ e.dataTransfer.setData('text/plain', String(idx)); }catch(_){ }
      }
      updateThumbDragClasses();
    };
    div.ondragenter=(e)=>{
      if(state.thumbDragIndex<0) return;
      e.preventDefault();
      if(state.thumbDropIndex!==idx){
        state.thumbDropIndex=idx;
        updateThumbDragClasses();
      }
    };
    div.ondragover=(e)=>{
      if(state.thumbDragIndex<0) return;
      e.preventDefault();
      if(e.dataTransfer) e.dataTransfer.dropEffect='move';
    };
    div.ondrop=(e)=>{
      if(state.thumbDragIndex<0) return;
      e.preventDefault();
      const from=state.thumbDragIndex, to=idx;
      reorderImageItems(from, to);
      state.thumbDragIndex=-1;
      state.thumbDropIndex=-1;
      renderThumbs();
      draw();
      commitHistory();
    };
    div.ondragend=()=>{
      state.thumbDragIndex=-1;
      state.thumbDropIndex=-1;
      updateThumbDragClasses();
    };
    els.thumbs.appendChild(div);
  });
  updateThumbDragClasses();
}
function renderTextList(){els.textList.innerHTML=''; state.texts.forEach((t,idx)=>{const div=document.createElement('div'); div.className='text-item'+(idx===state.selectedText?' active':''); div.innerHTML=`<div class="meta"><strong>Text ${idx+1}</strong><div class="small">${(t.text||'(empty)').replace(/\n/g,' / ').slice(0,70)}</div></div>`; div.onclick=()=>{state.selectedText=idx; syncTextControls(); renderTextList(); draw();}; els.textList.appendChild(div);});}
function renderDecoList(){els.decoList.innerHTML=''; state.decos.forEach((d,idx)=>{const div=document.createElement('div'); div.className='deco-item'+(idx===state.selectedDeco?' active':''); div.innerHTML=`<div class="meta"><strong>${d.type}</strong><div class="small">x:${Math.round(d.x)} y:${Math.round(d.y)} w:${Math.round(d.w)} h:${Math.round(d.h)}</div></div>`; div.onclick=()=>{state.selectedDeco=idx; syncDecoControls(); renderDecoList(); draw();}; els.decoList.appendChild(div);});}

function syncImageControls(){const item=state.images[state.selectedImage]; if(!item) return; els.zoom.value=item.zoom; const isFree=['freeform'].includes(els.layoutStyle.value); els.offsetX.value=Math.round(isFree ? (item.freeSlot?.x || 0) : item.offsetX); els.offsetY.value=Math.round(isFree ? (item.freeSlot?.y || 0) : item.offsetY); els.rotation.value=item.rotation; els.opacity.value=item.opacity;}
function syncTextControls(){const t=state.texts[state.selectedText]; if(!t) return; els.textContent.value=t.text; els.fontFamily.value=t.fontFamily; els.fontSize.value=t.size; els.textColor.value=t.color; els.textAlign.value=t.align; els.textOpacity.value=t.opacity; els.textX.value=Math.round(t.x); els.textY.value=Math.round(t.y); els.textRotation.value=t.rotation; els.textShadow.value=t.shadow; els.strokeColor.value=t.strokeColor; els.strokeWidth.value=t.strokeWidth; els.boldToggle.checked=t.bold; els.italicToggle.checked=t.italic;}
function syncDecoControls(){const d=state.decos[state.selectedDeco]; if(!d) return; els.decoColor.value=d.color; els.decoOpacity.value=d.opacity; els.decoX.value=Math.round(d.x); els.decoY.value=Math.round(d.y); els.decoW.value=Math.round(d.w); els.decoH.value=Math.round(d.h); els.decoRotation.value=d.rotation; els.decoStroke.value=d.strokeWidth;}


function swapImageItems(a,b){
  if(a===b || a<0 || b<0 || a>=state.images.length || b>=state.images.length) return;
  if(els.layoutStyle.value==='freeform'){
    const ia=state.images[a], ib=state.images[b];
    const temp={img:ia.img,url:ia.url,file:ia.file,zoom:ia.zoom,offsetX:ia.offsetX,offsetY:ia.offsetY,rotation:ia.rotation,opacity:ia.opacity};
    ia.img=ib.img; ia.url=ib.url; ia.file=ib.file; ia.zoom=ib.zoom; ia.offsetX=ib.offsetX; ia.offsetY=ib.offsetY; ia.rotation=ib.rotation; ia.opacity=ib.opacity;
    ib.img=temp.img; ib.url=temp.url; ib.file=temp.file; ib.zoom=temp.zoom; ib.offsetX=temp.offsetX; ib.offsetY=temp.offsetY; ib.rotation=temp.rotation; ib.opacity=temp.opacity;
  } else {
    [state.images[a], state.images[b]] = [state.images[b], state.images[a]];
  }
  state.selectedImage=b;
  syncImageControls();
  renderThumbs();
}
function reorderImageItems(fromIndex,toIndex){
  if(fromIndex===toIndex || fromIndex<0 || toIndex<0 || fromIndex>=state.images.length || toIndex>=state.images.length) return;
  const [moved]=state.images.splice(fromIndex,1);
  state.images.splice(toIndex,0,moved);
  state.selectedImage=toIndex;
  syncImageControls();
}
function drawSwapTarget(slot){
  if(!slot) return;
  const radius=parseInt(els.cornerRadius.value||0,10);
  ctx.save();
  ctx.strokeStyle='rgba(16,185,129,0.98)';
  ctx.fillStyle='rgba(16,185,129,0.12)';
  ctx.lineWidth=6;
  roundRectPath(ctx,slot.x+3,slot.y+3,slot.w-6,slot.h-6,radius);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function fillCurrentBackgroundArea(w,h){
  if(els.backgroundMode.value==='solid'){ctx.fillStyle=els.bg.value; ctx.fillRect(0,0,w,h); return;}
  if(els.backgroundMode.value==='gradient'){const grad=ctx.createLinearGradient(0,0,w,h); grad.addColorStop(0,els.bg.value); grad.addColorStop(1,getMaybeColor(els.bg2, els.bg2None)); ctx.fillStyle=grad; ctx.fillRect(0,0,w,h); return;}
  ctx.fillStyle=els.bg.value; ctx.fillRect(0,0,w,h); const g=parseInt(els.paperGrain.value||0,10);
  for(let i=0;i<g*35;i++){const x=Math.random()*w,y=Math.random()*h,a=Math.random()*0.06,s=Math.random()*2.4+0.4; ctx.fillStyle=`rgba(0,0,0,${a})`; ctx.fillRect(x,y,s,s);}
}
function drawBackground(w,h,exportMode=false){
  const style = els.layoutStyle.value;
  if(exportMode && isShapeLayoutStyle(style)){
    const clipped=clipToGlobalShape(style,w,h,parseInt(els.gap.value||0,10));
    fillCurrentBackgroundArea(w,h);
    restoreGlobalShapeClip(clipped);
    return;
  }
  fillCurrentBackgroundArea(w,h);
}
function getDrawParams(img,slot,item){
  const fitMode=els.fitMode.value, nw=img.naturalWidth, nh=img.naturalHeight;
  const baseScale=fitMode==='contain'?Math.min(slot.w/nw, slot.h/nh):Math.max(slot.w/nw, slot.h/nh);
  const scale=baseScale*item.zoom, dw=nw*scale, dh=nh*scale;
  const x=slot.x+(slot.w-dw)/2+item.offsetX, y=slot.y+(slot.h-dh)/2+item.offsetY;
  return {x,y,w:dw,h:dh};
}
function drawFrame(slot){
  const frame=parseInt(els.frameWidth.value||0,10);
  if(frame<=0) return;
  if(isShapeLayoutStyle(els.layoutStyle.value)) return;
  ctx.save();
  ctx.lineWidth=frame*2;
  ctx.strokeStyle=els.frameColor.value;
  ctx.lineJoin='miter';
  ctx.lineCap='butt';
  pathForSlot(ctx, slot);
  ctx.stroke();
  ctx.restore();
}
function drawShapeLayoutDividers(style,w,h,gap,count){
  const color=getMaybeColor(els.frameColor, els.frameColorNone);
  const frame=parseInt(els.frameWidth.value||0,10);
  if(!color || frame<=0 || !isShapeLayoutStyle(style)) return;
  const lineW=frame*2;
  const pad=Math.max(18,gap);
  ctx.save();
  ctx.strokeStyle=color;
  ctx.lineWidth=lineW;
  ctx.lineJoin='miter';
  ctx.lineCap='butt';
  if(style==='circleSplit'){
    const total=Math.max(1,count);
    const r=Math.max(80, Math.min(w,h)/2 - pad);
    const cx=w/2, cy=h/2;
    ctx.beginPath();
    ctx.arc(cx,cy,r,0,Math.PI*2);
    ctx.stroke();
    const startOffset=-Math.PI/2;
    for(let i=0;i<total;i++){
      const ang=startOffset + i*(Math.PI*2/total);
      const ex=cx + Math.cos(ang)*(r + lineW*0.25);
      const ey=cy + Math.sin(ang)*(r + lineW*0.25);
      ctx.beginPath();
      ctx.moveTo(cx,cy);
      ctx.lineTo(ex,ey);
      ctx.stroke();
    }
  } else if(style==='circleInCircle'){
    const total=Math.max(1,count);
    const r=Math.max(86, Math.min(w,h)/2 - pad);
    const cx=w/2, cy=h/2;
    const band=r/total;
    ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.stroke();
    for(let i=1;i<total;i++){
      const rr=r - i*band;
      if(rr>0){ ctx.beginPath(); ctx.arc(cx,cy,rr,0,Math.PI*2); ctx.stroke(); }
    }
  } else if(style==='triangleSplit3' || style==='triangleMosaic'){
    const A={x:w/2,y:pad}, B={x:w-pad,y:h-pad}, C={x:pad,y:h-pad};
    const G={x:(A.x+B.x+C.x)/3,y:(A.y+B.y+C.y)/3};
    const AB={x:(A.x+B.x)/2,y:(A.y+B.y)/2}, BC={x:(B.x+C.x)/2,y:(B.y+C.y)/2}, CA={x:(C.x+A.x)/2,y:(C.y+A.y)/2};
    pathPolygon(ctx,[A,B,C]);
    ctx.stroke();
    const lines = style==='triangleSplit3' ? [[G,A],[G,B],[G,C]] : [[G,A],[G,B],[G,C],[G,AB],[G,BC],[G,CA]];
    for(const [p1,p2] of lines){
      ctx.beginPath(); ctx.moveTo(p1.x,p1.y); ctx.lineTo(p2.x,p2.y); ctx.stroke();
    }
  }
  ctx.restore();
}
function drawTapeAt(x,y,w,h,angle){ctx.save(); ctx.translate(x,y); ctx.rotate(angle*Math.PI/180); ctx.fillStyle='rgba(255,245,200,0.52)'; ctx.strokeStyle='rgba(255,255,255,0.6)'; ctx.lineWidth=1; roundRectPath(ctx,-w/2,-h/2,w,h,6); ctx.fill(); ctx.stroke(); ctx.restore();}
function drawOneImage(item,slot,idx,showSelection=true){
  const radius=parseInt(els.cornerRadius.value||0,10), shadow=parseInt(els.shadowStrength.value||0,10);
  if(slot.card){
    ctx.save(); const pad=18, outerW=slot.w+pad*2, outerH=slot.h+pad*2+42, cx=slot.x+slot.w/2, cy=slot.y+slot.h/2;
    ctx.translate(cx,cy); ctx.rotate(((slot.angle||0)+item.rotation)*Math.PI/180); ctx.shadowColor='rgba(0,0,0,.18)'; ctx.shadowBlur=shadow; ctx.shadowOffsetY=Math.max(2,Math.round(shadow/2)); ctx.fillStyle='#fff'; ctx.fillRect(-outerW/2,-outerH/2,outerW,outerH); ctx.shadowColor='transparent';
    ctx.save(); roundRectPath(ctx,-slot.w/2,-slot.h/2-14,slot.w,slot.h,radius); ctx.clip(); const local={x:-slot.w/2,y:-slot.h/2-14,w:slot.w,h:slot.h}; const p=getDrawParams(item.img,local,item); ctx.globalAlpha=item.opacity; ctx.drawImage(item.img,p.x,p.y,p.w,p.h); ctx.restore();
    if(slot.tape){drawTapeAt(cx-outerW*0.22, cy-outerH*0.42, 120, 34, -18+(slot.angle||0)); drawTapeAt(cx+outerW*0.22, cy-outerH*0.42, 120, 34, 18+(slot.angle||0));}
    if(showSelection && idx===state.selectedImage){ctx.strokeStyle='rgba(37,99,235,.95)'; ctx.lineWidth=4; ctx.strokeRect(-outerW/2+2,-outerH/2+2,outerW-4,outerH-4);}
    ctx.restore(); return;
  }
  const bounds=getSlotBounds(slot);
  drawFrame(slot);
  ctx.save();
  ctx.shadowColor='rgba(0,0,0,.16)';
  ctx.shadowBlur=shadow;
  ctx.shadowOffsetY=Math.max(2,Math.round(shadow/3));
  pathForSlot(ctx, slot);
  ctx.clip();
  const p=getDrawParams(item.img,bounds,item);
  ctx.globalAlpha=item.opacity;
  ctx.translate(bounds.x+bounds.w/2,bounds.y+bounds.h/2);
  ctx.rotate(item.rotation*Math.PI/180);
  ctx.drawImage(item.img,p.x-(bounds.x+bounds.w/2),p.y-(bounds.y+bounds.h/2),p.w,p.h);
  ctx.restore();
  if(showSelection && idx===state.selectedImage){
    ctx.save();
    ctx.strokeStyle='rgba(37,99,235,.95)';
    ctx.lineWidth=4;
    pathForSlot(ctx, slot);
    ctx.stroke();
    if(state.adjustImageMode){
      ctx.setLineDash([12,10]);
      ctx.strokeStyle='rgba(255,255,255,.95)';
      ctx.lineWidth=2;
      pathForSlot(ctx, slot);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle='rgba(17,24,39,.82)';
      roundRectPath(ctx,bounds.x+14,bounds.y+14,168,34,10);
      ctx.fill();
      ctx.fillStyle='#ffffff';
      ctx.font='600 16px Arial';
      ctx.textAlign='left';
      ctx.textBaseline='middle';
      ctx.fillText('Adjust image mode', bounds.x+28, bounds.y+31);
      ctx.beginPath();
      ctx.arc(bounds.x+24, bounds.y+31, 5, 0, Math.PI*2);
      ctx.fill();
    }
    ctx.restore();
  }
}
function drawTextLayer(t,idx,showSelection=true){
  ctx.save(); ctx.translate(t.x,t.y); ctx.rotate(t.rotation*Math.PI/180); ctx.globalAlpha=t.opacity; ctx.textAlign=t.align; ctx.textBaseline='top'; ctx.fillStyle=t.color; ctx.shadowColor=`rgba(0,0,0,${Math.min(.8,t.shadow/40)})`; ctx.shadowBlur=t.shadow;
  const weight=t.bold?'700':'400', style=t.italic?'italic ':'';
  ctx.font=`${style}${weight} ${t.size}px ${t.fontFamily}`; const lines=t.text.split('\n'); const lineH=t.size*1.14;
  lines.forEach((line,i)=>{if(t.strokeWidth>0){ctx.lineWidth=t.strokeWidth; ctx.strokeStyle=t.strokeColor; ctx.strokeText(line,0,i*lineH);} ctx.fillText(line,0,i*lineH);});
  if(showSelection && idx===state.selectedText){const widths=lines.map(line=>ctx.measureText(line).width); const maxW=Math.max(40,...widths); let bx=0; if(t.align==='center') bx=-maxW/2; if(t.align==='right') bx=-maxW; ctx.shadowColor='transparent'; ctx.globalAlpha=1; ctx.strokeStyle='rgba(37,99,235,.95)'; ctx.lineWidth=2; ctx.strokeRect(bx-8,-8,maxW+16,lineH*lines.length+10);}
  ctx.restore();
}
function drawHeartPath(x,y,w,h){ctx.beginPath(); const tch=h*0.3; ctx.moveTo(x,y+tch); ctx.bezierCurveTo(x,y,x-w/2,y,x-w/2,y+tch); ctx.bezierCurveTo(x-w/2,y+(h+tch)/2,x,y+(h+tch)/2,x,y+h); ctx.bezierCurveTo(x,y+(h+tch)/2,x+w/2,y+(h+tch)/2,x+w/2,y+tch); ctx.bezierCurveTo(x+w/2,y,x,y,x,y+tch); ctx.closePath();}
function drawStarPath(cx,cy,spikes,outerR,innerR){let rot=Math.PI/2*3,x=cx,y=cy; const step=Math.PI/spikes; ctx.beginPath(); ctx.moveTo(cx,cy-outerR); for(let i=0;i<spikes;i++){x=cx+Math.cos(rot)*outerR; y=cy+Math.sin(rot)*outerR; ctx.lineTo(x,y); rot+=step; x=cx+Math.cos(rot)*innerR; y=cy+Math.sin(rot)*innerR; ctx.lineTo(x,y); rot+=step;} ctx.lineTo(cx,cy-outerR); ctx.closePath();}
function drawDeco(d,idx,showSelection=true){
  ctx.save(); ctx.translate(d.x,d.y); ctx.rotate(d.rotation*Math.PI/180); ctx.globalAlpha=d.opacity; ctx.fillStyle=d.color; ctx.strokeStyle='#ffffff'; ctx.lineWidth=d.strokeWidth;
  if(d.type==='tape'){roundRectPath(ctx,-d.w/2,-d.h/2,d.w,d.h,6); ctx.fill(); if(d.strokeWidth>0) ctx.stroke();}
  else if(d.type==='heart'){drawHeartPath(0,-d.h/2,d.w,d.h); ctx.fill(); if(d.strokeWidth>0) ctx.stroke();}
  else if(d.type==='star'){drawStarPath(0,0,5,d.w/2,d.w/4); ctx.fill(); if(d.strokeWidth>0) ctx.stroke();}
  else if(d.type==='circle'){ctx.beginPath(); ctx.ellipse(0,0,d.w/2,d.h/2,0,0,Math.PI*2); ctx.fill(); if(d.strokeWidth>0) ctx.stroke();}
  if(showSelection && idx===state.selectedDeco){ctx.globalAlpha=1; ctx.strokeStyle='rgba(37,99,235,.95)'; ctx.lineWidth=2; ctx.strokeRect(-d.w/2-6,-d.h/2-6,d.w+12,d.h+12); ctx.fillStyle='rgba(37,99,235,.98)'; ctx.fillRect(d.w/2+2,d.h/2+2,14,14);}
  ctx.restore();
}

function updatePreviewScale(){
  const mode=els.previewMode.value, zoom=parseFloat(els.previewZoom.value||1), wrap=els.canvasWrap, canvas=els.canvas;
  const canvasRatio=canvas.width/canvas.height, wrapW=Math.max(200,wrap.clientWidth-40), wrapH=Math.max(200,wrap.clientHeight-40);
  let baseScale=1; if(mode==='fit') baseScale=Math.min(wrapW/canvas.width, wrapH/canvas.height); else if(mode==='fillWidth') baseScale=wrapW/canvas.width;
  const finalScale=Math.max(0.15, baseScale*zoom), scaledW=Math.round(canvas.width*finalScale);
  els.canvasScaler.style.transform='none'; els.canvasScaler.style.width=scaledW+'px'; els.canvasScaler.style.height='auto'; canvas.style.width=scaledW+'px'; canvas.style.height='auto';
  if(mode==='fillWidth' || mode==='actual'){els.canvasWrap.style.alignItems='flex-start'; els.canvasWrap.style.justifyContent='flex-start';}
  else {els.canvasWrap.style.alignItems='flex-start'; els.canvasWrap.style.justifyContent='center';}
}

function renderCanvas(showSelection=true, exportMode=false){
  const w=parseInt(els.outW.value||1800,10), h=parseInt(els.outH.value||1200,10), gap=parseInt(els.gap.value||0,10), count=activeImageCount();
  els.canvas.width=w; els.canvas.height=h; ctx.clearRect(0,0,w,h); drawBackground(w,h,exportMode);
  const slots=getSlots(w,h,gap,count);
  const shapeClipped = exportMode && isShapeLayoutStyle(els.layoutStyle.value);
  if(shapeClipped){
    clipToGlobalShape(els.layoutStyle.value,w,h,gap);
  }
  for(let i=0;i<count;i++){
    const item=state.images[i];
    if(item&&item.img.complete){
      if(els.layoutStyle.value==='freeform'){
        if(!item.freeSlot) item.freeSlot=slots[i];
        drawOneImage(item,item.freeSlot||slots[i],i,showSelection);
      } else {
        drawOneImage(item,slots[i],i,showSelection);
      }
    }
  }
  drawShapeLayoutDividers(els.layoutStyle.value,w,h,gap,count);
  drawCustomSplitOverlay(w,h,gap);
  drawSnapDrawOverlay(w,h,gap);
  if(showSelection && state.dragType==='image-swap' && state.swapHoverIndex>=0){
    const swapSlot = els.layoutStyle.value==='freeform' ? (state.images[state.swapHoverIndex]?.freeSlot || slots[state.swapHoverIndex]) : slots[state.swapHoverIndex];
    drawSwapTarget(swapSlot);
  }
  state.decos.forEach((d,idx)=>drawDeco(d,idx,showSelection));
  state.texts.forEach((t,idx)=>drawTextLayer(t,idx,showSelection));
  if(shapeClipped) restoreGlobalShapeClip(true);
  if(state.images.length < count){
    ctx.save(); ctx.fillStyle='rgba(0,0,0,.48)'; ctx.textAlign='center'; ctx.font='600 30px Arial';
    ctx.fillText(`Add at least ${count} image(s) for this layout`, w/2, h/2); ctx.restore();
  }
}
function draw(){
  renderCanvas(true);
  updatePreviewScale();
}

function loadFiles(fileList){
  const files=Array.from(fileList||[]).filter(f=>f.type.startsWith('image/'));
  files.forEach(file=>{const url=URL.createObjectURL(file); const img=new Image(); img.onload=draw; img.src=url; state.images.push({file,url,img,zoom:1,offsetX:0,offsetY:0,rotation:0,opacity:1,freeSlot:{x:80+(state.images.length*35),y:80+(state.images.length*28),w:420,h:300,freeform:true}});});
  els.imageCount.value = Math.min(parseInt(els.imageCount.value||6,10), Math.min(state.images.length || 1, MAX_COLLAGE_IMAGES));
  renderThumbs(); syncImageControls(); draw();
  commitHistory();
}
function updateSelectedImageFromControls(){const item=state.images[state.selectedImage]; if(!item) return; item.zoom=parseFloat(els.zoom.value); if(els.layoutStyle.value==='freeform'){ item.freeSlot.x=parseFloat(els.offsetX.value||0); item.freeSlot.y=parseFloat(els.offsetY.value||0); } else { item.offsetX=parseFloat(els.offsetX.value||0); item.offsetY=parseFloat(els.offsetY.value||0); } item.rotation=parseFloat(els.rotation.value||0); item.opacity=parseFloat(els.opacity.value||1); renderThumbs(); draw();}
function defaultText(){return {text:'Your text here',fontFamily:'Arial, Helvetica, sans-serif',size:80,color:'#ffffff',align:'left',opacity:1,x:120,y:120,rotation:0,shadow:12,strokeColor:'#000000',strokeWidth:0,bold:true,italic:false};}
function applyTextPreset(name){const t=state.texts[state.selectedText]; if(!t) return; if(name==='title') Object.assign(t,{fontFamily:'Impact, sans-serif',size:120,color:'#ffffff',bold:true,italic:false,shadow:16}); if(name==='script') Object.assign(t,{fontFamily:'"Brush Script MT", cursive',size:96,color:'#ffffff',bold:false,italic:false,shadow:12}); if(name==='poster') Object.assign(t,{fontFamily:'"Trebuchet MS", sans-serif',size:72,color:'#111111',bold:true,italic:false,shadow:0}); if(name==='caption') Object.assign(t,{fontFamily:'Georgia, serif',size:42,color:'#ffffff',bold:false,italic:true,shadow:10}); syncTextControls(); renderTextList(); draw();}
function updateSelectedTextFromControls(){const t=state.texts[state.selectedText]; if(!t) return; t.text=els.textContent.value; t.fontFamily=els.fontFamily.value; t.size=parseFloat(els.fontSize.value||80); t.color=els.textColor.value; t.align=els.textAlign.value; t.opacity=parseFloat(els.textOpacity.value||1); t.x=parseFloat(els.textX.value||0); t.y=parseFloat(els.textY.value||0); t.rotation=parseFloat(els.textRotation.value||0); t.shadow=parseFloat(els.textShadow.value||0); t.strokeColor=getMaybeColor(els.strokeColor, els.strokeColorNone); t.strokeWidth=parseFloat(els.strokeWidth.value||0); t.bold=els.boldToggle.checked; t.italic=els.italicToggle.checked; renderTextList(); draw();}
function createDeco(type){const d={type,color:getMaybeColor(els.decoColor, els.decoColorNone),opacity:parseFloat(els.decoOpacity.value||0.9),x:parseFloat(els.decoX.value||100),y:parseFloat(els.decoY.value||100),w:parseFloat(els.decoW.value||140),h:parseFloat(els.decoH.value||40),rotation:parseFloat(els.decoRotation.value||0),strokeWidth:parseFloat(els.decoStroke.value||0)}; state.decos.push(d); state.selectedDeco=state.decos.length-1; renderDecoList(); syncDecoControls(); draw();}
function updateSelectedDecoFromControls(){const d=state.decos[state.selectedDeco]; if(!d) return; d.color=getMaybeColor(els.decoColor, els.decoColorNone); d.opacity=parseFloat(els.decoOpacity.value||0.9); d.x=parseFloat(els.decoX.value||100); d.y=parseFloat(els.decoY.value||100); d.w=parseFloat(els.decoW.value||140); d.h=parseFloat(els.decoH.value||40); d.rotation=parseFloat(els.decoRotation.value||0); d.strokeWidth=parseFloat(els.decoStroke.value||0); renderDecoList(); draw();}

function pointOnCanvas(evt){const rect=els.canvas.getBoundingClientRect(); return {x:(evt.clientX-rect.left)*(els.canvas.width/rect.width), y:(evt.clientY-rect.top)*(els.canvas.height/rect.height)};}
function pickText(pt){
  for(let i=state.texts.length-1;i>=0;i--){const t=state.texts[i]; ctx.save(); const weight=t.bold?'700':'400', style=t.italic?'italic ':''; ctx.font=`${style}${weight} ${t.size}px ${t.fontFamily}`; const lines=t.text.split('\n'); const widths=lines.map(line=>ctx.measureText(line).width); const maxW=Math.max(40,...widths); const lineH=t.size*1.14; const totalH=lineH*lines.length; let bx=t.x; if(t.align==='center') bx=t.x-maxW/2; if(t.align==='right') bx=t.x-maxW; ctx.restore(); if(pt.x>=bx-10&&pt.x<=bx+maxW+10&&pt.y>=t.y-10&&pt.y<=t.y+totalH+10) return i;}
  return -1;
}
function pickDeco(pt){for(let i=state.decos.length-1;i>=0;i--){const d=state.decos[i]; if(pt.x>=d.x-d.w/2-10&&pt.x<=d.x+d.w/2+18&&pt.y>=d.y-d.h/2-10&&pt.y<=d.y+d.h/2+18) return i;} return -1;}
function pointHitsDecoResizeHandle(pt,d){const hx=d.x+d.w/2+9, hy=d.y+d.h/2+9; return pt.x>=hx-12&&pt.x<=hx+12&&pt.y>=hy-12&&pt.y<=hy+12;}
function pickImage(pt){
  const slots=getSlots(els.canvas.width, els.canvas.height, parseInt(els.gap.value||0,10), activeImageCount());
  for(let i=Math.min(slots.length,state.images.length)-1;i>=0;i--){const s=els.layoutStyle.value==='freeform'?(state.images[i].freeSlot||slots[i]):slots[i]; if(pointInSlot(pt,s)) return i;}
  return -1;
}

els.filesButton.onclick=()=>els.files.click();
els.files.addEventListener('change', e=>{
  const files = Array.from(e.target.files || []);
  if(files.length === 0){
    els.filesLabel.textContent = 'No files selected';
  } else if(files.length === 1){
    els.filesLabel.textContent = files[0].name;
  } else {
    els.filesLabel.textContent = `${files.length} files selected`;
  }
  loadFiles(e.target.files);
});
[els.imageCount, els.layoutStyle, els.outW, els.outH, els.gap, els.cornerRadius, els.shapeInnerSize, els.backgroundMode, els.bg, els.bg2, els.fitMode, els.frameColor, els.frameWidth, els.shadowStrength, els.paperGrain, els.bg2None, els.frameColorNone].forEach(el=>{if(!el) return; el.addEventListener('input',()=>{ if(el===els.layoutStyle){ updateCustomSplitUi(); updateSnapDrawUi(); if(els.layoutStyle.value==='customSplit') ensureCustomSplitRooms(); if(els.layoutStyle.value==='snapDraw') ensureSnapDrawPolygons(); } updateColorPreviews(); draw();}); el.addEventListener('change',()=>{ if(el===els.layoutStyle){ updateCustomSplitUi(); updateSnapDrawUi(); if(els.layoutStyle.value==='customSplit') ensureCustomSplitRooms(); if(els.layoutStyle.value==='snapDraw') ensureSnapDrawPolygons(); } updateColorPreviews(); draw(); commitHistory();});});
[els.zoom, els.offsetX, els.offsetY, els.rotation, els.opacity].forEach(el=>{ el.addEventListener('input', updateSelectedImageFromControls); el.addEventListener('change', ()=>{ updateSelectedImageFromControls(); commitHistory(); }); });
[els.textContent, els.fontFamily, els.fontSize, els.textColor, els.textAlign, els.textOpacity, els.textX, els.textY, els.textRotation, els.textShadow, els.strokeColor, els.strokeWidth, els.boldToggle, els.italicToggle, els.strokeColorNone].forEach(el=>{if(!el) return; el.addEventListener('input',()=>{updateColorPreviews(); updateSelectedTextFromControls();}); el.addEventListener('change',()=>{updateColorPreviews(); updateSelectedTextFromControls(); commitHistory();});});
[els.decoColor, els.decoOpacity, els.decoX, els.decoY, els.decoW, els.decoH, els.decoRotation, els.decoStroke, els.decoColorNone].forEach(el=>{if(!el) return; el.addEventListener('input',()=>{updateColorPreviews(); updateSelectedDecoFromControls();}); el.addEventListener('change',()=>{updateColorPreviews(); updateSelectedDecoFromControls(); commitHistory();});});

els.applyLayoutDefaults.onclick=()=>{applyLayoutDefaults(); commitHistory();}; els.applyThemePack.onclick=()=>{applyThemePack(); commitHistory();}; els.applyOneClick.onclick=()=>{applyOneClickTemplate(); commitHistory();}; if(els.shuffleLayout) els.shuffleLayout.onclick=()=>{shuffleLayoutVariant(); commitHistory();}; els.renderBtn.onclick=draw; if(els.undoBtn) els.undoBtn.onclick=undoHistory; if(els.redoBtn) els.redoBtn.onclick=redoHistory; if(els.saveProjectBtn) els.saveProjectBtn.onclick=saveProject; if(els.openProjectBtn) els.openProjectBtn.onclick=()=>els.openProjectInput && els.openProjectInput.click(); if(els.openProjectInput) els.openProjectInput.addEventListener('change', e=>{ const file=e.target.files&&e.target.files[0]; openProjectFile(file); e.target.value=''; });
els.previewMode.onchange=updatePreviewScale; els.previewZoom.oninput=updatePreviewScale; window.addEventListener('resize', updatePreviewScale);
if(els.moveUp) els.moveUp.onclick=()=>nudgeSelectedImage(0, -getSelectedNudgeStep());
if(els.moveDown) els.moveDown.onclick=()=>nudgeSelectedImage(0, getSelectedNudgeStep());
if(els.moveLeft) els.moveLeft.onclick=()=>nudgeSelectedImage(-getSelectedNudgeStep(), 0);
if(els.moveRight) els.moveRight.onclick=()=>nudgeSelectedImage(getSelectedNudgeStep(), 0);
if(els.zoomInBtn) els.zoomInBtn.onclick=()=>zoomSelectedImage(0.1);
if(els.zoomOutBtn) els.zoomOutBtn.onclick=()=>zoomSelectedImage(-0.1);
if(els.centerImageBtn) els.centerImageBtn.onclick=centerSelectedImage;
if(els.adjustImageModeBtn) els.adjustImageModeBtn.onclick=toggleAdjustImageMode;
if(els.customSplitDrawMode) els.customSplitDrawMode.addEventListener('change', ()=>{ updateCustomSplitUi(); draw(); commitHistory(); });
if(els.customSplitReset) els.customSplitReset.onclick=()=>{ resetCustomSplitRooms(); draw(); commitHistory(); };
if(els.snapDrawMode) els.snapDrawMode.addEventListener('change', ()=>{ updateSnapDrawUi(); draw(); commitHistory(); });
if(els.snapDrawReset) els.snapDrawReset.onclick=()=>{ resetSnapDrawPolygons(); draw(); commitHistory(); };
els.downloadBtn.onclick=()=>{renderCanvas(false,true); const a=document.createElement('a'); a.href=els.canvas.toDataURL('image/png'); a.download='collage-pro-v38.png'; a.click(); draw();};
els.resetImage.onclick=()=>{const item=state.images[state.selectedImage]; if(!item) return; Object.assign(item,{zoom:1,offsetX:0,offsetY:0,rotation:0,opacity:1}); if(item.freeSlot){ item.freeSlot.x=80; item.freeSlot.y=80; } syncImageControls(); renderThumbs(); draw(); commitHistory();};
els.resetAll.onclick=()=>{state.images.forEach(item=>Object.assign(item,{zoom:1,offsetX:0,offsetY:0,rotation:0,opacity:1})); syncImageControls(); renderThumbs(); draw(); commitHistory();};
els.bringFront.onclick=()=>{const idx=state.selectedImage; if(idx<0||idx>=state.images.length) return; const item=state.images.splice(idx,1)[0]; state.images.push(item); state.selectedImage=state.images.length-1; renderThumbs(); draw(); commitHistory();};
els.sendBack.onclick=()=>{const idx=state.selectedImage; if(idx<0||idx>=state.images.length) return; const item=state.images.splice(idx,1)[0]; state.images.unshift(item); state.selectedImage=0; renderThumbs(); draw(); commitHistory();};
els.addText.onclick=()=>{state.texts.push(defaultText()); state.selectedText=state.texts.length-1; syncTextControls(); renderTextList(); draw(); commitHistory();};
els.removeText.onclick=()=>{if(state.selectedText<0) return; state.texts.splice(state.selectedText,1); state.selectedText=Math.min(state.selectedText,state.texts.length-1); if(state.selectedText>=0) syncTextControls(); renderTextList(); draw(); commitHistory();};
els.textPreset.onchange=()=>{if(els.textPreset.value!=='custom') applyTextPreset(els.textPreset.value);};
els.addTape.onclick=()=>{createDeco('tape'); commitHistory();}; els.addHeart.onclick=()=>{createDeco('heart'); commitHistory();}; els.addStar.onclick=()=>{createDeco('star'); commitHistory();}; els.addCircle.onclick=()=>{createDeco('circle'); commitHistory();};
els.removeDeco.onclick=()=>{if(state.selectedDeco<0) return; state.decos.splice(state.selectedDeco,1); state.selectedDeco=Math.min(state.selectedDeco,state.decos.length-1); if(state.selectedDeco>=0) syncDecoControls(); renderDecoList(); draw(); commitHistory();};

els.canvas.addEventListener('mousedown', evt=>{
  const pt=pointOnCanvas(evt);
  if(els.layoutStyle.value==='snapDraw' && els.snapDrawMode && els.snapDrawMode.checked){
    const w=parseInt(els.outW.value||1800,10), h=parseInt(els.outH.value||1200,10), gap=parseInt(els.gap.value||0,10);
    const polyIndex=findSnapDrawPolygonIndex(pt,w,h,gap);
    if(polyIndex>=0){
      const poly=getSnapDrawSlots(w,h,gap,state.snapDrawPolygons.length)[polyIndex];
      const start=getSnapPointForPolygon(pt, poly);
      if(start){
        state.dragging=true;
        state.pendingDragHistory=true;
        state.dragType='snap-draw';
        state.dragStart=pt;
        state.snapDrawGuide={polyIndex,start,current:start,poly};
        els.canvas.classList.add('dragging');
        draw();
        return;
      }
    }
  }
  if(els.layoutStyle.value==='customSplit' && els.customSplitDrawMode && els.customSplitDrawMode.checked){
    const w=parseInt(els.outW.value||1800,10), h=parseInt(els.outH.value||1200,10), gap=parseInt(els.gap.value||0,10);
    const roomIndex=findCustomSplitRoomIndex(pt,w,h,gap);
    if(roomIndex>=0){
      const slot=getCustomSplitSlots(w,h,gap,state.customSplitRooms.length)[roomIndex];
      state.dragging=true;
      state.pendingDragHistory=true;
      state.dragType='custom-split';
      state.dragStart=pt;
      state.customSplitGuide={roomIndex,start:pt,current:pt,orientation:'vertical',slot,x:pt.x,y:pt.y};
      els.canvas.classList.add('dragging');
      draw();
      return;
    }
  }
  const decoIdx=pickDeco(pt);
  if(decoIdx>=0){state.selectedDeco=decoIdx; syncDecoControls(); renderDecoList(); draw(); state.dragging=true; state.pendingDragHistory=true; state.dragStart=pt; const d=state.decos[decoIdx]; if(pointHitsDecoResizeHandle(pt,d)){state.dragType='deco-resize'; state.startOffsets={w:d.w,h:d.h};} else {state.dragType='deco'; state.startOffsets={x:d.x,y:d.y};} els.canvas.classList.add('dragging'); return;}
  const textIdx=pickText(pt);
  if(textIdx>=0){state.selectedText=textIdx; syncTextControls(); renderTextList(); draw(); state.dragging=true; state.pendingDragHistory=true; state.dragType='text'; state.dragStart=pt; const t=state.texts[textIdx]; state.startOffsets={x:t.x,y:t.y}; els.canvas.classList.add('dragging'); return;}
  const imgIdx=pickImage(pt);
  if(imgIdx>=0){
    state.selectedImage=imgIdx; state.dragOriginIndex=imgIdx; state.swapHoverIndex=-1; syncImageControls(); renderThumbs(); draw(); state.dragging=true; state.pendingDragHistory=true; state.dragStart=pt;
    const swapMode = !!(els.swapOnDrag && els.swapOnDrag.checked);
    if(state.adjustImageMode && els.layoutStyle.value !== 'freeform'){
      const it=state.images[imgIdx];
      state.dragType='image-adjust';
      state.startOffsets={x:it.offsetX,y:it.offsetY};
    } else if(swapMode){
      state.dragType='image-swap';
    } else {
      state.dragType='image';
      if(els.layoutStyle.value==='freeform'){const s=state.images[imgIdx].freeSlot; state.startOffsets={x:s.x,y:s.y};} else {const it=state.images[imgIdx]; state.startOffsets={x:it.offsetX,y:it.offsetY};}
    }
    els.canvas.classList.add('dragging');
  }
});
window.addEventListener('mousemove', evt=>{
  if(!state.dragging) return; const pt=pointOnCanvas(evt), dx=pt.x-state.dragStart.x, dy=pt.y-state.dragStart.y;
  if(state.dragType==='deco'){const d=state.decos[state.selectedDeco]; if(!d) return; d.x=state.startOffsets.x+dx; d.y=state.startOffsets.y+dy; syncDecoControls(); renderDecoList(); draw();}
  else if(state.dragType==='deco-resize'){const d=state.decos[state.selectedDeco]; if(!d) return; d.w=Math.max(20,state.startOffsets.w+dx); d.h=Math.max(20,state.startOffsets.h+dy); syncDecoControls(); renderDecoList(); draw();}
  else if(state.dragType==='text'){const t=state.texts[state.selectedText]; if(!t) return; t.x=state.startOffsets.x+dx; t.y=state.startOffsets.y+dy; syncTextControls(); renderTextList(); draw();}
  else if(state.dragType==='image'){const it=state.images[state.selectedImage]; if(!it) return; if(els.layoutStyle.value==='freeform'){it.freeSlot.x=state.startOffsets.x+dx; it.freeSlot.y=state.startOffsets.y+dy;} else {it.offsetX=state.startOffsets.x+dx; it.offsetY=state.startOffsets.y+dy; syncImageControls();} renderThumbs(); draw();}
  else if(state.dragType==='image-adjust'){const it=state.images[state.selectedImage]; if(!it) return; it.offsetX=state.startOffsets.x+dx; it.offsetY=state.startOffsets.y+dy; syncImageControls(); renderThumbs(); draw();}
  else if(state.dragType==='image-swap'){const hoverIdx=pickImage(pt); state.swapHoverIndex=(hoverIdx>=0 && hoverIdx!==state.dragOriginIndex)?hoverIdx:-1; draw();}
  else if(state.dragType==='snap-draw'){
    if(!state.snapDrawGuide) return;
    const g=state.snapDrawGuide;
    const snap=getSnapPointForPolygon(pt, g.poly);
    if(snap) g.current=snap;
    draw();
  }
  else if(state.dragType==='custom-split'){
    if(!state.customSplitGuide) return;
    const g=state.customSplitGuide;
    const dx=pt.x-g.start.x, dy=pt.y-g.start.y;
    g.current=pt;
    g.orientation=Math.abs(dx)>=Math.abs(dy)?'vertical':'horizontal';
    if(g.orientation==='vertical'){
      g.x=Math.max(g.slot.x+g.slot.w*0.08, Math.min(g.slot.x+g.slot.w*0.92, pt.x));
      g.y=pt.y;
    } else {
      g.y=Math.max(g.slot.y+g.slot.h*0.08, Math.min(g.slot.y+g.slot.h*0.92, pt.y));
      g.x=pt.x;
    }
    draw();
  }
});

els.canvas.addEventListener('dblclick', evt=>{
  const pt=pointOnCanvas(evt);
  const imgIdx=pickImage(pt);
  if(imgIdx>=0){
    state.selectedImage=imgIdx;
    syncImageControls();
    renderThumbs();
    setAdjustImageMode(true);
  }
});

els.canvas.addEventListener('wheel', evt=>{
  if(!state.adjustImageMode) return;
  const pt=pointOnCanvas(evt);
  const imgIdx=pickImage(pt);
  if(imgIdx<0) return;
  evt.preventDefault();
  state.selectedImage=imgIdx;
  const item=state.images[imgIdx];
  if(!item) return;
  const delta = evt.deltaY < 0 ? 0.08 : -0.08;
  item.zoom = Math.max(0.2, Math.min(4, Math.round((item.zoom + delta) * 100) / 100));
  syncImageControls();
  renderThumbs();
  draw();
  clearTimeout(state.adjustWheelCommitTimer);
  state.adjustWheelCommitTimer = setTimeout(()=>commitHistory(), 140);
}, {passive:false});

window.addEventListener('mouseup', ()=>{
  const hadDrag = state.dragging && state.pendingDragHistory;
  if(state.dragType==='snap-draw' && state.snapDrawGuide){
    const w=parseInt(els.outW.value||1800,10), h=parseInt(els.outH.value||1200,10), gap=parseInt(els.gap.value||0,10);
    const g=state.snapDrawGuide;
    const changed=splitSnapPolygonAt(g.polyIndex, g.start, g.current, w, h, gap);
    state.snapDrawGuide=null;
    state.dragging=false; state.dragType=null; state.swapHoverIndex=-1; state.dragOriginIndex=-1; state.pendingDragHistory=false; els.canvas.classList.remove('dragging'); draw();
    if(changed) commitHistory();
    return;
  }
  if(state.dragType==='custom-split' && state.customSplitGuide){
    const w=parseInt(els.outW.value||1800,10), h=parseInt(els.outH.value||1200,10), gap=parseInt(els.gap.value||0,10);
    const g=state.customSplitGuide;
    const changed=splitCustomRoomAt(g.roomIndex, g.orientation, g.orientation==='vertical' ? g.x : g.y, w, h, gap);
    state.customSplitGuide=null;
    state.dragging=false; state.dragType=null; state.swapHoverIndex=-1; state.dragOriginIndex=-1; state.pendingDragHistory=false; els.canvas.classList.remove('dragging'); draw();
    if(changed) commitHistory();
    return;
  }
  if(state.dragType==='image-swap' && state.dragOriginIndex>=0 && state.swapHoverIndex>=0){
    swapImageItems(state.dragOriginIndex, state.swapHoverIndex);
  }
  state.dragging=false; state.dragType=null; state.swapHoverIndex=-1; state.dragOriginIndex=-1; state.pendingDragHistory=false; els.canvas.classList.remove('dragging'); draw();
  if(hadDrag) commitHistory();
});
window.addEventListener('keydown', (evt)=>{const tag=(document.activeElement&&document.activeElement.tagName)?document.activeElement.tagName.toLowerCase():''; const typing=tag==='input'||tag==='textarea'||document.activeElement?.isContentEditable; const mod=evt.metaKey||evt.ctrlKey; if(mod && evt.key.toLowerCase()==='z' && !evt.shiftKey){evt.preventDefault(); undoHistory(); return;} if(mod && (evt.key.toLowerCase()==='y' || (evt.shiftKey && evt.key.toLowerCase()==='z'))){evt.preventDefault(); redoHistory(); return;} if(typing) return; if(evt.key.toLowerCase()==='a'){evt.preventDefault(); toggleAdjustImageMode(); return;} if(evt.key==='Escape' && state.adjustImageMode){evt.preventDefault(); setAdjustImageMode(false); return;} if((evt.key==='='||evt.key==='+') && state.adjustImageMode){evt.preventDefault(); zoomSelectedImage(0.1); return;} if((evt.key==='-'||evt.key==='_') && state.adjustImageMode){evt.preventDefault(); zoomSelectedImage(-0.1); return;} if((evt.key==='Backspace'||evt.key==='Delete')&&state.selectedDeco>=0){evt.preventDefault(); state.decos.splice(state.selectedDeco,1); state.selectedDeco=Math.min(state.selectedDeco,state.decos.length-1); if(state.selectedDeco>=0) syncDecoControls(); renderDecoList(); draw(); commitHistory(); return;} if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(evt.key)){evt.preventDefault(); const step=getSelectedNudgeStep(evt.shiftKey?5:1); if(evt.key==='ArrowUp') nudgeSelectedImage(0,-step); else if(evt.key==='ArrowDown') nudgeSelectedImage(0,step); else if(evt.key==='ArrowLeft') nudgeSelectedImage(-step,0); else if(evt.key==='ArrowRight') nudgeSelectedImage(step,0); }});

updateColorPreviews(); updateCustomSplitUi(); updateSnapDrawUi(); renderThumbs(); renderTextList(); renderDecoList(); syncImageControls(); syncTextControls(); syncDecoControls(); refreshUndoRedoButtons(); updateAdjustModeUi(); draw(); commitHistory(false);
