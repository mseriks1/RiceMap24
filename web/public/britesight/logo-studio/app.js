const templates=[{id:'clean-wordmark',name:'Clean Wordmark',family:'Professional'},{id:'food-badge',name:'Food Badge',family:'Food'},{id:'stacked-seal',name:'Stacked Seal',family:'Professional'},{id:'modern-app',name:'Modern App Icon',family:'Digital'},{id:'monogram',name:'Monogram',family:'Minimal'},{id:'signature-brand',name:'Signature Brand',family:'Elegant'},{id:'banner-lockup',name:'Banner Lockup',family:'Marketing'},{id:'stamp-round',name:'Round Stamp',family:'Badge'},{id:'premium-line',name:'Premium Line',family:'Minimal'},{id:'boxed-identity',name:'Boxed Identity',family:'Professional'},{id:'vertical-brand',name:'Vertical Brand',family:'Professional'},{id:'startup-glow',name:'Startup Glow',family:'Digital'},{id:'chef-seal',name:'Chef Seal',family:'Restaurant'},{id:'takeaway-label',name:'Takeaway Label',family:'Restaurant'},{id:'window-sign',name:'Window Sign',family:'Restaurant'},{id:'delivery-badge',name:'Delivery Badge',family:'Restaurant'},{id:'menu-stamp',name:'Menu Stamp',family:'Restaurant'},{id:'artisan-plate',name:'Artisan Plate',family:'Restaurant'},{id:'capsule-lockup',name:'Capsule Lockup',family:'Modern'},{id:'corner-frame',name:'Corner Frame',family:'Professional'},{id:'hero-panel',name:'Hero Panel',family:'Branding'},{id:'minimal-chip',name:'Minimal Chip',family:'Minimal'}];
const shapes=[{id:'circle',name:'Circle',cat:'general'},{id:'square',name:'Square',cat:'general'},{id:'diamond',name:'Diamond',cat:'general'},{id:'ring',name:'Ring',cat:'general'},{id:'spark',name:'Spark',cat:'general'},{id:'starburst',name:'Starburst',cat:'general'},{id:'wave',name:'Wave',cat:'general'},{id:'mountain',name:'Mountain',cat:'general'},{id:'sun',name:'Sun',cat:'general'},{id:'heart',name:'Heart',cat:'general'},{id:'bolt',name:'Bolt',cat:'general'},{id:'hex',name:'Hex',cat:'general'},{id:'orbit',name:'Orbit',cat:'general'},{id:'ribbon',name:'Ribbon',cat:'general'},{id:'grid-dot',name:'Grid Dot',cat:'general'},{id:'arc',name:'Arc',cat:'general'},{id:'lens',name:'Lens',cat:'general'},{id:'shield',name:'Shield',cat:'general'},{id:'bloom',name:'Bloom',cat:'general'},{id:'pinwheel',name:'Pinwheel',cat:'general'},{id:'link',name:'Link',cat:'general'},{id:'droplet',name:'Droplet',cat:'general'},{id:'crown',name:'Crown',cat:'general'},{id:'signal',name:'Signal',cat:'general'},{id:'halo-line',name:'Halo Line',cat:'general'},{id:'interlock-line',name:'Interlock',cat:'general'},{id:'ripple-line',name:'Ripple',cat:'general'},{id:'compass-line',name:'Compass',cat:'general'},{id:'constellation-line',name:'Constellation',cat:'general'},{id:'petal-line',name:'Petal Line',cat:'general'},{id:'axis-line',name:'Axis',cat:'general'},{id:'knot-line',name:'Knot',cat:'general'},{id:'nest-line',name:'Nest',cat:'general'},{id:'path-line',name:'Path',cat:'general'},{id:'prism-line',name:'Prism',cat:'general'},{id:'mono-circle',name:'Monogram Circle',cat:'letters'},{id:'mono-square',name:'Monogram Square',cat:'letters'},{id:'mono-ring',name:'Monogram Ring',cat:'letters'},{id:'mono-split',name:'Monogram Split',cat:'letters'},{id:'mono-stamp',name:'Monogram Stamp',cat:'letters'},{id:'mono-line',name:'Monogram Line',cat:'letters'},{id:'bowl',name:'Food Bowl',cat:'restaurant'},{id:'wok',name:'Wok',cat:'restaurant'},{id:'pizza',name:'Pizza Slice',cat:'restaurant'},{id:'burger',name:'Burger',cat:'restaurant'},{id:'cup',name:'Coffee Cup',cat:'restaurant'},{id:'forkknife',name:'Fork & Knife',cat:'restaurant'},{id:'cloche',name:'Serving Cloche',cat:'restaurant'},{id:'takeaway-box',name:'Takeaway Box',cat:'restaurant'},{id:'sushi',name:'Sushi',cat:'restaurant'},{id:'noodles',name:'Noodles',cat:'restaurant'},{id:'taco',name:'Taco',cat:'restaurant'},{id:'icecream',name:'Ice Cream',cat:'restaurant'},{id:'fish',name:'Fish',cat:'restaurant'},{id:'coffee-bean',name:'Coffee Bean',cat:'restaurant'},{id:'croissant',name:'Croissant',cat:'restaurant'},{id:'plate',name:'Plate',cat:'restaurant'},{id:'whisk',name:'Whisk',cat:'restaurant'},{id:'loaf',name:'Loaf',cat:'restaurant'},{id:'grain',name:'Grain',cat:'restaurant'},{id:'mortar',name:'Mortar Bowl',cat:'restaurant'},{id:'bottle',name:'Bottle',cat:'restaurant'},{id:'ramen-real',name:'Ramen Bowl',cat:'restaurant'},{id:'burger-real',name:'Burger',cat:'restaurant'},{id:'pizza-real',name:'Pizza Box',cat:'restaurant'},{id:'takeaway-cup-real',name:'Takeaway Cup',cat:'restaurant'},{id:'delivery-bag-real',name:'Delivery Bag',cat:'restaurant'},{id:'chef-hat-real',name:'Chef Hat',cat:'restaurant'},{id:'cloche-real',name:'Serving Tray',cat:'restaurant'},{id:'dumplings-real',name:'Dumplings',cat:'restaurant'},{id:'bento-real',name:'Bento Box',cat:'restaurant'},{id:'pastry-real',name:'Pastry Box',cat:'restaurant'},{id:'skewer-real',name:'BBQ Skewer',cat:'restaurant'},{id:'soup-pot-real',name:'Soup Pot',cat:'restaurant'},{id:'coffee-real',name:'Coffee',cat:'restaurant'},{id:'flame',name:'Flame',cat:'restaurant'},{id:'chopsticks',name:'Chopsticks',cat:'restaurant'},];
const variantSeeds=[{id:0,name:'Main',template:null,accentShift:0,bgShift:0,shape:null,layout:null},{id:1,name:'Minimal',template:'clean-wordmark',accentShift:-18,bgShift:0,shape:'circle',layout:'icon-left'},{id:2,name:'Badge',template:'food-badge',accentShift:8,bgShift:6,shape:'bowl',layout:'icon-left'},{id:3,name:'App',template:'modern-app',accentShift:16,bgShift:-4,shape:'spark',layout:'icon-top'},{id:4,name:'Monogram',template:'monogram',accentShift:0,bgShift:0,shape:'square',layout:'icon-left'},{id:5,name:'Elegant',template:'signature-brand',accentShift:-8,bgShift:0,shape:'ring',layout:'icon-left'},{id:6,name:'Delivery',template:'delivery-badge',accentShift:10,bgShift:3,shape:'takeaway-box',layout:'stacked'},{id:7,name:'Chef',template:'chef-seal',accentShift:-10,bgShift:2,shape:'cloche',layout:'stacked'}];
const defaultState={mode:'generic',brand:'Nordic Studio',tagline:'Simple sound and design',badgeText:'HOME KITCHEN BRAND',brandSize:44,tagSize:14,brandWrap:320,tagWrap:360,badgeWrap:220,spacing:2,font:'Inter, sans-serif',canvasBg:'#ffffff',panelBg:'#ffffff',bg:'#ffffff',frameColor:'#7c3aed',fg:'#0f172a',tagColor:'#0f172a',accent:'#7c3aed',layout:'icon-left',shape:'circle',iconScale:100,iconGap:28,iconOffsetX:0,iconOffsetY:0,showTagline:true,caps:false,transparent:false,template:'clean-wordmark',customIcon:null,shapeCategory:'all',outlineIcon:false};
const restaurantPreset={mode:'restaurant',brand:'Urban Bites',tagline:'Fresh takeaway and delivery',badgeText:'HOME KITCHEN BRAND',brandSize:44,tagSize:14,brandWrap:320,tagWrap:360,badgeWrap:220,spacing:2,font:'Trebuchet MS, sans-serif',canvasBg:'#ffffff',panelBg:'#fffaf2',bg:'#ffffff',frameColor:'#ea580c',fg:'#2a1d14',tagColor:'#2a1d14',accent:'#ea580c',layout:'icon-left',shape:'takeaway-box',iconScale:100,iconGap:28,iconOffsetX:0,iconOffsetY:0,showTagline:true,caps:false,transparent:false,template:'takeaway-label',customIcon:null,shapeCategory:'all',outlineIcon:false};
const riceMapPreset={mode:'ricemap24',brand:'Home Kitchen',tagline:'Fresh homemade meals near you',badgeText:'HOME KITCHEN BRAND',brandSize:44,tagSize:14,brandWrap:250,tagWrap:330,badgeWrap:220,spacing:2,font:'Trebuchet MS, sans-serif',canvasBg:'#ffffff',panelBg:'#fffaf2',bg:'#ffffff',frameColor:'#f59e0b',fg:'#2a1d14',tagColor:'#2a1d14',accent:'#f59e0b',layout:'icon-left',shape:'bowl',iconScale:100,iconGap:28,iconOffsetX:0,iconOffsetY:0,showTagline:true,caps:false,transparent:false,template:'food-badge',customIcon:null,shapeCategory:'all',outlineIcon:false};
let state={...defaultState}; let selectedVariantId=0;
const refs={saveProjectBtn:document.getElementById('saveProjectBtn'),openProjectBtn:document.getElementById('openProjectBtn'),openProjectFile:document.getElementById('openProjectFile'),exportPanelPng:document.getElementById('exportPanelPng'),exportTransparentPng:document.getElementById('exportTransparentPng'),brand:document.getElementById('brand'),tagline:document.getElementById('tagline'),badgeText:document.getElementById('badgeText'),brandSize:document.getElementById('brandSize'),tagSize:document.getElementById('tagSize'),brandWrap:document.getElementById('brandWrap'),tagWrap:document.getElementById('tagWrap'),badgeWrap:document.getElementById('badgeWrap'),spacing:document.getElementById('spacing'),font:document.getElementById('font'),layout:document.getElementById('layoutSelect'),canvasBg:document.getElementById('canvasBg'),panelBg:document.getElementById('panelBg'),bg:document.getElementById('bg'),frameColor:document.getElementById('frameColor'),fg:document.getElementById('fg'),tagColor:document.getElementById('tagColor'),accent:document.getElementById('accent'),showTagline:document.getElementById('showTagline'),caps:document.getElementById('caps'),shapeCategory:document.getElementById('shapeCategory'),iconScale:document.getElementById('iconScale'),iconGap:document.getElementById('iconGap'),iconOffsetX:document.getElementById('iconOffsetX'),iconOffsetY:document.getElementById('iconOffsetY'),iconUpload:document.getElementById('iconUpload'),outlineIcon:document.getElementById('outlineIcon'),symbolSearch:document.getElementById('symbolSearch'),templateGrid:document.getElementById('templateGrid'),symbolGrid:document.getElementById('symbolGrid'),mainPreview:document.getElementById('mainPreview'),variantList:document.getElementById('variantList'),activeTemplateBadge:document.getElementById('activeTemplateBadge'),activeModeBadge:document.getElementById('activeModeBadge'),activeShapeBadge:document.getElementById('activeShapeBadge'),resetBtn:document.getElementById('resetBtn'),applyVariantToMain:document.getElementById('applyVariantToMain'),modePills:[...document.querySelectorAll('.pill')],tabBtns:[...document.querySelectorAll('.tab-btn')],tabPanels:[...document.querySelectorAll('.tab-panel')]};
function clamp(v,min,max){return Math.min(max,Math.max(min,v))} function hexToRgb(hex){const clean=hex.replace('#','');const bigint=parseInt(clean,16);if(clean.length!==6||Number.isNaN(bigint)) return {r:0,g:0,b:0}; return {r:(bigint>>16)&255,g:(bigint>>8)&255,b:bigint&255}} function rgbToHex(r,g,b){return '#'+[r,g,b].map(v=>clamp(v,0,255).toString(16).padStart(2,'0')).join('')} function shiftHex(hex,amount){const {r,g,b}=hexToRgb(hex); return rgbToHex(r+amount,g+amount,b+amount)} function initials(str){return str.split(' ').filter(Boolean).slice(0,2).map(w=>w[0]).join('').toUpperCase()||'LM'} function escapeXml(str){return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function pathStroke(outline,accent,fg){return outline?`fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"`:`fill="${accent}" stroke="none"`}
function monoText(cfg,size=40,weight=800,tracking=1.2){
  const mark=escapeXml(initials(cfg.brand));
  const letterSpacing = tracking ? ` letter-spacing="${tracking}"` : '';
  return `<text x="70" y="70" text-anchor="middle" dominant-baseline="central" fill="${cfg.fg}" font-family="Inter, Arial, sans-serif" font-size="${size}" font-weight="${weight}"${letterSpacing}>${mark}</text>`;
}

function shapeSvg(type,accent,fg,outline=false,cfg={}){
  switch(type){
    case 'circle':
      return outline
        ? `<circle cx="70" cy="70" r="36" fill="none" stroke="${accent}" stroke-width="12"/><circle cx="70" cy="70" r="10" fill="${fg}" />`
        : `<circle cx="70" cy="70" r="48" fill="${accent}" opacity="0.16"/><circle cx="70" cy="70" r="31" fill="${accent}"/><circle cx="70" cy="70" r="12" fill="${fg}" opacity="0.92"/>`;
    case 'square':
      return outline
        ? `<rect x="32" y="32" width="76" height="76" rx="22" fill="none" stroke="${accent}" stroke-width="10"/><rect x="56" y="56" width="28" height="28" rx="8" fill="${fg}"/>`
        : `<rect x="24" y="24" width="92" height="92" rx="24" fill="${accent}" opacity="0.16"/><rect x="39" y="39" width="62" height="62" rx="16" fill="${accent}"/><rect x="57" y="57" width="26" height="26" rx="8" fill="${fg}" opacity="0.92"/>`;
    case 'diamond':
      return `<rect x="26" y="26" width="88" height="88" rx="18" transform="rotate(45 70 70)" fill="${outline?'none':accent}" stroke="${accent}" stroke-width="${outline?10:0}" opacity="${outline?1:0.16}"/><rect x="44" y="44" width="52" height="52" rx="10" transform="rotate(45 70 70)" fill="${outline?'none':accent}" stroke="${outline?accent:'none'}" stroke-width="${outline?8:0}"/><circle cx="70" cy="70" r="11" fill="${fg}" opacity="0.92"/>`;
    case 'ring':
      return `<circle cx="70" cy="70" r="46" fill="none" stroke="${accent}" stroke-width="12" opacity="0.18"/><circle cx="70" cy="70" r="31" fill="none" stroke="${accent}" stroke-width="14"/><path d="M54 73c6 10 26 10 32-10" fill="none" stroke="${fg}" stroke-width="8" stroke-linecap="round"/>`;
    case 'spark':
      return `<circle cx="70" cy="70" r="48" fill="${accent}" opacity="0.12"/><path d="M70 26 82 56 114 70 82 84 70 114 58 84 26 70 58 56Z" ${pathStroke(outline,accent,fg)}/><circle cx="70" cy="70" r="10" fill="${fg}" opacity="0.9"/>`;
    case 'leaf':
      return `<path d="M70 25C46 28 32 50 32 73c0 23 16 42 38 42 27 0 38-24 38-46 0-23-14-40-38-44Z" ${pathStroke(outline,accent,fg)}/><path d="M49 82c13-10 25-22 39-39" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/>`;
    case 'flame':
      return outline
        ? `<path d="M69 113c-20 0-34-14-34-34 0-14 7-27 19-38 9-8 14-18 14-31 18 13 28 31 28 49 0 3 0 6-1 9 5-6 12-10 20-10 12 0 21 10 21 23 0 9-4 18-11 24-11 11-25 18-56 8Z" fill="none" stroke="${accent}" stroke-width="8" stroke-linejoin="round"/><path d="M71 99c-10 0-17-7-17-17 0-8 4-15 11-22 4-4 7-10 7-18 10 8 16 18 16 29 0 2 0 4-1 5 3-3 7-5 11-5 8 0 14 6 14 14 0 5-2 10-6 13-8 7-16 11-35 1Z" fill="none" stroke="${fg}" stroke-width="6" stroke-linejoin="round" opacity="0.92"/>`
        : `<path d="M69 113c-20 0-34-14-34-34 0-14 7-27 19-38 9-8 14-18 14-31 18 13 28 31 28 49 0 3 0 6-1 9 5-6 12-10 20-10 12 0 21 10 21 23 0 9-4 18-11 24-11 11-25 18-56 8Z" fill="${accent}" opacity="0.96"/><path d="M71 99c-10 0-17-7-17-17 0-8 4-15 11-22 4-4 7-10 7-18 10 8 16 18 16 29 0 2 0 4-1 5 3-3 7-5 11-5 8 0 14 6 14 14 0 5-2 10-6 13-8 7-16 11-35 1Z" fill="${fg}" opacity="0.9"/>`;
    case 'starburst':
      return `<path d="M70 22 79 49 108 42 91 67 118 82 89 89 96 118 70 101 44 118 51 89 22 82 49 67 32 42 61 49Z" ${pathStroke(outline,accent,fg)}/>`;
    case 'wave':
      return `<path d="M22 84c16-18 29-18 45 0s29 18 45 0 29-18 46 0" fill="none" stroke="${accent}" stroke-width="12" stroke-linecap="round"/><circle cx="40" cy="46" r="10" fill="${fg}"/><circle cx="70" cy="34" r="8" fill="${accent}" opacity=".65"/>`;
    case 'mountain':
      return `<path d="M22 98 49 49 70 76 88 54 118 98Z" ${pathStroke(outline,accent,fg)}/><path d="M64 63 70 76 79 66" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round"/>`;
    case 'sun':
      return outline
        ? `<circle cx="70" cy="70" r="22" fill="none" stroke="${accent}" stroke-width="8"/><path d="M70 20v18M70 102v18M20 70h18M102 70h18M33 33l13 13M94 94l13 13M33 107l13-13M94 46l13-13" fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"/>`
        : `<circle cx="70" cy="70" r="24" fill="${accent}"/><path d="M70 18v16M70 106v16M18 70h16M106 70h16M35 35l11 11M94 94l11 11M35 105l11-11M94 46l11-11" fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round" opacity="0.82"/>`;
    case 'heart':
      return outline
        ? `<path d="M70 108 32 70c-10-10-10-26 0-36s26-10 36 0c10-10 26-10 36 0s10 26 0 36Z" fill="none" stroke="${accent}" stroke-width="8" stroke-linejoin="round"/>`
        : `<path d="M70 108 32 70c-10-10-10-26 0-36s26-10 36 0c10-10 26-10 36 0s10 26 0 36Z" fill="${accent}" opacity="0.95"/><circle cx="70" cy="70" r="8" fill="${fg}" opacity="0.9"/>`;
    case 'bolt':
      return `<path d="M80 20 40 78h24l-6 42 42-58H76Z" ${pathStroke(outline,accent,fg)}/>`;
    case 'hex':
      return outline
        ? `<path d="M44 28h52l26 42-26 42H44L18 70Z" fill="none" stroke="${accent}" stroke-width="8" stroke-linejoin="round"/><circle cx="70" cy="70" r="8" fill="${fg}"/>`
        : `<path d="M44 22h52l30 48-30 48H44L14 70Z" fill="${accent}" opacity="0.95"/><circle cx="70" cy="70" r="8" fill="${fg}"/>`;

    case 'orbit':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round"><circle cx="70" cy="70" r="${outline?18:16}" ${outline?'':'fill="none"'} /><ellipse cx="70" cy="70" rx="44" ry="20" transform="rotate(-22 70 70)"/><ellipse cx="70" cy="70" rx="44" ry="20" transform="rotate(22 70 70)" opacity="0.55"/></g><circle cx="70" cy="70" r="7" fill="${fg}"/>`;
    case 'ribbon':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round" stroke-linejoin="round"><path d="M34 48h58c11 0 20 9 20 20s-9 20-20 20H74l-12 14-12-14H34c-11 0-20-9-20-20s9-20 20-20Z"/><path d="M46 62h36"/></g>`;
    case 'grid-dot':
      return `<g fill="none" stroke="${accent}" stroke-width="5"><circle cx="46" cy="46" r="4" fill="${accent}"/><circle cx="70" cy="46" r="4" fill="${accent}"/><circle cx="94" cy="46" r="4" fill="${accent}"/><circle cx="46" cy="70" r="4" fill="${accent}"/><circle cx="70" cy="70" r="4" fill="${accent}"/><circle cx="94" cy="70" r="4" fill="${accent}"/><circle cx="46" cy="94" r="4" fill="${accent}"/><circle cx="70" cy="94" r="4" fill="${accent}"/><circle cx="94" cy="94" r="4" fill="${accent}"/></g>`;
    case 'arc':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?9:8}" stroke-linecap="round"><path d="M30 86c12-26 34-40 62-40 12 0 22 2 32 6"/><path d="M48 102h44" stroke="${fg}" stroke-width="7"/></g>`;
    case 'lens':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?9:8}" stroke-linecap="round"><circle cx="60" cy="60" r="24"/><path d="M79 79l26 26"/></g><circle cx="60" cy="60" r="6" fill="${fg}"/>`;
    case 'shield':
      return `<path d="M70 26 106 40v24c0 25-14 43-36 52C48 107 34 89 34 64V40l36-14Z" fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linejoin="round"/><path d="M52 72l12 12 24-29" fill="none" stroke="${fg}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>`;
    case 'bloom':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round"><circle cx="70" cy="46" r="13"/><circle cx="93" cy="59" r="13"/><circle cx="93" cy="85" r="13"/><circle cx="70" cy="98" r="13"/><circle cx="47" cy="85" r="13"/><circle cx="47" cy="59" r="13"/></g><circle cx="70" cy="72" r="7" fill="${fg}"/>`;
    case 'pinwheel':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linejoin="round"><path d="M70 70V34c15 0 25 10 25 25Z"/><path d="M70 70h36c0 15-10 25-25 25Z"/><path d="M70 70v36c-15 0-25-10-25-25Z"/><path d="M70 70H34c0-15 10-25 25-25Z"/></g><circle cx="70" cy="70" r="6" fill="${fg}"/>`;
    case 'link':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?9:8}" stroke-linecap="round"><path d="M50 84H40c-12 0-22-10-22-22s10-22 22-22h18"/><path d="M90 56h10c12 0 22 10 22 22s-10 22-22 22H82"/><path d="M54 70h32"/></g>`;
    case 'droplet':
      return `<path d="M70 26c13 18 30 33 30 50a30 30 0 1 1-60 0c0-17 17-32 30-50Z" fill="none" stroke="${accent}" stroke-width="${outline?8:7}"/><path d="M58 86c6 5 18 5 24 0" fill="none" stroke="${fg}" stroke-width="7" stroke-linecap="round"/>`;
    case 'crown':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round" stroke-linejoin="round"><path d="M30 96 42 48 64 68 70 40 76 68 98 48 110 96"/><path d="M40 96h60"/></g><circle cx="42" cy="48" r="4" fill="${fg}"/><circle cx="70" cy="40" r="4" fill="${fg}"/><circle cx="98" cy="48" r="4" fill="${fg}"/>`;
    case 'signal':
      return `<g fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round"><path d="M44 94a26 26 0 0 1 52 0"/><path d="M34 104a38 38 0 0 1 72 0" opacity="0.78"/><path d="M24 114a50 50 0 0 1 92 0" opacity="0.56"/></g><circle cx="70" cy="94" r="6" fill="${fg}"/>`;

    case 'halo-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"><circle cx="70" cy="70" r="22"/><circle cx="70" cy="70" r="42" opacity="0.9"/><path d="M70 16v16M70 108v16M16 70h16M108 70h16" opacity="0.7"/></g>`;
    case 'interlock-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"><circle cx="56" cy="70" r="22"/><circle cx="84" cy="70" r="22"/></g>`;
    case 'ripple-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"><path d="M24 54c10 8 18 8 28 0s18-8 28 0 18 8 28 0 18-8 28 0"/><path d="M24 76c10 8 18 8 28 0s18-8 28 0 18 8 28 0 18-8 28 0" opacity="0.8"/><path d="M24 98c10 8 18 8 28 0s18-8 28 0 18 8 28 0 18-8 28 0" opacity="0.6"/></g>`;
    case 'compass-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"><circle cx="70" cy="70" r="38"/><path d="M70 32l12 26 26 12-26 12-12 26-12-26-26-12 26-12Z"/></g><circle cx="70" cy="70" r="6" fill="${fg}"/>`;
    case 'constellation-line':
      return `<g fill="none" stroke="${accent}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"><path d="M34 88 52 52 78 62 100 38 110 82 72 100 34 88Z"/><circle cx="34" cy="88" r="4" fill="${accent}" stroke="none"/><circle cx="52" cy="52" r="4" fill="${accent}" stroke="none"/><circle cx="78" cy="62" r="4" fill="${accent}" stroke="none"/><circle cx="100" cy="38" r="4" fill="${accent}" stroke="none"/><circle cx="110" cy="82" r="4" fill="${accent}" stroke="none"/><circle cx="72" cy="100" r="4" fill="${accent}" stroke="none"/></g>`;
    case 'petal-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"><path d="M70 28c10 10 10 24 0 34-10-10-10-24 0-34Z"/><path d="M112 70c-10 10-24 10-34 0 10-10 24-10 34 0Z"/><path d="M70 112c-10-10-10-24 0-34 10 10 10 24 0 34Z"/><path d="M28 70c10-10 24-10 34 0-10 10-24 10-34 0Z"/><circle cx="70" cy="70" r="7"/></g>`;
    case 'axis-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"><path d="M70 22v96M22 70h96" opacity="0.55"/><circle cx="70" cy="70" r="26"/><path d="M70 40l14 18-14 12-14-12Z"/></g>`;
    case 'knot-line':
      return `<g fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"><path d="M40 52c0-10 8-18 18-18h12c10 0 18 8 18 18 0 10-8 18-18 18H58c-10 0-18 8-18 18 0 10 8 18 18 18h12c10 0 18-8 18-18"/></g>`;
    case 'nest-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"><path d="M34 84c10-6 22-8 36-8s26 2 36 8"/><path d="M28 70c14-10 28-14 42-14s28 4 42 14" opacity="0.82"/><path d="M40 98c8-4 16-6 30-6s22 2 30 6" opacity="0.64"/><circle cx="70" cy="52" r="10"/></g>`;
    case 'path-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"><path d="M28 98c10-26 22-42 40-42 24 0 20 30 42 30 8 0 14-2 20-6"/><circle cx="28" cy="98" r="5" fill="${accent}" stroke="none"/><circle cx="110" cy="80" r="5" fill="${accent}" stroke="none"/></g>`;
    case 'prism-line':
      return `<g fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"><path d="M70 28 106 50v40l-36 22-36-22V50Z"/><path d="M70 28v40m0 44V68m36-18L70 68 34 50" opacity="0.78"/></g>`;

    case 'mono-circle':
      return `<circle cx="70" cy="70" r="40" fill="none" stroke="${accent}" stroke-width="${outline?9:8}"/>${monoText({fg,brand:cfg.brand},46,800,1.2)}`;
    case 'mono-square':
      return `<rect x="30" y="30" width="80" height="80" rx="22" fill="none" stroke="${accent}" stroke-width="${outline?9:8}"/>${monoText({fg,brand:cfg.brand},42,800,1.1)}`;
    case 'mono-ring':
      return `<circle cx="70" cy="70" r="46" fill="none" stroke="${accent}" stroke-width="${outline?8:7}" opacity="0.32"/><circle cx="70" cy="70" r="34" fill="none" stroke="${accent}" stroke-width="${outline?8:7}"/>${monoText({fg,brand:cfg.brand},34,800,1.2)}`;
    case 'mono-split':
      return `<path d="M32 70h76" fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round"/><path d="M100 58l12 12-12 12" fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round" stroke-linejoin="round"/>${monoText({fg,brand:cfg.brand},36,800,1.2)}`;
    case 'mono-stamp':
      return `<rect x="28" y="28" width="84" height="84" rx="28" fill="${outline?'none':accent}" opacity="${outline?1:0.12}" stroke="${accent}" stroke-width="${outline?8:0}"/>${monoText({fg: outline?fg:accent,brand:cfg.brand},40,900,1.4)}<path d="M42 96h56" fill="none" stroke="${outline?accent:accent}" stroke-width="5" stroke-linecap="round" opacity="0.8"/>`;
    case 'mono-line':
      return `<path d="M28 102c18-28 34-40 58-40 10 0 18 2 28 8" fill="none" stroke="${accent}" stroke-width="${outline?8:7}" stroke-linecap="round"/>${monoText({fg,brand:cfg.brand},34,800,2)}<circle cx="36" cy="102" r="4" fill="${accent}"/><circle cx="104" cy="70" r="4" fill="${accent}"/>`;

    case 'bowl':
      return `<circle cx="70" cy="70" r="50" fill="${accent}" opacity="0.12"/><path d="M34 70h72c-3 24-17 38-36 38S37 94 34 70Z" ${pathStroke(outline,accent,fg)}/><path d="M46 56c8-12 18-18 18-28M66 58c7-10 15-20 15-32M84 58c8-9 18-18 20-30" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round" opacity="0.85"/>`;
    case 'wok':
      return `<path d="M28 72c8 22 26 36 42 36s34-14 42-36Z" ${pathStroke(outline,accent,fg)}/><path d="M91 49l22-13" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M45 53c8-10 15-17 15-26M67 53c5-9 10-17 10-28" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/>`;
    case 'chopsticks':
      return outline
        ? `<path d="M47 26 69 97" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M77 18 73 98" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M43 76c3 16 15 28 27 28s24-12 27-28" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="M50 76h40" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round" opacity="0.65"/>`
        : `<path d="M47 26 69 97" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M77 18 73 98" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M43 76c3 16 15 28 27 28s24-12 27-28" fill="${fg}" opacity="0.16" stroke="${fg}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="M50 76h40" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round" opacity="0.7"/>`;
    case 'pizza':
      return `<path d="M28 100 70 28l42 72Z" ${pathStroke(outline,accent,fg)}/><circle cx="67" cy="62" r="6" fill="${fg}"/><circle cx="53" cy="78" r="6" fill="${fg}"/><circle cx="82" cy="79" r="6" fill="${fg}"/>`;
    case 'burger':
      return `<path d="M36 58c4-14 18-24 34-24s30 10 34 24Z" ${pathStroke(outline,accent,fg)}/><rect x="34" y="61" width="72" height="14" rx="7" fill="${fg}" opacity=".88"/><rect x="38" y="79" width="64" height="16" rx="8" fill="${accent}" opacity=".95"/>`;
    case 'cup':
      return `<path d="M38 40h38v48c0 12-8 20-19 20S38 100 38 88Z" ${pathStroke(outline,accent,fg)}/><path d="M76 47h10c10 0 14 7 14 14s-4 14-14 14H76" fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"/><path d="M48 30c0-7 5-11 5-16M62 30c0-7 5-11 5-16" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round"/>`;
    case 'forkknife':
      return `<path d="M42 24v36M34 24v20M50 24v20M42 60v44" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M88 24c0 18-5 26-11 34v46" fill="none" stroke="${fg}" stroke-width="8" stroke-linecap="round"/>`;
    case 'cloche':
      return `<path d="M28 84h84" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M36 84c4-28 20-44 34-44s30 16 34 44" ${pathStroke(outline,accent,fg)}/><circle cx="70" cy="38" r="8" fill="${fg}"/>`;
    case 'takeaway-box':
      return `<path d="M48 36h44l14 18-10 50H44L34 54Z" ${pathStroke(outline,accent,fg)}/><path d="M56 36c0-8 6-14 14-14s14 6 14 14" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/>`;
    case 'sushi':
      return `<rect x="30" y="44" width="80" height="52" rx="18" ${pathStroke(outline,accent,fg)}/><rect x="46" y="56" width="48" height="28" rx="10" fill="${fg}" opacity=".9"/><circle cx="58" cy="70" r="6" fill="${accent}"/>`;
    case 'noodles':
      return `<rect x="36" y="74" width="68" height="18" rx="9" fill="${accent}" opacity=".95"/><path d="M42 66c6-14 16-22 16-32M58 66c4-13 12-22 12-34M74 66c5-13 12-21 12-32M90 66c5-13 11-20 11-30" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/>`;
    case 'taco':
      return `<path d="M34 84c6-26 24-42 43-42s37 16 43 42Z" ${pathStroke(outline,accent,fg)}/><circle cx="50" cy="69" r="5" fill="${fg}"/><circle cx="67" cy="62" r="5" fill="${fg}"/><circle cx="84" cy="69" r="5" fill="${fg}"/>`;
    case 'icecream':
      return `<path d="M70 26c13 0 24 10 24 24s-11 24-24 24-24-10-24-24 11-24 24-24Z" ${pathStroke(outline,accent,fg)}/><path d="M56 74h28L70 110Z" fill="${accent}"/>`;
    case 'fish':
      return `<path d="M30 70c12-17 24-24 40-24 16 0 30 7 40 24-10 17-24 24-40 24-16 0-28-7-40-24Z" ${pathStroke(outline,accent,fg)}/><circle cx="58" cy="68" r="5" fill="${fg}"/>`;
    case 'coffee-bean':
      return `<path d="M70 28c18 0 30 18 30 42s-12 42-30 42S40 94 40 70s12-42 30-42Z" ${pathStroke(outline,accent,fg)}/><path d="M78 34c-10 10-12 21-12 36s2 26 10 36" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/>`;
    case 'croissant':
      return `<path d="M30 76c8-22 24-34 40-34s32 12 40 34c-12 10-24 16-40 16S42 86 30 76Z" ${pathStroke(outline,accent,fg)}/><path d="M48 66c4 6 8 11 12 14M70 60c4 7 8 13 12 18M88 64c3 5 7 9 11 12" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round"/>`;
    case 'plate':
      return `<circle cx="70" cy="70" r="42" fill="none" stroke="${accent}" stroke-width="8"/><circle cx="70" cy="70" r="20" fill="none" stroke="${fg}" stroke-width="7"/>`;
    case 'spoon-fork':
      return `<path d="M46 24v36M39 24v18M53 24v18M46 60v52" fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"/><path d="M88 24c0 18-6 28-14 36v52" fill="none" stroke="${fg}" stroke-width="7" stroke-linecap="round"/>`;
    case 'whisk':
      return `<path d="M48 36c16 8 28 22 34 42" fill="none" stroke="${accent}" stroke-width="8" stroke-linecap="round"/><path d="M78 78l20 20" fill="none" stroke="${fg}" stroke-width="8" stroke-linecap="round"/><path d="M44 40c-8 10-8 20 0 30M56 34c-10 14-10 28 0 42M68 34c-10 14-10 28 0 42" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/>`;
    case 'loaf':
      return `<path d="M34 82c0-24 14-40 36-40s36 16 36 40Z" ${pathStroke(outline,accent,fg)}/><path d="M52 56c0 8 4 14 10 18M70 52c0 10 4 18 10 24M88 56c0 8 4 14 10 18" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/>`;
    case 'grain':
      return `<path d="M70 28v84" fill="none" stroke="${accent}" stroke-width="7" stroke-linecap="round"/><path d="M70 40c-12 0-18 10-18 18 12 0 18-8 18-18ZM70 58c12 0 18 10 18 18-12 0-18-8-18-18ZM70 76c-12 0-18 10-18 18 12 0 18-8 18-18ZM70 94c12 0 18 10 18 18-12 0-18-8-18-18Z" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>`;
    case 'lemon':
      return `<path d="M44 70c0-16 12-28 26-28s26 12 26 28-12 28-26 28S44 86 44 70Z" fill="none" stroke="${accent}" stroke-width="8"/><path d="M70 44c8 6 12 14 12 26s-4 20-12 26" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/>`;
    case 'mortar':
      return `<path d="M34 70h72c-4 24-18 38-36 38S38 94 34 70Z" ${pathStroke(outline,accent,fg)}/><path d="M88 44l16-16" fill="none" stroke="${fg}" stroke-width="8" stroke-linecap="round"/><path d="M78 54 94 38" fill="none" stroke="${accent}" stroke-width="10" stroke-linecap="round"/>`;
    case 'bottle':
      return `<path d="M58 34H82V46L88 54V98c0 6-4 10-10 10H62c-6 0-10-4-10-10V54l6-8Z" fill="none" stroke="${accent}" stroke-width="8" stroke-linejoin="round"/><path d="M56 72H84" fill="none" stroke="${fg}" stroke-width="6" opacity="0.88"/>`;

    case 'ramen-real':
      return `<g><ellipse cx="70" cy="92" rx="42" ry="13" fill="${accent}" opacity="0.14"/><path d="M30 74h80c-4 24-20 38-40 38S34 98 30 74Z" fill="${accent}" opacity="0.18" stroke="${accent}" stroke-width="6" stroke-linejoin="round"/><path d="M40 76c8 5 18 8 30 8s22-3 30-8" fill="none" stroke="${fg}" stroke-width="4" opacity="0.55"/><path d="M44 69c5-10 14-16 14-27M58 71c5-11 12-18 12-31M72 72c5-11 12-18 12-31M86 69c5-9 14-15 14-26" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round"/><path d="M46 52c8 6 13 11 20 15M82 50c7 6 11 10 16 15" fill="none" stroke="${accent}" stroke-width="4" stroke-linecap="round" opacity="0.7"/><path d="M99 36 116 22" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/><path d="M92 41 109 27" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round" opacity="0.8"/></g>`;
    case 'burger-real':
      return `<g><ellipse cx="70" cy="95" rx="40" ry="12" fill="${accent}" opacity="0.12"/><path d="M32 60c4-18 20-30 38-30s34 12 38 30c-10 4-24 6-38 6s-28-2-38-6Z" fill="${accent}" opacity="0.88" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M40 73h60c0 8-5 14-12 17H52c-7-3-12-9-12-17Z" fill="${fg}" opacity="0.92"/><path d="M35 68h70c4 0 7 3 7 7s-3 7-7 7H35c-4 0-7-3-7-7s3-7 7-7Z" fill="${accent}" opacity="0.55"/><path d="M36 89h68c0 10-8 17-18 17H54c-10 0-18-7-18-17Z" fill="${accent}" stroke="${fg}" stroke-width="4"/><circle cx="50" cy="48" r="2.3" fill="${fg}" opacity="0.7"/><circle cx="61" cy="42" r="2.3" fill="${fg}" opacity="0.7"/><circle cx="74" cy="44" r="2.3" fill="${fg}" opacity="0.7"/><circle cx="86" cy="49" r="2.3" fill="${fg}" opacity="0.7"/></g>`;
    case 'pizza-real':
      return `<g><path d="M36 40h68l10 14-9 46H35L26 54Z" fill="${accent}" opacity="0.16" stroke="${accent}" stroke-width="6" stroke-linejoin="round"/><path d="M44 51h54l7 38H38Z" fill="${fg}" opacity="0.12"/><path d="M50 50 70 82 90 50" fill="${accent}" opacity="0.9" stroke="${fg}" stroke-width="4" stroke-linejoin="round"/><path d="M53 49c10-5 24-8 34-8 7 0 13 1 18 3" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round" opacity="0.6"/><circle cx="68" cy="61" r="4.2" fill="${fg}"/><circle cx="79" cy="69" r="4.2" fill="${fg}"/><circle cx="59" cy="70" r="4.2" fill="${fg}"/></g>`;
    case 'takeaway-cup-real':
      return `<g><ellipse cx="70" cy="100" rx="28" ry="9" fill="${accent}" opacity="0.14"/><path d="M48 38h44l-6 60c-1 10-8 16-16 16h0c-8 0-15-6-16-16Z" fill="${accent}" opacity="0.18" stroke="${accent}" stroke-width="6" stroke-linejoin="round"/><path d="M44 35h52" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/><path d="M58 54h24M56 68h28M54 82h32" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round" opacity="0.45"/><path d="M80 30c0-9 7-14 7-20" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round"/></g>`;
    case 'delivery-bag-real':
      return `<g><path d="M42 46h56l8 54H34Z" fill="${accent}" opacity="0.18" stroke="${accent}" stroke-width="6" stroke-linejoin="round"/><path d="M55 48c0-10 7-18 15-18s15 8 15 18" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/><path d="M48 66h44" fill="none" stroke="${fg}" stroke-width="4" opacity="0.45"/><path d="M48 78h44" fill="none" stroke="${fg}" stroke-width="4" opacity="0.3"/><path d="M58 76l7 7 17-17" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>`;
    case 'chef-hat-real':
      return `<g><path d="M42 92h56v16H42Z" fill="${accent}" opacity="0.9"/><path d="M38 90c-8-18-2-33 11-36 2-13 12-22 24-22 11 0 21 7 24 18 14 0 23 11 23 24 0 6-2 11-6 16Z" fill="${accent}" opacity="0.18" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M54 90V68M70 90V62M86 90V68" fill="none" stroke="${fg}" stroke-width="4" opacity="0.35" stroke-linecap="round"/></g>`;
    case 'cloche-real':
      return `<g><ellipse cx="70" cy="100" rx="40" ry="8" fill="${accent}" opacity="0.12"/><path d="M28 92h84" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/><path d="M34 92c4-30 20-48 36-48s32 18 36 48" fill="${accent}" opacity="0.14" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><circle cx="70" cy="40" r="8" fill="${fg}"/><path d="M50 67c8-7 14-10 20-10s12 3 20 10" fill="none" stroke="${fg}" stroke-width="4" opacity="0.3" stroke-linecap="round"/></g>`;
    case 'dumplings-real':
      return `<g><ellipse cx="48" cy="78" rx="22" ry="18" fill="${accent}" opacity="0.2" stroke="${fg}" stroke-width="4"/><path d="M34 76c8-8 12-10 14-10 4 0 8 4 14 10" fill="none" stroke="${fg}" stroke-width="3" opacity="0.5"/><ellipse cx="88" cy="80" rx="24" ry="17" fill="${accent}" opacity="0.16" stroke="${fg}" stroke-width="4"/><path d="M72 79c7-8 11-10 15-10 5 0 9 4 15 10" fill="none" stroke="${fg}" stroke-width="3" opacity="0.5"/><path d="M30 98h76" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/></g>`;
    case 'bento-real':
      return `<g><rect x="28" y="34" width="84" height="72" rx="18" fill="${accent}" opacity="0.14" stroke="${fg}" stroke-width="5"/><path d="M56 40v60M82 40v60M34 68h72" fill="none" stroke="${fg}" stroke-width="4" opacity="0.45"/><circle cx="44" cy="54" r="7" fill="${accent}"/><rect x="62" y="48" width="14" height="12" rx="4" fill="${accent}" opacity="0.8"/><path d="M92 44 104 34M86 50 98 40" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round"/><rect x="88" y="76" width="16" height="12" rx="5" fill="${accent}" opacity="0.75"/></g>`;
    case 'pastry-real':
      return `<g><path d="M32 88 46 50h48l14 38c-12 10-24 16-38 16S44 98 32 88Z" fill="${accent}" opacity="0.16" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M46 50c8-9 16-13 24-13s16 4 24 13" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/><path d="M52 66c3 4 6 9 9 12M69 60c4 6 8 12 12 18M88 66c3 5 6 8 10 11" fill="none" stroke="${fg}" stroke-width="4" opacity="0.45" stroke-linecap="round"/></g>`;
    case 'skewer-real':
      return `<g><path d="M28 100 112 36" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round"/><rect x="44" y="70" width="16" height="16" rx="5" transform="rotate(-37 52 78)" fill="${accent}" opacity="0.95"/><rect x="61" y="58" width="16" height="16" rx="5" transform="rotate(-37 69 66)" fill="${fg}" opacity="0.85"/><rect x="79" y="45" width="16" height="16" rx="5" transform="rotate(-37 87 53)" fill="${accent}" opacity="0.7"/><path d="M37 88c8 8 12 10 20 10" fill="none" stroke="${accent}" stroke-width="5" opacity="0.4" stroke-linecap="round"/></g>`;
    case 'soup-pot-real':
      return `<g><path d="M34 56h72v18c0 20-14 34-36 34S34 94 34 74Z" fill="${accent}" opacity="0.16" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M28 58h10M102 58h10" fill="none" stroke="${fg}" stroke-width="6" stroke-linecap="round"/><path d="M48 46h44" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/><path d="M50 30c0-8 5-12 5-18M67 28c0-8 5-12 5-18M84 30c0-8 5-12 5-18" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round" opacity="0.8"/></g>`;
    case 'coffee-real':
      return `<g><ellipse cx="70" cy="98" rx="32" ry="8" fill="${accent}" opacity="0.12"/><path d="M38 48h40v34c0 12-8 20-19 20h0c-11 0-21-8-21-20Z" fill="${accent}" opacity="0.16" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M78 56h10c10 0 14 7 14 14s-4 14-14 14H78" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/><path d="M50 36c0-7 5-11 5-16M62 32c0-7 5-11 5-16" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round" opacity="0.8"/><path d="M48 74c8 4 16 6 24 6" fill="none" stroke="${fg}" stroke-width="4" opacity="0.35" stroke-linecap="round"/></g>`;

    case 'asian-face-woman-real':
      return `<g><path d="M38 58c0-15 4-27 12-35 9-9 18-13 30-13s22 4 30 13c8 8 12 20 12 35v12c0 5-1 11-2 16-4 16-19 32-40 32-22 0-37-16-41-33-1-5-1-10-1-15Z" fill="${fg}" opacity="0.98"/><path d="M46 63c0-20 11-33 24-33s24 13 24 33v19c0 17-10 29-24 29S46 99 46 82Z" fill="${accent}" opacity="0.22" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M42 63c4-3 8-4 12-4 4 0 7 1 10 3M88 63c4-3 8-4 10-4 5 0 9 2 12 5" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round" opacity="0.9"/><circle cx="57" cy="79" r="4.5" fill="${fg}"/><circle cx="83" cy="79" r="4.5" fill="${fg}"/><path d="M61 99c4 4 7 5 9 5s5-1 9-5" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round"/><path d="M52 70c3-3 7-5 12-5M76 70c3-3 7-5 12-5" fill="none" stroke="${fg}" stroke-width="3.5" stroke-linecap="round" opacity="0.35"/></g>`;
    case 'asian-face-man-real':
      return `<g><path d="M41 60c0-21 13-35 29-35s29 14 29 35v20c0 20-12 34-29 34S41 100 41 80Z" fill="${accent}" opacity="0.2" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M38 59c2-15 8-26 18-33 8-5 16-8 24-8 9 0 17 3 24 8 8 7 12 17 14 31-8-3-15-5-22-5-8 0-15 2-22 5-9 4-16 10-16 10-6-7-12-10-20-8Z" fill="${fg}"/><circle cx="57" cy="79" r="4.5" fill="${fg}"/><circle cx="83" cy="79" r="4.5" fill="${fg}"/><path d="M60 98c4 3 7 4 10 4s6-1 10-4" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round"/><path d="M52 70c3-2 7-4 12-4M76 70c3-2 7-4 12-4" fill="none" stroke="${fg}" stroke-width="3.5" stroke-linecap="round" opacity="0.35"/></g>`;
    case 'asian-chef-woman-real':
      return `<g><path d="M36 48c0-10 6-18 15-20 4-9 13-14 24-14 12 0 21 6 25 16 10 1 16 8 16 17 0 6-2 11-6 15H36Z" fill="${accent}" opacity="0.22" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M38 58c0-15 4-27 12-35 8-8 18-12 30-12 11 0 21 4 29 12 8 8 12 20 12 35v10c0 6-1 12-2 17-4 17-19 33-39 33-21 0-36-16-40-33-1-5-2-11-2-17Z" fill="${fg}" opacity="0.98"/><path d="M46 63c0-20 11-33 24-33s24 13 24 33v19c0 17-10 29-24 29S46 99 46 82Z" fill="${accent}" opacity="0.22" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M42 63c4-3 8-4 12-4 4 0 7 1 10 3M88 63c4-3 8-4 10-4 5 0 9 2 12 5" fill="none" stroke="${fg}" stroke-width="5" stroke-linecap="round" opacity="0.9"/><circle cx="57" cy="79" r="4.5" fill="${fg}"/><circle cx="83" cy="79" r="4.5" fill="${fg}"/><path d="M61 99c4 4 7 5 9 5s5-1 9-5" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round"/></g>`;
    case 'asian-chef-man-real':
      return `<g><path d="M36 48c0-10 6-18 15-20 4-10 14-15 25-15 12 0 21 6 26 16 9 1 15 8 15 17 0 6-2 11-6 15H36Z" fill="${accent}" opacity="0.22" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M41 62c0-21 13-36 29-36s29 15 29 36v18c0 20-12 34-29 34S41 100 41 80Z" fill="${accent}" opacity="0.2" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M39 59c2-15 8-26 18-33 8-5 16-8 24-8 9 0 17 2 24 8 8 6 12 15 14 27-8-3-15-4-22-4-8 0-15 2-22 6-8 4-15 9-15 9-6-6-12-9-21-5Z" fill="${fg}"/><circle cx="57" cy="79" r="4.5" fill="${fg}"/><circle cx="83" cy="79" r="4.5" fill="${fg}"/><path d="M60 98c4 3 7 4 10 4s6-1 10-4" fill="none" stroke="${fg}" stroke-width="4" stroke-linecap="round"/></g>`;
    case 'home-pan-real':
      return `<g><path d="M34 78c0-20 16-36 36-36s36 16 36 36H34Z" fill="${accent}" opacity="0.16" stroke="${fg}" stroke-width="5" stroke-linejoin="round"/><path d="M106 72h18c6 0 10 4 10 10s-4 10-10 10h-18" fill="none" stroke="${accent}" stroke-width="6" stroke-linecap="round"/><path d="M48 62c8 6 15 10 22 10s14-4 22-10" fill="none" stroke="${fg}" stroke-width="4" opacity="0.45" stroke-linecap="round"/><path d="M48 34c8 10 10 20 10 28M68 30c8 12 10 21 10 29" fill="none" stroke="${accent}" stroke-width="4" stroke-linecap="round" opacity="0.75"/></g>`;
    default:
      return `<circle cx="70" cy="70" r="30" fill="${accent}"/>`;
  }
}
function iconHtml(cfg,size=140){if(cfg.customIcon) return `<img src="${cfg.customIcon}" alt="Icon" style="width:${size}px;height:${size}px;object-fit:contain;display:block;" />`; return `<svg width="${size}" height="${size}" viewBox="0 0 140 140">${shapeSvg(cfg.shape,cfg.accent,cfg.fg,cfg.outlineIcon,cfg)}</svg>`}
function buildLogoHtml(cfg){const brand=cfg.caps?cfg.brand.toUpperCase():cfg.brand; const brandBox=`max-width:${cfg.brandWrap||320}px;width:${cfg.brandWrap||320}px;white-space:normal;overflow-wrap:anywhere;`; const tagBox=`max-width:${cfg.tagWrap||360}px;width:${cfg.tagWrap||360}px;white-space:normal;overflow-wrap:anywhere;`; const badgeBox=`max-width:${cfg.badgeWrap||220}px;width:${cfg.badgeWrap||220}px;white-space:normal;overflow-wrap:anywhere;justify-content:center;text-align:center;`; const brandStyle=`font-family:${cfg.font};color:${cfg.fg};font-size:${cfg.brandSize}px;font-weight:800;letter-spacing:${cfg.spacing*0.02}em;line-height:1;${brandBox}`; const tagStyle=`font-family:${cfg.font};color:${cfg.tagColor||cfg.fg};font-size:${cfg.tagSize}px;opacity:0.78;letter-spacing:0.1em;text-transform:uppercase;line-height:1.12;${tagBox}`; const gapDelta=(cfg.iconGap??28)-28; const iconTransform=`translate(${cfg.iconOffsetX||0}px, ${cfg.iconOffsetY||0}px) scale(${cfg.iconScale/100})`; const ico=`<div style="transform:${iconTransform};transform-origin:center;display:flex;align-items:center;justify-content:center;flex:0 0 auto;margin-right:${gapDelta}px;">${iconHtml(cfg)}</div>`; const icoVertical=`<div style="transform:${iconTransform};transform-origin:center;display:flex;align-items:center;justify-content:center;flex:0 0 auto;margin-bottom:${gapDelta}px;">${iconHtml(cfg)}</div>`; const textCol=`display:flex;flex-direction:column;align-items:flex-start;flex:0 0 auto;min-width:0;`; const tag=cfg.showTagline?`<div style="margin-top:10px;${tagStyle}">${escapeXml(cfg.tagline)}</div>`:''; const mark=initials(cfg.brand); switch(cfg.template){case 'food-badge':return `<div style="display:flex;align-items:center;gap:28px;padding:28px 34px;border-radius:32px;border:2px solid ${cfg.frameColor||cfg.accent};background:rgba(255,255,255,0.28);box-shadow:0 10px 30px rgba(15,23,42,0.06);">${ico}<div style="${textCol}"><div style="${brandStyle};font-size:${cfg.brandSize+4}px;">${escapeXml(brand)}</div>${tag}<div style="margin-top:15px;display:inline-flex;padding:8px 12px;border-radius:999px;background:${cfg.accent};color:${cfg.bg};font-size:11px;font-weight:800;letter-spacing:0.08em;${badgeBox}">${escapeXml(cfg.badgeText||'HOME KITCHEN BRAND')}</div></div></div>`;case 'stacked-seal':return `<div style="display:flex;flex-direction:column;align-items:center;text-align:center;">${icoVertical}<div style="margin-top:18px;height:1px;width:160px;background:${cfg.accent};"></div><div style="margin-top:14px;${brandStyle}">${escapeXml(brand)}</div>${tag}</div>`;case 'modern-app':return `<div style="display:flex;flex-direction:column;align-items:center;text-align:center;"><div style="padding:18px;border-radius:36px;background:linear-gradient(135deg,${cfg.accent},${cfg.fg});box-shadow:0 20px 50px rgba(0,0,0,0.14);"><div style="padding:10px;border-radius:28px;background:rgba(255,255,255,0.9);">${iconHtml(cfg)}</div></div><div style="margin-top:18px;${brandStyle}">${escapeXml(brand)}</div>${tag}</div>`;case 'monogram':return `<div style="display:flex;align-items:center;gap:26px;"><div style="width:144px;height:144px;border-radius:30px;border:2px solid ${cfg.frameColor||cfg.accent};display:flex;align-items:center;justify-content:center;font-family:${cfg.font};font-size:${cfg.brandSize+10}px;font-weight:800;color:${cfg.fg};">${escapeXml(mark)}</div><div><div style="${brandStyle}">${escapeXml(brand)}</div>${tag}</div></div>`;case 'signature-brand':return `<div style="display:flex;align-items:center;gap:28px;">${ico}<div style="${textCol}"><div style="font-family:${cfg.font};font-size:${cfg.brandSize+8}px;font-style:italic;font-weight:500;color:${cfg.fg};line-height:1;${brandBox}">${escapeXml(brand)}</div>${tag}</div></div>`;case 'banner-lockup':return `<div style="padding:26px 30px;border-radius:32px;background:${cfg.accent}12;border:2px solid ${cfg.frameColor||cfg.accent};"><div style="display:flex;align-items:center;gap:26px;">${ico}<div style="${textCol}"><div style="${brandStyle}">${escapeXml(brand)}</div>${tag}</div></div></div>`;case 'stamp-round':return `<div style="display:flex;flex-direction:column;align-items:center;text-align:center;"><div style="width:260px;height:260px;border-radius:50%;border:10px solid ${cfg.accent};display:flex;flex-direction:column;align-items:center;justify-content:center;">${iconHtml(cfg,110)}<div style="margin-top:6px;${brandStyle};font-size:${cfg.brandSize-4}px;">${escapeXml(brand)}</div></div>${tag}</div>`;case 'premium-line':return `<div style="display:flex;flex-direction:column;align-items:center;text-align:center;"><div style="height:1px;width:230px;background:${cfg.accent};margin-bottom:18px;"></div><div style="${brandStyle};font-weight:600;">${escapeXml(brand)}</div>${tag}<div style="height:1px;width:230px;background:${cfg.accent};margin-top:18px;"></div></div>`;case 'boxed-identity':return `<div style="display:flex;align-items:center;gap:26px;"><div style="padding:14px;border-radius:26px;background:${cfg.accent};">${iconHtml({...cfg,accent:cfg.bg},140)}</div><div style="${textCol}"><div style="display:inline-block;padding:12px 16px;border-radius:16px;background:${cfg.fg};color:${cfg.bg};font-family:${cfg.font};font-size:${cfg.brandSize}px;font-weight:800;line-height:1;${brandBox}">${escapeXml(brand)}</div>${tag}</div></div>`;case 'vertical-brand':return `<div style="display:flex;flex-direction:column;align-items:flex-start;gap:18px;">${icoVertical}<div style="${brandStyle};font-size:${cfg.brandSize+4}px;">${escapeXml(brand)}</div>${cfg.showTagline?`<div style="${tagStyle}">${escapeXml(cfg.tagline)}</div>`:''}</div>`;case 'startup-glow':return `<div style="display:flex;align-items:center;gap:26px;padding:28px 32px;border-radius:34px;background:radial-gradient(circle at top left, ${cfg.accent}25, transparent 45%), ${cfg.bg};box-shadow:0 20px 50px rgba(15,23,42,0.1);"><div style="padding:8px;border-radius:28px;box-shadow:0 0 40px ${cfg.accent}66;">${ico}</div><div><div style="${brandStyle}">${escapeXml(brand)}</div>${tag}</div></div>`;case 'chef-seal':return `<div style="display:flex;flex-direction:column;align-items:center;text-align:center;"><div style="width:270px;height:270px;border-radius:40px;background:${cfg.accent}16;border:2px solid ${cfg.frameColor||cfg.accent};display:flex;flex-direction:column;align-items:center;justify-content:center;">${iconHtml(cfg,108)}<div style="margin-top:10px;${brandStyle};font-size:${cfg.brandSize-2}px;">${escapeXml(brand)}</div></div>${tag}</div>`;case 'takeaway-label':return `<div style="padding:20px 24px;border-radius:24px;background:${cfg.accent};color:${cfg.bg};display:flex;align-items:center;gap:22px;"><div>${iconHtml({...cfg,accent:cfg.bg,fg:cfg.bg,outlineIcon:false},96)}</div><div style="${textCol}"><div style="font-family:${cfg.font};font-size:${cfg.brandSize+2}px;font-weight:800;line-height:1;color:${cfg.bg};${brandBox}">${escapeXml(brand)}</div>${cfg.showTagline?`<div style="margin-top:10px;font-family:${cfg.font};font-size:${cfg.tagSize}px;opacity:.92;letter-spacing:.08em;text-transform:uppercase;color:${cfg.bg};line-height:1.12;${tagBox}">${escapeXml(cfg.tagline)}</div>`:''}</div></div>`;case 'window-sign':return `<div style="padding:28px 32px;border-radius:28px;border:8px solid ${cfg.frameColor||cfg.accent};background:${panelBg};display:flex;flex-direction:column;align-items:center;text-align:center;">${iconHtml(cfg,120)}<div style="margin-top:16px;${brandStyle}">${escapeXml(brand)}</div>${tag}</div>`;case 'delivery-badge':return `<div style="display:flex;align-items:center;gap:24px;padding:22px 28px;border-radius:999px;background:${cfg.accent}18;border:2px solid ${cfg.frameColor||cfg.accent};">${iconHtml(cfg,96)}<div style="${textCol}"><div style="${brandStyle};font-size:${cfg.brandSize+1}px;">${escapeXml(brand)}</div>${tag}</div></div>`;case 'menu-stamp':return `<div style="padding:18px 22px;border-radius:22px;background:${panelBg};border:2px dashed ${cfg.frameColor||cfg.accent};display:flex;align-items:center;gap:20px;">${iconHtml(cfg,96)}<div style="${textCol}"><div style="${brandStyle}">${escapeXml(brand)}</div>${tag}</div></div>`;case 'artisan-plate':return `<div style="display:flex;flex-direction:column;align-items:center;text-align:center;"><div style="width:250px;height:250px;border-radius:50%;border:12px solid ${cfg.frameColor||cfg.accent};display:flex;align-items:center;justify-content:center;">${iconHtml(cfg,105)}</div><div style="margin-top:14px;${brandStyle};font-size:${cfg.brandSize-1}px;">${escapeXml(brand)}</div>${tag}</div>`;case 'capsule-lockup':return `<div style="display:flex;align-items:center;gap:24px;padding:18px 22px;border-radius:999px;background:${panelBg};border:2px solid ${cfg.frameColor||cfg.accent};box-shadow:0 12px 24px rgba(15,23,42,.06);"><div style="width:92px;height:92px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:${cfg.accent}18;">${iconHtml(cfg,72)}</div><div style="${textCol}"><div style="${brandStyle};font-size:${cfg.brandSize+1}px;">${escapeXml(brand)}</div>${tag}</div></div>`;case 'corner-frame':return `<div style="position:relative;padding:28px 34px;"><div style="position:absolute;left:0;top:0;width:84px;height:84px;border-left:6px solid ${cfg.frameColor||cfg.accent};border-top:6px solid ${cfg.frameColor||cfg.accent};border-radius:24px 0 0 0;"></div><div style="position:absolute;right:0;bottom:0;width:84px;height:84px;border-right:6px solid ${cfg.frameColor||cfg.accent};border-bottom:6px solid ${cfg.frameColor||cfg.accent};border-radius:0 0 24px 0;"></div><div style="display:flex;align-items:center;gap:26px;">${ico}<div style="${textCol}"><div style="${brandStyle};font-size:${cfg.brandSize+2}px;">${escapeXml(brand)}</div>${tag}</div></div></div>`;case 'hero-panel':return `<div style="display:flex;align-items:center;gap:28px;padding:28px 34px;border-radius:32px;border:2px solid ${cfg.frameColor||cfg.accent};background:linear-gradient(135deg, ${panelBg}, #ffffff);box-shadow:0 18px 36px rgba(15,23,42,0.08);">${ico}<div style="${textCol}"><div style="${brandStyle};font-size:${cfg.brandSize+6}px;">${escapeXml(brand)}</div>${tag}<div style="margin-top:16px;display:inline-flex;padding:10px 14px;border-radius:14px;background:${cfg.accent};color:${cfg.bg};font-size:12px;font-weight:800;letter-spacing:0.08em;${badgeBox}">${escapeXml(cfg.badgeText||'BRAND')}</div></div></div>`;case 'minimal-chip':return `<div style="display:flex;align-items:center;gap:16px;padding:14px 18px;border-radius:20px;background:${cfg.accent}14;border:2px solid ${cfg.frameColor||cfg.accent};">${iconHtml(cfg,64)}<div style="${textCol}"><div style="${brandStyle};font-size:${cfg.brandSize-2}px;">${escapeXml(brand)}</div>${cfg.showTagline?`<div style="margin-top:8px;${tagStyle};font-size:${cfg.tagSize-1}px;">${escapeXml(cfg.tagline)}</div>`:''}</div></div>`;default:return `<div style="display:flex;flex-direction:${cfg.layout==='icon-left'?'row':'column'};align-items:center;justify-content:center;gap:28px;text-align:${cfg.layout==='icon-left'?'left':'center'};">${cfg.layout==='icon-left'?ico:icoVertical}<div style="${textCol};align-items:${cfg.layout==='icon-left'?'flex-start':'center'};"><div style="${brandStyle}">${escapeXml(brand)}</div>${tag}</div></div>`;}}
function variantConfig(seed){const cfg={...state}; if(seed.template) cfg.template=seed.template; if(seed.shape) cfg.shape=seed.shape; if(seed.layout) cfg.layout=seed.layout; cfg.accent=shiftHex(cfg.accent,seed.accentShift||0); if(!cfg.transparent){ cfg.panelBg=shiftHex(cfg.panelBg||cfg.bg,seed.bgShift||0); } cfg.canvasBg=cfg.canvasBg||'#ffffff'; return cfg}
function renderTemplates(){refs.templateGrid.innerHTML=templates.map(t=>`<div class="template-card ${state.template===t.id?'active':''}" data-template="${t.id}"><div class="t1">${t.name}</div><div class="t2">${t.family}</div></div>`).join(''); refs.templateGrid.querySelectorAll('[data-template]').forEach(el=>el.addEventListener('click',()=>{state.template=el.dataset.template;selectedVariantId=0;render()}))}
function renderSymbols(){const search=(refs.symbolSearch.value||'').toLowerCase().trim(); const cat=refs.shapeCategory.value; const filtered=shapes.filter(s=>(cat==='all'||s.cat===cat)&&(!search||s.name.toLowerCase().includes(search)||s.id.toLowerCase().includes(search))); refs.symbolGrid.innerHTML=filtered.map(s=>{const cfg={...state,shape:s.id,customIcon:null}; return `<div class="symbol-card ${state.shape===s.id&&!state.customIcon?'active':''}" data-shape="${s.id}"><div>${iconHtml(cfg,58)}</div><div class="t1">${s.name}</div><div class="t2">${s.cat}</div></div>`}).join(''); refs.symbolGrid.querySelectorAll('[data-shape]').forEach(el=>el.addEventListener('click',()=>{state.shape=el.dataset.shape; state.customIcon=null; selectedVariantId=0; render()}))}
function logoInnerMaxWidth(cfg){if(['food-badge','hero-panel','takeaway-label','delivery-badge','capsule-lockup','banner-lockup','menu-stamp','corner-frame'].includes(cfg.template)) return 980; if(['stamp-round','chef-seal','artisan-plate','window-sign','modern-app','stacked-seal','premium-line'].includes(cfg.template)) return 760; return 860}
function wrapLogoHtml(cfg, frame='main'){const innerWidth=logoInnerMaxWidth(cfg); const scale=frame==='thumb'?0.27:1; const frameStyle=frame==='thumb'?`width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden;padding:10px;`:`width:100%;min-height:100%;display:flex;align-items:center;justify-content:center;padding:24px;`; const stageBg=cfg.panelBg||cfg.bg||'#ffffff'; const innerPad=frame==='thumb' ? 16 : 28; const radius=frame==='thumb' ? 26 : 34; return `<div style="${frameStyle}"><div style="width:${innerWidth}px;max-width:${innerWidth}px;display:flex;align-items:center;justify-content:center;transform:scale(${scale});transform-origin:center center;"><div style="background:${stageBg};border-radius:${radius}px;padding:${innerPad}px;display:flex;align-items:center;justify-content:center;">${buildLogoHtml(cfg)}</div></div></div>`}
function getActiveConfig(){return variantConfig(variantSeeds.find(v=>v.id===selectedVariantId)||variantSeeds[0])}
function renderVariants(){refs.variantList.innerHTML=variantSeeds.map(seed=>{const cfg=variantConfig(seed); return `<div class="variant-card ${selectedVariantId===seed.id?'active':''}" data-variant-id="${seed.id}"><div class="variant-preview" style="background:${cfg.transparent?'linear-gradient(45deg,#f8fafc,#eef2ff)':cfg.canvasBg};">${wrapLogoHtml(cfg,'thumb')}</div><div class="variant-meta"><strong>${seed.name}</strong><span>${(templates.find(t=>t.id===cfg.template)||{}).name||cfg.template}</span></div></div>`}).join(''); refs.variantList.querySelectorAll('[data-variant-id]').forEach(el=>el.addEventListener('click',()=>{selectedVariantId=Number(el.dataset.variantId);renderVariants();renderPreview()}))}
function renderPreview(){const cfg=getActiveConfig(); refs.mainPreview.style.background=cfg.transparent?'linear-gradient(135deg,#f8fafc,#eef2ff)':cfg.canvasBg; refs.mainPreview.innerHTML=wrapLogoHtml(cfg,'main'); refs.activeTemplateBadge.textContent=((templates.find(t=>t.id===cfg.template)||{}).name)||cfg.template; refs.activeModeBadge.textContent=cfg.mode==='ricemap24'?'Home Kitchen mode':cfg.mode==='restaurant'?'Restaurant mode':'Generic mode'; refs.activeShapeBadge.textContent=cfg.customIcon?'custom icon':cfg.shape}
function render(){renderTemplates();renderSymbols();renderVariants();renderPreview();refs.modePills.forEach(btn=>btn.classList.toggle('active',btn.dataset.mode===state.mode))}

