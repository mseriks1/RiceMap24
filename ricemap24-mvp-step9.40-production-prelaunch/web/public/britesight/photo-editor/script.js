
(function () {
  const state = {
    source: { image: null, dataUrl: "", width: 0, height: 0, name: "", type: "", size: 0 },
    document: {
      geometry: { rotationQuarterTurns: 0, straightenDegrees: 0, flipX: false, flipY: false },
      crop: { x: 0, y: 0, width: 0, height: 0 },
      adjustments: {
        exposure: 0, contrast: 0, saturation: 0, vibrance: 0,
        highlights: 0, whites: 0, shadows: 0, blacks: 0,
        temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0,
        sharpen: 0, vignette: 0
      },
      filterLayer: { preset: "none", intensity: 0.65 },
      masks: [
        { dataUrl: "", resolutionScale: 1, localAdjustments: { exposure: 0, contrast: 0, saturation: 0, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0 }, name: "Mask 1" },
        { dataUrl: "", resolutionScale: 1, localAdjustments: { exposure: 0, contrast: 0, saturation: 0, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0 }, name: "Mask 2" },
        { dataUrl: "", resolutionScale: 1, localAdjustments: { exposure: 0, contrast: 0, saturation: 0, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0 }, name: "Mask 3" }
      ],
      activeMaskIndex: 0,
      view: { baseScale: 1, zoomPercent: 100, panX: 0, panY: 0 }
    },
    runtime: {
      maskCanvases: [null, null, null],
      adjustDragReleaseTimer: 0,
      maskRevisions: [0, 0, 0]
    },
    cache: {
      dragRenderKey: "",
      dragRenderCanvas: null,
      baseAdjustKey: "",
      baseAdjustImageData: null,
      baseAdjustWidth: 0,
      baseAdjustHeight: 0,
      scaledMaskEntries: {},
      finalRenderKey: "",
      finalRenderCanvas: null
    },
    history: { undoStack: [], redoStack: [] },
    ui: {
      viewportWidth: 1200,
      viewportHeight: 700,
      isAdjustDragging: false,
      activeAdjustmentKey: "",
      cropMode: false,
      pendingCrop: null,
      cropDrag: null,
      maskMode: false,
      maskOverlayVisible: true,
      maskViewMode: "overlay",
      maskBrushMode: "paint",
      maskBrushSize: 80,
      maskBrushFeather: 0.6,
      maskStroke: null,
      maskHoverPos: null,
      cropAspect: "free",
      showOriginal: false,
      showOriginalMomentary: false,
      splitView: false,
      splitPosition: 0.5,
      splitDrag: null,
      adjustPresetKey: "none",
      adjustPresetAmount: 1,
      adjustPresetBaseAdjustments: null,
      adjustPresetFramePending: false,
          },
    uiView: {
      isPanning: false,
      panPointerId: null,
      panStartX: 0,
      panStartY: 0,
      panOriginX: 0,
      panOriginY: 0
    }
  };

  const canvas = document.getElementById("canvas");
  const ctx = canvas.getContext("2d");
  const stage = document.getElementById("stage");
  const status = document.getElementById("status");
  const statusText = document.getElementById("statusText");
  const importBtn = document.getElementById("importBtn");
  const fileInput = document.getElementById("fileInput");
  const saveProjectBtn = document.getElementById("saveProjectBtn");
  const openProjectBtn = document.getElementById("openProjectBtn");
  const projectFileInput = document.getElementById("projectFileInput");
  const savePresetBtn = document.getElementById("savePresetBtn");
  const openPresetBtn = document.getElementById("openPresetBtn");
  const presetFileInput = document.getElementById("presetFileInput");
  const exportFormatSelect = document.getElementById("exportFormatSelect");
    const exportScaleSelect = document.getElementById("exportScaleSelect");
  const exportScaleValue = document.getElementById("exportScaleValue");
  const exportQualityRange = document.getElementById("exportQualityRange");
  const exportQualityValue = document.getElementById("exportQualityValue");
  const exportQualityGroup = document.getElementById("exportQualityGroup");
      const exportOriginalHint = document.getElementById("exportOriginalHint");
  const exportSizeHint = document.getElementById("exportSizeHint");
  const exportFileSizeHint = document.getElementById("exportFileSizeHint");
  const exportImageBtn = document.getElementById("exportImageBtn");
  const exportFilenameInput = document.getElementById("exportFilenameInput");
  const exportExtensionHint = document.getElementById("exportExtensionHint");
  const rotateLeftBtn = document.getElementById("rotateLeftBtn");
  const rotateRightBtn = document.getElementById("rotateRightBtn");
  const resetGeometryBtn = document.getElementById("resetGeometryBtn");
  const flipHorizontalBtn = document.getElementById("flipHorizontalBtn");
  const flipVerticalBtn = document.getElementById("flipVerticalBtn");
  const straightenRange = document.getElementById("straightenRange");
  const straightenValue = document.getElementById("straightenValue");
  const cropModeBtn = document.getElementById("cropModeBtn");
  const cropAspectSelect = document.getElementById("cropAspectSelect");
  const cropAspectValue = document.getElementById("cropAspectValue");
  const applyCropBtn = document.getElementById("applyCropBtn");
  const cancelCropBtn = document.getElementById("cancelCropBtn");
  const resetCropBtn = document.getElementById("resetCropBtn");

  const exposureRange = document.getElementById("exposureRange");
  const exposureValue = document.getElementById("exposureValue");
  const contrastRange = document.getElementById("contrastRange");
  const contrastValue = document.getElementById("contrastValue");
  const saturationRange = document.getElementById("saturationRange");
  const saturationValue = document.getElementById("saturationValue");
  const vibranceRange = document.getElementById("vibranceRange");
  const vibranceValue = document.getElementById("vibranceValue");
  const highlightsRange = document.getElementById("highlightsRange");
  const highlightsValue = document.getElementById("highlightsValue");
  const whitesRange = document.getElementById("whitesRange");
  const whitesValue = document.getElementById("whitesValue");
  const shadowsRange = document.getElementById("shadowsRange");
  const shadowsValue = document.getElementById("shadowsValue");
  const blacksRange = document.getElementById("blacksRange");
  const blacksValue = document.getElementById("blacksValue");
  const temperatureRange = document.getElementById("temperatureRange");
  const temperatureValue = document.getElementById("temperatureValue");
  const tintRange = document.getElementById("tintRange");
  const tintValue = document.getElementById("tintValue");
  const hueRange = document.getElementById("hueRange");
  const hueValue = document.getElementById("hueValue");
  const sepiaRange = document.getElementById("sepiaRange");
  const sepiaValue = document.getElementById("sepiaValue");
  const blurRange = document.getElementById("blurRange");
  const blurValue = document.getElementById("blurValue");
  const sharpenRange = document.getElementById("sharpenRange");
  const sharpenValue = document.getElementById("sharpenValue");
  const vignetteRange = document.getElementById("vignetteRange");
  const vignetteValue = document.getElementById("vignetteValue");
  const maskModeBtn = document.getElementById("maskModeBtn");
  const activeMaskSelect = document.getElementById("activeMaskSelect");
  const addMaskBtn = document.getElementById("addMaskBtn");
  const deleteMaskBtn = document.getElementById("deleteMaskBtn");
  const maskOverlayBtn = document.getElementById("maskOverlayBtn");
  const maskViewSelect = document.getElementById("maskViewSelect");
  const maskViewValue = document.getElementById("maskViewValue");
  const maskBrushSizeRange = document.getElementById("maskBrushSizeRange");
  const maskBrushSizeValue = document.getElementById("maskBrushSizeValue");
  const maskBrushFeatherRange = document.getElementById("maskBrushFeatherRange");
  const maskBrushFeatherValue = document.getElementById("maskBrushFeatherValue");
  const maskBrushModeValue = document.getElementById("maskBrushModeValue");
  const maskPaintBtn = document.getElementById("maskPaintBtn");
  const maskEraseBtn = document.getElementById("maskEraseBtn");
  const invertMaskBtn = document.getElementById("invertMaskBtn");
  const maskExposureRange = document.getElementById("maskExposureRange");
  const maskExposureValue = document.getElementById("maskExposureValue");
  const maskContrastRange = document.getElementById("maskContrastRange");
  const maskContrastValue = document.getElementById("maskContrastValue");
  const maskSaturationRange = document.getElementById("maskSaturationRange");
  const maskSaturationValue = document.getElementById("maskSaturationValue");
  const maskTemperatureRange = document.getElementById("maskTemperatureRange");
  const maskTemperatureValue = document.getElementById("maskTemperatureValue");
  const maskTintRange = document.getElementById("maskTintRange");
  const maskTintValue = document.getElementById("maskTintValue");
  const maskHueRange = document.getElementById("maskHueRange");
  const maskHueValue = document.getElementById("maskHueValue");
  const maskSepiaRange = document.getElementById("maskSepiaRange");
  const maskSepiaValue = document.getElementById("maskSepiaValue");
  const maskBlurRange = document.getElementById("maskBlurRange");
  const maskBlurValue = document.getElementById("maskBlurValue");
  const maskSharpenRange = document.getElementById("maskSharpenRange");
  const maskSharpenValue = document.getElementById("maskSharpenValue");
  const filterPresetSelect = document.getElementById("filterPresetSelect");
  const filterPresetValue = document.getElementById("filterPresetValue");
  const filterIntensityRange = document.getElementById("filterIntensityRange");
  const filterIntensityValue = document.getElementById("filterIntensityValue");
  const resetFilterBtn = document.getElementById("resetFilterBtn");
  const adjustPresetSelect = document.getElementById("adjustPresetSelect");
  const adjustPresetValue = document.getElementById("adjustPresetValue");
  const adjustPresetAmountRange = document.getElementById("adjustPresetAmountRange");
  const adjustPresetAmountValue = document.getElementById("adjustPresetAmountValue");
  const applyAdjustPresetBtn = document.getElementById("applyAdjustPresetBtn");
  const resetAdjustPresetBtn = document.getElementById("resetAdjustPresetBtn");

  const resetAdjustmentsBtn = document.getElementById("resetAdjustmentsBtn");
  const resetMaskAdjustmentsBtn = document.getElementById("resetMaskAdjustmentsBtn");
  const fitBtn = document.getElementById("fitBtn");
  const actualSizeBtn = document.getElementById("actualSizeBtn");
  const beforeAfterBtn = document.getElementById("beforeAfterBtn");
  const zoomRange = document.getElementById("zoomRange");
  const zoomValue = document.getElementById("zoomValue");
  const undoBtn = document.getElementById("undoBtn");
  const redoBtn = document.getElementById("redoBtn");

  const adjustmentControls = [
    ["exposure", exposureRange, exposureValue],
    ["contrast", contrastRange, contrastValue],
    ["saturation", saturationRange, saturationValue],
    ["vibrance", vibranceRange, vibranceValue],
    ["highlights", highlightsRange, highlightsValue],
    ["whites", whitesRange, whitesValue],
    ["shadows", shadowsRange, shadowsValue],
    ["blacks", blacksRange, blacksValue],
    ["temperature", temperatureRange, temperatureValue],
    ["tint", tintRange, tintValue],
    ["hue", hueRange, hueValue],
    ["sepia", sepiaRange, sepiaValue],
    ["blur", blurRange, blurValue],
    ["sharpen", sharpenRange, sharpenValue],
    ["vignette", vignetteRange, vignetteValue],
  ];

  const maskAdjustmentControls = [
    ["exposure", maskExposureRange, maskExposureValue],
    ["contrast", maskContrastRange, maskContrastValue],
    ["saturation", maskSaturationRange, maskSaturationValue],
    ["temperature", maskTemperatureRange, maskTemperatureValue],
    ["tint", maskTintRange, maskTintValue],
    ["hue", maskHueRange, maskHueValue],
    ["sepia", maskSepiaRange, maskSepiaValue],
    ["blur", maskBlurRange, maskBlurValue],
    ["sharpen", maskSharpenRange, maskSharpenValue],
  ];

  const FILTER_PRESET_LABELS = {
    none: "None",
    cleanStudio: "Clean Studio",
    softFade: "Soft Fade",
    tealOrange: "Teal Orange",
    monoFilm: "Mono Film",
    goldenHour: "Golden Hour",
    nightBlue: "Night Blue",
    forestMatte: "Forest Matte",
    roseGlow: "Rose Glow",
    crispPop: "Crisp Pop",
    autumnCine: "Autumn Cine",
    silverMist: "Silver Mist",
    magentaDream: "Magenta Dream",
    arcticGlass: "Arctic Glass",
    desertDust: "Desert Dust",
    oceanMist: "Ocean Mist",
    emberGlow: "Ember Glow",
    lavenderHaze: "Lavender Haze",
    noirFade: "Noir Fade",
    porcelain: "Porcelain",
    punchColor: "Punch Color",
    sunwashed: "Sunwashed",
    cobaltPunch: "Cobalt Punch",
    berryBloom: "Berry Bloom",
    oliveCine: "Olive Cine",
    copperStreet: "Copper Street",
    blueSteel: "Blue Steel",
    peachAir: "Peach Air",
    plumNight: "Plum Night",
    emeraldPop: "Emerald Pop",
    sepiaPaper: "Sepia Paper",
    icyMono: "Icy Mono",
    mokaMatte: "Moka Matte",
    neonPulse: "Neon Pulse",
    stormGray: "Storm Gray",
    creamBloom: "Cream Bloom",
    duskLavender: "Dusk Lavender"
  };

  const ADJUST_PRESET_LABELS = {
    none: "None",
    cleanBright: "Clean Bright",
    warmPortrait: "Warm Portrait",
    softMatte: "Soft Matte",
    crispProduct: "Crisp Product",
    deepContrast: "Deep Contrast",
    moodyCool: "Moody Cool",
    goldenLift: "Golden Lift",
    monoPunch: "Mono Punch",
    dreamyGlow: "Dreamy Glow",
    socialPop: "Social Pop",
    freshAir: "Fresh Air",
    sunsetSkin: "Sunset Skin",
    pastelFade: "Pastel Fade",
    studioNeutral: "Studio Neutral",
    punchyColor: "Punchy Color",
    filmWash: "Film Wash",
    noirPortrait: "Noir Portrait",
    coolStreet: "Cool Street",
    brightMatte: "Bright Matte",
    richWarmth: "Rich Warmth",
    cleanMono: "Clean Mono",
    emeraldPopAdjust: "Emerald Pop",
    cocoaFade: "Cocoa Fade",
    blueMood: "Blue Mood",
    peachGlow: "Peach Glow"
  };

  const ADJUST_PRESET_VALUES = {
    none: {},
    cleanBright: { exposure: 0.55, contrast: 0.18, saturation: 0.10, vibrance: 0.22, highlights: -0.22, whites: 0.18, shadows: 0.24, blacks: -0.08, temperature: 0.03, tint: 0.02, hue: 0, sepia: 0, blur: 0, sharpen: 0.28, vignette: 0.06 },
    warmPortrait: { exposure: 0.28, contrast: 0.04, saturation: 0.10, vibrance: 0.18, highlights: -0.12, whites: 0.05, shadows: 0.18, blacks: 0.03, temperature: 0.28, tint: 0.10, hue: 0, sepia: 0.10, blur: 0, sharpen: 0.12, vignette: 0.12 },
    softMatte: { exposure: 0.14, contrast: -0.30, saturation: -0.06, vibrance: 0.04, highlights: -0.18, whites: -0.14, shadows: 0.32, blacks: 0.34, temperature: 0.06, tint: 0.02, hue: 0, sepia: 0.12, blur: 0, sharpen: 0.04, vignette: 0.18 },
    crispProduct: { exposure: 0.24, contrast: 0.34, saturation: 0.06, vibrance: 0.12, highlights: -0.10, whites: 0.26, shadows: 0.08, blacks: -0.22, temperature: -0.02, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0.72, vignette: 0.04 },
    deepContrast: { exposure: -0.05, contrast: 0.52, saturation: 0.08, vibrance: 0.14, highlights: -0.28, whites: 0.10, shadows: -0.12, blacks: -0.42, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0.28, vignette: 0.36 },
    moodyCool: { exposure: -0.12, contrast: 0.24, saturation: -0.10, vibrance: 0.04, highlights: -0.18, whites: -0.04, shadows: -0.04, blacks: -0.22, temperature: -0.34, tint: -0.05, hue: 0, sepia: 0, blur: 0, sharpen: 0.12, vignette: 0.32 },
    goldenLift: { exposure: 0.34, contrast: 0.08, saturation: 0.14, vibrance: 0.18, highlights: -0.14, whites: 0.12, shadows: 0.16, blacks: -0.08, temperature: 0.38, tint: 0.05, hue: 6, sepia: 0.12, blur: 0, sharpen: 0.14, vignette: 0.10 },
    monoPunch: { exposure: 0.10, contrast: 0.44, saturation: -1, vibrance: 0, highlights: -0.22, whites: 0.16, shadows: 0.10, blacks: -0.28, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0.28, vignette: 0.26 },
    dreamyGlow: { exposure: 0.30, contrast: -0.22, saturation: 0.05, vibrance: 0.10, highlights: 0.10, whites: 0.14, shadows: 0.20, blacks: 0.10, temperature: 0.15, tint: 0.08, hue: 0, sepia: 0.08, blur: 0.45, sharpen: 0.02, vignette: 0.14 },
    socialPop: { exposure: 0.16, contrast: 0.24, saturation: 0.22, vibrance: 0.38, highlights: -0.12, whites: 0.18, shadows: 0.14, blacks: -0.14, temperature: 0.05, tint: 0.03, hue: 0, sepia: 0, blur: 0, sharpen: 0.34, vignette: 0.12 },
    freshAir: { exposure: 0.26, contrast: 0.06, saturation: 0.04, vibrance: 0.14, highlights: -0.12, whites: 0.12, shadows: 0.18, blacks: -0.04, temperature: -0.12, tint: 0.01, hue: 0, sepia: 0, blur: 0, sharpen: 0.16, vignette: 0.04 },
    sunsetSkin: { exposure: 0.18, contrast: 0.02, saturation: 0.12, vibrance: 0.16, highlights: -0.08, whites: 0.04, shadows: 0.16, blacks: 0.02, temperature: 0.34, tint: 0.12, hue: 2, sepia: 0.10, blur: 0, sharpen: 0.08, vignette: 0.12 },
    pastelFade: { exposure: 0.22, contrast: -0.20, saturation: -0.08, vibrance: 0.05, highlights: 0.08, whites: 0.10, shadows: 0.14, blacks: 0.10, temperature: 0.08, tint: 0.08, hue: 4, sepia: 0.04, blur: 0.12, sharpen: 0.02, vignette: 0.08 },
    studioNeutral: { exposure: 0.12, contrast: 0.10, saturation: 0.02, vibrance: 0.06, highlights: -0.10, whites: 0.14, shadows: 0.10, blacks: -0.08, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0.18, vignette: 0.02 },
    punchyColor: { exposure: 0.10, contrast: 0.28, saturation: 0.24, vibrance: 0.42, highlights: -0.14, whites: 0.12, shadows: 0.10, blacks: -0.16, temperature: 0.02, tint: 0.01, hue: 0, sepia: 0, blur: 0, sharpen: 0.30, vignette: 0.10 },
    filmWash: { exposure: 0.08, contrast: -0.16, saturation: -0.04, vibrance: 0.02, highlights: 0.06, whites: -0.04, shadows: 0.18, blacks: 0.16, temperature: 0.10, tint: -0.02, hue: -2, sepia: 0.16, blur: 0.08, sharpen: 0.04, vignette: 0.18 },
    noirPortrait: { exposure: 0.02, contrast: 0.40, saturation: -1, vibrance: 0, highlights: -0.20, whites: 0.10, shadows: 0.04, blacks: -0.30, temperature: 0, tint: 0, hue: 0, sepia: 0.04, blur: 0, sharpen: 0.24, vignette: 0.30 },
    coolStreet: { exposure: -0.04, contrast: 0.20, saturation: -0.02, vibrance: 0.08, highlights: -0.16, whites: 0.02, shadows: 0.02, blacks: -0.18, temperature: -0.24, tint: -0.04, hue: -3, sepia: 0, blur: 0, sharpen: 0.18, vignette: 0.20 },
    brightMatte: { exposure: 0.32, contrast: -0.18, saturation: 0.02, vibrance: 0.06, highlights: 0.04, whites: 0.12, shadows: 0.24, blacks: 0.18, temperature: 0.04, tint: 0.01, hue: 0, sepia: 0.02, blur: 0, sharpen: 0.08, vignette: 0.06 },
    richWarmth: { exposure: 0.12, contrast: 0.12, saturation: 0.14, vibrance: 0.20, highlights: -0.12, whites: 0.06, shadows: 0.12, blacks: -0.08, temperature: 0.26, tint: 0.06, hue: 3, sepia: 0.08, blur: 0, sharpen: 0.14, vignette: 0.10 },
    cleanMono: { exposure: 0.16, contrast: 0.24, saturation: -1, vibrance: 0, highlights: -0.10, whites: 0.16, shadows: 0.12, blacks: -0.14, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0.20, vignette: 0.10 },
    emeraldPopAdjust: { exposure: 0.06, contrast: 0.18, saturation: 0.12, vibrance: 0.26, highlights: -0.10, whites: 0.08, shadows: 0.10, blacks: -0.10, temperature: -0.04, tint: -0.02, hue: -8, sepia: 0, blur: 0, sharpen: 0.20, vignette: 0.12 },
    cocoaFade: { exposure: 0.06, contrast: -0.10, saturation: -0.04, vibrance: 0.02, highlights: -0.08, whites: -0.04, shadows: 0.16, blacks: 0.12, temperature: 0.18, tint: 0.02, hue: 2, sepia: 0.18, blur: 0.04, sharpen: 0.06, vignette: 0.16 },
    blueMood: { exposure: -0.08, contrast: 0.16, saturation: -0.04, vibrance: 0.02, highlights: -0.14, whites: -0.02, shadows: 0.02, blacks: -0.16, temperature: -0.30, tint: -0.02, hue: -6, sepia: 0, blur: 0.02, sharpen: 0.14, vignette: 0.22 },
    peachGlow: { exposure: 0.24, contrast: -0.06, saturation: 0.10, vibrance: 0.14, highlights: 0.06, whites: 0.12, shadows: 0.16, blacks: 0.04, temperature: 0.20, tint: 0.10, hue: 4, sepia: 0.04, blur: 0.10, sharpen: 0.04, vignette: 0.08 }
  };

  function getDefaultAdjustments() {
    return {
      exposure: 0, contrast: 0, saturation: 0, vibrance: 0,
      highlights: 0, whites: 0, shadows: 0, blacks: 0,
      temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0,
      sharpen: 0, vignette: 0
    };
  }

  function getDefaultFilterLayer() {
    return { preset: "none", intensity: 0.65 };
  }

  function getDefaultMaskAdjustments() {
    return { exposure: 0, contrast: 0, saturation: 0, temperature: 0, tint: 0, hue: 0, sepia: 0, blur: 0, sharpen: 0 };
  }

  function createDefaultMask(name) {
    return { dataUrl: "", resolutionScale: 1, localAdjustments: getDefaultMaskAdjustments(), name: name || "Mask" };
  }

  function ensureMaskStateStructure() {
    if (!Array.isArray(state.document.masks) || !state.document.masks.length) {
      const legacyMask = state.document.mask && typeof state.document.mask === "object" ? state.document.mask : null;
      state.document.masks = [legacyMask ? Object.assign(createDefaultMask("Mask 1"), legacyMask) : createDefaultMask("Mask 1"), createDefaultMask("Mask 2"), createDefaultMask("Mask 3")];
    }
    while (state.document.masks.length < 3) state.document.masks.push(createDefaultMask(`Mask ${state.document.masks.length + 1}`));
    state.document.masks = state.document.masks.slice(0, 3).map(function(mask, idx) {
      const out = Object.assign(createDefaultMask(`Mask ${idx + 1}`), mask || {});
      out.localAdjustments = Object.assign(getDefaultMaskAdjustments(), out.localAdjustments || {});
      Object.keys(getDefaultMaskAdjustments()).forEach(function(key) {
        out.localAdjustments[key] = Number(out.localAdjustments[key] || 0);
      });
      out.name = String(out.name || `Mask ${idx + 1}`);
      return out;
    });
    state.document.activeMaskIndex = clamp(Number(state.document.activeMaskIndex || 0), 0, 2);
    if (!Array.isArray(state.runtime.maskCanvases)) state.runtime.maskCanvases = [null, null, null];
    while (state.runtime.maskCanvases.length < 3) state.runtime.maskCanvases.push(null);
    if (!Array.isArray(state.runtime.maskRevisions)) state.runtime.maskRevisions = [0, 0, 0];
    while (state.runtime.maskRevisions.length < 3) state.runtime.maskRevisions.push(0);
  }

  function getActiveMaskIndex() { ensureMaskStateStructure(); return clamp(Number(state.document.activeMaskIndex || 0), 0, 2); }
  function getActiveMask() { ensureMaskStateStructure(); return state.document.masks[getActiveMaskIndex()]; }
  function getMaskAt(index) { ensureMaskStateStructure(); return state.document.masks[clamp(Number(index || 0), 0, 2)]; }
  function getRuntimeMaskCanvas(index) { ensureMaskStateStructure(); return state.runtime.maskCanvases[clamp(Number(index || 0), 0, 2)] || null; }
  function setRuntimeMaskCanvas(index, canvas) { ensureMaskStateStructure(); state.runtime.maskCanvases[clamp(Number(index || 0), 0, 2)] = canvas || null; }
  function getMaskLabel(index) { const mask = getMaskAt(index); return mask.name || `Mask ${index + 1}`; }
  function getMaskCacheEntry(index) { ensureMaskStateStructure(); if (!state.cache.scaledMaskEntries) state.cache.scaledMaskEntries = {}; if (!state.cache.scaledMaskEntries[index]) state.cache.scaledMaskEntries[index] = { scaledMaskKey: "", scaledMaskCanvas: null, scaledMaskImageDataKey: "", scaledMaskImageData: null, scaledMaskAlphaKey: "", scaledMaskAlpha: null }; return state.cache.scaledMaskEntries[index]; }
  function clearMaskCache(index) { if (!state.cache.scaledMaskEntries) state.cache.scaledMaskEntries = {}; if (index === undefined) { state.cache.scaledMaskEntries = {}; return; } delete state.cache.scaledMaskEntries[index]; }
  function forEachMask(callback) { ensureMaskStateStructure(); state.document.masks.forEach(function(mask, index) { callback(mask, index, getRuntimeMaskCanvas(index)); }); }
  function anyMaskPixels() { ensureMaskStateStructure(); return state.document.masks.some(function(mask, index) { return !!(getRuntimeMaskCanvas(index) || (mask && mask.dataUrl)); }); }
  function maskSlotHasVisiblePixels(index) {
    ensureMaskStateStructure();
    const runtime = getRuntimeMaskCanvas(index);
    if (runtime && maskCanvasHasVisiblePixels(runtime)) return true;
    const mask = getMaskAt(index);
    return !!(mask && mask.dataUrl);
  }
  function hasVisibleMaskAdjustments(adjustments) {
    const defaults = getDefaultMaskAdjustments();
    const src = adjustments || {};
    return Object.keys(defaults).some(function(key) {
      return Math.abs(Number(src[key] || 0) - Number(defaults[key] || 0)) > 0.0001;
    });
  }
  function anyNonDefaultMaskAdjustments() { ensureMaskStateStructure(); return state.document.masks.some(function(mask) { return hasVisibleMaskAdjustments(mask.localAdjustments || {}); }); }

  function getMaskCanvasMaxDimension() {
    return 1200;
  }

  function getMaskResolutionScale() {
    if (!state.source.width || !state.source.height) return 1;
    const maxDim = Math.max(state.source.width, state.source.height);
    return Math.min(1, getMaskCanvasMaxDimension() / maxDim);
  }

  function getMaskCanvasDimensions() {
    const scale = getMaskResolutionScale();
    return {
      width: Math.max(1, Math.round(state.source.width * scale)),
      height: Math.max(1, Math.round(state.source.height * scale)),
      scale
    };
  }

  async function readAsDataURL(file) {
    return await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = function () { resolve(reader.result); };
      reader.onerror = function () { reject(new Error("FileReader failed")); };
      reader.readAsDataURL(file);
    });
  }

  async function loadImageFromDataURL(dataUrl) {
    return await new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = function () { resolve(image); };
      image.onerror = function () { reject(new Error("Image decode failed")); };
      image.src = dataUrl;
    });
  }

  function getDefaultCropRect() {
    return { x: 0, y: 0, width: state.source.width, height: state.source.height };
  }

  async function importFile(file) {
    const dataUrl = await readAsDataURL(file);
    const image = await loadImageFromDataURL(dataUrl);

    state.source.image = image;
    state.source.dataUrl = dataUrl;
    state.source.width = image.naturalWidth;
    state.source.height = image.naturalHeight;
    state.source.name = file.name || "";
    syncExportFilenameFromSource(true);
    state.source.type = file.type || "unknown";
    state.source.size = file.size || 0;

    state.document.geometry.rotationQuarterTurns = 0;
    state.document.geometry.straightenDegrees = 0;
    state.document.geometry.flipX = false;
    state.document.geometry.flipY = false;
    invalidateRenderCache();
    state.document.crop = getDefaultCropRect();
    invalidateRenderCache();
    for (const [key] of adjustmentControls) state.document.adjustments[key] = 0;
    state.ui.isAdjustDragging = false;
    state.ui.cropMode = false;
    state.ui.pendingCrop = null;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    state.ui.cropDrag = null;
    state.ui.maskMode = false;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    state.ui.maskStroke = null;
    state.ui.maskHoverPos = null;
    state.ui.cropAspect = "free";
    state.document.masks = [createDefaultMask("Mask 1"), createDefaultMask("Mask 2"), createDefaultMask("Mask 3")];
    state.document.activeMaskIndex = 0;
    state.runtime.maskCanvases = [null, null, null];
    state.runtime.maskRevisions = [0, 0, 0];
    state.history.undoStack = [];
    state.history.redoStack = [];
    fitView();
    syncControls();
    invalidateRenderCache();
    renderAll();
  }

  function buildProjectPayload() {
    return {
      app: "Photo Editor Pro",
      version: "0.16.54",
      savedAt: new Date().toISOString(),
      source: {
        name: state.source.name,
        type: state.source.type,
        size: state.source.size,
        width: state.source.width,
        height: state.source.height,
        embeddedImageDataUrl: state.source.dataUrl || ""
      },
      document: snapshotDocument()
    };
  }

  function downloadTextFile(filename, text, mimeType) {
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 0);
  }

  function getProjectDownloadName() {
    const baseName = (state.source.name || "photo-project").replace(/\.[^.]+$/, "") || "photo-project";
    return `${baseName}.pedit`;
  }

  function getScaledAdjustmentPreset(presetKey, amount) {
    const preset = ADJUST_PRESET_VALUES[presetKey] || {};
    const scaled = getDefaultAdjustments();
    const factor = clamp(Number(amount ?? 1), 0, 1.5);
    Object.keys(scaled).forEach(function(key) {
      const value = Number(preset[key] || 0);
      scaled[key] = key === "hue" ? Math.round(value * factor) : Number((value * factor).toFixed(4));
    });
    return scaled;
  }

  function applyAdjustPreset(presetKey, amount) {
    const key = ADJUST_PRESET_LABELS[presetKey] ? presetKey : "none";
    const scaled = getScaledAdjustmentPreset(key, amount);
    const next = Object.assign(getDefaultAdjustments(), scaled);
    Object.keys(next).forEach(function(adjKey) {
      state.document.adjustments[adjKey] = next[adjKey];
    });
    state.ui.adjustPresetKey = key;
    state.ui.adjustPresetAmount = clamp(Number(amount ?? 1), 0, 1.5);
  }

  function snapshotAdjustmentsOnly() {
    return JSON.parse(JSON.stringify(state.document.adjustments || getDefaultAdjustments()));
  }

  function restoreAdjustPresetBaseIfPresent() {
    if (!state.ui.adjustPresetBaseAdjustments) return false;
    const base = Object.assign(getDefaultAdjustments(), state.ui.adjustPresetBaseAdjustments || {});
    Object.keys(base).forEach(function (adjKey) {
      state.document.adjustments[adjKey] = base[adjKey];
    });
    return true;
  }

  function clearAdjustPresetPreviewState() {
    state.ui.adjustPresetBaseAdjustments = null;
    state.ui.adjustPresetFramePending = false;
  }

  function sanitizeProjectFilename(input) {
    const raw = String(input || "").trim();
    const noExt = raw.replace(/\.pedit$/i, "");
    const cleaned = noExt
      .replace(/[\/:*?"<>|]+/g, "-")
      .replace(/\s+/g, " ")
      .replace(/\.+$/g, "")
      .trim();
    return (cleaned || "photo-project") + ".pedit";
  }

  function askProjectDownloadName() {
    const suggested = getProjectDownloadName();
    const answer = window.prompt("Choose project filename", suggested);
    if (answer === null) return null;
    return sanitizeProjectFilename(answer || suggested);
  }

  function buildPresetPayload() {
    return {
      app: "Photo Editor Pro",
      type: "adjustment-preset",
      version: "0.16.54",
      savedAt: new Date().toISOString(),
      adjustments: JSON.parse(JSON.stringify(state.document.adjustments)),
      filterLayer: JSON.parse(JSON.stringify(state.document.filterLayer || getDefaultFilterLayer()))
    };
  }

  function getPresetDownloadName() {
    const baseName = (state.source.name || "photo-preset").replace(/\.[^.]+$/, "") || "photo-preset";
    return `${baseName}-preset.ppreset`;
  }

  function sanitizePresetFilename(input) {
    const raw = String(input || "").trim();
    const noExt = raw.replace(/\.ppreset$/i, "");
    const cleaned = noExt
      .replace(/[\/:*?"<>|]+/g, "-")
      .replace(/\s+/g, " ")
      .replace(/\.+$/g, "")
      .trim();
    return (cleaned || "photo-preset") + ".ppreset";
  }

  function askPresetDownloadName() {
    const suggested = getPresetDownloadName();
    const answer = window.prompt("Choose preset filename", suggested);
    if (answer === null) return null;
    return sanitizePresetFilename(answer || suggested);
  }

  function validatePresetPayload(payload) {
    if (!payload || typeof payload !== "object") throw new Error("Invalid preset file");
    if (!payload.adjustments || typeof payload.adjustments !== "object") throw new Error("Preset is missing adjustment data");
  }

  async function openPresetFile(file) {
    const text = await file.text();
    let payload;
    try {
      payload = JSON.parse(text);
    } catch {
      throw new Error("Preset file is not valid JSON");
    }
    validatePresetPayload(payload);
    pushUndoSnapshot();
    for (const [key] of adjustmentControls) {
      state.document.adjustments[key] = Number(payload.adjustments[key] || 0);
    }
    state.document.filterLayer = Object.assign(getDefaultFilterLayer(), payload.filterLayer || {});
    state.document.filterLayer.preset = FILTER_PRESET_LABELS[state.document.filterLayer.preset] ? state.document.filterLayer.preset : "none";
    state.document.filterLayer.intensity = clamp(Number(state.document.filterLayer.intensity ?? 0.65), 0, 1);
    state.ui.isAdjustDragging = false;
    state.ui.activeAdjustmentKey = "";
    state.ui.adjustPresetKey = "none";
    state.ui.adjustPresetAmount = 1;
    invalidateRenderCache();
    syncControls();
    renderAll();
  }

  function validateProjectPayload(payload) {
    if (!payload || typeof payload !== "object") throw new Error("Invalid project file");
    if (!payload.document || typeof payload.document !== "object") throw new Error("Project is missing document data");
    if (!payload.source || typeof payload.source !== "object") throw new Error("Project is missing source data");
    const doc = payload.document;
    if (!doc.geometry || !doc.crop || !doc.adjustments || !doc.view) throw new Error("Project data is incomplete");
    doc.filterLayer = Object.assign(getDefaultFilterLayer(), doc.filterLayer || {});
    doc.filterLayer.preset = FILTER_PRESET_LABELS[doc.filterLayer.preset] ? doc.filterLayer.preset : "none";
    doc.filterLayer.intensity = clamp(Number(doc.filterLayer.intensity ?? 0.65), 0, 1);
    if (!Array.isArray(doc.masks) || !doc.masks.length) {
      const legacyMask = doc.mask && typeof doc.mask === "object" ? doc.mask : null;
      doc.masks = [legacyMask ? Object.assign(createDefaultMask("Mask 1"), legacyMask) : createDefaultMask("Mask 1"), createDefaultMask("Mask 2"), createDefaultMask("Mask 3")];
    }
    while (doc.masks.length < 3) doc.masks.push(createDefaultMask(`Mask ${doc.masks.length + 1}`));
    doc.masks = doc.masks.slice(0, 3).map(function(mask, idx) {
      const out = Object.assign(createDefaultMask(`Mask ${idx + 1}`), mask || {});
      out.localAdjustments = Object.assign(getDefaultMaskAdjustments(), out.localAdjustments || {});
      return out;
    });
    doc.activeMaskIndex = clamp(Number(doc.activeMaskIndex || 0), 0, 2);
  }

  async function openProjectFile(file) {
    const text = await file.text();
    let payload;
    try {
      payload = JSON.parse(text);
    } catch {
      throw new Error("Project file is not valid JSON");
    }
    validateProjectPayload(payload);

    const embeddedDataUrl = payload.source.embeddedImageDataUrl || "";
    if (!embeddedDataUrl) {
      throw new Error("Project file does not contain embedded image data");
    }

    const image = await loadImageFromDataURL(embeddedDataUrl);
    state.source.image = image;
    state.source.dataUrl = embeddedDataUrl;
    state.source.width = image.naturalWidth;
    state.source.height = image.naturalHeight;
    state.source.name = payload.source.name || file.name || "project-image";
    syncExportFilenameFromSource(true);
    state.source.type = payload.source.type || "image/*";
    state.source.size = Number(payload.source.size || 0);

    state.document = JSON.parse(JSON.stringify(payload.document));
    state.document.crop = normalizeCropRect(state.document.crop || getDefaultCropRect());
    state.document.geometry.rotationQuarterTurns = Number(state.document.geometry.rotationQuarterTurns || 0);
    state.document.geometry.straightenDegrees = Number(state.document.geometry.straightenDegrees || 0);
    state.document.geometry.flipX = !!state.document.geometry.flipX;
    state.document.geometry.flipY = !!state.document.geometry.flipY;
    for (const [key] of adjustmentControls) {
      state.document.adjustments[key] = Number(state.document.adjustments[key] || 0);
    }
    state.document.filterLayer = Object.assign(getDefaultFilterLayer(), state.document.filterLayer || {});
    state.document.filterLayer.preset = FILTER_PRESET_LABELS[state.document.filterLayer.preset] ? state.document.filterLayer.preset : "none";
    state.document.filterLayer.intensity = clamp(Number(state.document.filterLayer.intensity ?? 0.65), 0, 1);
    ensureMaskStateStructure();
    for (let i = 0; i < 3; i++) {
      const mask = getMaskAt(i);
      if (!mask.localAdjustments || typeof mask.localAdjustments !== "object") {
        mask.localAdjustments = getDefaultMaskAdjustments();
      }
      for (const [key] of maskAdjustmentControls) {
        mask.localAdjustments[key] = Number(mask.localAdjustments[key] || 0);
      }
    }
    if (!state.document.view || !Number.isFinite(Number(state.document.view.baseScale))) {
      state.document.view = { baseScale: 1, zoomPercent: 100, panX: 0, panY: 0 };
    } else {
      state.document.view.baseScale = Math.max(0.0001, Number(state.document.view.baseScale));
      state.document.view.zoomPercent = clamp(Number(state.document.view.zoomPercent || 100), 25, 300);
      state.document.view.panX = Number(state.document.view.panX || 0);
      state.document.view.panY = Number(state.document.view.panY || 0);
    }
    clampPanToBounds();

    state.runtime.maskCanvases = [null, null, null];
    for (let i = 0; i < 3; i++) {
      setRuntimeMaskCanvas(i, await loadMaskCanvasFromDataUrl(getMaskAt(i).dataUrl || "", i));
      markMaskDirty(i);
    }
    state.ui.isAdjustDragging = false;
    state.ui.cropMode = false;
    state.ui.pendingCrop = null;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    state.ui.cropDrag = null;
    state.ui.maskMode = false;
    state.ui.maskStroke = null;
    state.ui.maskHoverPos = null;
    state.ui.cropAspect = "free";
    state.history.undoStack = [];
    state.history.redoStack = [];
    syncControls();
    invalidateRenderCache();
    renderAll();
  }

  function invalidateRenderCache() {
    state.cache.dragRenderKey = "";
    state.cache.dragRenderCanvas = null;
    state.cache.baseAdjustKey = "";
    state.cache.baseAdjustImageData = null;
    state.cache.baseAdjustWidth = 0;
    state.cache.baseAdjustHeight = 0;
    clearMaskCache();
    state.cache.finalRenderKey = "";
    state.cache.finalRenderCanvas = null;
  }

  function fitContainScale(contentW, contentH, boxW, boxH) {
    if (!contentW || !contentH || !boxW || !boxH) return 1;
    return Math.min(boxW / contentW, boxH / contentH);
  }

  function updateViewport() {
    const rect = stage.getBoundingClientRect();
    state.ui.viewportWidth = Math.max(320, Math.floor(rect.width));
    state.ui.viewportHeight = Math.max(320, Math.floor(rect.height));
    clampPanToBounds();
    syncControls();
    renderAll();
  }

  function getActiveCropRect() {
    const c = state.document.crop;
    return c && c.width > 0 && c.height > 0 ? c : getDefaultCropRect();
  }

  function fitView() {
    if (!state.source.image) return;
    const crop = getActiveCropRect();
    const rotated = getRotatedImageDimensions(getRotationNormalized(), crop.width, crop.height);
    const bounds = getRotatedBoundingSize(rotated.width, rotated.height, getStraightenRadians());
    state.document.view.baseScale = fitContainScale(bounds.width, bounds.height, state.ui.viewportWidth, state.ui.viewportHeight);
    state.document.view.zoomPercent = 100;
    state.document.view.panX = 0;
    state.document.view.panY = 0;
  }

  function getZoomScale() {
    return Math.max(0.25, Math.min(3, Number(state.document.view.zoomPercent || 100) / 100));
  }

  function getDisplayScale() {
    return Math.max(0.0001, state.document.view.baseScale * getZoomScale());
  }

  function getViewCenter() {
    return {
      x: Math.round(state.ui.viewportWidth / 2) + Number(state.document.view.panX || 0),
      y: Math.round(state.ui.viewportHeight / 2) + Number(state.document.view.panY || 0)
    };
  }

  function clampPanToBounds() {
    if (!state.source.image) return;
    const crop = getActiveCropRect();
    const rotationTurns = getRotationNormalized();
    const displayScale = getDisplayScale();
    const drawWidth = crop.width * displayScale;
    const drawHeight = crop.height * displayScale;
    const rotatedWidth = rotationTurns % 2 === 1 ? drawHeight : drawWidth;
    const rotatedHeight = rotationTurns % 2 === 1 ? drawWidth : drawHeight;
    const bounds = getRotatedBoundingSize(rotatedWidth, rotatedHeight, getStraightenRadians());
    const boundsWidth = bounds.width;
    const boundsHeight = bounds.height;
    const maxPanX = Math.max(0, (boundsWidth - state.ui.viewportWidth) / 2);
    const maxPanY = Math.max(0, (boundsHeight - state.ui.viewportHeight) / 2);
    state.document.view.panX = clamp(Number(state.document.view.panX || 0), -maxPanX, maxPanX);
    state.document.view.panY = clamp(Number(state.document.view.panY || 0), -maxPanY, maxPanY);
  }

  function setZoomPercent(percent, resetPan = false) {
    state.document.view.zoomPercent = clamp(Math.round(percent), 25, 300);
    if (resetPan) {
      state.document.view.panX = 0;
      state.document.view.panY = 0;
    }
    clampPanToBounds();
    syncControls();
  }

  function hasActiveFilterLayer() {
    const filterLayer = state.document.filterLayer || getDefaultFilterLayer();
    return filterLayer.preset !== "none" && Number(filterLayer.intensity || 0) > 0.001;
  }

  function hasNonDefaultAdjustments() {
    return Object.values(state.document.adjustments).some(v => v !== 0) || hasActiveFilterLayer();
  }

  function hasNonDefaultCrop() {
    const c = getActiveCropRect();
    return c.x !== 0 || c.y !== 0 || c.width !== state.source.width || c.height !== state.source.height;
  }

  function resetAdjustments() {
    for (const [key] of adjustmentControls) state.document.adjustments[key] = 0;
    syncControls();
    invalidateRenderCache();
  }

  function getRotationNormalized() {
    return ((state.document.geometry.rotationQuarterTurns % 4) + 4) % 4;
  }

  function getStraightenRadians() {
    return (Number(state.document.geometry.straightenDegrees || 0) * Math.PI) / 180;
  }

  function getRenderAngleRadians() {
    return state.document.geometry.rotationQuarterTurns * Math.PI / 2 + getStraightenRadians();
  }

  function getFlipScaleX() {
    return state.document.geometry.flipX ? -1 : 1;
  }

  function getFlipScaleY() {
    return state.document.geometry.flipY ? -1 : 1;
  }

  function getRotatedBoundingSize(width, height, angleRad) {
    const c = Math.abs(Math.cos(angleRad));
    const s = Math.abs(Math.sin(angleRad));
    return { width: width * c + height * s, height: width * s + height * c };
  }

  function getCropAspectRatioValue() {
    const value = state.ui.cropAspect || "free";
    if (value === "free") return null;
    const parts = value.split(":").map(Number);
    if (parts.length !== 2 || !parts[0] || !parts[1]) return null;
    return parts[0] / parts[1];
  }

  function applyCropAspectToRect(rect) {
    const aspect = getCropAspectRatioValue();
    if (!aspect) return normalizeCropRect(rect);
    const cx = rect.x + rect.width / 2;
    const cy = rect.y + rect.height / 2;
    let width = rect.width;
    let height = rect.height;
    if (width / height > aspect) width = height * aspect;
    else height = width / aspect;
    width = Math.min(width, state.source.width);
    height = Math.min(height, state.source.height);
    let x = clamp(cx - width / 2, 0, state.source.width - width);
    let y = clamp(cy - height / 2, 0, state.source.height - height);
    return normalizeCropRect({ x, y, width, height });
  }

  function setCropAspect(value) {
    state.ui.cropAspect = value || "free";
    if (state.ui.cropMode && state.ui.pendingCrop) state.ui.pendingCrop = applyCropAspectToRect(state.ui.pendingCrop);
    syncControls();
    renderAll();
  }
  function snapshotDocument() {
    ensureMaskStateStructure();
    for (let i = 0; i < 3; i++) {
      if (getRuntimeMaskCanvas(i) && !getMaskAt(i).dataUrl) syncMaskDataUrl(i);
    }
    return JSON.parse(JSON.stringify(state.document));
  }

  function pushUndoSnapshot() {
    state.history.undoStack.push(snapshotDocument());
    if (state.history.undoStack.length > 100) state.history.undoStack.shift();
    state.history.redoStack = [];
  }

  async function applyDocumentSnapshot(snapshot) {
    state.document = JSON.parse(JSON.stringify(snapshot));
    state.ui.adjustPresetKey = "none";
    state.ui.adjustPresetAmount = 1;
    ensureMaskStateStructure();
    state.runtime.maskCanvases = [null, null, null];
    for (let i = 0; i < 3; i++) {
      setRuntimeMaskCanvas(i, await loadMaskCanvasFromDataUrl(getMaskAt(i).dataUrl || "", i));
      markMaskDirty(i);
    }
    syncControls();
  }

  function syncControls() {
    ensureMaskStateStructure();
    if (beforeAfterBtn) beforeAfterBtn.textContent = state.ui.splitView ? "Split view on" : "Split view";
    if (maskModeBtn) maskModeBtn.textContent = state.ui.maskMode ? "Edit mask on" : "Edit mask";
    if (maskOverlayBtn) maskOverlayBtn.textContent = state.ui.maskOverlayVisible ? "Overlay on" : "Overlay off";
    if (maskViewSelect) maskViewSelect.value = state.ui.maskViewMode || "overlay";
    if (maskViewValue) {
      const labels = { overlay: "Overlay", bw: "Black/White mask", result: "Result only" };
      maskViewValue.textContent = labels[state.ui.maskViewMode || "overlay"] || "Overlay";
    }
    if (activeMaskSelect) {
      activeMaskSelect.innerHTML = state.document.masks.map((mask, index) => `<option value="${index}">${escapeHtml(mask.name || `Mask ${index + 1}`)}</option>`).join("");
      activeMaskSelect.value = String(getActiveMaskIndex());
    }
    for (const [key, rangeEl, valueEl] of adjustmentControls) {
      rangeEl.value = String(state.document.adjustments[key]);
      valueEl.textContent = key === "hue" ? String(Math.round(state.document.adjustments[key])) : state.document.adjustments[key].toFixed(2);
    }
    for (const [key, rangeEl, valueEl] of maskAdjustmentControls) {
      rangeEl.value = String(getActiveMask().localAdjustments[key]);
      if (key === "hue") valueEl.textContent = `${Math.round(getActiveMask().localAdjustments[key])}°`;
      else valueEl.textContent = Number(getActiveMask().localAdjustments[key]).toFixed(2);
    }
    maskBrushSizeRange.value = String(state.ui.maskBrushSize);
    maskBrushSizeValue.textContent = String(Math.round(state.ui.maskBrushSize));
    maskBrushFeatherRange.value = String(state.ui.maskBrushFeather);
    maskBrushFeatherValue.textContent = Number(state.ui.maskBrushFeather).toFixed(2);
    maskBrushModeValue.textContent = state.ui.maskBrushMode === "erase" ? "Erase" : "Paint";
    straightenRange.value = String(Number(state.document.geometry.straightenDegrees || 0).toFixed(1));
    straightenValue.textContent = `${Number(state.document.geometry.straightenDegrees || 0).toFixed(1)}°`;
    cropAspectSelect.value = state.ui.cropAspect || "free";
    cropAspectValue.textContent = state.ui.cropAspect === "free" ? "Free" : state.ui.cropAspect;
    zoomRange.value = String(Math.round(state.document.view.zoomPercent || 100));
    zoomValue.textContent = `${Math.round(state.document.view.zoomPercent || 100)}%`;
    if (adjustPresetSelect) adjustPresetSelect.value = ADJUST_PRESET_LABELS[state.ui.adjustPresetKey] ? state.ui.adjustPresetKey : "none";
    if (adjustPresetValue) adjustPresetValue.textContent = ADJUST_PRESET_LABELS[state.ui.adjustPresetKey || "none"] || "None";
    if (adjustPresetAmountRange) adjustPresetAmountRange.value = String(clamp(Number(state.ui.adjustPresetAmount ?? 1), 0, 1.5));
    if (adjustPresetAmountValue) adjustPresetAmountValue.textContent = clamp(Number(state.ui.adjustPresetAmount ?? 1), 0, 1.5).toFixed(2);
    if (applyAdjustPresetBtn) {
      applyAdjustPresetBtn.hidden = true;
      applyAdjustPresetBtn.style.display = "none";
      applyAdjustPresetBtn.disabled = true;
    }
    if (resetAdjustPresetBtn) resetAdjustPresetBtn.disabled = (state.ui.adjustPresetKey || "none") === "none" && !state.ui.adjustPresetBaseAdjustments;
    if (filterPresetSelect) filterPresetSelect.value = (state.document.filterLayer && FILTER_PRESET_LABELS[state.document.filterLayer.preset]) ? state.document.filterLayer.preset : "none";
    if (filterPresetValue) filterPresetValue.textContent = FILTER_PRESET_LABELS[(state.document.filterLayer && state.document.filterLayer.preset) || "none"] || "None";
    if (filterIntensityRange) filterIntensityRange.value = String(Number((state.document.filterLayer && state.document.filterLayer.intensity) ?? 0.65));
    if (filterIntensityValue) filterIntensityValue.textContent = Number((state.document.filterLayer && state.document.filterLayer.intensity) ?? 0.65).toFixed(2);
    if (exportScaleSelect) exportScaleValue.textContent = `${Math.round(Number(exportScaleSelect.value || 1) * 100)}%`;
    updateExportUiState();
  }

  function updateMaskAdjustmentControlValue(key, rangeEl, valueEl) {
    const value = Number(getActiveMask().localAdjustments[key] || 0);
    if (rangeEl) rangeEl.value = String(value);
    if (valueEl) {
      if (key === "hue") valueEl.textContent = `${Math.round(value)}°`;
      else valueEl.textContent = value.toFixed(2);
    }
  }

  async function undo() {
    if (!state.history.undoStack.length) return;
    state.history.redoStack.push(snapshotDocument());
    await applyDocumentSnapshot(state.history.undoStack.pop());
    state.ui.cropMode = false;
    state.ui.pendingCrop = null;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    state.ui.cropDrag = null;
    state.ui.maskMode = false;
    state.ui.maskStroke = null;
    state.ui.maskHoverPos = null;
    invalidateRenderCache();
    renderAll();
  }

  async function redo() {
    if (!state.history.redoStack.length) return;
    state.history.undoStack.push(snapshotDocument());
    await applyDocumentSnapshot(state.history.redoStack.pop());
    state.ui.cropMode = false;
    state.ui.pendingCrop = null;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    state.ui.cropDrag = null;
    state.ui.maskMode = false;
    state.ui.maskStroke = null;
    state.ui.maskHoverPos = null;
    invalidateRenderCache();
    renderAll();
  }

  function createEmptyMaskCanvas(index = getActiveMaskIndex()) {
    if (!state.source.width || !state.source.height) return null;
    const dims = getMaskCanvasDimensions();
    const out = document.createElement("canvas");
    out.width = dims.width;
    out.height = dims.height;
    getMaskAt(index).resolutionScale = dims.scale;
    return out;
  }

  async function loadMaskCanvasFromDataUrl(dataUrl, index = getActiveMaskIndex()) {
    if (!dataUrl) return null;
    const image = await loadImageFromDataURL(dataUrl);
    const out = createEmptyMaskCanvas(index);
    if (!out) return null;
    out.getContext("2d").drawImage(image, 0, 0, out.width, out.height);
    return out;
  }

  async function hydrateMaskCanvas(index = getActiveMaskIndex()) {
    if (getRuntimeMaskCanvas(index)) return getRuntimeMaskCanvas(index);
    const mask = getMaskAt(index);
    if (mask && mask.dataUrl) {
      const hydrated = await loadMaskCanvasFromDataUrl(mask.dataUrl, index);
      if (hydrated) {
        setRuntimeMaskCanvas(index, hydrated);
        markMaskDirty(index);
        return hydrated;
      }
    }
    return null;
  }

  function ensureMaskCanvas(index = getActiveMaskIndex()) {
    const runtime = getRuntimeMaskCanvas(index);
    if (runtime) return runtime;
    const mask = getMaskAt(index);
    if (mask && mask.dataUrl) return runtime;
    const empty = createEmptyMaskCanvas(index);
    setRuntimeMaskCanvas(index, empty);
    return empty;
  }

  function sourcePointToMaskPoint(sourcePos, index = getActiveMaskIndex()) {
    const maskCanvas = ensureMaskCanvas(index);
    if (!maskCanvas || !sourcePos) return null;
    return {
      x: sourcePos.x * (maskCanvas.width / state.source.width),
      y: sourcePos.y * (maskCanvas.height / state.source.height)
    };
  }

  function markMaskDirty(index = getActiveMaskIndex()) {
    ensureMaskStateStructure();
    state.runtime.maskRevisions[index] = (state.runtime.maskRevisions[index] || 0) + 1;
    clearMaskCache(index);
    state.cache.finalRenderKey = "";
    state.cache.finalRenderCanvas = null;
  }

  function maskCanvasHasVisiblePixels(canvas, alphaThreshold = 6) {
    if (!canvas) return false;
    const mctx = canvas.getContext("2d", { willReadFrequently: true });
    const imageData = mctx.getImageData(0, 0, canvas.width, canvas.height).data;
    for (let i = 3; i < imageData.length; i += 4) {
      if (imageData[i] > alphaThreshold) return true;
    }
    return false;
  }

  function pruneMaskCanvas(index = getActiveMaskIndex(), alphaThreshold = 6) {
    const canvas = getRuntimeMaskCanvas(index);
    if (!canvas) return false;
    const mctx = canvas.getContext("2d", { willReadFrequently: true });
    const image = mctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = image.data;
    let changed = false;
    let hasVisiblePixels = false;
    for (let i = 3; i < data.length; i += 4) {
      const a = data[i];
      if (a <= alphaThreshold) {
        if (a !== 0) {
          data[i - 3] = 0;
          data[i - 2] = 0;
          data[i - 1] = 0;
          data[i] = 0;
          changed = true;
        }
      } else {
        hasVisiblePixels = true;
      }
    }
    if (changed) mctx.putImageData(image, 0, 0);
    if (!hasVisiblePixels) {
      mctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    return changed || !hasVisiblePixels;
  }

  function syncMaskDataUrl(index = getActiveMaskIndex()) {
    const canvas = getRuntimeMaskCanvas(index);
    if (!canvas || !maskCanvasHasVisiblePixels(canvas)) {
      setRuntimeMaskCanvas(index, canvas || null);
      getMaskAt(index).dataUrl = "";
      markMaskDirty(index);
      return;
    }
    getMaskAt(index).dataUrl = canvas.toDataURL("image/png");
    markMaskDirty(index);
  }

  function resetMaskAdjustments() {
    const defaults = getDefaultMaskAdjustments();
    Object.keys(defaults).forEach(function(key) { getActiveMask().localAdjustments[key] = defaults[key]; });
    invalidateRenderCache();
    syncControls();
    renderAll();
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function normalizeCropRect(rect) {
    const minSize = 20;
    let x = clamp(rect.x, 0, state.source.width - minSize);
    let y = clamp(rect.y, 0, state.source.height - minSize);
    let width = clamp(rect.width, minSize, state.source.width - x);
    let height = clamp(rect.height, minSize, state.source.height - y);
    return { x, y, width, height };
  }

  function enterCropMode() {
    if (!state.source.image) return;
    state.ui.cropMode = true;
    state.ui.pendingCrop = applyCropAspectToRect(JSON.parse(JSON.stringify(getActiveCropRect())));
    state.ui.cropDrag = null;
    renderAll();
  }

  function cancelCropMode() {
    state.ui.cropMode = false;
    state.ui.pendingCrop = null;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    state.ui.cropDrag = null;
    renderAll();
  }

  function applyCrop() {
    if (!state.ui.cropMode || !state.ui.pendingCrop) return;
    pushUndoSnapshot();
    state.document.crop = normalizeCropRect(state.ui.pendingCrop);
    invalidateRenderCache();
    state.ui.cropMode = false;
    state.ui.pendingCrop = null;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    state.ui.cropDrag = null;
    fitView();
    renderAll();
  }

  function resetCrop() {
    if (!state.source.image) return;
    if (state.ui.cropMode) {
      state.ui.pendingCrop = applyCropAspectToRect(getDefaultCropRect());
      state.ui.cropDrag = null;
      renderAll();
      return;
    }
    if (!hasNonDefaultCrop()) return;
    pushUndoSnapshot();
    state.document.crop = getDefaultCropRect();
    invalidateRenderCache();
    fitView();
    renderAll();
  }

  function getRotatedImageDimensions(rotationTurns, width, height) {
    return rotationTurns % 2 === 1 ? { width: height, height: width } : { width, height };
  }

  function sourceRectToRotatedRect(rect, rotationTurns) {
    const W = state.source.width;
    const H = state.source.height;
    const r = ((rotationTurns % 4) + 4) % 4;
    if (r === 0) return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    if (r === 1) return { x: H - (rect.y + rect.height), y: rect.x, width: rect.height, height: rect.width };
    if (r === 2) return { x: W - (rect.x + rect.width), y: H - (rect.y + rect.height), width: rect.width, height: rect.height };
    return { x: rect.y, y: W - (rect.x + rect.width), width: rect.height, height: rect.width };
  }

  function rotatedRectToSourceRect(rect, rotationTurns) {
    const W = state.source.width;
    const H = state.source.height;
    const r = ((rotationTurns % 4) + 4) % 4;
    if (r === 0) return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    if (r === 1) return { x: rect.y, y: H - (rect.x + rect.width), width: rect.height, height: rect.width };
    if (r === 2) return { x: W - (rect.x + rect.width), y: H - (rect.y + rect.height), width: rect.width, height: rect.height };
    return { x: W - (rect.y + rect.height), y: rect.x, width: rect.height, height: rect.width };
  }

  function getCropModeDisplayRect() {
    const rotationTurns = getRotationNormalized();
    const rotated = getRotatedImageDimensions(rotationTurns, state.source.width, state.source.height);
    const scale = fitContainScale(rotated.width, rotated.height, state.ui.viewportWidth, state.ui.viewportHeight);
    const width = rotated.width * scale;
    const height = rotated.height * scale;
    return { x: (state.ui.viewportWidth - width) / 2, y: (state.ui.viewportHeight - height) / 2, width, height, scale, imageWidth: rotated.width, imageHeight: rotated.height };
  }

  function getPointerCanvasPos(event) {
    const rect = canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  function canvasPosToSourcePos(pos) {
    if (!state.source.image) return null;
    const crop = getActiveCropRect();
    const scale = getDisplayScale();
    const drawWidth = crop.width * scale;
    const drawHeight = crop.height * scale;
    const center = getViewCenter();
    const dx = pos.x - center.x;
    const dy = pos.y - center.y;
    const angle = -getRenderAngleRadians();
    const rx = dx * Math.cos(angle) - dy * Math.sin(angle);
    const ry = dx * Math.sin(angle) + dy * Math.cos(angle);
    let imgX = rx + drawWidth / 2;
    let imgY = ry + drawHeight / 2;
    if (state.document.geometry.flipX) imgX = drawWidth - imgX;
    if (state.document.geometry.flipY) imgY = drawHeight - imgY;
    if (imgX < 0 || imgY < 0 || imgX > drawWidth || imgY > drawHeight) return null;
    return { x: crop.x + imgX / scale, y: crop.y + imgY / scale };
  }

  function sourceBrushRadius() {
    return Math.max(1, (state.ui.maskBrushSize / 2) / Math.max(0.01, getDisplayScale()));
  }

  function getMaskScaleX() {
    const maskCanvas = ensureMaskCanvas();
    return maskCanvas ? (maskCanvas.width / Math.max(1, state.source.width)) : 1;
  }

  function getMaskScaleY() {
    const maskCanvas = ensureMaskCanvas();
    return maskCanvas ? (maskCanvas.height / Math.max(1, state.source.height)) : 1;
  }

  function maskBrushRadius() {
    const maskCanvas = ensureMaskCanvas();
    return Math.max(1, sourceBrushRadius() * (maskCanvas.width / Math.max(1, state.source.width)));
  }

  function paintMaskDab(sourcePos) {
    const maskCanvas = ensureMaskCanvas();
    const mctx = maskCanvas.getContext("2d");
    const maskPos = sourcePointToMaskPoint(sourcePos);
    if (!maskPos) return;
    const radius = maskBrushRadius();
    const feather = clamp(state.ui.maskBrushFeather, 0, 1);
    const inner = radius * (1 - feather * 0.95);
    const grad = mctx.createRadialGradient(maskPos.x, maskPos.y, inner, maskPos.x, maskPos.y, radius);
    if (state.ui.maskBrushMode === "erase") {
      mctx.save();
      mctx.globalCompositeOperation = "destination-out";
      grad.addColorStop(0, "rgba(0,0,0,1)");
      grad.addColorStop(1, "rgba(0,0,0,0)");
      mctx.fillStyle = grad;
      mctx.beginPath();
      mctx.arc(maskPos.x, maskPos.y, radius, 0, Math.PI * 2);
      mctx.fill();
      mctx.restore();
    } else {
      grad.addColorStop(0, "rgba(255,255,255,1)");
      grad.addColorStop(1, "rgba(255,255,255,0)");
      mctx.fillStyle = grad;
      mctx.beginPath();
      mctx.arc(maskPos.x, maskPos.y, radius, 0, Math.PI * 2);
      mctx.fill();
    }
    markMaskDirty();
  }

  function paintMaskStroke(fromPos, toPos) {
    const dx = toPos.x - fromPos.x;
    const dy = toPos.y - fromPos.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const step = Math.max(1, sourceBrushRadius() * 0.35);
    const count = Math.max(1, Math.ceil(dist / step));
    for (let i = 0; i <= count; i++) {
      const t = i / count;
      paintMaskDab({ x: fromPos.x + dx * t, y: fromPos.y + dy * t });
    }
  }

  function getPendingCropScreenRect() {
    const display = getCropModeDisplayRect();
    const crop = state.ui.pendingCrop || getDefaultCropRect();
    const rotatedCrop = sourceRectToRotatedRect(crop, getRotationNormalized());
    return {
      x: display.x + rotatedCrop.x * display.scale,
      y: display.y + rotatedCrop.y * display.scale,
      width: rotatedCrop.width * display.scale,
      height: rotatedCrop.height * display.scale
    };
  }

  function hitTestCrop(pos) {
    const rect = getPendingCropScreenRect();
    const handle = 12;
    const near = (px, py, x, y) => Math.abs(px - x) <= handle && Math.abs(py - y) <= handle;

    if (near(pos.x, pos.y, rect.x, rect.y)) return "nw";
    if (near(pos.x, pos.y, rect.x + rect.width, rect.y)) return "ne";
    if (near(pos.x, pos.y, rect.x, rect.y + rect.height)) return "sw";
    if (near(pos.x, pos.y, rect.x + rect.width, rect.y + rect.height)) return "se";
    if (pos.x >= rect.x && pos.x <= rect.x + rect.width && pos.y >= rect.y && pos.y <= rect.y + rect.height) return "move";
    return null;
  }

  function updatePendingCropFromDrag(pos) {
    if (!state.ui.cropDrag || !state.ui.pendingCrop) return;
    const display = getCropModeDisplayRect();
    const dx = (pos.x - state.ui.cropDrag.startX) / display.scale;
    const dy = (pos.y - state.ui.cropDrag.startY) / display.scale;
    const start = state.ui.cropDrag.startRect;
    const minSize = 20;
    let next = { ...start };

    if (state.ui.cropDrag.mode === "move") {
      next.x = clamp(start.x + dx, 0, display.imageWidth - start.width);
      next.y = clamp(start.y + dy, 0, display.imageHeight - start.height);
    } else if (state.ui.cropDrag.mode === "nw") {
      const right = start.x + start.width;
      const bottom = start.y + start.height;
      next.x = clamp(start.x + dx, 0, right - minSize);
      next.y = clamp(start.y + dy, 0, bottom - minSize);
      next.width = right - next.x;
      next.height = bottom - next.y;
    } else if (state.ui.cropDrag.mode === "ne") {
      const left = start.x;
      const bottom = start.y + start.height;
      const newRight = clamp(left + start.width + dx, left + minSize, display.imageWidth);
      next.y = clamp(start.y + dy, 0, bottom - minSize);
      next.x = left;
      next.width = newRight - left;
      next.height = bottom - next.y;
    } else if (state.ui.cropDrag.mode === "sw") {
      const right = start.x + start.width;
      const top = start.y;
      const newBottom = clamp(top + start.height + dy, top + minSize, display.imageHeight);
      next.x = clamp(start.x + dx, 0, right - minSize);
      next.y = top;
      next.width = right - next.x;
      next.height = newBottom - top;
    } else if (state.ui.cropDrag.mode === "se") {
      const left = start.x;
      const top = start.y;
      const newRight = clamp(left + start.width + dx, left + minSize, display.imageWidth);
      const newBottom = clamp(top + start.height + dy, top + minSize, display.imageHeight);
      next.x = left;
      next.y = top;
      next.width = newRight - left;
      next.height = newBottom - top;
    }

    let nextSource = normalizeCropRect(rotatedRectToSourceRect(next, getRotationNormalized()));
    nextSource = applyCropAspectToRect(nextSource);
    state.ui.pendingCrop = nextSource;
  }

  function boxBlurRGBA(data, width, height, radius) {
    if (radius <= 0) return;
    const src = new Uint8ClampedArray(data);
    const channels = 4;
    const size = radius * 2 + 1;

    // Horizontal
    for (let y = 0; y < height; y++) {
      let r = 0, g = 0, b = 0, a = 0;
      for (let i = -radius; i <= radius; i++) {
        const x = Math.max(0, Math.min(width - 1, i));
        const idx = (y * width + x) * channels;
        r += src[idx]; g += src[idx + 1]; b += src[idx + 2]; a += src[idx + 3];
      }
      for (let x = 0; x < width; x++) {
        const outIdx = (y * width + x) * channels;
        data[outIdx] = r / size;
        data[outIdx + 1] = g / size;
        data[outIdx + 2] = b / size;
        data[outIdx + 3] = a / size;

        const removeX = Math.max(0, Math.min(width - 1, x - radius));
        const addX = Math.max(0, Math.min(width - 1, x + radius + 1));
        const removeIdx = (y * width + removeX) * channels;
        const addIdx = (y * width + addX) * channels;
        r += src[addIdx] - src[removeIdx];
        g += src[addIdx + 1] - src[removeIdx + 1];
        b += src[addIdx + 2] - src[removeIdx + 2];
        a += src[addIdx + 3] - src[removeIdx + 3];
      }
    }

    const tmp = new Uint8ClampedArray(data);

    // Vertical
    for (let x = 0; x < width; x++) {
      let r = 0, g = 0, b = 0, a = 0;
      for (let i = -radius; i <= radius; i++) {
        const y = Math.max(0, Math.min(height - 1, i));
        const idx = (y * width + x) * channels;
        r += tmp[idx]; g += tmp[idx + 1]; b += tmp[idx + 2]; a += tmp[idx + 3];
      }
      for (let y = 0; y < height; y++) {
        const outIdx = (y * width + x) * channels;
        data[outIdx] = r / size;
        data[outIdx + 1] = g / size;
        data[outIdx + 2] = b / size;
        data[outIdx + 3] = a / size;

        const removeY = Math.max(0, Math.min(height - 1, y - radius));
        const addY = Math.max(0, Math.min(height - 1, y + radius + 1));
        const removeIdx = (removeY * width + x) * channels;
        const addIdx = (addY * width + x) * channels;
        r += tmp[addIdx] - tmp[removeIdx];
        g += tmp[addIdx + 1] - tmp[removeIdx + 1];
        b += tmp[addIdx + 2] - tmp[removeIdx + 2];
        a += tmp[addIdx + 3] - tmp[removeIdx + 3];
      }
    }
  }

  function createWorkingCanvas(width, height) {
    const out = document.createElement("canvas");
    out.width = width;
    out.height = height;
    return out;
  }

  function buildBaseAdjustKey(crop, workingWidth, workingHeight) {
    const a = state.document.adjustments;
    return [
      crop.x, crop.y, crop.width, crop.height, workingWidth, workingHeight,
      a.exposure, a.contrast, a.saturation, a.vibrance, a.highlights, a.whites, a.shadows, a.blacks, a.temperature, a.tint, a.hue, a.sepia
    ].join("|");
  }

  function cloneImageData(imageData) {
    return new ImageData(new Uint8ClampedArray(imageData.data), imageData.width, imageData.height);
  }

  function countEnabledAdjustments(adjustments, epsilon = 0.01) {
    if (!adjustments) return 0;
    let count = 0;
    Object.keys(adjustments).forEach(function (key) {
      if (Math.abs(Number(adjustments[key] || 0)) > epsilon) count += 1;
    });
    return count;
  }

  function estimateLivePreviewComplexity(hasLocalMaskAdjustments) {
    const a = state.document.adjustments;
    let score = 0;
    score += countEnabledAdjustments(a);
    if (a.blur > 0.01) score += 3;
    if (a.sharpen > 0.01) score += 2;
    if (a.vignette > 0.01) score += 1;
    if (hasLocalMaskAdjustments) {
      forEachMask(function(mask) {
        if (!mask || !mask.localAdjustments) return;
        if (Object.values(mask.localAdjustments).some(v => Math.abs(Number(v || 0)) > 0.01)) {
          score += 2 + countEnabledAdjustments(mask.localAdjustments);
          if (mask.localAdjustments.blur > 0.01) score += 2;
          if (mask.localAdjustments.sharpen > 0.01) score += 2;
        }
      });
    }
    if (state.ui.maskMode) score += 1;
    if (state.ui.splitView) score += 1;
    return score;
  }

  function applyTemperatureTint(r, g, b, temperature, tint) {
    return { r: r + temperature * 35 + tint * 12, g: g - tint * 24, b: b - temperature * 35 + tint * 12 };
  }

  function applyContrastValue(v, contrast) {
    return (v - 128) * (1 + contrast) + 128;
  }

  function applyHueShift(r, g, b, degrees) {
    if (!degrees) return { r, g, b };
    const rad = degrees * Math.PI / 180;
    const cosA = Math.cos(rad);
    const sinA = Math.sin(rad);
    return {
      r: (0.213 + cosA * 0.787 - sinA * 0.213) * r + (0.715 - cosA * 0.715 - sinA * 0.715) * g + (0.072 - cosA * 0.072 + sinA * 0.928) * b,
      g: (0.213 - cosA * 0.213 + sinA * 0.143) * r + (0.715 + cosA * 0.285 + sinA * 0.140) * g + (0.072 - cosA * 0.072 - sinA * 0.283) * b,
      b: (0.213 - cosA * 0.213 - sinA * 0.787) * r + (0.715 - cosA * 0.715 + sinA * 0.715) * g + (0.072 + cosA * 0.928 + sinA * 0.072) * b
    };
  }

  function applySepiaTone(r, g, b, amount) {
    if (!amount) return { r, g, b };
    const sr = r * 0.393 + g * 0.769 + b * 0.189;
    const sg = r * 0.349 + g * 0.686 + b * 0.168;
    const sb = r * 0.272 + g * 0.534 + b * 0.131;
    return { r: r * (1 - amount) + sr * amount, g: g * (1 - amount) + sg * amount, b: b * (1 - amount) + sb * amount };
  }

  function applySaturationValue(r, g, b, saturation) {
    if (!saturation) return { r, g, b };
    const gray = 0.299 * r + 0.587 * g + 0.114 * b;
    const factor = 1 + saturation;
    return { r: gray + (r - gray) * factor, g: gray + (g - gray) * factor, b: gray + (b - gray) * factor };
  }

  function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s; const l = (max + min) / 2;
    if (max === min) { h = s = 0; }
    else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        default: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    return [h, s, l];
  }

  function hue2rgb(p, q, t) {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  }

  function hslToRgb(h, s, l) {
    let r, g, b;
    if (s === 0) { r = g = b = l; }
    else {
      const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      const p = 2 * l - q;
      r = hue2rgb(p, q, h + 1 / 3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1 / 3);
    }
    return [r * 255, g * 255, b * 255];
  }

  function applySepiaMix(r, g, b, amount) {
    if (amount <= 0) return [r, g, b];
    const sr = r * 0.393 + g * 0.769 + b * 0.189;
    const sg = r * 0.349 + g * 0.686 + b * 0.168;
    const sb = r * 0.272 + g * 0.534 + b * 0.131;
    return [
      r * (1 - amount) + sr * amount,
      g * (1 - amount) + sg * amount,
      b * (1 - amount) + sb * amount
    ];
  }

  function applyToneAdjustments(r, g, b, adjustments) {
    let lum = 0.299 * r + 0.587 * g + 0.114 * b;
    if (adjustments.shadows) {
      const t = lum < 128 ? 1 - lum / 128 : 0;
      const delta = adjustments.shadows * 90 * t;
      r += delta; g += delta; b += delta;
    }
    if (adjustments.highlights) {
      const t = lum > 127 ? (lum - 127) / 128 : 0;
      const delta = adjustments.highlights * 90 * t;
      r += delta; g += delta; b += delta;
    }
    if (adjustments.blacks) {
      const t = lum < 85 ? 1 - lum / 85 : 0;
      const delta = adjustments.blacks * 110 * t;
      r += delta; g += delta; b += delta;
    }
    if (adjustments.whites) {
      const t = lum > 170 ? (lum - 170) / 85 : 0;
      const delta = adjustments.whites * 110 * t;
      r += delta; g += delta; b += delta;
    }
    return [r, g, b];
  }

  function applyPixelAdjustments(r, g, b, adjustments) {
    const exposureFactor = Math.pow(2, adjustments.exposure || 0);
    let contrastFactor = 1 + (adjustments.contrast || 0);
    let saturationFactor = 1 + (adjustments.saturation || 0);
    r *= exposureFactor; g *= exposureFactor; b *= exposureFactor;
    [r, g, b] = applyToneAdjustments(r, g, b, adjustments);
    r += (adjustments.temperature || 0) * 35;
    b -= (adjustments.temperature || 0) * 35;
    r += (adjustments.tint || 0) * 12;
    g -= (adjustments.tint || 0) * 24;
    b += (adjustments.tint || 0) * 12;
    r = (r - 128) * contrastFactor + 128;
    g = (g - 128) * contrastFactor + 128;
    b = (b - 128) * contrastFactor + 128;
    const gray = 0.299 * r + 0.587 * g + 0.114 * b;
    r = gray + (r - gray) * saturationFactor;
    g = gray + (g - gray) * saturationFactor;
    b = gray + (b - gray) * saturationFactor;
    if (adjustments.vibrance) {
      const maxC = Math.max(r, g, b);
      const avgC = (r + g + b) / 3;
      const amt = (Math.abs(maxC - avgC) * 2 / 255) * adjustments.vibrance;
      r += (maxC - r) * -amt;
      g += (maxC - g) * -amt;
      b += (maxC - b) * -amt;
    }
    if (adjustments.hue) {
      let [h, s, l] = rgbToHsl(r, g, b);
      h = (h + (adjustments.hue || 0) / 360) % 1;
      if (h < 0) h += 1;
      [r, g, b] = hslToRgb(h, s, l);
    }
    if (adjustments.sepia) {
      [r, g, b] = applySepiaMix(r, g, b, adjustments.sepia);
    }
    return [
      Math.max(0, Math.min(255, Math.round(r))),
      Math.max(0, Math.min(255, Math.round(g))),
      Math.max(0, Math.min(255, Math.round(b)))
    ];
  }

  function hueDistanceDegrees(a, b) {
    const diff = Math.abs((a - b) % 360);
    return diff > 180 ? 360 - diff : diff;
  }

  function wrapHueDegrees(value) {
    let out = value % 360;
    if (out < 0) out += 360;
    return out;
  }

  function blendHueDegrees(fromDeg, toDeg, t) {
    const a = wrapHueDegrees(fromDeg);
    const b = wrapHueDegrees(toDeg);
    let delta = b - a;
    if (delta > 180) delta -= 360;
    if (delta < -180) delta += 360;
    return wrapHueDegrees(a + delta * t);
  }

  function hueDegreesToCss(value, saturation = 100, lightness = 50) {
    return `hsl(${Math.round(wrapHueDegrees(Number(value) || 0))} ${saturation}% ${lightness}%)`;
  }

  function sampleSourcePixelAt(sourcePos) {
    if (!state.source.image || !sourcePos) return null;
    const crop = getActiveCropRect();
    const x = Math.max(crop.x, Math.min(crop.x + crop.width - 1, sourcePos.x));
    const y = Math.max(crop.y, Math.min(crop.y + crop.height - 1, sourcePos.y));
    const sampleCanvas = document.createElement("canvas");
    sampleCanvas.width = 1;
    sampleCanvas.height = 1;
    const sctx = sampleCanvas.getContext("2d", { willReadFrequently: true });
    sctx.drawImage(state.source.image, -Math.floor(x), -Math.floor(y));
    const px = sctx.getImageData(0, 0, 1, 1).data;
    return { r: px[0], g: px[1], b: px[2] };
  }

  function rgbToHex(color) {
    const c = normalizeStoredRgb(color, { r: 0, g: 0, b: 0 });
    return `#${c.r.toString(16).padStart(2, "0")}${c.g.toString(16).padStart(2, "0")}${c.b.toString(16).padStart(2, "0")}`;
  }

  function hexToRgb(value, fallback = null) {
    const raw = String(value || "").trim();
    const match = raw.match(/^#?([0-9a-f]{6})$/i);
    if (!match) return fallback ? normalizeStoredRgb(fallback, fallback) : null;
    const hex = match[1];
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16)
    };
  }

  function srgbToLinear(channel) {
    const c = channel / 255;
    return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  }

  function linearToSrgb(channel) {
    const c = channel <= 0.0031308 ? channel * 12.92 : 1.055 * Math.pow(channel, 1 / 2.4) - 0.055;
    return Math.max(0, Math.min(255, Math.round(c * 255)));
  }

  function rgbToLab(r, g, b) {
    const rl = srgbToLinear(r), gl = srgbToLinear(g), bl = srgbToLinear(b);
    const x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047;
    const y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000;
    const z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883;
    const fx = x > 0.008856 ? Math.cbrt(x) : (7.787 * x + 16 / 116);
    const fy = y > 0.008856 ? Math.cbrt(y) : (7.787 * y + 16 / 116);
    const fz = z > 0.008856 ? Math.cbrt(z) : (7.787 * z + 16 / 116);
    return { L: 116 * fy - 16, a: 500 * (fx - fy), b: 200 * (fy - fz) };
  }

  function labToRgb(L, a, b) {
    const fy = (L + 16) / 116;
    const fx = a / 500 + fy;
    const fz = fy - b / 200;
    const fx3 = fx * fx * fx, fy3 = fy * fy * fy, fz3 = fz * fz * fz;
    const xr = fx3 > 0.008856 ? fx3 : (fx - 16 / 116) / 7.787;
    const yr = fy3 > 0.008856 ? fy3 : (fy - 16 / 116) / 7.787;
    const zr = fz3 > 0.008856 ? fz3 : (fz - 16 / 116) / 7.787;
    const x = xr * 0.95047;
    const y = yr * 1.00000;
    const z = zr * 1.08883;
    const rl = x * 3.2404542 + y * -1.5371385 + z * -0.4985314;
    const gl = x * -0.9692660 + y * 1.8760108 + z * 0.0415560;
    const bl = x * 0.0556434 + y * -0.2040259 + z * 1.0572252;
    return [linearToSrgb(Math.max(0, rl)), linearToSrgb(Math.max(0, gl)), linearToSrgb(Math.max(0, bl))];
  }

  function deltaE76(labA, labB) {
    const dL = labA.L - labB.L;
    const da = labA.a - labB.a;
    const db = labA.b - labB.b;
    return Math.sqrt(dL * dL + da * da + db * db);
  }

  function getFilterLayerConfig() {
    const filterLayer = Object.assign(getDefaultFilterLayer(), state.document.filterLayer || {});
    filterLayer.preset = FILTER_PRESET_LABELS[filterLayer.preset] ? filterLayer.preset : "none";
    filterLayer.intensity = clamp(Number(filterLayer.intensity ?? 0.65), 0, 1);
    return filterLayer;
  }

  function applyFilterLayer(ctx2d, width, height, filterLayerInput) {
    const filterLayer = Object.assign(getDefaultFilterLayer(), filterLayerInput || {});
    const intensity = clamp(Number(filterLayer.intensity ?? 0.65), 0, 1);
    if (!width || !height || filterLayer.preset === "none" || intensity <= 0.0001) return;

    const t = intensity;
    const soft = smoothstep01(t);
    const strong = Math.pow(t, 0.72);
    const bold = Math.min(1, Math.pow(t, 0.58));

    ctx2d.save();

    const fill = (mode, alpha, style) => {
      if (alpha <= 0.0001) return;
      ctx2d.globalCompositeOperation = mode;
      ctx2d.globalAlpha = Math.max(0, Math.min(1, alpha));
      ctx2d.fillStyle = style;
      ctx2d.fillRect(0, 0, width, height);
    };
    const vignetteGradient = () => {
      const g = ctx2d.createRadialGradient(width * 0.5, height * 0.45, Math.min(width, height) * 0.10, width * 0.5, height * 0.5, Math.max(width, height) * 0.80);
      g.addColorStop(0, "rgba(255,255,255,0)");
      g.addColorStop(0.72, "rgba(0,0,0,0.18)");
      g.addColorStop(1, "rgba(0,0,0,1)");
      return g;
    };
    const verticalGradient = (top, bottom) => {
      const g = ctx2d.createLinearGradient(0, 0, 0, height);
      g.addColorStop(0, top);
      g.addColorStop(1, bottom);
      return g;
    };
    const horizontalGradient = (left, right) => {
      const g = ctx2d.createLinearGradient(0, 0, width, 0);
      g.addColorStop(0, left);
      g.addColorStop(1, right);
      return g;
    };
    const radial = (inner, outer, x = 0.5, y = 0.45, innerR = 0.06, outerR = 0.92) => {
      const maxR = Math.max(width, height) * outerR;
      const minR = Math.max(1, Math.min(width, height) * innerR);
      const g = ctx2d.createRadialGradient(width * x, height * y, minR, width * x, height * y, maxR);
      g.addColorStop(0, inner);
      g.addColorStop(1, outer);
      return g;
    };

    switch (filterLayer.preset) {
      case "cleanStudio":
        fill("screen", 0.20 * strong, "#f5f7ff");
        fill("soft-light", 0.34 * bold, verticalGradient("rgba(255,244,228,1)", "rgba(220,236,255,1)"));
        fill("overlay", 0.12 * soft, "#f2f6ff");
        break;
      case "softFade":
        fill("screen", 0.28 * strong, "#f7efe5");
        fill("multiply", 0.20 * soft, "#9b7f6a");
        fill("soft-light", 0.16 * soft, radial("rgba(255,235,220,1)", "rgba(200,168,145,1)", 0.5, 0.42, 0.08, 0.95));
        break;
      case "tealOrange":
        fill("soft-light", 0.40 * bold, verticalGradient("rgba(16,122,128,1)", "rgba(214,117,48,1)"));
        fill("overlay", 0.18 * strong, horizontalGradient("rgba(19,134,148,1)", "rgba(255,154,84,1)"));
        break;
      case "monoFilm":
        fill("saturation", 1, "#808080");
        fill("soft-light", 0.26 * strong, "#d3c2a2");
        fill("multiply", 0.12 * soft, "#6f6458");
        break;
      case "goldenHour":
        fill("screen", 0.24 * strong, "#ffd9a6");
        fill("soft-light", 0.38 * bold, verticalGradient("rgba(255,210,130,1)", "rgba(190,110,56,1)"));
        fill("overlay", 0.18 * soft, radial("rgba(255,221,160,1)", "rgba(176,95,42,1)", 0.58, 0.38, 0.07, 0.95));
        break;
      case "nightBlue":
        fill("multiply", 0.30 * strong, "#20324a");
        fill("screen", 0.18 * soft, verticalGradient("rgba(124,165,255,1)", "rgba(20,33,66,1)"));
        fill("soft-light", 0.16 * strong, "#234d8a");
        break;
      case "forestMatte":
        fill("multiply", 0.24 * strong, "#2d4431");
        fill("soft-light", 0.30 * bold, verticalGradient("rgba(184,170,114,1)", "rgba(49,88,58,1)"));
        fill("screen", 0.10 * soft, "#d8d0ac");
        break;
      case "roseGlow":
        fill("screen", 0.26 * strong, "#ffd8e6");
        fill("soft-light", 0.34 * bold, radial("rgba(255,228,240,1)", "rgba(214,116,150,1)", 0.52, 0.38, 0.05, 0.92));
        fill("multiply", 0.10 * soft, "#9c6073");
        break;
      case "crispPop":
        fill("overlay", 0.24 * strong, "#ffffff");
        fill("soft-light", 0.18 * soft, verticalGradient("rgba(255,244,224,1)", "rgba(214,234,255,1)"));
        fill("multiply", 0.08 * soft, "#44505a");
        break;
      case "autumnCine":
        fill("multiply", 0.18 * soft, "#5a341f");
        fill("soft-light", 0.36 * bold, verticalGradient("rgba(214,133,60,1)", "rgba(108,52,30,1)"));
        fill("screen", 0.12 * strong, "#ffca86");
        break;
      case "silverMist":
        fill("screen", 0.16 * soft, "#edf4ff");
        fill("soft-light", 0.28 * bold, verticalGradient("rgba(222,230,240,1)", "rgba(124,141,160,1)"));
        fill("multiply", 0.10 * soft, "#5d6773");
        break;
      case "magentaDream":
        fill("screen", 0.18 * soft, "#ffd8ff");
        fill("soft-light", 0.38 * bold, horizontalGradient("rgba(123,94,255,1)", "rgba(255,93,177,1)"));
        fill("overlay", 0.14 * strong, radial("rgba(252,210,255,1)", "rgba(82,52,138,1)", 0.50, 0.40, 0.06, 0.94));
        break;
      case "arcticGlass":
        fill("screen", 0.22 * strong, "#eef7ff");
        fill("soft-light", 0.34 * bold, verticalGradient("rgba(235,246,255,1)", "rgba(137,186,232,1)"));
        fill("overlay", 0.14 * soft, "#d9ecff");
        break;
      case "desertDust":
        fill("screen", 0.16 * soft, "#f5dfc4");
        fill("multiply", 0.16 * strong, "#8b6c4b");
        fill("soft-light", 0.34 * bold, verticalGradient("rgba(240,201,142,1)", "rgba(168,118,74,1)"));
        break;
      case "oceanMist":
        fill("screen", 0.18 * soft, "#d8f4ff");
        fill("soft-light", 0.36 * bold, horizontalGradient("rgba(94,182,210,1)", "rgba(199,241,255,1)"));
        fill("multiply", 0.08 * soft, "#446b7a");
        break;
      case "emberGlow":
        fill("screen", 0.18 * strong, "#ffd3b2");
        fill("overlay", 0.22 * strong, horizontalGradient("rgba(255,88,52,1)", "rgba(255,196,86,1)"));
        fill("multiply", 0.10 * soft, "#6b3022");
        break;
      case "lavenderHaze":
        fill("screen", 0.18 * soft, "#f1e7ff");
        fill("soft-light", 0.34 * bold, verticalGradient("rgba(210,187,255,1)", "rgba(123,104,195,1)"));
        fill("overlay", 0.12 * strong, "#dec8ff");
        break;
      case "noirFade":
        fill("saturation", 1, "#808080");
        fill("multiply", 0.18 * strong, "#2f3138");
        fill("screen", 0.10 * soft, "#ddd9d2");
        fill("soft-light", 0.16 * soft, verticalGradient("rgba(240,236,228,1)", "rgba(70,72,82,1)"));
        break;
      case "porcelain":
        fill("screen", 0.24 * strong, "#fff7f2");
        fill("soft-light", 0.30 * bold, radial("rgba(255,247,241,1)", "rgba(234,214,204,1)", 0.50, 0.36, 0.04, 0.92));
        fill("multiply", 0.06 * soft, "#977f73");
        break;
      case "punchColor":
        fill("overlay", 0.26 * strong, "#ffffff");
        fill("soft-light", 0.18 * soft, horizontalGradient("rgba(255,228,196,1)", "rgba(194,231,255,1)"));
        fill("multiply", 0.06 * soft, "#273039");
        break;
      case "sunwashed":
        fill("screen", 0.26 * strong, "#fff0d6");
        fill("soft-light", 0.28 * bold, verticalGradient("rgba(255,229,176,1)", "rgba(255,176,123,1)"));
        fill("overlay", 0.10 * soft, "#fff7ea");
        break;
      case "cobaltPunch":
        fill("multiply", 0.12 * soft, "#243654");
        fill("soft-light", 0.40 * bold, horizontalGradient("rgba(74,117,255,1)", "rgba(116,220,255,1)"));
        fill("overlay", 0.12 * strong, "#cbe5ff");
        break;
      case "berryBloom":
        fill("screen", 0.18 * soft, "#ffe0ef");
        fill("soft-light", 0.36 * bold, verticalGradient("rgba(255,158,204,1)", "rgba(142,61,110,1)"));
        fill("multiply", 0.08 * soft, "#6e3853");
        break;
      case "oliveCine":
        fill("multiply", 0.16 * strong, "#4d5032");
        fill("soft-light", 0.34 * bold, verticalGradient("rgba(191,173,98,1)", "rgba(80,93,49,1)"));
        fill("screen", 0.08 * soft, "#f1e6b8");
        break;
      case "copperStreet":
        fill("screen", 0.14 * soft, "#ffd7bf");
        fill("soft-light", 0.36 * bold, horizontalGradient("rgba(173,90,52,1)", "rgba(238,164,113,1)"));
        fill("multiply", 0.10 * strong, "#5d3428");
        break;
      case "blueSteel":
        fill("multiply", 0.20 * strong, "#3b4958");
        fill("soft-light", 0.32 * bold, verticalGradient("rgba(176,198,220,1)", "rgba(74,98,128,1)"));
        fill("screen", 0.08 * soft, "#dfeeff");
        break;
      case "peachAir":
        fill("screen", 0.24 * strong, "#ffe6d8");
        fill("soft-light", 0.28 * bold, radial("rgba(255,236,226,1)", "rgba(255,178,146,1)", 0.52, 0.36, 0.05, 0.90));
        fill("overlay", 0.08 * soft, "#fff4ee");
        break;
      case "plumNight":
        fill("multiply", 0.22 * strong, "#34264f");
        fill("soft-light", 0.36 * bold, verticalGradient("rgba(116,93,183,1)", "rgba(52,38,79,1)"));
        fill("screen", 0.08 * soft, "#d8ccff");
        break;
      case "emeraldPop":
        fill("overlay", 0.16 * strong, "#eefbf5");
        fill("soft-light", 0.40 * bold, horizontalGradient("rgba(50,172,129,1)", "rgba(181,243,220,1)"));
        fill("multiply", 0.08 * soft, "#1e4f44");
        break;
      case "sepiaPaper":
        fill("screen", 0.14 * soft, "#f3e4c8");
        fill("multiply", 0.16 * strong, "#8b6f49");
        fill("soft-light", 0.30 * bold, verticalGradient("rgba(226,202,153,1)", "rgba(150,117,73,1)"));
        break;
      case "icyMono":
        fill("saturation", 1, "#808080");
        fill("screen", 0.16 * soft, "#e7f4ff");
        fill("soft-light", 0.28 * bold, verticalGradient("rgba(214,233,255,1)", "rgba(110,144,178,1)"));
        fill("multiply", 0.08 * soft, "#4b5f73");
        break;
      case "mokaMatte":
        fill("multiply", 0.18 * strong, "#5b463c");
        fill("soft-light", 0.30 * bold, verticalGradient("rgba(201,170,145,1)", "rgba(91,70,60,1)"));
        fill("screen", 0.08 * soft, "#e8d8cd");
        break;
      case "neonPulse":
        fill("overlay", 0.18 * strong, horizontalGradient("rgba(70,255,222,1)", "rgba(255,72,196,1)"));
        fill("soft-light", 0.22 * bold, radial("rgba(235,255,250,1)", "rgba(86,36,120,1)", 0.50, 0.38, 0.05, 0.92));
        fill("multiply", 0.06 * soft, "#2c2142");
        break;
      case "stormGray":
        fill("multiply", 0.18 * strong, "#4d5662");
        fill("soft-light", 0.30 * bold, verticalGradient("rgba(198,205,214,1)", "rgba(83,94,107,1)"));
        fill("screen", 0.08 * soft, "#edf2f7");
        break;
      case "creamBloom":
        fill("screen", 0.24 * strong, "#fff6df");
        fill("soft-light", 0.24 * bold, radial("rgba(255,248,228,1)", "rgba(241,213,158,1)", 0.52, 0.38, 0.04, 0.92));
        fill("overlay", 0.08 * soft, "#fffaf0");
        break;
      case "duskLavender":
        fill("multiply", 0.12 * soft, "#4a4066");
        fill("soft-light", 0.36 * bold, horizontalGradient("rgba(255,188,157,1)", "rgba(165,146,255,1)"));
        fill("screen", 0.08 * soft, "#f2e9ff");
        break;
      default:
        break;
    }

    if (filterLayer.preset !== "none") {
      fill("multiply", 0.11 * strong, vignetteGradient());
    }
    ctx2d.restore();
  }

  function smoothstep01(t) {
    const x = Math.max(0, Math.min(1, t));
    return x * x * (3 - 2 * x);
  }

  function applyBaseAdjustmentsToImageData(imageData, adjustments) {
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      const out = applyPixelAdjustments(data[i], data[i + 1], data[i + 2], adjustments);
      data[i] = out[0];
      data[i + 1] = out[1];
      data[i + 2] = out[2];
    }
  }

  function getOriginalRenderSource(cropOverride) {
    if (!state.source.image) return null;
    const crop = cropOverride || getActiveCropRect();
    const fullCrop = crop.x === 0 && crop.y === 0 && crop.width === state.source.width && crop.height === state.source.height;
    if (fullCrop) return state.source.image;
    const out = createWorkingCanvas(Math.max(1, Math.round(crop.width)), Math.max(1, Math.round(crop.height)));
    const octx = out.getContext("2d", { willReadFrequently: true });
    octx.drawImage(state.source.image, crop.x, crop.y, crop.width, crop.height, 0, 0, out.width, out.height);
    return out;
  }

  function getAdjustedRenderSource(cropOverride) {
    if (!state.source.image) return null;
    ensureMaskStateStructure();

    const crop = cropOverride || getActiveCropRect();
    const fullCrop = crop.x === 0 && crop.y === 0 && crop.width === state.source.width && crop.height === state.source.height;
    const activeMasks = [];
    forEachMask(function(mask, index) {
      const hasPixels = maskSlotHasVisiblePixels(index);
      const hasAdjustments = hasVisibleMaskAdjustments(mask.localAdjustments || {});
      if (hasPixels && hasAdjustments) activeMasks.push({ index, adjustments: mask.localAdjustments });
    });
    const hasLocalMaskAdjustments = activeMasks.length > 0;
    if (!hasNonDefaultAdjustments() && !hasLocalMaskAdjustments && fullCrop) return state.source.image;

    const isFastPreview = state.ui.isAdjustDragging || !!state.ui.maskStroke;
    const deviceScale = window.devicePixelRatio || 1;
    const viewportMaxDimension = Math.max(state.ui.viewportWidth, state.ui.viewportHeight) * deviceScale;
    const detailSensitivePreview = (state.ui.activeAdjustmentKey === "blur" || state.ui.activeAdjustmentKey === "mask-blur" || state.ui.activeAdjustmentKey === "sharpen" || state.ui.activeAdjustmentKey === "mask-sharpen" || state.document.adjustments.blur > 0.01 || state.document.adjustments.sharpen > 0.01 || activeMasks.some(m => m.adjustments.blur > 0.01 || m.adjustments.sharpen > 0.01));
    const livePreviewComplexity = estimateLivePreviewComplexity(hasLocalMaskAdjustments);
    const maxPreviewDimension = isFastPreview
      ? (detailSensitivePreview
          ? (livePreviewComplexity >= 10 ? Math.min(1120, Math.max(700, Math.round(viewportMaxDimension * 0.66))) : (livePreviewComplexity >= 6 ? Math.min(1250, Math.max(760, Math.round(viewportMaxDimension * 0.74))) : Math.min(1400, Math.max(820, Math.round(viewportMaxDimension * 0.82)))))
          : (livePreviewComplexity >= 10 ? Math.min(560, Math.max(340, Math.round(viewportMaxDimension * 0.32))) : (livePreviewComplexity >= 6 ? Math.min(660, Math.max(400, Math.round(viewportMaxDimension * 0.40))) : Math.min(760, Math.max(460, Math.round(viewportMaxDimension * 0.48))))))
      : (detailSensitivePreview ? Math.min(1900, Math.max(1100, Math.round(viewportMaxDimension * (state.ui.maskMode ? 1.10 : 1.22)))) : (state.ui.maskMode ? Math.min(1500, Math.max(920, Math.round(viewportMaxDimension * 0.94))) : Math.min(1600, Math.max(980, Math.round(viewportMaxDimension * 1.02)))));
    const sourceMaxDimension = Math.max(crop.width, crop.height);
    const previewScale = Math.min(1, maxPreviewDimension / Math.max(1, sourceMaxDimension));

    const workingWidth = Math.max(1, Math.round(crop.width * previewScale));
    const workingHeight = Math.max(1, Math.round(crop.height * previewScale));

    const adjustmentsKey = JSON.stringify(state.document.adjustments);
    const filterKey = JSON.stringify(getFilterLayerConfig());
    const masksKey = activeMasks.map(m => `${m.index}:${JSON.stringify(m.adjustments)}:${state.runtime.maskRevisions[m.index] || 0}`).join("|") || "no-local-mask";
    const finalRenderKey = [crop.x, crop.y, crop.width, crop.height, workingWidth, workingHeight, isFastPreview ? 1 : 0, state.ui.maskMode ? 1 : 0, adjustmentsKey, filterKey, masksKey].join("|");
    if (!state.ui.isAdjustDragging && state.cache.finalRenderKey === finalRenderKey && state.cache.finalRenderCanvas) return state.cache.finalRenderCanvas;

    const dragOnlyKey = [crop.x, crop.y, crop.width, crop.height, workingWidth, workingHeight, state.document.adjustments.blur, state.document.adjustments.sharpen, state.document.adjustments.vignette, filterKey, masksKey].join("|");
    if (state.ui.isAdjustDragging && state.cache.dragRenderKey === dragOnlyKey && state.cache.dragRenderCanvas) return state.cache.dragRenderCanvas;

    const out = createWorkingCanvas(workingWidth, workingHeight);
    const octx = out.getContext("2d", { willReadFrequently: true });
    octx.drawImage(state.source.image, crop.x, crop.y, crop.width, crop.height, 0, 0, workingWidth, workingHeight);
    if (!hasNonDefaultAdjustments() && !hasLocalMaskAdjustments) return out;

    const imageData = octx.getImageData(0, 0, workingWidth, workingHeight);
    const baseAdjustKey = buildBaseAdjustKey(crop, workingWidth, workingHeight);
    if (state.cache.baseAdjustKey === baseAdjustKey && state.cache.baseAdjustImageData && state.cache.baseAdjustWidth === workingWidth && state.cache.baseAdjustHeight === workingHeight) imageData.data.set(state.cache.baseAdjustImageData.data);
    else {
      applyBaseAdjustmentsToImageData(imageData, state.document.adjustments);
      state.cache.baseAdjustKey = baseAdjustKey;
      state.cache.baseAdjustImageData = cloneImageData(imageData);
      state.cache.baseAdjustWidth = workingWidth;
      state.cache.baseAdjustHeight = workingHeight;
    }

    const data = imageData.data;
    const a = state.document.adjustments;
    if (a.blur > 0) {
      const blurred = new Uint8ClampedArray(data);
      const radius = Math.max(1, Math.min(8, isFastPreview ? Math.round(a.blur * 1.4) : Math.round(a.blur * 3.2)));
      const mix = Math.max(0.10, Math.min(1, isFastPreview ? a.blur * 0.30 : a.blur * 0.58));
      boxBlurRGBA(blurred, workingWidth, workingHeight, radius);
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.max(0, Math.min(255, Math.round(data[i] * (1 - mix) + blurred[i] * mix)));
        data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] * (1 - mix) + blurred[i + 1] * mix)));
        data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] * (1 - mix) + blurred[i + 2] * mix)));
      }
    }

    for (const maskInfo of activeMasks) {
      const maskAdjust = maskInfo.adjustments;
      const maskAlpha = getScaledMaskAlpha(maskInfo.index, crop, workingWidth, workingHeight);
      if (!maskAlpha) continue;
      let blurredLocal = null;
      if (maskAdjust.blur > 0 || maskAdjust.sharpen > 0) {
        blurredLocal = new Uint8ClampedArray(data);
        const localRadius = state.ui.isAdjustDragging ? (maskAdjust.blur > 0 ? Math.max(1, Math.min(3, Math.round(maskAdjust.blur * 1.1))) : 1) : (maskAdjust.blur > 0 ? Math.max(1, Math.min(7, Math.round(maskAdjust.blur * 2.6))) : 1);
        boxBlurRGBA(blurredLocal, workingWidth, workingHeight, localRadius);
      }
      for (let p = 0, i = 0; p < maskAlpha.length; p++, i += 4) {
        const alphaByte = maskAlpha[p];
        if (alphaByte <= 1) continue;
        const alpha = alphaByte / 255;
        let outPx = applyPixelAdjustments(data[i], data[i + 1], data[i + 2], maskAdjust);
        data[i] = Math.max(0, Math.min(255, Math.round(data[i] * (1 - alpha) + outPx[0] * alpha)));
        data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] * (1 - alpha) + outPx[1] * alpha)));
        data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] * (1 - alpha) + outPx[2] * alpha)));
        if (maskAdjust.blur > 0 && blurredLocal) {
          const blurMix = Math.max(0, Math.min(1, alpha * maskAdjust.blur * (state.ui.isAdjustDragging ? 0.24 : 0.48)));
          data[i] = Math.round(data[i] * (1 - blurMix) + blurredLocal[i] * blurMix);
          data[i + 1] = Math.round(data[i + 1] * (1 - blurMix) + blurredLocal[i + 1] * blurMix);
          data[i + 2] = Math.round(data[i + 2] * (1 - blurMix) + blurredLocal[i + 2] * blurMix);
        }
        if (maskAdjust.sharpen > 0 && blurredLocal && !state.ui.isAdjustDragging) {
          const amt = alpha * maskAdjust.sharpen * 1.2;
          data[i] = Math.max(0, Math.min(255, Math.round(data[i] + (data[i] - blurredLocal[i]) * amt)));
          data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] + (data[i + 1] - blurredLocal[i + 1]) * amt)));
          data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] + (data[i + 2] - blurredLocal[i + 2]) * amt)));
        }
      }
    }

    if (a.sharpen > 0) {
      const blurred = new Uint8ClampedArray(data);
      const radius = isFastPreview ? 1 : 2;
      boxBlurRGBA(blurred, workingWidth, workingHeight, radius);
      const amount = isFastPreview ? a.sharpen * 0.75 : a.sharpen * 1.7;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.max(0, Math.min(255, Math.round(data[i] + (data[i] - blurred[i]) * amount)));
        data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] + (data[i + 1] - blurred[i + 1]) * amount)));
        data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] + (data[i + 2] - blurred[i + 2]) * amount)));
      }
    }
    if (a.vignette > 0) {
      const cx = workingWidth / 2, cy = workingHeight / 2, maxDist = Math.sqrt(cx * cx + cy * cy);
      const strength = isFastPreview ? a.vignette * 0.95 : a.vignette * 1.45;
      const start = isFastPreview ? 0.34 : 0.24;
      const span = Math.max(0.001, 1 - start);
      for (let y = 0; y < workingHeight; y++) {
        for (let x = 0; x < workingWidth; x++) {
          const idx = (y * workingWidth + x) * 4;
          const dx = x - cx, dy = y - cy;
          const dist = Math.sqrt(dx * dx + dy * dy) / maxDist;
          const falloff = Math.max(0, (dist - start) / span);
          const darken = Math.max(0.08, 1 - falloff * falloff * strength * 0.9);
          data[idx] = Math.round(data[idx] * darken); data[idx + 1] = Math.round(data[idx + 1] * darken); data[idx + 2] = Math.round(data[idx + 2] * darken);
        }
      }
    }

    octx.putImageData(imageData, 0, 0);
    applyFilterLayer(octx, workingWidth, workingHeight, getFilterLayerConfig());
    if (state.ui.isAdjustDragging) { state.cache.dragRenderKey = dragOnlyKey; state.cache.dragRenderCanvas = out; state.cache.finalRenderKey = ""; state.cache.finalRenderCanvas = null; }
    else { state.cache.dragRenderKey = ""; state.cache.dragRenderCanvas = null; state.cache.finalRenderKey = finalRenderKey; state.cache.finalRenderCanvas = out; }
    return out;
  }

  function drawBackground() {
    ctx.fillStyle = "#123b33";
    ctx.fillRect(0, 0, state.ui.viewportWidth, state.ui.viewportHeight);
    ctx.strokeStyle = "rgba(184,255,232,0.10)";
    for (let x = 0; x < state.ui.viewportWidth; x += 24) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, state.ui.viewportHeight); ctx.stroke();
    }
    for (let y = 0; y < state.ui.viewportHeight; y += 24) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(state.ui.viewportWidth, y); ctx.stroke();
    }
  }

  function buildScaledMaskCanvas(maskIndex, crop, width, height) {
    const runtimeMask = getRuntimeMaskCanvas(maskIndex);
    if (!runtimeMask) return null;
    const entry = getMaskCacheEntry(maskIndex);
    const maskKey = [crop.x, crop.y, crop.width, crop.height, width, height, getMaskAt(maskIndex).dataUrl || "", getMaskAt(maskIndex).resolutionScale || 1, state.runtime.maskRevisions[maskIndex] || 0].join("|");
    if (entry.scaledMaskKey === maskKey && entry.scaledMaskCanvas) return entry.scaledMaskCanvas;
    const out = createWorkingCanvas(width, height);
    const octx = out.getContext("2d", { willReadFrequently: true });
    const sx = crop.x * (runtimeMask.width / Math.max(1, state.source.width));
    const sy = crop.y * (runtimeMask.height / Math.max(1, state.source.height));
    const sw = crop.width * (runtimeMask.width / Math.max(1, state.source.width));
    const sh = crop.height * (runtimeMask.height / Math.max(1, state.source.height));
    octx.drawImage(runtimeMask, sx, sy, sw, sh, 0, 0, width, height);
    entry.scaledMaskKey = maskKey; entry.scaledMaskCanvas = out; entry.scaledMaskImageDataKey = ""; entry.scaledMaskImageData = null; entry.scaledMaskAlphaKey = ""; entry.scaledMaskAlpha = null;
    return out;
  }

  function getScaledMaskImageData(maskIndex, crop, width, height) {
    const maskScaled = buildScaledMaskCanvas(maskIndex, crop, width, height);
    if (!maskScaled) return null;
    const entry = getMaskCacheEntry(maskIndex);
    const imageKey = [crop.x, crop.y, crop.width, crop.height, width, height, state.runtime.maskRevisions[maskIndex] || 0].join("|");
    if (entry.scaledMaskImageDataKey === imageKey && entry.scaledMaskImageData) return entry.scaledMaskImageData;
    const imageData = maskScaled.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, width, height);
    entry.scaledMaskImageDataKey = imageKey; entry.scaledMaskImageData = imageData; entry.scaledMaskAlphaKey = ""; entry.scaledMaskAlpha = null;
    return imageData;
  }

  function getScaledMaskAlpha(maskIndex, crop, width, height) {
    const imageData = getScaledMaskImageData(maskIndex, crop, width, height);
    if (!imageData) return null;
    const entry = getMaskCacheEntry(maskIndex);
    const alphaKey = [crop.x, crop.y, crop.width, crop.height, width, height, state.runtime.maskRevisions[maskIndex] || 0].join("|");
    if (entry.scaledMaskAlphaKey === alphaKey && entry.scaledMaskAlpha) return entry.scaledMaskAlpha;
    const src = imageData.data;
    const alpha = new Uint8ClampedArray(width * height);
    for (let i = 0, p = 0; i < src.length; i += 4, p++) alpha[p] = src[i + 3];
    entry.scaledMaskAlphaKey = alphaKey; entry.scaledMaskAlpha = alpha;
    return alpha;
  }

  function drawMaskOverlay() {
    const activeMaskIndex = getActiveMaskIndex();
    if (!getRuntimeMaskCanvas(activeMaskIndex) || !state.ui.maskOverlayVisible || !anyMaskPixels()) return;
    const crop = getActiveCropRect();
    const overlayScale = Math.min(1, 800 / Math.max(crop.width, crop.height));
    const renderMask = buildScaledMaskCanvas(activeMaskIndex, crop, Math.max(1, Math.round(crop.width * overlayScale)), Math.max(1, Math.round(crop.height * overlayScale)));
    if (!renderMask) return;
    const drawWidth = crop.width * getDisplayScale();
    const drawHeight = crop.height * getDisplayScale();
    const center = getViewCenter();
    ctx.save();
    ctx.translate(center.x, center.y);
    ctx.rotate(getRenderAngleRadians());
    ctx.scale(getFlipScaleX(), getFlipScaleY());
    const viewMode = state.ui.maskViewMode || "overlay";
    if (viewMode === "bw") {
      const bwWidth = Math.max(1, renderMask.width || Math.round(crop.width * overlayScale));
      const bwHeight = Math.max(1, renderMask.height || Math.round(crop.height * overlayScale));
      const alpha = getScaledMaskAlpha(activeMaskIndex, crop, bwWidth, bwHeight);
      if (alpha) {
        const bwCanvas = createWorkingCanvas(bwWidth, bwHeight);
        const bwCtx = bwCanvas.getContext("2d", { willReadFrequently: true });
        const bwImage = bwCtx.createImageData(bwWidth, bwHeight);
        const dst = bwImage.data;
        for (let p = 0, i = 0; p < alpha.length; p++, i += 4) {
          const v = alpha[p];
          dst[i] = v; dst[i + 1] = v; dst[i + 2] = v; dst[i + 3] = 255;
        }
        bwCtx.putImageData(bwImage, 0, 0);
        ctx.drawImage(bwCanvas, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);
      }
    } else if (viewMode === "overlay") {
      ctx.globalAlpha = 0.36;
      ctx.drawImage(renderMask, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);
      ctx.globalCompositeOperation = "source-atop";
      ctx.fillStyle = "rgba(255,255,255,0.82)";
      ctx.fillRect(-drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);
    }
    ctx.restore();
  }

  function drawMaskBrushCursor() {
    if (!state.ui.maskMode) return;
    const pos = state.ui.maskStroke && state.ui.maskStroke.lastCanvasPos ? state.ui.maskStroke.lastCanvasPos : state.ui.maskHoverPos;
    if (!pos) return;
    const radius = state.ui.maskBrushSize / 2;
    ctx.save();
    ctx.strokeStyle = "rgba(0,0,0,0.92)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = "rgba(255,255,255,0.98)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(pos.x - 6, pos.y);
    ctx.lineTo(pos.x + 6, pos.y);
    ctx.moveTo(pos.x, pos.y - 6);
    ctx.lineTo(pos.x, pos.y + 6);
    ctx.stroke();
    ctx.restore();
  }

  function drawCropOverlay() {
    const display = getCropModeDisplayRect();
    const crop = sourceRectToRotatedRect(state.ui.pendingCrop || getDefaultCropRect(), getRotationNormalized());
    const cropX = display.x + crop.x * display.scale;
    const cropY = display.y + crop.y * display.scale;
    const cropW = crop.width * display.scale;
    const cropH = crop.height * display.scale;

    ctx.save();
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.beginPath();
    ctx.rect(display.x, display.y, display.width, display.height);
    ctx.rect(cropX, cropY, cropW, cropH);
    ctx.fill("evenodd");

    ctx.strokeStyle = "rgba(255,255,255,0.9)";
    ctx.lineWidth = 2;
    ctx.strokeRect(cropX, cropY, cropW, cropH);

    ctx.strokeStyle = "rgba(255,255,255,0.35)";
    ctx.lineWidth = 1;
    for (let i = 1; i <= 2; i++) {
      const vx = cropX + (cropW / 3) * i;
      const hy = cropY + (cropH / 3) * i;
      ctx.beginPath(); ctx.moveTo(vx, cropY); ctx.lineTo(vx, cropY + cropH); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cropX, hy); ctx.lineTo(cropX + cropW, hy); ctx.stroke();
    }

    const size = 10;
    [[cropX, cropY], [cropX + cropW, cropY], [cropX, cropY + cropH], [cropX + cropW, cropY + cropH]].forEach(([px, py]) => {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(px - size / 2, py - size / 2, size, size);
    });
    ctx.restore();
  }

  function isShowingOriginal() {
    return !!(state.ui.showOriginal || state.ui.showOriginalMomentary);
  }

  function setShowOriginal(value) {
    state.ui.showOriginal = !!value;
    renderAll();
  }

  function setShowOriginalMomentary(value) {
    if (!state.source.image || state.ui.cropMode) return;
    state.ui.showOriginalMomentary = !!value;
    renderAll();
  }

  function isSplitViewActive() {
    return !!(state.ui.splitView && state.source.image && !state.ui.cropMode);
  }

  function getSplitScreenX() {
    return Math.round(clamp(Number(state.ui.splitPosition || 0.5), 0, 1) * state.ui.viewportWidth);
  }

  function drawSplitView(renderEdited, drawFn) {
    const splitX = getSplitScreenX();

    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, splitX, state.ui.viewportHeight);
    ctx.clip();
    drawFn(state.source.image);
    ctx.restore();

    ctx.save();
    ctx.beginPath();
    ctx.rect(splitX, 0, Math.max(0, state.ui.viewportWidth - splitX), state.ui.viewportHeight);
    ctx.clip();
    drawFn(renderEdited);
    ctx.restore();

    ctx.save();
    ctx.strokeStyle = "rgba(255,255,255,0.95)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(splitX + 0.5, 0);
    ctx.lineTo(splitX + 0.5, state.ui.viewportHeight);
    ctx.stroke();

    ctx.strokeStyle = "rgba(0,0,0,0.35)";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(splitX + 0.5, 0);
    ctx.lineTo(splitX + 0.5, state.ui.viewportHeight);
    ctx.stroke();

    const handleY = Math.round(state.ui.viewportHeight / 2);
    const handleW = 28;
    const handleH = 58;
    const handleX = splitX - handleW / 2;
    const handleTop = handleY - handleH / 2;

    ctx.fillStyle = "rgba(18,18,18,0.82)";
    roundRect(ctx, handleX, handleTop, handleW, handleH, 12);
    ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.22)";
    ctx.lineWidth = 1;
    roundRect(ctx, handleX, handleTop, handleW, handleH, 12);
    ctx.stroke();

    ctx.fillStyle = "rgba(255,255,255,0.92)";
    for (const off of [-8, 0, 8]) {
      ctx.fillRect(splitX - 1, handleY + off - 7, 2, 14);
    }

    ctx.font = "600 12px sans-serif";
    ctx.textAlign = "left";
    ctx.fillStyle = "rgba(255,255,255,0.92)";
    ctx.fillText("Before", 16, 26);
    ctx.textAlign = "right";
    ctx.fillText("After", state.ui.viewportWidth - 16, 26);
    ctx.restore();
  }

  function renderCanvas() {
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(state.ui.viewportWidth * dpr);
    canvas.height = Math.floor(state.ui.viewportHeight * dpr);
    canvas.style.width = state.ui.viewportWidth + "px";
    canvas.style.height = state.ui.viewportHeight + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, state.ui.viewportWidth, state.ui.viewportHeight);

    drawBackground();

    if (!state.source.image) {
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.font = "600 20px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Import an image to begin", state.ui.viewportWidth / 2, state.ui.viewportHeight / 2 - 10);
      ctx.font = "400 14px sans-serif";
      ctx.fillStyle = "rgba(255,255,255,0.6)";
      ctx.fillText("Ready", state.ui.viewportWidth / 2, state.ui.viewportHeight / 2 + 18);
      return;
    }

    if (state.ui.cropMode) {
      const display = getCropModeDisplayRect();
      const renderSource = isShowingOriginal() ? state.source.image : getAdjustedRenderSource(getDefaultCropRect());
      const centerX = Math.round(state.ui.viewportWidth / 2);
      const centerY = Math.round(state.ui.viewportHeight / 2);
      const rotationTurns = getRotationNormalized();
      const drawWidth = state.source.width * display.scale;
      const drawHeight = state.source.height * display.scale;
      const bounds = getRotatedImageDimensions(rotationTurns, drawWidth, drawHeight);
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(state.document.geometry.rotationQuarterTurns * Math.PI / 2);
      ctx.scale(getFlipScaleX(), getFlipScaleY());
      ctx.shadowColor = "rgba(0,0,0,0.35)";
      ctx.shadowBlur = 20;
      ctx.drawImage(renderSource, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);
      ctx.restore();
      ctx.strokeStyle = "rgba(255,255,255,0.22)";
      ctx.strokeRect(centerX - bounds.width / 2, centerY - bounds.height / 2, bounds.width, bounds.height);
      drawCropOverlay();
      return;
    }

    const crop = getActiveCropRect();
    const originalRenderSource = getOriginalRenderSource(crop);
    const renderSource = isShowingOriginal() ? originalRenderSource : getAdjustedRenderSource(crop);
    const drawWidth = crop.width * getDisplayScale();
    const drawHeight = crop.height * getDisplayScale();
    const center = getViewCenter();
    const centerX = center.x;
    const centerY = center.y;
    const rotationTurns = getRotationNormalized();

    const drawMainImage = function (sourceImage) {
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(getRenderAngleRadians());
      ctx.scale(getFlipScaleX(), getFlipScaleY());
      ctx.shadowColor = "rgba(0,0,0,0.35)";
      ctx.shadowBlur = 20;
      ctx.drawImage(sourceImage, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);
      ctx.restore();
    };

    if (isSplitViewActive()) drawSplitView(renderSource, function (sourceImage) {
      drawMainImage(sourceImage === state.source.image ? originalRenderSource : sourceImage);
    });
    else drawMainImage(renderSource);
    drawMaskOverlay();
    drawMaskBrushCursor();

    const rotatedWidth = rotationTurns % 2 === 1 ? drawHeight : drawWidth;
    const rotatedHeight = rotationTurns % 2 === 1 ? drawWidth : drawHeight;
    const bounds = getRotatedBoundingSize(rotatedWidth, rotatedHeight, getStraightenRadians());
    const boundsWidth = bounds.width;
    const boundsHeight = bounds.height;
    ctx.strokeStyle = "rgba(255,255,255,0.22)";
    ctx.strokeRect(centerX - boundsWidth / 2, centerY - boundsHeight / 2, boundsWidth, boundsHeight);
  }


  function getExportExtension(mimeType) {
    if (mimeType === "image/jpeg") return "jpg";
    return "png";
  }

  function getExportFormatLabel(mimeType) {
    if (mimeType === "image/jpeg") return "JPG";
    return "PNG";
  }

  function formatFileSize(bytes) {
    const value = Math.max(0, Number(bytes) || 0);
    if (value < 1000) return `${Math.round(value)} B`;
    if (value < 1000000) return `${(value / 1000).toFixed(value >= 100000 ? 0 : 1)} KB`;
    if (value < 1000000000) return `${(value / 1000000).toFixed(value >= 10000000 ? 1 : 2)} MB`;
    return `${(value / 1000000000).toFixed(2)} GB`;
  }

  function getExportEstimateValue(mimeType, quality) {
    const formatLabel = getExportFormatLabel(mimeType);
    if (mimeType === "image/jpeg") {
      return `${formatLabel} · quality ${quality.toFixed(2)}`;
    }
    return formatLabel;
  }

  function sanitizeBaseFilename(name) {
    const raw = String(name || "photo").trim();
    const noExt = raw.replace(/\.(png|jpe?g)$/i, "");
    const cleaned = noExt
      .replace(/[\/:*?"<>|]+/g, "-")
      .replace(/\s+/g, " ")
      .replace(/\.+$/g, "")
      .trim();
    return cleaned || "photo";
  }

  function downloadBlob(filename, blob) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function canvasToBlobAsync(canvasEl, mimeType, quality) {
    return new Promise(function (resolve, reject) {
      canvasEl.toBlob(function (blob) {
        if (blob) resolve(blob);
        else reject(new Error("Could not create export blob."));
      }, mimeType, quality);
    });
  }

  function renderAdjustedSourceForExport(crop, scale) {
    ensureMaskStateStructure();
    const workingWidth = Math.max(1, Math.round(crop.width * scale));
    const workingHeight = Math.max(1, Math.round(crop.height * scale));
    const out = createWorkingCanvas(workingWidth, workingHeight);
    const octx = out.getContext("2d", { willReadFrequently: true });
    octx.drawImage(state.source.image, crop.x, crop.y, crop.width, crop.height, 0, 0, workingWidth, workingHeight);

    const imageData = octx.getImageData(0, 0, workingWidth, workingHeight);
    applyBaseAdjustmentsToImageData(imageData, state.document.adjustments);
    const data = imageData.data;
    const a = state.document.adjustments;

    if (a.blur > 0) {
      const blurred = new Uint8ClampedArray(data);
      const radius = Math.max(1, Math.min(12, Math.round(a.blur * 3.2)));
      const mix = Math.max(0.10, Math.min(1, a.blur * 0.58));
      boxBlurRGBA(blurred, workingWidth, workingHeight, radius);
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.max(0, Math.min(255, Math.round(data[i] * (1 - mix) + blurred[i] * mix)));
        data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] * (1 - mix) + blurred[i + 1] * mix)));
        data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] * (1 - mix) + blurred[i + 2] * mix)));
      }
    }

    const activeMasks = [];
    forEachMask(function (mask, index) {
      const hasPixels = maskSlotHasVisiblePixels(index);
      const hasAdjustments = hasVisibleMaskAdjustments(mask.localAdjustments || {});
      if (hasPixels && hasAdjustments) activeMasks.push({ index, adjustments: mask.localAdjustments });
    });

    for (const maskInfo of activeMasks) {
      const maskAdjust = maskInfo.adjustments;
      const maskAlpha = getScaledMaskAlpha(maskInfo.index, crop, workingWidth, workingHeight);
      if (!maskAlpha) continue;
      let blurredLocal = null;
      if (maskAdjust.blur > 0 || maskAdjust.sharpen > 0) {
        blurredLocal = new Uint8ClampedArray(data);
        const localRadius = maskAdjust.blur > 0 ? Math.max(1, Math.min(10, Math.round(maskAdjust.blur * 2.6))) : 1;
        boxBlurRGBA(blurredLocal, workingWidth, workingHeight, localRadius);
      }
      for (let p = 0, i = 0; p < maskAlpha.length; p++, i += 4) {
        const alphaByte = maskAlpha[p];
        if (alphaByte <= 1) continue;
        const alpha = alphaByte / 255;
        const outPx = applyPixelAdjustments(data[i], data[i + 1], data[i + 2], maskAdjust);
        data[i] = Math.max(0, Math.min(255, Math.round(data[i] * (1 - alpha) + outPx[0] * alpha)));
        data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] * (1 - alpha) + outPx[1] * alpha)));
        data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] * (1 - alpha) + outPx[2] * alpha)));
        if (maskAdjust.blur > 0 && blurredLocal) {
          const blurMix = Math.max(0, Math.min(1, alpha * maskAdjust.blur * 0.48));
          data[i] = Math.round(data[i] * (1 - blurMix) + blurredLocal[i] * blurMix);
          data[i + 1] = Math.round(data[i + 1] * (1 - blurMix) + blurredLocal[i + 1] * blurMix);
          data[i + 2] = Math.round(data[i + 2] * (1 - blurMix) + blurredLocal[i + 2] * blurMix);
        }
        if (maskAdjust.sharpen > 0 && blurredLocal) {
          const amt = alpha * maskAdjust.sharpen * 1.2;
          data[i] = Math.max(0, Math.min(255, Math.round(data[i] + (data[i] - blurredLocal[i]) * amt)));
          data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] + (data[i + 1] - blurredLocal[i + 1]) * amt)));
          data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] + (data[i + 2] - blurredLocal[i + 2]) * amt)));
        }
      }
    }

    if (a.sharpen > 0) {
      const blurred = new Uint8ClampedArray(data);
      boxBlurRGBA(blurred, workingWidth, workingHeight, 2);
      const amount = a.sharpen * 1.7;
      for (let i = 0; i < data.length; i += 4) {
        data[i] = Math.max(0, Math.min(255, Math.round(data[i] + (data[i] - blurred[i]) * amount)));
        data[i + 1] = Math.max(0, Math.min(255, Math.round(data[i + 1] + (data[i + 1] - blurred[i + 1]) * amount)));
        data[i + 2] = Math.max(0, Math.min(255, Math.round(data[i + 2] + (data[i + 2] - blurred[i + 2]) * amount)));
      }
    }

    if (a.vignette > 0) {
      const cx = workingWidth / 2, cy = workingHeight / 2, maxDist = Math.sqrt(cx * cx + cy * cy);
      const strength = a.vignette * 1.45;
      const start = 0.24;
      const span = Math.max(0.001, 1 - start);
      for (let y = 0; y < workingHeight; y++) {
        for (let x = 0; x < workingWidth; x++) {
          const idx = (y * workingWidth + x) * 4;
          const dx = x - cx, dy = y - cy;
          const dist = Math.sqrt(dx * dx + dy * dy) / maxDist;
          const falloff = Math.max(0, (dist - start) / span);
          const darken = Math.max(0.08, 1 - falloff * falloff * strength * 0.9);
          data[idx] = Math.round(data[idx] * darken);
          data[idx + 1] = Math.round(data[idx + 1] * darken);
          data[idx + 2] = Math.round(data[idx + 2] * darken);
        }
      }
    }

    octx.putImageData(imageData, 0, 0);
    applyFilterLayer(octx, workingWidth, workingHeight, getFilterLayerConfig());
    return out;
  }

  function renderExportCanvas(scale) {
    if (!state.source.image) throw new Error("No image loaded.");
    const crop = getActiveCropRect();
    const adjustedSource = renderAdjustedSourceForExport(crop, scale);
    const drawWidth = adjustedSource.width;
    const drawHeight = adjustedSource.height;
    const rotationTurns = getRotationNormalized();
    const rotatedWidth = rotationTurns % 2 === 1 ? drawHeight : drawWidth;
    const rotatedHeight = rotationTurns % 2 === 1 ? drawWidth : drawHeight;
    const bounds = getRotatedBoundingSize(rotatedWidth, rotatedHeight, getStraightenRadians());
    const exportCanvas = createWorkingCanvas(Math.max(1, Math.ceil(bounds.width)), Math.max(1, Math.ceil(bounds.height)));
    const ectx = exportCanvas.getContext("2d", { willReadFrequently: true });
    ectx.translate(exportCanvas.width / 2, exportCanvas.height / 2);
    ectx.rotate(getRenderAngleRadians());
    ectx.scale(getFlipScaleX(), getFlipScaleY());
    ectx.drawImage(adjustedSource, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);
    return exportCanvas;
  }

  function getExportBaseFilename() {
    const fallbackBase = sanitizeBaseFilename(state.source.name || "") || "photo";
    const fallback = `${fallbackBase}-edited`;
    if (!exportFilenameInput) return fallback;
    const cleaned = sanitizeBaseFilename(exportFilenameInput.value || "");
    return cleaned || fallback;
  }

  function syncExportFilenameFromSource(force) {
    if (!exportFilenameInput) return;
    const current = sanitizeBaseFilename(exportFilenameInput.value || "");
    if (!force && current) return;
    const sourceBase = sanitizeBaseFilename(state.source.name || "") || "photo";
    exportFilenameInput.value = `${sourceBase}-edited`;
  }

  function updateExportExtensionHint() {
    if (!exportExtensionHint) return;
    const mimeType = exportFormatSelect ? exportFormatSelect.value : "image/png";
    exportExtensionHint.textContent = `.${getExportExtension(mimeType)}`;
  }

  function getExportScaleFactor() {
    return Math.max(0.1, Math.min(4, Number(exportScaleSelect ? exportScaleSelect.value : 1) || 1));
  }

  function getEstimatedExportSize() {
    if (!state.source.image) return null;
    const crop = state.ui.cropMode && state.ui.pendingCrop ? state.ui.pendingCrop : getActiveCropRect();
    if (!crop || !crop.width || !crop.height) return null;
    const rotationQuarterTurns = getRotationNormalized();
    const scale = getExportScaleFactor();
    const drawWidth = Math.max(1, Math.round(crop.width * scale));
    const drawHeight = Math.max(1, Math.round(crop.height * scale));
    const rotatedWidth = rotationQuarterTurns % 2 === 1 ? drawHeight : drawWidth;
    const rotatedHeight = rotationQuarterTurns % 2 === 1 ? drawWidth : drawHeight;
    const bounds = getRotatedBoundingSize(rotatedWidth, rotatedHeight, getStraightenRadians());
    const width = Math.max(1, Math.ceil(bounds.width));
    const height = Math.max(1, Math.ceil(bounds.height));
    return { width, height, megapixels: (width * height) / 1000000, scale };
  }

  function updateExportSizeHint() {
    if (!exportSizeHint) return;
    const size = getEstimatedExportSize();
    if (!size) {
      exportSizeHint.textContent = "—";
      return;
    }
    const megapixelsText = size.megapixels >= 0.1 ? ` · ${size.megapixels.toFixed(size.megapixels >= 10 ? 1 : 2)} megapixels` : "";
    exportSizeHint.textContent = `${size.width} × ${size.height} px${megapixelsText}`;
  }

  function updateExportFileSizeHint(text) {
    if (exportOriginalHint) {
      exportOriginalHint.textContent = state.source.image ? formatFileSize(state.source.size || 0) : "—";
    }
    if (!exportFileSizeHint) return;
    exportFileSizeHint.textContent = text;
  }

  async function refreshExportFileSizeEstimate() {
    if (!state.source.image) {
      updateExportFileSizeHint("—");
      return;
    }
    const mimeType = exportFormatSelect ? exportFormatSelect.value : "image/png";
    const scale = getExportScaleFactor();
    const quality = (mimeType === "image/jpeg") ? Math.max(0.5, Math.min(1, Number(exportQualityRange ? exportQualityRange.value : 0.92) || 0.92)) : undefined;
    const size = getEstimatedExportSize();
    if (!size) {
      updateExportFileSizeHint("—");
      return;
    }
    if (Math.max(size.width, size.height) > 12000 || (size.width * size.height) > 48000000) {
      updateExportFileSizeHint("Unavailable for very large exports");
      return;
    }

    const estimateValuePrefix = getExportEstimateValue(mimeType, quality || 0.92);
    const token = ++exportEstimateToken;
    updateExportFileSizeHint(`${estimateValuePrefix} · calculating...`);

    try {
      const exportCanvas = renderExportCanvas(scale);
      const blob = await canvasToBlobAsync(exportCanvas, mimeType, quality);
      if (token !== exportEstimateToken) return;
      updateExportFileSizeHint(`${estimateValuePrefix} · ${formatFileSize(blob.size)}`);
    } catch (err) {
      if (token !== exportEstimateToken) return;
      updateExportFileSizeHint(`${estimateValuePrefix} · unavailable`);
    }
  }

  function scheduleExportFileSizeEstimate() {
    if (!exportFileSizeHint) return;
    if (exportEstimateTimer) clearTimeout(exportEstimateTimer);
    if (!state.source.image) {
      updateExportFileSizeHint("—");
      return;
    }
    exportEstimateTimer = setTimeout(function () {
      exportEstimateTimer = null;
      refreshExportFileSizeEstimate();
    }, 220);
  }

  function updateExportUiState() {
    const mimeType = exportFormatSelect ? exportFormatSelect.value : "image/png";
    const qualityEnabled = mimeType === "image/jpeg";
    if (exportOriginalHint) exportOriginalHint.textContent = state.source.image ? formatFileSize(state.source.size || 0) : "—";
    if (exportQualityRange) exportQualityRange.disabled = !qualityEnabled;
    if (exportQualityGroup) exportQualityGroup.style.opacity = qualityEnabled ? "1" : "0.55";
    if (exportQualityValue) exportQualityValue.textContent = qualityEnabled ? Number(exportQualityRange ? exportQualityRange.value : 0.92).toFixed(2) : "N/A";
    updateExportExtensionHint();
    updateExportSizeHint();
    scheduleExportFileSizeEstimate();
  }

  async function exportEditedImage() {
    if (!state.source.image) return;
    const mimeType = exportFormatSelect ? exportFormatSelect.value : "image/png";
    const formatLabel = getExportFormatLabel(mimeType);
    const scale = getExportScaleFactor();
    const quality = (mimeType === "image/jpeg") ? Math.max(0.5, Math.min(1, Number(exportQualityRange ? exportQualityRange.value : 0.92) || 0.92)) : undefined;
    const filename = `${getExportBaseFilename()}.${getExportExtension(mimeType)}`;
    statusText.textContent = `Exporting ${formatLabel}...`;
    const exportCanvas = renderExportCanvas(scale);
    const maxDimension = Math.max(exportCanvas.width, exportCanvas.height);
    const totalPixels = exportCanvas.width * exportCanvas.height;
    if (maxDimension > 12000 || totalPixels > 48000000) {
      throw new Error(`Export is too large (${exportCanvas.width} × ${exportCanvas.height}px). Try a lower Scale value.`);
    }
    const blob = await canvasToBlobAsync(exportCanvas, mimeType, quality);
    downloadBlob(filename, blob);
    updateExportFileSizeHint(`Last exported file: ${formatLabel} · ${formatFileSize(blob.size)}`);
    statusText.textContent = `Exported ${formatLabel} · ${exportCanvas.width} × ${exportCanvas.height}px · ${formatFileSize(blob.size)}`;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function renderStatus() {
    ensureMaskStateStructure();
    const hasImage = !!state.source.image;
    const cropEditable = hasImage;
    const activeMaskHasPixels = maskSlotHasVisiblePixels(getActiveMaskIndex());
    const activeMaskHasAdjustments = hasVisibleMaskAdjustments(getActiveMask().localAdjustments || {});

    saveProjectBtn.disabled = !hasImage || state.ui.cropMode;
    openProjectBtn.disabled = state.ui.cropMode;
    rotateLeftBtn.disabled = !hasImage || state.ui.cropMode;
    rotateRightBtn.disabled = !hasImage || state.ui.cropMode;
    resetGeometryBtn.disabled = !hasImage || state.ui.cropMode;
    flipHorizontalBtn.disabled = !hasImage || state.ui.cropMode;
    flipVerticalBtn.disabled = !hasImage || state.ui.cropMode;
    straightenRange.disabled = !hasImage || state.ui.cropMode;
    adjustmentControls.forEach(([, rangeEl]) => rangeEl.disabled = !hasImage || state.ui.cropMode || state.ui.maskMode);
    maskAdjustmentControls.forEach(([, rangeEl]) => rangeEl.disabled = !hasImage || state.ui.cropMode || !activeMaskHasPixels);
    cropModeBtn.disabled = !cropEditable || state.ui.cropMode || state.ui.maskMode;
    cropAspectSelect.disabled = !hasImage || state.ui.maskMode;
    applyCropBtn.disabled = !(state.ui.cropMode && state.ui.pendingCrop);
    cancelCropBtn.disabled = !state.ui.cropMode;
    resetCropBtn.disabled = !hasImage || state.ui.maskMode;
    maskModeBtn.disabled = !hasImage || state.ui.cropMode;
    if (activeMaskSelect) activeMaskSelect.disabled = !hasImage || state.ui.cropMode;
    if (addMaskBtn) addMaskBtn.disabled = !hasImage || state.ui.cropMode;
    if (deleteMaskBtn) deleteMaskBtn.disabled = !hasImage || state.ui.cropMode || (!activeMaskHasPixels && !activeMaskHasAdjustments);
    maskOverlayBtn.disabled = !hasImage || state.ui.cropMode || !anyMaskPixels();
    maskViewSelect.disabled = !hasImage || state.ui.cropMode || !activeMaskHasPixels || !state.ui.maskOverlayVisible;
    maskPaintBtn.disabled = !hasImage || state.ui.cropMode;
    maskEraseBtn.disabled = !hasImage || state.ui.cropMode;
    invertMaskBtn.disabled = !hasImage || state.ui.cropMode || !activeMaskHasPixels;
    resetAdjustmentsBtn.disabled = !hasImage || !Object.values(state.document.adjustments).some(v => v !== 0) || state.ui.cropMode || state.ui.maskMode;
    resetMaskAdjustmentsBtn.disabled = !hasImage || !activeMaskHasAdjustments || state.ui.cropMode;
    if (adjustPresetSelect) adjustPresetSelect.disabled = !hasImage || state.ui.cropMode || state.ui.maskMode;
    if (adjustPresetAmountRange) adjustPresetAmountRange.disabled = !hasImage || state.ui.cropMode || state.ui.maskMode || !ADJUST_PRESET_LABELS[state.ui.adjustPresetKey || "none"] || (state.ui.adjustPresetKey || "none") === "none";
    if (applyAdjustPresetBtn) applyAdjustPresetBtn.disabled = !hasImage || state.ui.cropMode || state.ui.maskMode || (state.ui.adjustPresetKey || "none") === "none";
    if (resetAdjustPresetBtn) resetAdjustPresetBtn.disabled = state.ui.cropMode || state.ui.maskMode;
    if (filterPresetSelect) filterPresetSelect.disabled = !hasImage || state.ui.cropMode || state.ui.maskMode;
    if (filterIntensityRange) filterIntensityRange.disabled = !hasImage || state.ui.cropMode || state.ui.maskMode || ((state.document.filterLayer && state.document.filterLayer.preset) || "none") === "none";
    if (resetFilterBtn) resetFilterBtn.disabled = !hasImage || !hasActiveFilterLayer() || state.ui.cropMode || state.ui.maskMode;
    fitBtn.disabled = !hasImage || state.ui.cropMode;
    actualSizeBtn.disabled = !hasImage || state.ui.cropMode;
    beforeAfterBtn.disabled = !hasImage || state.ui.cropMode;
    zoomRange.disabled = !hasImage || state.ui.cropMode;
    undoBtn.disabled = state.history.undoStack.length === 0;
    redoBtn.disabled = state.history.redoStack.length === 0;

    if (!state.source.image) {
      status.innerHTML = `<div class="card"><div class="title">Ready</div><div>Import an image, or open a saved .pedit project.</div></div>`;
      statusText.textContent = "Ready";
      return;
    }

    const crop = state.ui.cropMode && state.ui.pendingCrop ? state.ui.pendingCrop : getActiveCropRect();
    const drawWidth = Math.round(crop.width * getDisplayScale());
    const drawHeight = Math.round(crop.height * getDisplayScale());
    const a = state.document.adjustments;
    const activeLabel = getMaskLabel(getActiveMaskIndex());
    const filledCount = state.document.masks.filter((mask, index) => !!(getRuntimeMaskCanvas(index) || mask.dataUrl)).length;
    status.innerHTML = `
      <div class="card"><div class="title">Loaded image</div><div class="row"><span>Name</span><strong>${escapeHtml(state.source.name)}</strong></div><div class="row"><span>Pixels</span><strong>${state.source.width} × ${state.source.height}</strong></div><div class="row"><span>Preview size</span><strong>${drawWidth} × ${drawHeight}</strong></div></div>
      <div class="card"><div class="title">Geometry</div><div class="row"><span>Rotation</span><strong>${getRotationNormalized() * 90}°</strong></div><div class="row"><span>Straighten</span><strong>${Number(state.document.geometry.straightenDegrees || 0).toFixed(1)}°</strong></div><div class="row"><span>Flip H / V</span><strong>${state.document.geometry.flipX ? "On" : "Off"} / ${state.document.geometry.flipY ? "On" : "Off"}</strong></div></div>
      <div class="card"><div class="title">Masks</div><div class="row"><span>Active</span><strong>${escapeHtml(activeLabel)}</strong></div><div class="row"><span>Masks with paint</span><strong>${filledCount}/3</strong></div><div class="row"><span>Edit mask</span><strong>${state.ui.maskMode ? "On" : "Off"}</strong></div><div class="row"><span>Overlay</span><strong>${state.ui.maskOverlayVisible ? "On" : "Off"}</strong></div><div class="row"><span>Overlay view</span><strong>${state.ui.maskViewMode === "bw" ? "Black/White mask" : (state.ui.maskViewMode === "result" ? "Result only" : "Overlay")}</strong></div></div>
      <div class="card"><div class="title">Adjustments</div><div class="row"><span>Exposure</span><strong>${a.exposure.toFixed(2)}</strong></div><div class="row"><span>Contrast</span><strong>${a.contrast.toFixed(2)}</strong></div><div class="row"><span>Blur</span><strong>${a.blur.toFixed(2)}</strong></div><div class="row"><span>Sharpen</span><strong>${a.sharpen.toFixed(2)}</strong></div><div class="row"><span>Vignette</span><strong>${a.vignette.toFixed(2)}</strong></div><div class="row"><span>Filter</span><strong>${FILTER_PRESET_LABELS[getFilterLayerConfig().preset] || "None"}</strong></div><div class="row"><span>Filter intensity</span><strong>${getFilterLayerConfig().intensity.toFixed(2)}</strong></div><div class="row"><span>Preview mode</span><strong>${state.ui.isAdjustDragging ? "Fast preview" : "Full quality"}</strong></div></div>
      <div class="card"><div class="title">View</div><div class="row"><span>Zoom</span><strong>${Math.round(state.document.view.zoomPercent || 100)}%</strong></div><div class="row"><span>Pan</span><strong>${Math.round(state.document.view.panX || 0)}, ${Math.round(state.document.view.panY || 0)}</strong></div><div class="row"><span>Compare</span><strong>${isSplitViewActive() ? `Split ${(state.ui.splitPosition * 100).toFixed(0)}%` : (isShowingOriginal() ? "Original" : "Edited")}</strong></div></div>`;
    statusText.textContent = state.ui.cropMode ? "Crop mode" : (state.ui.maskMode ? `Edit ${activeLabel}` : ((state.ui.maskOverlayVisible && activeMaskHasPixels) ? `Mask preview: ${activeLabel}` : "Loaded"));
  }

  let renderQueued = false;
  let exportEstimateTimer = null;
  let exportEstimateToken = 0;
  function queueRender() {
    if (renderQueued) return;
    renderQueued = true;
    requestAnimationFrame(function () {
      renderQueued = false;
      renderAll();
      statusText.textContent = `Preset applied: ${ADJUST_PRESET_LABELS[presetKey] || "Preset"}`;
    });
  }

  function renderAll() {
    renderCanvas();
    renderStatus();
  }

  importBtn.addEventListener("click", function () { fileInput.click(); });
  openProjectBtn.addEventListener("click", function () { projectFileInput.click(); });
  openPresetBtn.addEventListener("click", function () { presetFileInput.click(); });

  saveProjectBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    const filename = askProjectDownloadName();
    if (!filename) return;
    const payload = buildProjectPayload();
    downloadTextFile(filename, JSON.stringify(payload, null, 2), "application/json");
  });

  savePresetBtn.addEventListener("click", function () {
    if (state.ui.cropMode || state.ui.maskMode) return;
    const filename = askPresetDownloadName();
    if (!filename) return;
    const payload = buildPresetPayload();
    downloadTextFile(filename, JSON.stringify(payload, null, 2), "application/json");
  });


  function applySelectedAdjustPresetLive(pushHistory, options = {}) {
    if (!state.source.image || state.ui.cropMode || state.ui.maskMode) return;
    const presetKey = ADJUST_PRESET_LABELS[state.ui.adjustPresetKey] ? state.ui.adjustPresetKey : "none";
    if (presetKey === "none") return;
    const fastPreview = !!options.fastPreview;
    if (!state.ui.adjustPresetBaseAdjustments) state.ui.adjustPresetBaseAdjustments = snapshotAdjustmentsOnly();
    if (pushHistory) pushUndoSnapshot();
    applyAdjustPreset(presetKey, state.ui.adjustPresetAmount);
    invalidateRenderCache();
    if (fastPreview) {
      if (adjustPresetAmountValue) adjustPresetAmountValue.textContent = clamp(Number(state.ui.adjustPresetAmount ?? 1), 0, 1.5).toFixed(2);
      queueAdjustmentPreviewRender();
    } else {
      syncControls();
      renderAll();
    }
    if (statusText) statusText.textContent = `Preset preview: ${ADJUST_PRESET_LABELS[presetKey] || "Preset"}`;
  }

  function queueAdjustPresetPreview(pushHistory, options = {}) {
    if (state.ui.adjustPresetFramePending) return;
    state.ui.adjustPresetFramePending = true;
    requestAnimationFrame(function () {
      state.ui.adjustPresetFramePending = false;
      applySelectedAdjustPresetLive(pushHistory, options);
    });
  }

  if (adjustPresetSelect) {
    adjustPresetSelect.addEventListener("change", function () {
      const nextKey = ADJUST_PRESET_LABELS[adjustPresetSelect.value] ? adjustPresetSelect.value : "none";
      const prevKey = state.ui.adjustPresetKey || "none";
      if (nextKey === "none") {
        const restored = restoreAdjustPresetBaseIfPresent();
        state.ui.adjustPresetKey = "none";
        state.ui.adjustPresetAmount = 1;
        clearAdjustPresetPreviewState();
        invalidateRenderCache();
        syncControls();
        renderAll();
        if (statusText) statusText.textContent = restored ? "Preset preview cleared" : "Preset choice reset";
        return;
      }
      if (prevKey === "none") state.ui.adjustPresetBaseAdjustments = snapshotAdjustmentsOnly();
      state.ui.adjustPresetKey = nextKey;
      queueAdjustPresetPreview(true);
    });
  }

  if (adjustPresetAmountRange) {
    adjustPresetAmountRange.addEventListener("pointerdown", function () {
      if (!state.source.image || state.ui.cropMode || state.ui.maskMode || (state.ui.adjustPresetKey || "none") === "none") return;
      beginFastPreview("adjust-preset");
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
    });
    adjustPresetAmountRange.addEventListener("input", function () {
      state.ui.adjustPresetAmount = clamp(Number(adjustPresetAmountRange.value || 1), 0, 1.5);
      if ((state.ui.adjustPresetKey || "none") === "none") {
        syncControls();
        return;
      }
      beginFastPreview("adjust-preset");
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
      queueAdjustPresetPreview(false, { fastPreview: true });
    });
    adjustPresetAmountRange.addEventListener("change", function () {
      if ((state.ui.adjustPresetKey || "none") === "none") {
        state.ui.isAdjustDragging = false;
        state.ui.activeAdjustmentKey = "";
        return;
      }
      if (state.runtime.adjustDragReleaseTimer) {
        clearTimeout(state.runtime.adjustDragReleaseTimer);
        state.runtime.adjustDragReleaseTimer = 0;
      }
      state.ui.isAdjustDragging = false;
      state.ui.activeAdjustmentKey = "";
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
      applySelectedAdjustPresetLive(false, { fastPreview: false });
    });
  }

  if (applyAdjustPresetBtn) {
    applyAdjustPresetBtn.hidden = true;
    applyAdjustPresetBtn.style.display = "none";
    applyAdjustPresetBtn.disabled = true;
  }

  if (resetAdjustPresetBtn) {
    resetAdjustPresetBtn.addEventListener("click", function () {
      const restored = restoreAdjustPresetBaseIfPresent();
      state.ui.adjustPresetKey = "none";
      state.ui.adjustPresetAmount = 1;
      clearAdjustPresetPreviewState();
      invalidateRenderCache();
      syncControls();
      renderAll();
      if (statusText) statusText.textContent = restored ? "Preset preview reset" : "Preset choice reset";
    });
  }

  if (filterPresetSelect) {
    filterPresetSelect.addEventListener("change", function () {
      if (!state.source.image) return;
      pushUndoSnapshot();
      state.document.filterLayer = Object.assign(getDefaultFilterLayer(), state.document.filterLayer || {});
      state.document.filterLayer.preset = FILTER_PRESET_LABELS[filterPresetSelect.value] ? filterPresetSelect.value : "none";
      if (state.document.filterLayer.preset === "none") state.document.filterLayer.intensity = clamp(Number(state.document.filterLayer.intensity ?? 0.65), 0, 1);
      invalidateRenderCache();
      syncControls();
      renderAll();
    });
  }

  if (filterIntensityRange) {
    const rememberFilterIntensityStart = function () {
      filterIntensityRange.dataset.startValue = String((state.document.filterLayer && state.document.filterLayer.intensity) ?? 0.65);
    };
    filterIntensityRange.addEventListener("pointerdown", rememberFilterIntensityStart);
    filterIntensityRange.addEventListener("focus", rememberFilterIntensityStart);
    filterIntensityRange.addEventListener("input", function () {
      if (!state.source.image) return;
      state.document.filterLayer = Object.assign(getDefaultFilterLayer(), state.document.filterLayer || {});
      state.document.filterLayer.intensity = clamp(Number(filterIntensityRange.value || 0), 0, 1);
      syncControls();
      queueRender();
    });
    filterIntensityRange.addEventListener("change", function () {
      if (!state.source.image) return;
      const startValue = clamp(Number(filterIntensityRange.dataset.startValue ?? ((state.document.filterLayer && state.document.filterLayer.intensity) ?? 0.65)), 0, 1);
      const current = clamp(Number(filterIntensityRange.value || 0), 0, 1);
      if (Math.abs(current - startValue) > 0.0001) {
        const snapshot = snapshotDocument();
        snapshot.filterLayer = Object.assign(getDefaultFilterLayer(), snapshot.filterLayer || {});
        snapshot.filterLayer.intensity = startValue;
        state.history.undoStack.push(snapshot);
        state.history.redoStack = [];
      }
      state.document.filterLayer = Object.assign(getDefaultFilterLayer(), state.document.filterLayer || {});
      state.document.filterLayer.intensity = current;
      invalidateRenderCache();
      renderAll();
    });
  }

  if (resetFilterBtn) {
    resetFilterBtn.addEventListener("click", function () {
      if (!state.source.image || !hasActiveFilterLayer()) return;
      pushUndoSnapshot();
      state.document.filterLayer = getDefaultFilterLayer();
      invalidateRenderCache();
      syncControls();
      renderAll();
    });
  }

  if (exportFormatSelect) {
    exportFormatSelect.addEventListener("change", function () {
      syncControls();
      renderStatus();
    });
  }
  if (exportScaleSelect) {
    exportScaleSelect.addEventListener("change", function () {
      syncControls();
      renderStatus();
    });
  }
  if (exportQualityRange) {
    exportQualityRange.addEventListener("input", function () {
      syncControls();
    });
  }
  if (exportImageBtn) {
    exportImageBtn.addEventListener("click", async function () {
      try {
        await exportEditedImage();
      } catch (err) {
        statusText.textContent = "Export failed";
        status.innerHTML = `<div class="card"><div class="title">Export failed</div><div>${escapeHtml(err && err.message ? err.message : "Unknown error")}</div></div>`;
      }
    });
  }

  if (exportFilenameInput) {
    exportFilenameInput.addEventListener("blur", function () {
      exportFilenameInput.value = getExportBaseFilename();
    });
  }

  fileInput.addEventListener("change", async function (event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    try {
      statusText.textContent = "Loading...";
      await importFile(file);
    } catch (err) {
      statusText.textContent = "Import failed";
      status.innerHTML = `<div class="card"><div class="title">Import failed</div><div>${escapeHtml(err && err.message ? err.message : "Unknown error")}</div><div>Type: ${escapeHtml(file.type || "unknown")}</div><div>Name: ${escapeHtml(file.name || "unknown")}</div></div>`;
    } finally {
      fileInput.value = "";
    }
  });

  projectFileInput.addEventListener("change", async function (event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    try {
      statusText.textContent = "Opening project...";
      await openProjectFile(file);
    } catch (err) {
      statusText.textContent = "Open project failed";
      status.innerHTML = `<div class="card"><div class="title">Open project failed</div><div>${escapeHtml(err && err.message ? err.message : "Unknown error")}</div><div>Name: ${escapeHtml(file.name || "unknown")}</div></div>`;
    } finally {
      projectFileInput.value = "";
    }
  });

  presetFileInput.addEventListener("change", async function (event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    try {
      statusText.textContent = "Opening preset...";
      await openPresetFile(file);
    } catch (err) {
      statusText.textContent = "Open preset failed";
      status.innerHTML = `<div class="card"><div class="title">Open preset failed</div><div>${escapeHtml(err && err.message ? err.message : "Unknown error")}</div><div>Name: ${escapeHtml(file.name || "unknown")}</div></div>`;
    } finally {
      presetFileInput.value = "";
    }
  });

  rotateLeftBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    pushUndoSnapshot();
    state.document.geometry.rotationQuarterTurns -= 1;
    invalidateRenderCache();
    fitView();
    renderAll();
  });

  rotateRightBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    pushUndoSnapshot();
    state.document.geometry.rotationQuarterTurns += 1;
    invalidateRenderCache();
    fitView();
    renderAll();
  });

  flipHorizontalBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    pushUndoSnapshot();
    state.document.geometry.flipX = !state.document.geometry.flipX;
    renderAll();
  });

  flipVerticalBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    pushUndoSnapshot();
    state.document.geometry.flipY = !state.document.geometry.flipY;
    renderAll();
  });

  let straightenDragStart = null;
  straightenRange.addEventListener("pointerdown", function () {
    if (!state.source.image || state.ui.cropMode) return;
    straightenDragStart = snapshotDocument();
  });

  straightenRange.addEventListener("input", function () {
    if (!state.source.image || state.ui.cropMode) return;
    state.document.geometry.straightenDegrees = Number(straightenRange.value);
    clampPanToBounds();
    syncControls();
    queueRender();
  });

  straightenRange.addEventListener("change", function () {
    if (!state.source.image || state.ui.cropMode) return;
    if (!straightenDragStart) straightenDragStart = snapshotDocument();
    const before = Number(straightenDragStart.geometry.straightenDegrees || 0);
    const after = Number(state.document.geometry.straightenDegrees || 0);
    if (before !== after) {
      state.history.undoStack.push(straightenDragStart);
      if (state.history.undoStack.length > 100) state.history.undoStack.shift();
      state.history.redoStack = [];
      fitView();
    }
    straightenDragStart = null;
    renderAll();
  });

  resetGeometryBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    if (state.document.geometry.rotationQuarterTurns === 0 && !state.document.geometry.flipX && !state.document.geometry.flipY && Number(state.document.geometry.straightenDegrees || 0) === 0) return;
    pushUndoSnapshot();
    state.document.geometry.rotationQuarterTurns = 0;
    state.document.geometry.straightenDegrees = 0;
    state.document.geometry.flipX = false;
    state.document.geometry.flipY = false;
    invalidateRenderCache();
    fitView();
    renderAll();
  });

  let adjustRenderFrame = 0;

  function queueAdjustmentPreviewRender() {
    if (adjustRenderFrame) return;
    adjustRenderFrame = requestAnimationFrame(function () {
      adjustRenderFrame = 0;
      renderCanvas();
      renderStatus();
    });
  }

  function beginFastPreview(activeKey = "") {
    state.ui.isAdjustDragging = true;
    state.ui.activeAdjustmentKey = activeKey || state.ui.activeAdjustmentKey || "";
    if (state.runtime.adjustDragReleaseTimer) {
      clearTimeout(state.runtime.adjustDragReleaseTimer);
      state.runtime.adjustDragReleaseTimer = 0;
    }
  }

  function clearFastPreviewSoon(delay = 120) {
    if (state.runtime.adjustDragReleaseTimer) clearTimeout(state.runtime.adjustDragReleaseTimer);
    state.runtime.adjustDragReleaseTimer = setTimeout(function () {
      state.runtime.adjustDragReleaseTimer = 0;
      state.ui.isAdjustDragging = false;
      state.ui.activeAdjustmentKey = "";
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
      renderAll();
    }, delay);
  }

  function registerAdjustmentSlider(key, rangeEl) {
    let dragStart = null;
    rangeEl.addEventListener("pointerdown", function () {
      if (!state.source.image || state.ui.cropMode) return;
      dragStart = snapshotDocument();
      beginFastPreview(key);
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
    });

    rangeEl.addEventListener("input", function () {
      if (!state.source.image || state.ui.cropMode) return;
      beginFastPreview(key);
      state.document.adjustments[key] = Number(rangeEl.value);
      syncControls();
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
      queueAdjustmentPreviewRender();
    });

    rangeEl.addEventListener("change", function () {
      if (!state.source.image || state.ui.cropMode) return;
      if (!dragStart) dragStart = snapshotDocument();
      const changed = dragStart.adjustments[key] !== state.document.adjustments[key];
      if (changed) {
        state.history.undoStack.push(dragStart);
        if (state.history.undoStack.length > 100) state.history.undoStack.shift();
        state.history.redoStack = [];
      }
      dragStart = null;
      if (state.runtime.adjustDragReleaseTimer) {
        clearTimeout(state.runtime.adjustDragReleaseTimer);
        state.runtime.adjustDragReleaseTimer = 0;
      }
      state.ui.isAdjustDragging = false;
      state.ui.activeAdjustmentKey = "";
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
      renderAll();
    });
  }

  adjustmentControls.forEach(([key, rangeEl]) => registerAdjustmentSlider(key, rangeEl));

  function switchActiveMask(index) {
    ensureMaskStateStructure();
    state.document.activeMaskIndex = clamp(Number(index || 0), 0, 2);
    state.ui.maskStroke = null;
    state.ui.maskHoverPos = null;
    hydrateMaskCanvas(getActiveMaskIndex()).finally(function () {
      invalidateRenderCache();
      syncControls();
      renderAll();
    });
    invalidateRenderCache();
    syncControls();
    renderAll();
  }

  function addMaskSlot() {
    ensureMaskStateStructure();
    for (let i = 0; i < 3; i++) {
      const mask = getMaskAt(i);
      if (!maskSlotHasVisiblePixels(i) && !hasVisibleMaskAdjustments(mask.localAdjustments || {})) {
        switchActiveMask(i);
        return;
      }
    }
    window.alert("All 3 mask slots are already in use.");
  }

  function deleteActiveMask() {
    if (!state.source.image || state.ui.cropMode) return;
    pushUndoSnapshot();
    const idx = getActiveMaskIndex();
    state.document.masks[idx] = createDefaultMask(`Mask ${idx + 1}`);
    setRuntimeMaskCanvas(idx, null);
    markMaskDirty(idx);
    invalidateRenderCache();
    syncControls();
    renderAll();
  }

  cropAspectSelect.addEventListener("change", function () {
    setCropAspect(cropAspectSelect.value);
  });
  function endActiveMaskStroke(event, options = {}) {
    const stroke = state.ui.maskStroke;
    if (!stroke) return false;
    if (event && stroke.pointerId != null && event.pointerId != null && stroke.pointerId !== event.pointerId) return false;
    const startSnapshot = stroke.startSnapshot || null;
    const strokeMaskIndex = clamp(Number(stroke.maskIndex != null ? stroke.maskIndex : getActiveMaskIndex()), 0, 2);
    const hadCanvas = !!getRuntimeMaskCanvas(strokeMaskIndex);
    if (hadCanvas && state.ui.maskBrushMode === "erase") pruneMaskCanvas(strokeMaskIndex, 8);
    if (hadCanvas) syncMaskDataUrl(strokeMaskIndex);
    const startMask = startSnapshot && Array.isArray(startSnapshot.masks) ? startSnapshot.masks[strokeMaskIndex] : null;
    const currentMask = getMaskAt(strokeMaskIndex);
    const changed = !startMask || (startMask.dataUrl || "") !== (currentMask.dataUrl || "");
    if (!options.skipHistory && changed && startSnapshot) {
      state.history.undoStack.push(startSnapshot);
      if (state.history.undoStack.length > 100) state.history.undoStack.shift();
      state.history.redoStack = [];
    }
    state.ui.maskStroke = null;
    state.ui.maskHoverPos = null;
    if (event && canvas.releasePointerCapture) {
      try { canvas.releasePointerCapture(event.pointerId); } catch {}
    }
    invalidateRenderCache();
    renderAll();
    return true;
  }

  function toggleMaskMode() {
    if (!state.source.image || state.ui.cropMode) return;
    if (state.ui.maskMode && state.ui.maskStroke) endActiveMaskStroke(null);
    state.ui.maskMode = !state.ui.maskMode;
    state.ui.maskHoverPos = null;
    if (state.ui.maskMode) {
      hydrateMaskCanvas(getActiveMaskIndex()).finally(function () {
        syncControls();
        renderAll();
      });
    }
    syncControls();
    renderAll();
  }

  function toggleMaskOverlay() {
    if (!state.source.image || state.ui.cropMode || !anyMaskPixels()) return;
    state.ui.maskOverlayVisible = !state.ui.maskOverlayVisible;
    syncControls();
    renderAll();
  }

  function setMaskViewMode(mode) {
    state.ui.maskViewMode = ["overlay", "bw", "result"].includes(mode) ? mode : "overlay";
    syncControls();
    renderAll();
  }

  function setMaskBrushMode(mode) {
    state.ui.maskBrushMode = mode;
    syncControls();
    renderStatus();
  }

  function invertMask() {
    if (!anyMaskPixels()) return;
    pushUndoSnapshot();
    const maskCanvas = ensureMaskCanvas();
    const mctx = maskCanvas.getContext("2d", { willReadFrequently: true });
    const imageData = mctx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) data[i + 3] = 255 - data[i + 3];
    mctx.putImageData(imageData, 0, 0);
    syncMaskDataUrl();
    invalidateRenderCache();
    renderAll();
  }

  function registerMaskAdjustmentSlider(key, rangeEl, valueEl) {
    let dragStart = null;
    let dragMaskIndex = null;

    function getLocalMaskAdjustmentKey() {
      return `mask-${key}`;
    }

    function getSelectedMaskIndexForSlider() {
      if (activeMaskSelect && activeMaskSelect.value !== "") return clamp(Number(activeMaskSelect.value || 0), 0, 2);
      return getActiveMaskIndex();
    }

    function getGestureMask(indexOverride) {
      const index = clamp(Number(indexOverride != null ? indexOverride : getSelectedMaskIndexForSlider()), 0, 2);
      return { index, mask: getMaskAt(index) };
    }

    function beginMaskSliderGesture() {
      if (!state.source.image || state.ui.cropMode) return null;
      const ctx = getGestureMask();
      if (!dragStart) dragStart = snapshotDocument();
      if (dragMaskIndex == null) dragMaskIndex = ctx.index;
      beginFastPreview(getLocalMaskAdjustmentKey());
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
      return ctx;
    }

    function endMaskSliderGesture() {
      if (state.runtime.adjustDragReleaseTimer) {
        clearTimeout(state.runtime.adjustDragReleaseTimer);
        state.runtime.adjustDragReleaseTimer = 0;
      }
      state.ui.isAdjustDragging = false;
      state.ui.activeAdjustmentKey = "";
      state.cache.dragRenderKey = "";
      state.cache.dragRenderCanvas = null;
      dragMaskIndex = null;
    }

    rangeEl.addEventListener("pointerdown", beginMaskSliderGesture);
    rangeEl.addEventListener("mousedown", beginMaskSliderGesture);
    rangeEl.addEventListener("touchstart", beginMaskSliderGesture, { passive: true });
    rangeEl.addEventListener("input", function () {
      if (!state.source.image || state.ui.cropMode) return;
      const ctx = beginMaskSliderGesture() || getGestureMask(dragMaskIndex);
      ctx.mask.localAdjustments[key] = Number(rangeEl.value);
      if (ctx.index === getActiveMaskIndex()) updateMaskAdjustmentControlValue(key, rangeEl, valueEl);
      invalidateRenderCache();
      queueAdjustmentPreviewRender();
    });
    rangeEl.addEventListener("change", function () {
      if (!state.source.image || state.ui.cropMode) return;
      const ctx = beginMaskSliderGesture() || getGestureMask(dragMaskIndex);
      const beforeMask = ((dragStart && dragStart.masks) || [])[ctx.index] || { localAdjustments: {} };
      const beforeValue = Number((beforeMask.localAdjustments || {})[key] || 0);
      const afterValue = Number(ctx.mask.localAdjustments[key] || 0);
      if (beforeValue !== afterValue && dragStart) {
        state.history.undoStack.push(dragStart);
        if (state.history.undoStack.length > 100) state.history.undoStack.shift();
        state.history.redoStack = [];
      }
      dragStart = null;
      if (ctx.index === getActiveMaskIndex()) updateMaskAdjustmentControlValue(key, rangeEl, valueEl);
      invalidateRenderCache();
      endMaskSliderGesture();
      renderAll();
    });
  }

  maskAdjustmentControls.forEach(([key, rangeEl, valueEl]) => registerMaskAdjustmentSlider(key, rangeEl, valueEl));
  maskBrushSizeRange.addEventListener("input", function () { state.ui.maskBrushSize = Number(maskBrushSizeRange.value); syncControls(); queueRender(); });
  maskBrushFeatherRange.addEventListener("input", function () { state.ui.maskBrushFeather = Number(maskBrushFeatherRange.value); syncControls(); queueRender(); });
  maskModeBtn.addEventListener("click", toggleMaskMode);
  if (activeMaskSelect) activeMaskSelect.addEventListener("change", function () { switchActiveMask(activeMaskSelect.value); });
  if (addMaskBtn) addMaskBtn.addEventListener("click", addMaskSlot);
  if (deleteMaskBtn) deleteMaskBtn.addEventListener("click", deleteActiveMask);
  maskOverlayBtn.addEventListener("click", toggleMaskOverlay);
  maskViewSelect.addEventListener("change", function () { setMaskViewMode(maskViewSelect.value); });
  maskPaintBtn.addEventListener("click", function () { setMaskBrushMode("paint"); });
  maskEraseBtn.addEventListener("click", function () { setMaskBrushMode("erase"); });
  invertMaskBtn.addEventListener("click", invertMask);

  cropModeBtn.addEventListener("click", enterCropMode);
  applyCropBtn.addEventListener("click", applyCrop);
  cancelCropBtn.addEventListener("click", cancelCropMode);
  resetCropBtn.addEventListener("click", resetCrop);

  resetAdjustmentsBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode || state.ui.maskMode || !hasNonDefaultAdjustments()) return;
    pushUndoSnapshot();
    resetAdjustments();
    invalidateRenderCache();
    renderAll();
  });

  resetMaskAdjustmentsBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode || !anyNonDefaultMaskAdjustments()) return;
    pushUndoSnapshot();
    resetMaskAdjustments();
    invalidateRenderCache();
    renderAll();
  });

  fitBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    pushUndoSnapshot();
    fitView();
    syncControls();
    renderAll();
  });

  actualSizeBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    pushUndoSnapshot();
    setZoomPercent(Math.max(100, Math.round((1 / Math.max(0.0001, state.document.view.baseScale)) * 100)), true);
    renderAll();
  });

  beforeAfterBtn.addEventListener("click", function () {
    if (!state.source.image || state.ui.cropMode) return;
    state.ui.splitView = !state.ui.splitView;
    state.ui.showOriginal = false;
    state.ui.showOriginalMomentary = false;
    syncControls();
    renderAll();
  });

  zoomRange.addEventListener("input", function () {
    if (!state.source.image || state.ui.cropMode) return;
    setZoomPercent(Number(zoomRange.value));
    renderAll();
  });

  zoomRange.addEventListener("change", function () {
    if (!state.source.image || state.ui.cropMode) return;
    clampPanToBounds();
    renderAll();
  });

  undoBtn.addEventListener("click", undo);
  redoBtn.addEventListener("click", redo);

  canvas.addEventListener("pointerdown", function (event) {
    const pos = getPointerCanvasPos(event);
    if (isSplitViewActive()) {
      const splitX = getSplitScreenX();
      if (Math.abs(pos.x - splitX) <= 26) {
        state.ui.splitDrag = { pointerId: event.pointerId };
        if (canvas.setPointerCapture) { try { canvas.setPointerCapture(event.pointerId); } catch {} }
        return;
      }
    }
    if (!state.ui.maskMode && !state.ui.cropMode && state.source.image && getZoomScale() > 1.001) {
      state.uiView.isPanning = true;
      state.uiView.panPointerId = event.pointerId;
      state.uiView.panStartX = pos.x;
      state.uiView.panStartY = pos.y;
      state.uiView.panOriginX = Number(state.document.view.panX || 0);
      state.uiView.panOriginY = Number(state.document.view.panY || 0);
      if (canvas.setPointerCapture) { try { canvas.setPointerCapture(event.pointerId); } catch {} }
      return;
    }
    if (state.ui.maskMode) {
      const sourcePos = canvasPosToSourcePos(pos);
      state.ui.maskHoverPos = pos;
      state.ui.maskStroke = { pointerId: event.pointerId, maskIndex: getActiveMaskIndex(), lastSourcePos: sourcePos, lastCanvasPos: pos, startSnapshot: snapshotDocument() };
      if (sourcePos) {
        paintMaskDab(sourcePos);
        invalidateRenderCache();
        renderAll();
      }
      if (canvas.setPointerCapture) { try { canvas.setPointerCapture(event.pointerId); } catch {} }
      return;
    }
    if (!state.ui.cropMode) return;
    const mode = hitTestCrop(pos);
    if (!mode) return;
    state.ui.cropDrag = { mode, startX: pos.x, startY: pos.y, startRect: JSON.parse(JSON.stringify(state.ui.pendingCrop)) };
    if (canvas.setPointerCapture) { try { canvas.setPointerCapture(event.pointerId); } catch {} }
  });

  canvas.addEventListener("pointermove", function (event) {
    const pos = getPointerCanvasPos(event);
    if (state.ui.splitDrag && state.ui.splitDrag.pointerId === event.pointerId) {
      state.ui.splitPosition = clamp(pos.x / Math.max(1, state.ui.viewportWidth), 0.02, 0.98);
      syncControls();
      queueRender();
      return;
    }
    if (state.uiView.isPanning) {
      const dx = pos.x - state.uiView.panStartX;
      const dy = pos.y - state.uiView.panStartY;
      state.document.view.panX = state.uiView.panOriginX + dx;
      state.document.view.panY = state.uiView.panOriginY + dy;
      clampPanToBounds();
      syncControls();
      renderAll();
      return;
    }
    if (state.ui.maskMode) {
      if (state.ui.maskStroke) {
        if (state.ui.maskStroke.pointerId != null && event.pointerId !== state.ui.maskStroke.pointerId) return;
        if (typeof event.buttons === "number" && event.buttons === 0) {
          endActiveMaskStroke(event);
          return;
        }
        const sourcePos = canvasPosToSourcePos(pos);
        if (sourcePos && state.ui.maskStroke.lastSourcePos) {
          paintMaskStroke(state.ui.maskStroke.lastSourcePos, sourcePos);
          state.ui.maskStroke.lastSourcePos = sourcePos;
          state.ui.maskStroke.lastCanvasPos = pos;
          state.ui.maskHoverPos = pos;
          invalidateRenderCache();
          queueRender();
        } else {
          if (!sourcePos) state.ui.maskStroke.lastSourcePos = null;
          state.ui.maskStroke.lastCanvasPos = pos;
          state.ui.maskHoverPos = pos;
          queueRender();
        }
      } else {
        state.ui.maskHoverPos = pos;
        queueRender();
      }
      return;
    }
    if (!state.ui.cropMode || !state.ui.cropDrag) return;
    updatePendingCropFromDrag(pos);
    renderAll();
  });

  function endMaskOrCropDrag(event) {
    if (state.ui.splitDrag && (!event || state.ui.splitDrag.pointerId === event.pointerId)) {
      if (event && canvas.releasePointerCapture) { try { canvas.releasePointerCapture(event.pointerId); } catch {} }
      state.ui.splitDrag = null;
      renderAll();
      return;
    }
    if (state.uiView.isPanning) {
      if (!event || state.uiView.panPointerId == null || state.uiView.panPointerId === event.pointerId) {
        if (event && canvas.releasePointerCapture) { try { canvas.releasePointerCapture(event.pointerId); } catch {} }
        state.uiView.isPanning = false;
        state.uiView.panPointerId = null;
        clampPanToBounds();
        renderAll();
        return;
      }
    }
    if (endActiveMaskStroke(event)) return;
    state.ui.cropDrag = null;
  }
  canvas.addEventListener("pointerup", endMaskOrCropDrag);
  canvas.addEventListener("pointercancel", endMaskOrCropDrag);
  canvas.addEventListener("lostpointercapture", endMaskOrCropDrag);
  canvas.addEventListener("pointerleave", function (event) {
    if (state.ui.maskStroke && typeof event.buttons === "number" && event.buttons === 0) endMaskOrCropDrag(event);
  });
  window.addEventListener("blur", function () {
    if (state.ui.maskStroke) endActiveMaskStroke(null);
  });

  window.addEventListener("keydown", function (event) {
    if (event.repeat) return;
    if (event.code !== "Space") return;
    const tag = document.activeElement && document.activeElement.tagName ? document.activeElement.tagName.toLowerCase() : "";
    if (tag === "input" || tag === "select" || tag === "textarea" || state.ui.cropMode || !state.source.image || state.ui.splitView) return;
    event.preventDefault();
    setShowOriginalMomentary(true);
  });

  window.addEventListener("keyup", function (event) {
    if (event.code !== "Space") return;
    if (!state.ui.showOriginalMomentary) return;
    event.preventDefault();
    state.ui.showOriginalMomentary = false;
    renderAll();
  });

  window.addEventListener("resize", updateViewport);

  stage.addEventListener("dblclick", function () {
    if (!state.source.image || state.ui.cropMode) return;
    fitView();
    syncControls();
    renderAll();
  });

  syncControls();
  renderAll();
  updateViewport();
})();
