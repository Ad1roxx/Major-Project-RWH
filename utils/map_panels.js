// utils/map_panels.js
// Collapsible map panels, grouped overlay list, and keeping popups clear of the
// panels. Injected by utils/map_renderer.py, which fills in the Leaflet map
// variable (the double-underscore placeholder below). Display only.
//
// Runs after the current script finishes, because Folium creates the layer box
// and the data-layer panel later in the same script.
(function () {
  var map = __MAP__;
  if (!map) { return; }

  // Keep popups away from the title, the zoom buttons and the collapsed headers.
  L.Popup.prototype.options.autoPanPaddingTopLeft = L.point(60, 60);
  L.Popup.prototype.options.autoPanPaddingBottomRight = L.point(20, 80);

  var NARROW_PX = 900;
  var STORE = "rwh.panel.";
  var panels = [];

  function stored(id) {
    try { return window.localStorage.getItem(STORE + id); } catch (e) { return null; }
  }
  function remember(id, collapsed) {
    try { window.localStorage.setItem(STORE + id, collapsed ? "1" : "0"); } catch (e) { /* private mode */ }
  }

  function setCollapsed(p, on) {
    p.el.classList.toggle("rwh-collapsed", on);
    p.btn.setAttribute("aria-expanded", on ? "false" : "true");
    p.btn.setAttribute("aria-label", (on ? "Expand " : "Collapse ") + p.title);
    p.btn.textContent = on ? "▸" : "▾";
  }

  function wire(id, el, title) {
    var head = el.querySelector(".rwh-head");
    var btn = el.querySelector(".rwh-toggle");
    if (!head || !btn) { return; }
    var p = { id: id, el: el, btn: btn, title: title, temp: false };
    panels.push(p);
    var saved = stored(id);
    setCollapsed(p, saved === null ? window.innerWidth < NARROW_PX : saved === "1");
    head.addEventListener("click", function () {
      var on = !el.classList.contains("rwh-collapsed");
      p.temp = false;           // the user's choice now outranks the popup's
      setCollapsed(p, on);
      remember(id, on);
    });
  }

  // ── Layer box: header and grouped overlays ───────────────────────────────
  var GROUPS = [
    ["Base data", /Boundary|Rivers/],
    ["Suitability", /High Suitability/],
    ["Candidate sites", /Candidate|Sites\s/],
    ["MGNREGA works", /MGNREGA|Photo-confirmed/]
  ];

  function heading(text) {
    var d = document.createElement("div");
    d.className = "rwh-group";
    d.textContent = text;
    return d;
  }

  // Moving the labels is safe: Leaflet finds its inputs through its own list, not
  // their position, and the layer names stay exactly as Folium wrote them.
  function arrangeOverlays(list) {
    var labels = Array.prototype.slice.call(list.querySelectorAll("label"));
    var used = [];
    GROUPS.forEach(function (g) {
      var members = labels.filter(function (l) {
        return used.indexOf(l) < 0 && g[1].test(l.textContent);
      });
      if (!members.length) { return; }
      list.appendChild(heading(g[0]));
      members.forEach(function (l) { used.push(l); list.appendChild(l); });
    });
    labels.forEach(function (l) { if (used.indexOf(l) < 0) { list.appendChild(l); } });
  }

  function setUpLayerBox() {
    var box = document.querySelector(".leaflet-control-layers");
    if (!box) { return; }
    var head = document.createElement("div");
    head.className = "rwh-head";
    head.innerHTML = '<span class="rwh-h">Layers</span>' +
      '<button type="button" class="rwh-toggle"></button>';
    box.insertBefore(head, box.firstChild);

    var base = box.querySelector(".leaflet-control-layers-base");
    if (base) { base.parentNode.insertBefore(heading("Basemap"), base); }

    var overlays = box.querySelector(".leaflet-control-layers-overlays");
    if (overlays) {
      arrangeOverlays(overlays);
      // Leaflet rebuilds this list if a layer is added from code.
      new MutationObserver(function () {
        if (!overlays.querySelector(".rwh-group")) { arrangeOverlays(overlays); }
      }).observe(overlays, { childList: true });
    }
    wire("layers", box, "layer list");
  }

  // ── Popups: only panels actually in the way move ─────────────────────────
  function overlaps(a, b) {
    return a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  }

  function clearPopup(popup) {
    if (!popup || !map.hasLayer(popup)) { return; }
    var el = popup.getElement();
    if (!el) { return; }
    var r = el.getBoundingClientRect();
    panels.forEach(function (p) {
      if (!p.el.classList.contains("rwh-collapsed") && overlaps(r, p.el.getBoundingClientRect())) {
        p.temp = true;
        setCollapsed(p, true);
      }
    });
    // These two have no header to shrink to, so they step aside while it's open.
    document.querySelectorAll("#rwh-map-title, .rwh-legend").forEach(function (el2) {
      if (overlaps(r, el2.getBoundingClientRect())) { el2.classList.add("rwh-step-aside"); }
    });
  }

  var openPopup = null;
  map.on("popupopen", function (e) {
    openPopup = e.popup;
    clearPopup(e.popup);
    window.setTimeout(function () { clearPopup(e.popup); }, 350);   // after auto-pan
  });
  map.on("rwhpopupcontent", function () { clearPopup(openPopup); });
  map.on("popupclose", function () {
    openPopup = null;
    panels.forEach(function (p) {
      if (p.temp) { p.temp = false; setCollapsed(p, false); }
    });
    document.querySelectorAll(".rwh-step-aside").forEach(function (el) {
      el.classList.remove("rwh-step-aside");
    });
  });

  // ── View and layers survive changing page ────────────────────────────────
  // Leaving the Map page destroys this iframe, so its state is kept for the tab.
  var VIEW_KEY = "rwh.mapstate";

  // Layer names can hold live text in brackets, such as the selected algorithm.
  function layerName(label) {
    return label.textContent.split("(")[0].replace(/\s+/g, " ").trim();
  }

  function saveState() {
    var s = { center: map.getCenter(), zoom: map.getZoom(), checks: {} };
    document.querySelectorAll(".leaflet-control-layers label").forEach(function (l) {
      var input = l.querySelector("input");
      if (input) { s.checks[layerName(l)] = input.checked; }
    });
    var sel = document.getElementById("rwh-layer");
    if (sel) {
      s.layer = sel.value;
      s.score = document.getElementById("rwh-score").checked;
      s.opacity = document.getElementById("rwh-opacity").value;
    }
    try { window.sessionStorage.setItem(VIEW_KEY, JSON.stringify(s)); } catch (e) { /* private mode */ }
  }

  function startSaving() {
    map.on("moveend overlayadd overlayremove baselayerchange", saveState);
    var data = document.querySelector(".rwh-panel");
    if (data) { data.addEventListener("change", saveState); data.addEventListener("input", saveState); }
  }

  function restoreState() {
    var s = null;
    try { s = JSON.parse(window.sessionStorage.getItem(VIEW_KEY)); } catch (e) { /* none saved */ }
    if (!s) { startSaving(); return; }

    // The map's first fit to the district animates, and ending would undo a view
    // set now, so a restored view waits for it. Saving starts only after that.
    function restoreView() {
      map.setView(s.center, s.zoom, { animate: false });
      startSaving();
    }
    if (map._animatingZoom) { map.once("zoomend", restoreView); } else { restoreView(); }

    document.querySelectorAll(".leaflet-control-layers label").forEach(function (l) {
      var input = l.querySelector("input"), want = s.checks[layerName(l)];
      if (input && want !== undefined && input.checked !== want && (input.type === "checkbox" || want)) {
        input.click();
      }
    });
    var sel = document.getElementById("rwh-layer");
    if (sel && s.layer && sel.querySelector('option[value="' + s.layer + '"]')) {
      var opacity = document.getElementById("rwh-opacity"), score = document.getElementById("rwh-score");
      opacity.value = s.opacity;
      opacity.dispatchEvent(new Event("input"));
      sel.value = s.layer;
      sel.dispatchEvent(new Event("change"));
      if (score.checked !== s.score && !score.disabled) { score.click(); }
    }
  }

  window.setTimeout(function () {
    setUpLayerBox();
    var legend = document.getElementById("rwh-main-legend");
    if (legend) { wire("legend", legend, "map legend"); }
    var data = document.querySelector(".rwh-panel");
    if (data) { wire("data", data, "data layer panel"); }

    restoreState();
  }, 0);
})();
