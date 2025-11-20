// Quebec Forest Fire Burn Viewer — Map logic

// 1. Initialize map, centered on Quebec
const map = L.map('map', { scrollWheelZoom: true }).setView([48.5, -71.5], 6);

// Base layers
const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const carto = L.tileLayer(
  'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  {
    maxZoom: 20,
    attribution: '&copy; OpenStreetMap & Carto'
  }
);

// 2. PRE-GENERATED TILES
// For now, define them manually. Later you can generate this list from Python.
// bounds = [[lat_min, lon_min], [lat_max, lon_max]]

const PRESET_TILES = 
[
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
;


// Keep track of overlay layers + rectangles
const presetLayers = [];
const presetRects = [];

let boundsUnion = null;

function extendBounds(union, b) {
  if (!union) return L.latLngBounds(b);
  return union.extend(b);
}

// Create overlay + clickable rectangle for each pre-generated tile
PRESET_TILES.forEach(tile => {
  const layer = L.imageOverlay(tile.url, tile.bounds, { opacity: 0.75 });

  // Yellow outline for the tile
  const rect = L.rectangle(tile.bounds, {
    color: '#ffd166',
    weight: 1,
    fillOpacity: 0
  });

  rect.on('click', () => {
    showTileInfo(tile);
    highlightRect(rect);
  });

  layer.addTo(map);
  rect.addTo(map);

  presetLayers.push({ tile, layer });
  presetRects.push(rect);

  boundsUnion = extendBounds(boundsUnion, tile.bounds);
});

// Fit map to cover all tiles if we have any, otherwise keep default view
if (boundsUnion) {
  map.fitBounds(boundsUnion.pad(0.1));
}

// 3. Layer controls
const baseLayers = {
  'OpenStreetMap': osm,
  'Carto Light': carto
};

const overlayLayers = {};
presetLayers.forEach(({ tile, layer }) => {
  overlayLayers[tile.label] = layer;
});

L.control.layers(baseLayers, overlayLayers, { collapsed: false }).addTo(map);

// 4. Sidebar controls: show/hide all preset tiles
const chkPresetTiles = document.getElementById('chkPresetTiles');

if (chkPresetTiles) {
  chkPresetTiles.addEventListener('change', evt => {
    const checked = evt.target.checked;
    presetLayers.forEach(({ layer }) => {
      if (checked) {
        layer.addTo(map);
      } else {
        map.removeLayer(layer);
      }
    });
    presetRects.forEach(rect => {
      if (checked) {
        rect.addTo(map);
      } else {
        map.removeLayer(rect);
      }
    });
  });
}

// 5. Tile info UI

const tileInfoDiv = document.getElementById('tileInfo');
let lastHighlighted = null;

function showTileInfo(tile) {
  if (!tileInfoDiv) return;

  const percentText =
    tile.percentChanged == null
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

// --- Custom analysis (API) wiring ---

// --- Custom analysis (API) wiring ---

const runApiBtn   = document.getElementById("runApiBtn");
const apiResultEl = document.getElementById("apiResult");

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
      const resp = await fetch("/api/run_dnbr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path,
          row,
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

      apiResultEl.innerHTML = `
        <p><strong>Valid pixels:</strong> ${s.valid_pixels ?? "?"}</p>
        <p><strong>Changed pixels:</strong> ${s.changed_pixels ?? "?"}</p>
        <p><strong>% burned:</strong> ${percent}</p>
      `;
    } catch (err) {
      apiResultEl.textContent = "Request failed: " + err.message;
      console.error(err);
    }
  });
}
