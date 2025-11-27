// Quebec Forest Fire Burn Viewer — Map logic

// 1. Initialize map, centered on Quebec
const map = L.map('map', { scrollWheelZoom: true }).setView([48.5, -71.5], 6);

// Single basemap (ESRI World Imagery)
const esriImagery = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri'
  }
).addTo(map);

// 2. PRE-GENERATED TILES
// For now, define them manually. Later you can generate this list from Python.
// bounds = [[lat_min, lon_min], [lat_max, lon_max]]

const PRESET_GROUPS = [
  {
    name: "2022–2023 strip",
    tiles: [
      {
        "id": "P017R015_20220622_20231017",
        "label": "Path 017 Row 015 (20220622 vs 20231017)",
        "url": "assets/batch_tiles/delta_nbr_P017R015.png",
        "bounds": [
          [
            64.45358231348361,
            -70.47596139775203
          ],
          [
            66.66239192535278,
            -64.96400865783008
          ]
        ],
        "preDate": "2022-06-22",
        "postDate": "2023-10-17",
        "percentChanged": 1.6233000982643335
      },
      {
        "id": "P017R016_20220621_20231008",
        "label": "Path 017 Row 016 (20220621 vs 20231008)",
        "url": "assets/batch_tiles/delta_nbr_P017R016.png",
        "bounds": [
          [
            61.642450523362676,
            -74.06334280729966
          ],
          [
            64.01941822651042,
            -69.31067099111203
          ]
        ],
        "preDate": "2022-06-21",
        "postDate": "2023-10-08",
        "percentChanged": 2.6595412237377247
      },
      {
        "id": "P017R017_20220621_20230924",
        "label": "Path 017 Row 017 (20220621 vs 20230924)",
        "url": "assets/batch_tiles/delta_nbr_P017R017.png",
        "bounds": [
          [
            61.642450523362676,
            -74.06334280729966
          ],
          [
            64.01941822651042,
            -69.31067099111203
          ]
        ],
        "preDate": "2022-06-21",
        "postDate": "2023-09-24",
        "percentChanged": NaN
      },
      {
        "id": "P017R018_20220613_20230921",
        "label": "Path 017 Row 018 (20220613 vs 20230921)",
        "url": "assets/batch_tiles/delta_nbr_P017R018.png",
        "bounds": [
          [
            60.39481958302447,
            -75.07466650281606
          ],
          [
            62.508126729595986,
            -70.37572637785071
          ]
        ],
        "preDate": "2022-06-13",
        "postDate": "2023-09-21",
        "percentChanged": NaN
      },
      {
        "id": "P017R019_20220613_20230929",
        "label": "Path 017 Row 019 (20220613 vs 20230929)",
        "url": "assets/batch_tiles/delta_nbr_P017R019.png",
        "bounds": [
          [
            58.993455372617966,
            -75.91738792120645
          ],
          [
            61.14646162083876,
            -71.47490985050965
          ]
        ],
        "preDate": "2022-06-13",
        "postDate": "2023-09-29",
        "percentChanged": NaN
      },
      {
        "id": "P017R020_20220613_20230929",
        "label": "Path 017 Row 020 (20220613 vs 20230929)",
        "url": "assets/batch_tiles/delta_nbr_P017R020.png",
        "bounds": [
          [
            57.589458646252055,
            -76.70482199153804
          ],
          [
            59.77587510993793,
            -72.4919709439425
          ]
        ],
        "preDate": "2022-06-13",
        "postDate": "2023-09-29",
        "percentChanged": NaN
      },
      {
        "id": "P017R021_20220613_20230929",
        "label": "Path 017 Row 021 (20220613 vs 20230929)",
        "url": "assets/batch_tiles/delta_nbr_P017R021.png",
        "bounds": [
          [
            56.18083542699742,
            -77.4394565038548
          ],
          [
            58.39733064381791,
            -73.43258507203021
          ]
        ],
        "preDate": "2022-06-13",
        "postDate": "2023-09-29",
        "percentChanged": 0.005500049051855906
      },
      {
        "id": "P017R022_20220601_20231015",
        "label": "Path 017 Row 022 (20220601 vs 20231015)",
        "url": "assets/batch_tiles/delta_nbr_P017R022.png",
        "bounds": [
          [
            53.360591740265306,
            -72.58768125372254
          ],
          [
            55.62022410035092,
            -68.9314840243011
          ]
        ],
        "preDate": "2022-06-01",
        "postDate": "2023-10-15",
        "percentChanged": NaN
      },
      {
        "id": "P017R023_20220601_20231016",
        "label": "Path 017 Row 023 (20220601 vs 20231016)",
        "url": "assets/batch_tiles/delta_nbr_P017R023.png",
        "bounds": [
          [
            51.9449926199231,
            -73.20715492311919
          ],
          [
            54.227081386192815,
            -69.70231264418501
          ]
        ],
        "preDate": "2022-06-01",
        "postDate": "2023-10-16",
        "percentChanged": NaN
      },
      {
        "id": "P017R024_20220623_20231016",
        "label": "Path 017 Row 024 (20220623 vs 20231016)",
        "url": "assets/batch_tiles/delta_nbr_P017R024.png",
        "bounds": [
          [
            50.590002812588565,
            -76.96959729969399
          ],
          [
            52.761172370422656,
            -73.53115373204574
          ]
        ],
        "preDate": "2022-06-23",
        "postDate": "2023-10-16",
        "percentChanged": 0.4373250375905166
      },
      {
        "id": "P017R025_20220623_20231016",
        "label": "Path 017 Row 025 (20220623 vs 20231016)",
        "url": "assets/batch_tiles/delta_nbr_P017R025.png",
        "bounds": [
          [
            49.167745005623004,
            -77.52993525660447
          ],
          [
            51.362388251674005,
            -74.2184123114753
          ]
        ],
        "preDate": "2022-06-23",
        "postDate": "2023-10-16",
        "percentChanged": 2.7716693528560112
      },
      {
        "id": "P017R026_20220623_20231001",
        "label": "Path 017 Row 026 (20220623 vs 20231001)",
        "url": "assets/batch_tiles/delta_nbr_P017R026.png",
        "bounds": [
          [
            47.74299847240343,
            -78.064425247893
          ],
          [
            49.95661289475822,
            -74.86874671940906
          ]
        ],
        "preDate": "2022-06-23",
        "postDate": "2023-10-01",
        "percentChanged": 0.0023518786806901353
      },
      {
        "id": "P017R027_20220623_20230930",
        "label": "Path 017 Row 027 (20220623 vs 20230930)",
        "url": "assets/batch_tiles/delta_nbr_P017R027.png",
        "bounds": [
          [
            46.318780573030125,
            -78.5762543129112
          ],
          [
            48.54970750434361,
            -75.48624997913186
          ]
        ],
        "preDate": "2022-06-23",
        "postDate": "2023-09-30",
        "percentChanged": 0.7798319101163529
      },
      {
        "id": "P017R028_20220623_20230930",
        "label": "Path 017 Row 028 (20220623 vs 20230930)",
        "url": "assets/batch_tiles/delta_nbr_P017R028.png",
        "bounds": [
          [
            46.318780573030125,
            -78.5762543129112
          ],
          [
            48.54970750434361,
            -75.48624997913186
          ]
        ],
        "preDate": "2022-06-23",
        "postDate": "2023-09-30",
        "percentChanged": 0.14668664730119946
      },
      {
        "id": "P017R029_20220623_20230930",
        "label": "Path 017 Row 029 (20220623 vs 20230930)",
        "url": "assets/batch_tiles/delta_nbr_P017R029.png",
        "bounds": [
          [
            42.15190928732031,
            -80.0440052110615
          ],
          [
            44.18720543072206,
            -77.13986510212898
          ]
        ],
        "preDate": "2022-06-23",
        "postDate": "2023-09-30",
        "percentChanged": 0.6325609189046061
      },
      {
        "id": "P017R030_20220623_20230922",
        "label": "Path 017 Row 030 (20220623 vs 20230922)",
        "url": "assets/batch_tiles/delta_nbr_P017R030.png",
        "bounds": [
          [
            42.15190928732031,
            -80.0440052110615
          ],
          [
            44.18720543072206,
            -77.13986510212898
          ]
        ],
        "preDate": "2022-06-23",
        "postDate": "2023-09-22",
        "percentChanged": 0.5065433787595666
      }
    ]
  },
  {
    name: "2022–2023 add-ons",
    tiles: [
      {
        "id": "P015R025_20220715_20230901",
        "label": "Path 015 Row 025 (20220715 vs 20230901)",
        "url": "assets/batch_tiles/delta_nbr_P015R025.png",
        "bounds": [
          [
            49.234577957006906,
            -74.43837933751148
          ],
          [
            51.29105460751917,
            -71.0739584724096
          ]
        ],
        "preDate": "2022-07-15",
        "postDate": "2023-09-01",
        "percentChanged": 0.37476667287530907
      },
      {
        "id": "P015R026_20220715_20230901",
        "label": "Path 015 Row 026 (20220715 vs 20230901)",
        "url": "assets/batch_tiles/delta_nbr_P015R026.png",
        "bounds": [
          [
            47.81091525134761,
            -74.97081517578542
          ],
          [
            49.8888000219215,
            -71.72380131049442
          ]
        ],
        "preDate": "2022-07-15",
        "postDate": "2023-09-01",
        "percentChanged": 0.03619493494843399
      },
      {
        "id": "P016R023_20220715_20230901",
        "label": "Path 016 Row 023 (20220715 vs 20230901)",
        "url": "assets/batch_tiles/delta_nbr_P016R023.png",
        "bounds": [
          [
            52.04436334124006,
            -74.83691208027719
          ],
          [
            54.12164780295728,
            -71.23352298129514
          ]
        ],
        "preDate": "2022-07-15",
        "postDate": "2023-09-01",
        "percentChanged": 3.781955986122586
      },
      {
        "id": "P018R023_20220715_20230901",
        "label": "Path 018 Row 023 (20220715 vs 20230901)",
        "url": "assets/batch_tiles/delta_nbr_P018R023.png",
        "bounds": [
          [
            51.97478799531794,
            -77.85539498072897
          ],
          [
            54.194814135121064,
            -74.3131023474264
          ]
        ],
        "preDate": "2022-07-15",
        "postDate": "2023-09-01",
        "percentChanged": 9.227399722664932
      }
    ]
  },
  {
    name: "2017–2018 test",
    tiles: [
      {
        id: "DELTA_NBR_P017R022_20170601_20180601",
        label: "P017R022 (2017-06-01 → 2018-06-01)",
        url: "/outputs/delta_nbr_p017r022_20170601_20180601.png",
        bounds: [
          [
            53.393540863387805,
            -75.7506401592215
          ],
          [
            55.5878952905581,
            -71.98272730094362
          ]
        ]
      },
      {
        id: "DELTA_NBR_P017R027_20170601_20180601",
        label: "P017R027 (2017-06-01 → 2018-06-01)",
        url: "/outputs/delta_nbr_p017r027_20170601_20180601.png",
        bounds: [
          [
            46.32044098340104,
            -78.66981257067991
          ],
          [
            48.5499031817902,
            -75.41961211190095
          ]
        ]
      },
      {
        id: "DELTA_NBR_P017R028_20170601_20180601",
        label: "P017R028 (2017-06-01 → 2018-06-01)",
        url: "/outputs/delta_nbr_p017r028_20170601_20180601.png",
        bounds: [
          [
            44.891991199819415,
            -79.17543196184306
          ],
          [
            47.139831220272455,
            -75.9875677434451
          ]
        ]
      },
      {
        id: "DELTA_NBR_P017R029_20170601_20180601",
        label: "P017R029 (2017-06-01 → 2018-06-01)",
        url: "/outputs/delta_nbr_p017r029_20170601_20180601.png",
        bounds: [
          [
            43.512426708005606,
            -79.53486093854629
          ],
          [
            45.67639082455029,
            -76.54783957575974
          ]
        ]
      },
      {
        id: "DELTA_NBR_P017R030_20170601_20180601",
        label: "P017R030 (2017-06-01 → 2018-06-01)",
        url: "/outputs/delta_nbr_p017r030_20170601_20180601.png",
        bounds: [
          [
            42.093684617008606,
            -79.99317792715875
          ],
          [
            44.25042111994814,
            -77.08737032632604
          ]
        ]
      }
    ]
  }
  // 2023–2024 group removed for performance
];