function makeProjectData(){
  return {
    format:'lmaker',
    version:'1.64',
    savedAt:new Date().toISOString(),
    state:{...state},
    selectedVariantId,
    symbolSearch:refs.symbolSearch ? (refs.symbolSearch.value||'') : ''
  };
}
function applyLoadedProject(data){
  if(!data || (data.format && data.format!=='lmaker')) throw new Error('Invalid project file.');
  const incoming=(data && data.state) ? data.state : data;
  state={...defaultState,...incoming};
  selectedVariantId=Number.isFinite(Number(data && data.selectedVariantId)) ? Number(data.selectedVariantId) : 0;
  syncInputs();
  if(refs.symbolSearch) refs.symbolSearch.value = data && typeof data.symbolSearch==='string' ? data.symbolSearch : '';
  if(refs.iconUpload) refs.iconUpload.value='';
  render();
}
function saveProjectFile(){
  const payload=JSON.stringify(makeProjectData(),null,2);
  const blob=new Blob([payload],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const defaultName=(state.brand||'logo-project').trim().toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'logo-project';
  const requestedName=window.prompt('Project filename', defaultName);
  if(requestedName===null){
    URL.revokeObjectURL(url);
    return;
  }
  const cleanBase=String(requestedName||'').replace(/\.lmaker$/i,'').trim();
  const safeName=cleanBase.toLowerCase().replace(/[^a-z0-9._-]+/g,'-').replace(/^-+|-+$/g,'')||defaultName;
  const a=document.createElement('a');
  a.href=url;
  a.download=`${safeName}.lmaker`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function openProjectPicker(){
  if(refs.openProjectFile){
    refs.openProjectFile.value='';
    refs.openProjectFile.click();
  }
}
function handleOpenProjectFile(file){
  if(!file) return;
  const reader=new FileReader();
  reader.onload=()=>{
    try{
      const parsed=JSON.parse(String(reader.result||'{}'));
      applyLoadedProject(parsed);
    }catch(err){
      alert('Could not open this .lmaker file.');
      console.error(err);
    }
  };
  reader.readAsText(file);
}

function syncInputs(){refs.brand.value=state.brand; refs.tagline.value=state.tagline; if(refs.badgeText) refs.badgeText.value=state.badgeText||'HOME KITCHEN BRAND'; refs.brandSize.value=state.brandSize; refs.tagSize.value=state.tagSize; refs.brandWrap.value=state.brandWrap; refs.tagWrap.value=state.tagWrap; refs.badgeWrap.value=state.badgeWrap; refs.spacing.value=state.spacing; refs.font.value=state.font; refs.layout.value=state.layout; refs.canvasBg.value=state.canvasBg; if(refs.panelBg) refs.panelBg.value=state.panelBg||'#ffffff'; refs.bg.value=state.bg; if(refs.frameColor) refs.frameColor.value=state.frameColor||state.accent; refs.fg.value=state.fg; if(refs.tagColor) refs.tagColor.value=state.tagColor||state.fg; refs.accent.value=state.accent; refs.showTagline.checked=state.showTagline; refs.caps.checked=state.caps; refs.shapeCategory.value=state.shapeCategory; refs.iconScale.value=state.iconScale; if(refs.iconGap) refs.iconGap.value=state.iconGap ?? 28; if(refs.iconOffsetX) refs.iconOffsetX.value=state.iconOffsetX ?? 0; if(refs.iconOffsetY) refs.iconOffsetY.value=state.iconOffsetY ?? 0; refs.outlineIcon.checked=state.outlineIcon}
function activateTab(tab){refs.tabBtns.forEach(b=>b.classList.toggle('active',b.dataset.tab===tab)); refs.tabPanels.forEach(p=>p.classList.toggle('hidden',p.dataset.panel!==tab))}
refs.tabBtns.forEach(btn=>btn.addEventListener('click',()=>activateTab(btn.dataset.tab)));
refs.brand.addEventListener('input',e=>{state.brand=e.target.value;render()}); refs.tagline.addEventListener('input',e=>{state.tagline=e.target.value;render()}); if(refs.badgeText) refs.badgeText.addEventListener('input',e=>{state.badgeText=e.target.value;render()}); refs.brandSize.addEventListener('input',e=>{state.brandSize=Number(e.target.value);render()}); refs.tagSize.addEventListener('input',e=>{state.tagSize=Number(e.target.value);render()}); refs.brandWrap.addEventListener('input',e=>{state.brandWrap=Number(e.target.value);render()}); refs.tagWrap.addEventListener('input',e=>{state.tagWrap=Number(e.target.value);render()}); refs.badgeWrap.addEventListener('input',e=>{state.badgeWrap=Number(e.target.value);render()}); refs.spacing.addEventListener('input',e=>{state.spacing=Number(e.target.value);render()}); refs.font.addEventListener('change',e=>{state.font=e.target.value;render()}); refs.layout.addEventListener('change',e=>{state.layout=e.target.value;render()}); refs.canvasBg.addEventListener('input',e=>{state.canvasBg=e.target.value;render()}); if(refs.panelBg) refs.panelBg.addEventListener('input',e=>{state.panelBg=e.target.value;render()}); refs.bg.addEventListener('input',e=>{state.bg=e.target.value;render()}); if(refs.frameColor) refs.frameColor.addEventListener('input',e=>{state.frameColor=e.target.value;render()}); refs.fg.addEventListener('input',e=>{state.fg=e.target.value;render()}); if(refs.tagColor) refs.tagColor.addEventListener('input',e=>{state.tagColor=e.target.value;render()}); refs.accent.addEventListener('input',e=>{state.accent=e.target.value;render()}); refs.showTagline.addEventListener('change',e=>{state.showTagline=e.target.checked;render()}); refs.caps.addEventListener('change',e=>{state.caps=e.target.checked;render()});  refs.shapeCategory.addEventListener('change',e=>{state.shapeCategory=e.target.value;renderSymbols()}); refs.iconScale.addEventListener('input',e=>{state.iconScale=Number(e.target.value);render()}); if(refs.iconGap) refs.iconGap.addEventListener('input',e=>{state.iconGap=Number(e.target.value);render()}); if(refs.iconOffsetX) refs.iconOffsetX.addEventListener('input',e=>{state.iconOffsetX=Number(e.target.value);render()}); if(refs.iconOffsetY) refs.iconOffsetY.addEventListener('input',e=>{state.iconOffsetY=Number(e.target.value);render()}); refs.outlineIcon.addEventListener('change',e=>{state.outlineIcon=e.target.checked;render()}); refs.symbolSearch.addEventListener('input',()=>renderSymbols()); refs.iconUpload.addEventListener('change',e=>{const file=e.target.files&&e.target.files[0]; if(!file) return; const reader=new FileReader(); reader.onload=()=>{state.customIcon=reader.result; render()}; reader.readAsDataURL(file)});
refs.modePills.forEach(btn=>btn.addEventListener('click',()=>{const keepShapeCategory=state.shapeCategory||'all'; const keepSearch=refs.symbolSearch.value||''; state=btn.dataset.mode==='ricemap24'?{...riceMapPreset}:btn.dataset.mode==='restaurant'?{...restaurantPreset}:{...defaultState}; state.shapeCategory=keepShapeCategory; selectedVariantId=0; syncInputs(); refs.symbolSearch.value=keepSearch; render()}));
if(refs.saveProjectBtn) refs.saveProjectBtn.addEventListener('click',saveProjectFile); if(refs.openProjectBtn) refs.openProjectBtn.addEventListener('click',openProjectPicker); if(refs.openProjectFile) refs.openProjectFile.addEventListener('change',e=>handleOpenProjectFile(e.target.files&&e.target.files[0])); if(refs.exportPanelPng) refs.exportPanelPng.addEventListener('click',()=>exportLogo('panel')); if(refs.exportTransparentPng) refs.exportTransparentPng.addEventListener('click',()=>exportLogo('transparent'));
refs.resetBtn.addEventListener('click',()=>{state=state.mode==='ricemap24'?{...riceMapPreset}:state.mode==='restaurant'?{...restaurantPreset}:{...defaultState}; state.customIcon=null; refs.iconUpload.value=''; selectedVariantId=0; syncInputs(); render()}); refs.applyVariantToMain.addEventListener('click',()=>{const seed=variantSeeds.find(v=>v.id===selectedVariantId); if(!seed) return; const cfg=variantConfig(seed); state.template=cfg.template||state.template; state.shape=cfg.shape||state.shape; state.layout=cfg.layout||state.layout; state.accent=cfg.accent; if(!state.transparent){ state.panelBg=cfg.panelBg||cfg.bg; state.bg=cfg.bg; } syncInputs(); selectedVariantId=0; render()}); syncInputs(); activateTab('brand'); render();


function loadImage(src){
  return new Promise((resolve,reject)=>{
    const img=new Image();
    img.onload=()=>resolve(img);
    img.onerror=reject;
    img.src=src;
  });
}

function roundedRectPath(ctx,x,y,w,h,r){
  const rr=Math.max(0,Math.min(r,Math.min(w,h)/2));
  ctx.beginPath();
  ctx.moveTo(x+rr,y);
  ctx.arcTo(x+w,y,x+w,y+h,rr);
  ctx.arcTo(x+w,y+h,x,y+h,rr);
  ctx.arcTo(x,y+h,x,y,rr);
  ctx.arcTo(x,y,x+w,y,rr);
  ctx.closePath();
}

function drawRoundedRect(ctx,x,y,w,h,r,fill=null,stroke=null,lineWidth=1,dashed=false){
  ctx.save();
  if(dashed) ctx.setLineDash([10,8]);
  roundedRectPath(ctx,x,y,w,h,r);
  if(fill){ ctx.fillStyle=fill; ctx.fill(); }
  if(stroke){ ctx.lineWidth=lineWidth; ctx.strokeStyle=stroke; ctx.stroke(); }
  ctx.restore();
}

function fitFontFamily(font){
  return (font||'Inter, sans-serif').split(',')[0].trim().replace(/^['"]|['"]$/g,'') || 'Inter';
}

function measureSpacedText(ctx,text,letterSpacing){
  if(!text) return 0;
  const chars=[...text];
  let width=0;
  for(let i=0;i<chars.length;i++) width += ctx.measureText(chars[i]).width + (i<chars.length-1?letterSpacing:0);
  return width;
}

function wrapTextForWidth(ctx,text,maxWidth,letterSpacing){
  const clean=(text||'').replace(/\s+/g,' ').trim();
  if(!clean) return [''];
  const words=clean.split(' ');
  const lines=[];
  let current='';
  const pushCurrent=()=>{ if(current) { lines.push(current); current=''; } };
  for(const word of words){
    const candidate=current?`${current} ${word}`:word;
    if(measureSpacedText(ctx,candidate,letterSpacing)<=maxWidth){
      current=candidate;
      continue;
    }
    if(current) pushCurrent();
    if(measureSpacedText(ctx,word,letterSpacing)<=maxWidth){
      current=word;
      continue;
    }
    let chunk='';
    for(const ch of [...word]){
      const c=chunk+ch;
      if(measureSpacedText(ctx,c,letterSpacing)<=maxWidth || !chunk){
        chunk=c;
      } else {
        lines.push(chunk);
        chunk=ch;
      }
    }
    current=chunk;
  }
  pushCurrent();
  return lines.length?lines:[''];
}

function drawSpacedText(ctx,text,x,y,letterSpacing){
  const chars=[...text];
  let cx=x;
  for(let i=0;i<chars.length;i++){
    ctx.fillText(chars[i],cx,y);
    cx += ctx.measureText(chars[i]).width + (i<chars.length-1?letterSpacing:0);
  }
}

function prepareTextBlock(ctx,text,maxWidth,size,weight,family,color,opts={}){
  const lineHeight=opts.lineHeight || 1.1;
  const letterSpacing=(opts.letterSpacingEm||0)*size;
  const transform=opts.uppercase ? String(text||'').toUpperCase() : String(text||'');
  ctx.font=`${weight} ${size}px ${family}`;
  const lines=wrapTextForWidth(ctx,transform,maxWidth,letterSpacing);
  const width=Math.max(...lines.map(line=>measureSpacedText(ctx,line,letterSpacing)),0);
  const height=Math.max(size*lineHeight*lines.length, size);
  return {text:transform, lines, width, height, size, weight, family, color, lineHeight, letterSpacing};
}

function drawPreparedText(ctx,block,x,y,align='left'){
  ctx.save();
  ctx.font=`${block.weight} ${block.size}px ${block.family}`;
  ctx.fillStyle=block.color;
  ctx.textBaseline='top';
  for(let i=0;i<block.lines.length;i++){
    const line=block.lines[i];
    const lw=measureSpacedText(ctx,line,block.letterSpacing);
    const dx=align==='center'?x+(block.width-lw)/2:x;
    drawSpacedText(ctx,line,dx,y+i*(block.size*block.lineHeight),block.letterSpacing);
  }
  ctx.restore();
}

async function drawIconToCanvas(ctx,cfg,x,y,size){
  const src=cfg.customIcon
    ? cfg.customIcon
    : `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140" viewBox="0 0 140 140">${shapeSvg(cfg.shape,cfg.accent,cfg.fg,cfg.outlineIcon)}</svg>`)}`;
  const img=await loadImage(src);
  ctx.drawImage(img,x,y,size,size);
}

function buildExportModel(cfg,mode){
  const family=fitFontFamily(cfg.font);
  const brandSize=cfg.template==='food-badge'?cfg.brandSize+4:(cfg.template==='hero-panel'?cfg.brandSize+6:cfg.brandSize);
  const tagSize=(cfg.template==='minimal-chip')?cfg.tagSize-1:cfg.tagSize;
  const badgeSize=cfg.template==='hero-panel'?12:11;
  const uppercaseTag=true;
  const iconSizeBase=(cfg.iconScale||100)/100;
  const horizontalTemplates=new Set(['food-badge','banner-lockup','boxed-identity','delivery-badge','menu-stamp','capsule-lockup','corner-frame','hero-panel','minimal-chip','takeaway-label','clean-wordmark','signature-brand','monogram','startup-glow']);
  const verticalTemplates=new Set(['stacked-seal','modern-app','stamp-round','premium-line','vertical-brand','chef-seal','window-sign','artisan-plate']);
  let orientation='horizontal';
  if(verticalTemplates.has(cfg.template)) orientation='vertical';
  if(cfg.layout!=='icon-left' && !verticalTemplates.has(cfg.template) && !horizontalTemplates.has(cfg.template)) orientation='vertical';
  const iconSize=Math.round((orientation==='vertical'?120:140) * iconSizeBase);
  const padX=mode==='panel'?28:0;
  const padY=mode==='panel'?24:0;
  return {family,brandSize,tagSize,badgeSize,uppercaseTag,iconSize,padX,padY,orientation};
}

async function exportLogo(mode){
  const cfg=getActiveConfig();
  const m=buildExportModel(cfg,mode);
  const measureCanvas=document.createElement('canvas');
  const measureCtx=measureCanvas.getContext('2d');
  const brandBlock=prepareTextBlock(measureCtx,cfg.caps?cfg.brand.toUpperCase():cfg.brand,cfg.brandWrap||320,m.brandSize,800,m.family,cfg.fg,{lineHeight:1.0,letterSpacingEm:(cfg.spacing||0)*0.02});
  const tagBlock=cfg.showTagline ? prepareTextBlock(measureCtx,cfg.tagline,cfg.tagWrap||360,m.tagSize,500,m.family,cfg.tagColor||cfg.fg,{lineHeight:1.12,letterSpacingEm:0.1,uppercase:m.uppercaseTag}) : null;
  const badgeBlock=(mode==='panel' && (cfg.template==='food-badge' || cfg.template==='hero-panel'))
    ? prepareTextBlock(measureCtx,cfg.badgeText||'HOME KITCHEN BRAND',cfg.badgeWrap||220,m.badgeSize,800,m.family,cfg.bg,{lineHeight:1.0,letterSpacingEm:0.08,uppercase:true})
    : null;

  let gap=28;
  if(cfg.template==='minimal-chip') gap=16;
  if(cfg.template==='takeaway-label') gap=22;
  if(cfg.template==='delivery-badge') gap=24;
  if(cfg.template==='capsule-lockup') gap=24;
  let contentW=0, contentH=0;
  let textW=Math.max(brandBlock.width, tagBlock?tagBlock.width:0, badgeBlock?badgeBlock.width+24:0);
  let textH=brandBlock.height + (tagBlock?10+tagBlock.height:0) + (badgeBlock?15+badgeBlock.height+16:0);

  if(m.orientation==='horizontal'){
    contentW = m.iconSize + gap + textW;
    contentH = Math.max(m.iconSize, textH);
  } else {
    const topGap=18;
    contentW = Math.max(m.iconSize, textW, badgeBlock?badgeBlock.width+24:0);
    contentH = m.iconSize + topGap + brandBlock.height + (tagBlock?10+tagBlock.height:0) + (badgeBlock?15+badgeBlock.height+16:0);
    if(cfg.template==='premium-line') contentH += 36;
    if(cfg.template==='stamp-round' || cfg.template==='chef-seal' || cfg.template==='artisan-plate'){
      const circleSize = cfg.template==='stamp-round'?260:(cfg.template==='chef-seal'?270:250);
      contentW = Math.max(circleSize, textW, badgeBlock?badgeBlock.width+24:0);
      contentH = circleSize + 14 + brandBlock.height + (tagBlock?10+tagBlock.height:0);
    }
  }

  let extraW=0, extraH=0;
  if(mode==='panel'){
    extraW = m.padX*2;
    extraH = m.padY*2;
    if(cfg.template==='food-badge' || cfg.template==='hero-panel' || cfg.template==='banner-lockup' || cfg.template==='startup-glow') { extraW += 24; extraH += 24; }
    if(cfg.template==='takeaway-label' || cfg.template==='delivery-badge' || cfg.template==='menu-stamp' || cfg.template==='capsule-lockup' || cfg.template==='minimal-chip') { extraW += 16; extraH += 16; }
  }
  const baseWidth=Math.ceil(contentW+extraW);
  const baseHeight=Math.ceil(contentH+extraH);
  const maxSide=Math.max(baseWidth, baseHeight);
  const deviceScale=(typeof window!=='undefined' && window.devicePixelRatio) ? window.devicePixelRatio : 1;
  const exportScale=Math.max(3, Math.min(6, Math.ceil(deviceScale*2)));
  const oversample=(maxSide * exportScale) <= 6000 ? exportScale : Math.max(2, Math.floor(6000 / Math.max(1, maxSide)));
  const canvas=document.createElement('canvas');
  canvas.width=Math.max(1, Math.round(baseWidth * oversample));
  canvas.height=Math.max(1, Math.round(baseHeight * oversample));
  const ctx=canvas.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.setTransform(oversample,0,0,oversample,0,0);
  ctx.clearRect(0,0,baseWidth,baseHeight);

  let ox=(baseWidth-contentW)/2;
  let oy=(baseHeight-contentH)/2;

  if(mode==='panel'){
    const fill=cfg.panelBg||cfg.bg||'#ffffff';
    const border=cfg.frameColor||cfg.accent;
    // Always draw the outer preview panel so the exported PNG matches the main preview.
    drawRoundedRect(ctx,0,0,baseWidth,baseHeight,34,fill,null,0,false);
    if(cfg.template==='food-badge' || cfg.template==='hero-panel'){
      drawRoundedRect(ctx,ox-12,oy-12,contentW+24,contentH+24,32,fill,border,2,false);
    } else if(cfg.template==='banner-lockup' || cfg.template==='startup-glow'){
      drawRoundedRect(ctx,ox-12,oy-12,contentW+24,contentH+24,32,fill,border,2,false);
    } else if(cfg.template==='takeaway-label'){
      drawRoundedRect(ctx,ox-8,oy-8,contentW+16,contentH+16,24,cfg.accent,null,0,false);
    } else if(cfg.template==='delivery-badge' || cfg.template==='capsule-lockup'){
      drawRoundedRect(ctx,ox-8,oy-8,contentW+16,contentH+16,999,fill,border,2,false);
    } else if(cfg.template==='menu-stamp'){
      drawRoundedRect(ctx,ox-8,oy-8,contentW+16,contentH+16,22,fill,border,2,true);
    } else if(cfg.template==='minimal-chip'){
      drawRoundedRect(ctx,ox-8,oy-8,contentW+16,contentH+16,20,fill,border,2,false);
    }
  }

  const brandXBase = m.orientation==='horizontal' ? ox + m.iconSize + gap : ox + (contentW-brandBlock.width)/2;
  const iconX = m.orientation==='horizontal' ? ox : ox + (contentW-m.iconSize)/2;
  let iconY, brandY;

  if(m.orientation==='horizontal'){
    iconY = oy + (contentH - m.iconSize)/2;
    brandY = oy + (contentH - textH)/2;
  } else {
    if(cfg.template==='stamp-round' || cfg.template==='chef-seal' || cfg.template==='artisan-plate'){
      const circleSize = cfg.template==='stamp-round'?260:(cfg.template==='chef-seal'?270:250);
      iconY = oy + (circleSize-m.iconSize)/2 - 8;
      brandY = oy + circleSize + 14;
      const cx=ox + (contentW-circleSize)/2;
      const cy=oy;
      if(mode==='panel' || cfg.template!=='artisan-plate'){
        if(cfg.template==='stamp-round' || cfg.template==='artisan-plate'){
          ctx.save();
          ctx.beginPath();
          ctx.arc(cx+circleSize/2, cy+circleSize/2, circleSize/2 - (cfg.template==='artisan-plate'?6:5), 0, Math.PI*2);
          ctx.strokeStyle=cfg.frameColor||cfg.accent;
          ctx.lineWidth=cfg.template==='stamp-round'?10:12;
          ctx.stroke();
          ctx.restore();
        }
        if(cfg.template==='chef-seal'){
          drawRoundedRect(ctx,cx,cy,circleSize,circleSize,40,(cfg.panelBg||cfg.bg||'#ffffff'),cfg.frameColor||cfg.accent,2,false);
        }
      }
    } else {
      iconY = oy;
      brandY = oy + m.iconSize + 18;
    }
  }

  if(cfg.template==='takeaway-label' && mode==='panel'){
    const bgColor=cfg.bg;
    await drawIconToCanvas(ctx,{...cfg,accent:bgColor,fg:bgColor,outlineIcon:false},iconX,iconY,Math.round(m.iconSize*0.7));
  } else if(cfg.template==='boxed-identity' && mode==='panel'){
    const iconPad=14, boxSize=m.iconSize+iconPad*2;
    drawRoundedRect(ctx,iconX-iconPad,iconY-iconPad,boxSize,boxSize,26,cfg.accent,null,0,false);
    await drawIconToCanvas(ctx,{...cfg,accent:cfg.bg},iconX,iconY,m.iconSize);
  } else {
    await drawIconToCanvas(ctx,cfg,iconX,iconY,m.iconSize);
  }

  if(cfg.template==='premium-line' && mode==='panel'){
    ctx.strokeStyle=cfg.accent;
    ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(ox+(contentW-230)/2, oy+6); ctx.lineTo(ox+(contentW+230)/2, oy+6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ox+(contentW-230)/2, oy+contentH-6); ctx.lineTo(ox+(contentW+230)/2, oy+contentH-6); ctx.stroke();
  }
  if(cfg.template==='corner-frame'){
    ctx.strokeStyle=cfg.frameColor||cfg.accent; ctx.lineWidth=6;
    const w=84,h=84;
    ctx.beginPath(); ctx.moveTo(ox,oy+h); ctx.lineTo(ox,oy); ctx.lineTo(ox+w,oy); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ox+contentW-w,oy+contentH); ctx.lineTo(ox+contentW,oy+contentH); ctx.lineTo(ox+contentW,oy+contentH-h); ctx.stroke();
  }

  if(cfg.template==='boxed-identity' && mode==='panel'){
    const boxX=brandXBase;
    const boxY=brandY;
    drawRoundedRect(ctx,boxX,boxY,Math.max(brandBlock.width+32,cfg.brandWrap||320),brandBlock.height+24,16,cfg.fg,null,0,false);
    const invBrand={...brandBlock,color:cfg.bg};
    drawPreparedText(ctx,invBrand,boxX+16,boxY+12,'left');
    if(tagBlock) drawPreparedText(ctx,tagBlock,brandXBase,boxY+brandBlock.height+34,'left');
  } else {
    drawPreparedText(ctx,brandBlock,brandXBase,brandY,m.orientation==='vertical'?'center':'left');
    if(tagBlock){
      const tx = m.orientation==='vertical' ? ox + (contentW-tagBlock.width)/2 : brandXBase;
      drawPreparedText(ctx,tagBlock,tx,brandY+brandBlock.height+10,m.orientation==='vertical'?'center':'left');
    }
    if(badgeBlock){
      const by=brandY+brandBlock.height+(tagBlock?10+tagBlock.height:0)+15;
      const bw=badgeBlock.width+24;
      const bh=badgeBlock.height+16;
      const bx=m.orientation==='vertical'?ox+(contentW-bw)/2:brandXBase;
      drawRoundedRect(ctx,bx,by,bw,bh,cfg.template==='food-badge'?999:14,cfg.accent,null,0,false);
      drawPreparedText(ctx,badgeBlock,bx+12,by+8,'center');
    }
  }

  const safeName=(cfg.brand||'logo').trim().toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'logo';
  const suffix=mode==='panel'?'with-panel':'transparent';
  const a=document.createElement('a');
  a.href=canvas.toDataURL('image/png');
  a.download=`${safeName}-${suffix}.png`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}


(function(){
  const fileInput = document.getElementById('iconUpload');
  const fileBtn = document.getElementById('iconUploadBtn');
  const fileName = document.getElementById('iconUploadName');
  if(fileInput && fileBtn){
    fileBtn.addEventListener('click', () => fileInput.click());
    const syncFileName = () => {
      const f = fileInput.files && fileInput.files[0];
      if(fileName) fileName.textContent = f ? f.name : 'No file selected';
    };
    fileInput.addEventListener('change', syncFileName);
    syncFileName();
  }
})();


(function(){
  const vp = document.querySelector('.right-panel .panel-body');
  const vl = document.getElementById('variantList');
  if(vp){
    vp.style.overflowY = 'auto';
    vp.style.overflowX = 'hidden';
    vp.style.maxHeight = 'none';
    vp.style.height = 'auto';
  }
  if(vl){
    vl.style.maxHeight = 'none';
    vl.style.height = 'auto';
    vl.style.overflow = 'visible';
    vl.style.display = 'grid';
    vl.style.gridTemplateColumns = '1fr';
  }
})();
