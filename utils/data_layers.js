// utils/data_layers.js
// Data-layer picker, raw/score switch, opacity, legend and click-to-read for
// the Folium map. Injected by utils/map_renderer.py, which fills in the
// Leaflet map variable and the payload from utils/data_layers.py (the two
// double-underscore placeholders below; do not repeat them elsewhere in this
// file). Display only.
(function () {
  var map = __MAP__;
  var P = __PAYLOAD__;
  if (!map || !P) { return; }

  var LAYER_GROUPS = [
    ["Criteria (model inputs)", [
      ["rainfall", "Rainfall (2014–2024 mean)"],
      ["slope", "Slope"],
      ["drainage", "Drainage density"],
      ["settlement", "Distance to settlement"],
      ["soil", "Soil texture"],
      ["lulc", "Land cover"]
    ]],
    ["Population", [
      ["population", "Population density"],
      ["pop_heat", "Population heatmap"]
    ]],
    ["Model output", [
      ["suitability", "Suitability score"]
    ]],
    ["Hydrology (supporting)", [
      ["cn", "SCS Curve Number"],
      ["runoff", "Runoff depth (design storm)"],
      ["runoff_coef", "Runoff coefficient"]
    ]]
  ];

  // ── State ─────────────────────────────────────────────────────────────────
  var state = { layer: "none", score: false, opacity: 0.8 };
  var overlay = null;

  // Images sit under the zones, boundary, rivers and sites (see map_renderer
  // pane z-indices) and never take the mouse, so clicks reach the map.
  if (!map.getPane("dataPane")) {
    map.createPane("dataPane");
    map.getPane("dataPane").style.zIndex = 210;
    map.getPane("dataPane").style.pointerEvents = "none";
  }

  function currentSpec() {
    if (state.layer === "none") { return null; }
    if (state.score && P.scoreOf[state.layer]) {
      var s = P.scores[P.scoreOf[state.layer]];
      return s ? { image: s.image, legend: s.legend, crisp: true } : null;
    }
    return P.layers[state.layer] || null;
  }

  function redraw() {
    if (overlay) { map.removeLayer(overlay); overlay = null; }
    var spec = currentSpec();
    renderLegend(spec ? spec.legend : null);
    if (!spec) { return; }
    overlay = L.imageOverlay(spec.image, P.bounds, {
      pane: "dataPane",
      opacity: state.opacity,
      interactive: false,
      className: spec.crisp ? "rwh-crisp" : "rwh-smooth"
    }).addTo(map);
  }

  // ── Control panel ─────────────────────────────────────────────────────────
  var Panel = L.Control.extend({
    options: { position: "topright" },
    onAdd: function () {
      var div = L.DomUtil.create("div", "rwh-panel");
      var opts = '<option value="none">None (zones and sites only)</option>';
      LAYER_GROUPS.forEach(function (g) {
        var inner = "";
        g[1].forEach(function (l) {
          if (P.layers[l[0]]) { inner += '<option value="' + l[0] + '">' + l[1] + "</option>"; }
        });
        if (inner) { opts += '<optgroup label="' + g[0] + '">' + inner + "</optgroup>"; }
      });
      div.innerHTML =
        '<div class="rwh-h">Data layer</div>' +
        '<select id="rwh-layer">' + opts + "</select>" +
        '<label class="rwh-row" id="rwh-score-row" title="Show the 0–1 score the model gives this criterion instead of the measured value">' +
        '<input type="checkbox" id="rwh-score"> Show model score (0–1)</label>' +
        '<label class="rwh-row">Opacity <input type="range" id="rwh-opacity" min="0" max="100" value="80"></label>' +
        '<div class="rwh-hint">Click anywhere in the district to read its values.</div>';
      L.DomEvent.disableClickPropagation(div);
      L.DomEvent.disableScrollPropagation(div);
      return div;
    }
  });
  new Panel().addTo(map);

  var selLayer = document.getElementById("rwh-layer");
  var chkScore = document.getElementById("rwh-score");
  var rowScore = document.getElementById("rwh-score-row");
  var rngOpacity = document.getElementById("rwh-opacity");

  function syncScoreSwitch() {
    var has = !!P.scoreOf[state.layer];
    chkScore.disabled = !has;
    rowScore.classList.toggle("rwh-disabled", !has);
    rowScore.title = has
      ? "Show the 0–1 score the model gives this criterion instead of the measured value"
      : "This layer has no model score: it is a model output or a supporting surface";
  }

  selLayer.addEventListener("change", function () {
    state.layer = selLayer.value; syncScoreSwitch(); redraw();
  });
  chkScore.addEventListener("change", function () {
    state.score = chkScore.checked; redraw();
  });
  rngOpacity.addEventListener("input", function () {
    state.opacity = rngOpacity.value / 100;
    if (overlay) { overlay.setOpacity(state.opacity); }
  });
  syncScoreSwitch();

  // ── Legend ────────────────────────────────────────────────────────────────
  var Legend = L.Control.extend({
    options: { position: "bottomright" },
    onAdd: function () {
      var div = L.DomUtil.create("div", "rwh-legend");
      div.style.display = "none";
      L.DomEvent.disableClickPropagation(div);
      L.DomEvent.disableScrollPropagation(div);
      return div;
    }
  });
  var legend = new Legend().addTo(map);

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderLegend(lg) {
    var div = legend.getContainer();
    if (!lg) { div.style.display = "none"; div.innerHTML = ""; return; }
    var h = '<div class="rwh-lt">' + esc(lg.title) + "</div>";
    if (lg.unit) { h += '<div class="rwh-unit">' + esc(lg.unit) + "</div>"; }
    if (lg.kind === "ramp") {
      h += '<div class="rwh-bar" style="background:linear-gradient(to right,' +
        lg.colors.join(",") + ')">';
      (lg.marks || []).forEach(function (m) {
        h += '<span class="rwh-mark" style="left:' + (m.pos * 100).toFixed(2) + '%"></span>';
      });
      h += "</div><div class=\"rwh-ticks\">";
      lg.ticks.forEach(function (t) {
        h += '<span style="left:' + (t.pos * 100).toFixed(2) + '%">' + esc(t.label) + "</span>";
      });
      h += "</div>";
      if (lg.marks && lg.marks.length) {
        h += '<div class="rwh-marks">';
        lg.marks.forEach(function (m) {
          h += '<span style="left:' + (m.pos * 100).toFixed(2) + '%">' + esc(m.label) + "</span>";
        });
        h += "</div>";
      }
    } else {
      h += '<div class="rwh-classes">';
      lg.items.forEach(function (it) {
        h += '<div class="rwh-item"><span class="rwh-sw" style="background:' + it.color +
          '"></span><span>' + esc(it.label) + '</span><span class="rwh-sub">' +
          esc(it.sub) + "</span></div>";
      });
      h += "</div>";
    }
    if (lg.note) { h += '<div class="rwh-note">' + esc(lg.note) + "</div>"; }
    h += '<div class="rwh-src">' + esc(lg.source) + "</div>";
    div.innerHTML = h;
    div.style.display = "block";
  }

  // ── Click-to-read ─────────────────────────────────────────────────────────
  function decode(block) {
    // Deflated (zlib) little-endian arrays, decoded in the browser.
    if (typeof DecompressionStream === "undefined") {
      return Promise.reject(new Error("unsupported"));
    }
    var bin = atob(block.data);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) { bytes[i] = bin.charCodeAt(i); }
    var stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate"));
    return new Response(stream).arrayBuffer().then(function (buf) {
      var n = P.grid.h * P.grid.w, out = {};
      block.fields.forEach(function (f) {
        out[f.key] = {
          arr: f.bytes === 2 ? new Uint16Array(buf, f.offset, n) : new Uint8Array(buf, f.offset, n),
          scale: f.scale, nodata: f.bytes === 2 ? 65535 : 255
        };
      });
      return out;
    });
  }

  var dataPromise = null;
  function loadData() {
    if (!dataPromise) {
      var parts = [decode(P.readout)];
      if (P.suitability) { parts.push(decode(P.suitability)); }
      dataPromise = Promise.all(parts).then(function (r) {
        var all = r[0];
        if (r[1]) { for (var k in r[1]) { all[k] = r[1][k]; } }
        return all;
      });
    }
    return dataPromise;
  }

  function val(d, key, idx) {
    var f = d[key];
    if (!f) { return null; }
    var q = f.arr[idx];
    return q === f.nodata ? null : q * f.scale;
  }

  function num(v, dp) {
    return v.toLocaleString("en-IN", { minimumFractionDigits: dp, maximumFractionDigits: dp });
  }

  var ROWS = [
    // [layer key for highlighting, label, value field, formatter, score field]
    ["rainfall", "Rainfall", "rainfall", function (v) { return num(v, 0) + " mm/yr"; }, "s_rainfall"],
    ["slope", "Slope", "slope", function (v) { return num(v, 2) + "°"; }, "s_slope"],
    ["soil", "Soil texture", "soil", function (v) { return P.soilLabels[String(v)] || "code " + v; }, "s_soil"],
    ["lulc", "Land cover", "lulc", function (v) { return P.lulcLabels[String(v)] || "code " + v; }, "s_lulc"],
    ["drainage", "Drainage density", "drainage", function (v) { return num(v, 2) + " km/km²"; }, "s_drainage"],
    ["settlement", "To nearest settlement", "settlement", function (v) { return num(v, 1) + " km"; }, "s_population"],
    ["population", "Population density", "population", function (v) { return num(v, 0) + " people/km²"; }, null],
    ["cn", "Curve Number", "cn", function (v) { return num(v, 0); }, null],
    ["runoff", "Runoff, " + (P.stormMm || 100) + " mm storm", "runoff",
      function (v) { return num(v, 1) + " mm (C " + num(v / (P.stormMm || 100), 2) + ")"; }, null]
  ];

  function suitClass(v) {
    if (v <= P.thresholds[0]) { return "Low"; }
    if (v <= P.thresholds[1]) { return "Medium"; }
    return "High";
  }

  map.on("click", function (e) {
    // Let candidate sites and rivers keep their own popups.
    var t = e.originalEvent && e.originalEvent.target;
    if (t && t.closest && t.closest(".leaflet-interactive")) { return; }

    var g = P.grid;
    var col = Math.floor((e.latlng.lng - g.west) / g.dlon);
    var row = Math.floor((g.north - e.latlng.lat) / g.dlat);
    var where = num(e.latlng.lat, 4) + "°N, " + num(e.latlng.lng, 4) + "°E";
    var popup = L.popup({ maxWidth: 330, className: "rwh-pop" }).setLatLng(e.latlng);

    if (row < 0 || col < 0 || row >= g.h || col >= g.w) {
      popup.setContent("<b>" + where + "</b><br>Outside the analysis area.").openOn(map);
      return;
    }
    popup.setContent("<b>" + where + "</b><br>Reading values…").openOn(map);

    loadData().then(function (d) {
      var idx = row * g.w + col;
      if (val(d, "s_slope", idx) === null && val(d, "rainfall", idx) === null) {
        popup.setContent("<b>" + where + "</b><br>Outside the district: no data.");
        return;
      }
      var h = "<div class=\"rwh-pop-h\">" + where + "</div><table>";
      var s = val(d, "suitability", idx);
      if (s !== null) {
        h += '<tr class="' + (state.layer === "suitability" ? "rwh-on" : "") +
          '"><td>Suitability score</td><td><b>' + num(s, 3) + "</b> · " + suitClass(s) + "</td></tr>";
      }
      ROWS.forEach(function (r) {
        var v = val(d, r[2], idx);
        if (v === null) { return; }
        var on = state.layer === r[0] ||
          (r[0] === "population" && state.layer === "pop_heat") ||
          (r[0] === "runoff" && state.layer === "runoff_coef");
        var sc = r[4] ? val(d, r[4], idx) : null;
        h += '<tr class="' + (on ? "rwh-on" : "") + '"><td>' + r[1] + "</td><td>" + r[3](v) +
          (sc !== null ? ' <span class="rwh-sc">score ' + num(sc, 2) + "</span>" : "") + "</td></tr>";
      });
      h += "</table><div class=\"rwh-pop-f\">Cell of the ≈300 m analysis grid.</div>";
      popup.setContent(h);
    }).catch(function () {
      popup.setContent("<b>" + where + "</b><br>Value readout needs a recent browser (Chrome, Edge, Firefox or Safari 16.4+).");
    });
  });
})();