// Overlay opacity for pre-generated rasters
const PRESET_OVERLAY_OPACITY = 0.75;

// Keep track of overlay layers + rectangles
const presetGroups = [];
const presetRects = [];

// WRS grid (clipped to Quebec) — expects GeoJSON at this path
const WRS_GRID_URL = 'assets/QcGridGJ.geojson';
const wrsGridGroup = L.layerGroup();       // togglable layer for the grid
const wrsSelection = L.geoJSON(null, {     // highlight of the chosen tile
  style: { color: '#00c2ff', weight: 2, fillOpacity: 0 }
}).addTo(wrsGridGroup);
let wrsFeatures = [];
let lastFeatureClick = 0;
// Keep track of latest API result overlays so we can replace them
let latestApiLayers = [];
const MAX_SELECTED_TILES = 5;

let boundsUnion = null;

function extendBounds(union, b) {
  if (!union) return L.latLngBounds(b);
  return union.extend(b);
}

function buildPresetTiles() {
  boundsUnion = null;
  PRESET_GROUPS.forEach(group => {
    const grpLayer = L.layerGroup();
    group.tiles.forEach(tile => {
      const bounds = tile.bounds;
      const layer = L.imageOverlay(tile.url, bounds, { opacity: PRESET_OVERLAY_OPACITY });

      const rect = L.rectangle(bounds, {
        color: '#ffd166',
        weight: 1,
        fillOpacity: 0
      });

      rect.on('click', () => {
        showTileInfo(tile);
        highlightRect(rect);
      });

      layer.addTo(grpLayer);
      rect.addTo(grpLayer);
      presetRects.push(rect);
      boundsUnion = extendBounds(boundsUnion, bounds);
    });
    presetGroups.push({ name: group.name, layer: grpLayer });
  });

  if (boundsUnion) {
    map.fitBounds(boundsUnion.pad(0.1));
  }
}

buildPresetTiles();

// Show the grid by default
wrsGridGroup.addTo(map);

// Sidebar group toggles
const chkStrip = document.getElementById("chkStrip");
const chkAddons = document.getElementById("chkAddons");
const chkTest = document.getElementById("chkTest");
const chkGrid = document.getElementById("chkGrid");

// Initial visibility: only grid on by default
setGroupVisibility("2022–2023 strip", chkStrip && chkStrip.checked);
setGroupVisibility("2022–2023 add-ons", chkAddons && chkAddons.checked);
setGroupVisibility("2017–2018 test", chkTest && chkTest.checked);

function setGroupVisibility(name, visible) {
  const grp = presetGroups.find(g => g.name === name);
  if (!grp) return;
  if (visible) {
    grp.layer.addTo(map);
  } else {
    map.removeLayer(grp.layer);
  }
}

if (chkStrip) {
  chkStrip.addEventListener("change", e => setGroupVisibility("2022–2023 strip", e.target.checked));
}
if (chkAddons) {
  chkAddons.addEventListener("change", e => setGroupVisibility("2022–2023 add-ons", e.target.checked));
}
if (chkTest) {
  chkTest.addEventListener("change", e => setGroupVisibility("2017–2018 test", e.target.checked));
}
if (chkGrid) {
  chkGrid.addEventListener("change", e => {
    if (e.target.checked) {
      wrsGridGroup.addTo(map);
    } else {
      map.removeLayer(wrsGridGroup);
    }
  });
}

// 5. Tile info UI

const tileInfoDiv = document.getElementById('tileInfo');
let lastHighlighted = null;

function showTileInfo(tile) {
  if (!tileInfoDiv) return;

  const percentText =
    tile.percentChanged == null || !Number.isFinite(tile.percentChanged)
      ? 'Percent changed: (not calculated yet)'
      : `Percent changed: ${tile.percentChanged.toFixed(1)}%`;

  tileInfoDiv.innerHTML = `
    <p><strong>${tile.label}</strong></p>
    <p>Tile ID: <code>${tile.id}</code></p>
    <p>Pre-fire date: ${tile.preDate}</p>
    <p>Post-fire date: ${tile.postDate}</p>
    <p>${percentText}</p>
    <p class="muted">In the future, clicking here could trigger a live API run for this tile + custom dates.</p>
  `;
}

function highlightRect(rect) {
  if (lastHighlighted) {
    lastHighlighted.setStyle({ weight: 1, color: '#ffd166' });
  }
  rect.setStyle({ weight: 3, color: '#ffffff' });
  lastHighlighted = rect;
}

// --- WRS grid loading + selection ---

function propsPath(f) {
  const p = f && f.properties ? f.properties : {};
  return p.PATH || p.path || p.Path || p.wrs_path || p.WRS_PATH || null;
}

function propsRow(f) {
  const p = f && f.properties ? f.properties : {};
  return p.ROW || p.row || p.Row || p.wrs_row || p.WRS_ROW || null;
}

function featureKey(f) {
  const p = propsPath(f);
  const r = propsRow(f);
  return p != null && r != null ? `${p}-${r}` : null;
}

const selectedFeatures = new Map();
// removed per-tile date choices and popup

function baseWrsStyle() {
  return { color: '#ffd166', weight: 0.6, fillOpacity: 0, opacity: 0.7 };
}

fetch(WRS_GRID_URL)
  .then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  })
  .then(data => {
    wrsFeatures = (data && data.features) || [];
    L.geoJSON(data, {
      style: baseWrsStyle,
      onEachFeature: (feature, layer) => {
        layer.on('mouseover', () => {
          layer.setStyle({ color: '#ffffff', weight: 2, fillOpacity: 0, opacity: 1 });
          if (layer.bringToFront) layer.bringToFront();
        });
        layer.on('mouseout', () => {
          layer.setStyle(baseWrsStyle());
        });
        layer.on('click', (e) => {
          lastFeatureClick = Date.now();
          const isShift = e.originalEvent && e.originalEvent.shiftKey;
          if (isShift) {
            toggleFeature(feature);
          } else {
            setSelection([feature]);
          }
          if (L.DomEvent && L.DomEvent.stopPropagation) {
            L.DomEvent.stopPropagation(e);
          }
        });
      }
    }).addTo(wrsGridGroup);
    console.log(`Loaded WRS grid with ${wrsFeatures.length} features`);
  })
  .catch(err => {
    console.warn("Could not load WRS grid", err);
  });

function highlightWrsSelection(feature) {
  wrsSelection.clearLayers();
  if (feature) {
    wrsSelection.addData(feature);
  }
}

function applyWrsSelection(feature) {
  const path = propsPath(feature);
  const row = propsRow(feature);

  const pathInput = document.getElementById("apiPath");
  const rowInput = document.getElementById("apiRow");
  if (pathInput && path != null) pathInput.value = path;
  if (rowInput && row != null) rowInput.value = row;

  if (tileInfoDiv && path != null && row != null) {
    tileInfoDiv.innerHTML = `
      <p><strong>Selected path/row:</strong> ${String(path).padStart(3, "0")}/${String(row).padStart(3, "0")}</p>
      <p class="muted">Click “Run analysis” to fetch delta NBR for these dates.</p>
    `;
  }

  updateSelectedList();
}

function setSelection(features) {
  selectedFeatures.clear();
  (features || []).forEach(f => {
    const key = featureKey(f);
    if (key) selectedFeatures.set(key, f);
  });
  updateSelectionLayer();
  updateSelectedList();

  // If single selection, fill form
  if (selectedFeatures.size === 1) {
    const only = [...selectedFeatures.values()][0];
    applyWrsSelection(only);
  } else if (tileInfoDiv && selectedFeatures.size > 1) {
    const list = [...selectedFeatures.values()].map(f => {
      const p = String(propsPath(f) || "").padStart(3, "0");
      const r = String(propsRow(f) || "").padStart(3, "0");
      return `${p}/${r}`;
    }).join(", ");
    tileInfoDiv.innerHTML = `
      <p><strong>Selected tiles:</strong> ${list}</p>
      <p class="muted">Shift-click to add/remove tiles. Dates come from the form.</p>
    `;
  }
}

function toggleFeature(feature) {
  const key = featureKey(feature);
  if (!key) return;
  if (!selectedFeatures.has(key) && selectedFeatures.size >= MAX_SELECTED_TILES) {
    alert(`You can select up to ${MAX_SELECTED_TILES} tiles at once.`);
    return;
  }
  if (selectedFeatures.has(key)) {
    selectedFeatures.delete(key);
  } else {
    selectedFeatures.set(key, feature);
  }
  updateSelectionLayer();
  updateSelectedList();

  if (selectedFeatures.size === 1) {
    applyWrsSelection(selectedFeatures.values().next().value);
  } else if (tileInfoDiv) {
    const list = [...selectedFeatures.values()].map(f => {
      const p = String(propsPath(f) || "").padStart(3, "0");
      const r = String(propsRow(f) || "").padStart(3, "0");
      return `${p}/${r}`;
    }).join(", ");
    tileInfoDiv.innerHTML = `
      <p><strong>Selected tiles:</strong> ${list}</p>
      <p class="muted">Shift-click to add/remove tiles. Dates come from the form.</p>
    `;
  }
}

function updateSelectionLayer() {
  wrsSelection.clearLayers();
  selectedFeatures.forEach(f => wrsSelection.addData(f));
}

function updateSelectedList() {
  const box = document.getElementById("selectedList");
  if (!box) return;
  if (selectedFeatures.size === 0) {
    box.innerHTML = "<p><strong>Selected tiles:</strong> (none)</p>";
    return;
  }
  const list = [...selectedFeatures.values()].map(f => {
    const p = String(propsPath(f) || "").padStart(3, "0");
    const r = String(propsRow(f) || "").padStart(3, "0");
    return `${p}/${r}`;
  }).join(", ");
  box.innerHTML = `<p><strong>Selected tiles:</strong> ${list}</p>`;
}


// Also allow map clicks: pick the containing feature whose centroid is closest
map.on('click', e => {
  if (Date.now() - lastFeatureClick < 50) return;
  if (!wrsFeatures.length || typeof turf === "undefined") return;

  const pt = turf.point([e.latlng.lng, e.latlng.lat]);
  const hits = wrsFeatures.filter(f => turf.booleanPointInPolygon(pt, f));
  if (!hits.length) return;

  const chosen = hits.slice().sort((a, b) => {
    const da = turf.distance(pt, turf.centroid(a));
    const db = turf.distance(pt, turf.centroid(b));
    return da - db;
  })[0];

  setSelection([chosen]);
});

// --- Custom analysis (API) wiring ---

// --- Custom analysis (API) wiring ---

const runApiBtn   = document.getElementById("runApiBtn");
const apiResultEl = document.getElementById("apiResult");
const loadingOverlay = document.getElementById("loadingOverlay");

// Clear date fields and disable browser autocomplete
["preStart","preEnd","postStart","postEnd"].forEach(id => {
  const el = document.getElementById(id);
  if (el) {
    el.value = "";
    el.setAttribute("autocomplete", "off");
  }
});

function clearApiOverlays() {
  latestApiLayers.forEach(layer => {
    map.removeLayer(layer);
  });
  latestApiLayers = [];
}

if (runApiBtn && apiResultEl) {
  runApiBtn.addEventListener("click", async () => {
    const path      = parseInt(document.getElementById("apiPath").value, 10);
    const row       = parseInt(document.getElementById("apiRow").value, 10);
    const preStart  = document.getElementById("preStart").value;
    const preEnd    = document.getElementById("preEnd").value;
    const postStart = document.getElementById("postStart").value;
    const postEnd   = document.getElementById("postEnd").value;

    if (!preStart || !preEnd || !postStart || !postEnd) {
      apiResultEl.textContent = "Please fill all date fields.";
      return;
    }

    apiResultEl.textContent = "Running analysis...";

    try {
      clearApiOverlays();
      if (loadingOverlay) loadingOverlay.classList.remove("hidden");

      // Build payload: batch if multiple selections, else single
      const requests = [];
      if (selectedFeatures.size > 0) {
        selectedFeatures.forEach(f => {
          const p = propsPath(f);
          const r = propsRow(f);
          if (p != null && r != null) {
            requests.push({
              path: p,
              row: r,
              pre_start: preStart,
              pre_end: preEnd,
              post_start: postStart,
              post_end: postEnd
            });
          }
        });
      } else {
        requests.push({
          path,
          row,
          pre_start: preStart,
          pre_end: preEnd,
          post_start: postStart,
          post_end: postEnd
        });
      }

      if (requests.length === 0) {
        apiResultEl.textContent = "Please select tiles or enter path/row.";
        return;
      }

      // If multiple requests, use batch endpoint
      if (requests.length > 1) {
        const batchResp = await fetch("/api/run_dnbr_batch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ requests })
        });

        if (!batchResp.ok) {
          const text = await batchResp.text();
          throw new Error(`HTTP ${batchResp.status}: ${text}`);
        }

        const data = await batchResp.json();
        if (data.error) {
          apiResultEl.textContent = "Error: " + data.error;
          return;
        }

        const errors = data.errors || [];
        const results = data.results || [];

        const rows = [];
        results.forEach(res => {
          const s = res.stats || {};
          const percent =
            s.percent_changed != null
              ? s.percent_changed.toFixed(1) + "%"
              : "?";

          rows.push(`<p><strong>P${String(res.path).padStart(3, "0")}R${String(res.row).padStart(3, "0")}:</strong> valid ${s.valid_pixels ?? "?"}, changed ${s.changed_pixels ?? "?"}, % ${percent}</p>`);

          if (res.png_url && res.bounds) {
            const b = res.bounds;
            if (
              b.min_lat != null && b.min_lon != null &&
              b.max_lat != null && b.max_lon != null
            ) {
              const apiBounds = [
                [b.min_lat, b.min_lon],
                [b.max_lat, b.max_lon]
              ];
          const label = `Custom P${String(res.path).padStart(3, "0")}R${String(res.row).padStart(3, "0")} (${preStart} → ${postStart})`;

              const layer = L.imageOverlay(res.png_url, apiBounds, { opacity: 0.75 });
              layer.addTo(map);
              latestApiLayers.push(layer);
            }
          }
        });

        errors.forEach(err => {
          rows.push(`<p class="muted">Error P${String(err.path || "?").padStart(3, "0")}R${String(err.row || "?").padStart(3, "0")}: ${err.error}</p>`);
        });

        apiResultEl.innerHTML = rows.join("") || "No results.";
      } else {
        const resp = await fetch("/api/run_dnbr", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            path: requests[0].path,
            row: requests[0].row,
            pre_start: preStart,
            pre_end: preEnd,
            post_start: postStart,
            post_end: postEnd
          })
        });

        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(`HTTP ${resp.status}: ${text}`);
        }

        const data = await resp.json();

        if (data.error) {
          apiResultEl.textContent = "Error: " + data.error;
          return;
        }

        const s = data.stats || {};
        const percent =
          s.percent_changed != null
            ? s.percent_changed.toFixed(1) + "%"
            : "?";

        if (data.png_url && data.bounds) {
          const b = data.bounds;
          if (
            b.min_lat != null && b.min_lon != null &&
            b.max_lat != null && b.max_lon != null
          ) {
            const apiBounds = [
              [b.min_lat, b.min_lon],
              [b.max_lat, b.max_lon]
            ];
            const pathVal = document.getElementById("apiPath").value;
            const rowVal = document.getElementById("apiRow").value;
            const label = `Custom P${pathVal}R${rowVal} (${preStart} → ${postStart})`;

            const layer = L.imageOverlay(data.png_url, apiBounds, { opacity: 0.75 });
            layer.addTo(map);
            latestApiLayers.push(layer);
          }
        }

        apiResultEl.innerHTML = `
          <p><strong>Valid pixels:</strong> ${s.valid_pixels ?? "?"}</p>
          <p><strong>Changed pixels:</strong> ${s.changed_pixels ?? "?"}</p>
          <p><strong>% burned:</strong> ${percent}</p>
        `;
      }
    } catch (err) {
      apiResultEl.textContent = "Request failed: " + err.message;
      console.error(err);
    } finally {
      if (loadingOverlay) loadingOverlay.classList.add("hidden");
    }
  });
}
