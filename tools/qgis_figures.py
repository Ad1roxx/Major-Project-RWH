"""QGIS print-layout figures (the map figures in docs/FIGURE_SPECS.md).

Runs under QGIS's own Python, not the project venv:

    "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" -P tools/qgis_figures.py fig07

Writes outputs/figures/figNN.png (300 dpi) and outputs/figures/qgis/figNN.qgz,
the same layout as an editable QGIS project. Layers are read from the repo, so
the figures show exactly the data behind the paper's numbers.

House style shared with tools/make_figures.py: CLASS_COLOURS, DejaVu Sans
(loaded from matplotlib's own font files, so it matches even where the font is
not installed), a finding title, and the plain "N" arrow of _add_north. QGIS
output is not covered by the generator's palette check, so colours chosen here
are checked by hand: rivers are dark grey because blue means High.
"""
import glob
import math
import os
import sys

# The offscreen Qt platform has no font database on Windows and draws every
# glyph as a box, so the normal platform is used; no window is shown.

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
    QgsPalettedRasterRenderer, QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol,
    QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutPoint,
    QgsLayoutSize, QgsUnitTypes, QgsRectangle, QgsLayoutItemLegend, QgsLayoutItemScaleBar,
    QgsLayoutItemLabel, QgsLayoutExporter, QgsLayoutItemMapGrid, QgsProperty, QgsSymbolLayer,
    QgsCoordinateTransform, QgsPointXY, QgsGeometry, QgsFeature, QgsVectorFileWriter,
    QgsLegendStyle, QgsLayoutItemMapOverview, QgsMapLayerLegendUtils, QgsLegendPatchShape,
    QgsSymbol, QgsLayoutItemPolyline, QgsPropertyCollection, QgsTextBackgroundSettings,
)
from qgis.PyQt.QtCore import QPointF, QSizeF
from qgis.PyQt.QtGui import QColor, QFont, QFontDatabase, QPolygonF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "figures")
QGZ = os.path.join(OUT, "qgis")
UTM = QgsCoordinateReferenceSystem("EPSG:32644")
WGS = QgsCoordinateReferenceSystem("EPSG:4326")
CLASS_COLOURS = {1: ("#B2182B", "Low (≤ 0.65)"),
                 2: ("#E8E4DC", "Medium (0.65–0.85)"),
                 3: ("#2166AC", "High (> 0.85)")}
RIVER_COLOUR = "#7f7f7f"               # not blue (blue means High); lighter than the black boundary
FONT = "DejaVu Sans"
PAGE_W, PAGE_H = 174.0, 137.0          # mm; full-width journal figure
TOP = 10.5                             # mm reserved for the title
SEPARATION_KM = 5.0                    # candidate extraction's minimum spacing
INSET_HALF_KM = 5.4                    # inset half-width: the circle plus a margin


def _path(*p):
    return os.path.join(ROOT, *p)


def _load_house_font():
    """Register matplotlib's DejaVu Sans so the maps match the generated set."""
    hits = glob.glob(_path("venv", "Lib", "site-packages", "matplotlib", "mpl-data",
                           "fonts", "ttf", "DejaVuSans*.ttf"))
    for f in hits:
        if "Mono" not in f and "Display" not in f:
            QFontDatabase.addApplicationFont(f)
    if FONT not in QFontDatabase().families():
        raise RuntimeError("DejaVu Sans not found; the figures must share one font family")


def _text(size, bold=False, buffer_mm=0.0, colour="#000000"):
    f = QgsTextFormat()
    font = QFont(FONT)
    font.setBold(bold)
    f.setFont(font)
    f.setSize(size)
    f.setSizeUnit(QgsUnitTypes.RenderPoints)
    f.setColor(QColor(colour))
    if buffer_mm:
        b = QgsTextBufferSettings()
        b.setEnabled(True)
        b.setSize(buffer_mm)
        b.setColor(QColor("#ffffff"))
        f.setBuffer(b)
    return f


def _label(layout, text, x, y, w, h, size=8, bold=False):
    item = QgsLayoutItemLabel(layout)
    item.setText(text)
    item.setTextFormat(_text(size, bold))
    item.attemptMove(QgsLayoutPoint(x, y, QgsUnitTypes.LayoutMillimeters))
    item.attemptResize(QgsLayoutSize(w, h, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(item)
    return item



def _export_checked(layout, png, checks):
    """Export at 300 dpi, then fail unless every listed feature got a placed label.

    `checks` is [(map item, layer, field)]. Uses the labelling results of this
    very export: a separate test render can place labels differently, and
    QgsLabelingResults also lists labels it tried and failed to place
    (isUnplaced), which an earlier version of this check counted as placed.
    """
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300
    res = exporter.exportToImage(png, settings)
    if res != QgsLayoutExporter.Success:
        raise RuntimeError(f"export failed: {res}")
    results = exporter.labelingResults()
    problems = []
    for item, layer, field in checks:
        placed = {lab.featureId for lab in results[item.uuid()].allLabels()
                  if lab.layerID == layer.id() and not lab.isUnplaced}
        missing = [str(f[field]) for f in layer.getFeatures() if f.id() not in placed]
        if missing:
            problems.append(f"{layer.name()}: {', '.join(missing)}")
    if problems:
        raise RuntimeError("labels not placed: " + "; ".join(problems))


def _north_arrow(layout, x, y):
    """The plain arrow-and-N of make_figures._add_north."""
    line = QgsLayoutItemPolyline(QPolygonF([QPointF(x, y + 8.5), QPointF(x, y + 4.4)]), layout)
    line.setEndMarker(QgsLayoutItemPolyline.ArrowHead)
    line.setArrowHeadWidth(1.8)
    line.setSymbol(QgsLineSymbol.createSimple({"color": "#000000", "width": "0.35"}))
    layout.addLayoutItem(line)
    n = _label(layout, "N", x - 2, y - 0.6, 4, 4, size=8, bold=True)
    n.setHAlign(4)                         # Qt.AlignHCenter


def _layers(project):
    suit = QgsRasterLayer(_path("outputs", "rwh_suitability_classified.tif"), "Suitability class")
    classes = [QgsPalettedRasterRenderer.Class(v, QColor(c), lab)
               for v, (c, lab) in sorted(CLASS_COLOURS.items(), reverse=True)]
    suit.setRenderer(QgsPalettedRasterRenderer(suit.dataProvider(), 1, classes))

    rivers = QgsVectorLayer(_path("data", "rivers.geojson"), "Rivers (HydroRIVERS)", "ogr")
    sym = QgsLineSymbol.createSimple({"color": RIVER_COLOUR, "width": "0.12", "capstyle": "round"})
    # Higher Strahler order draws thicker, so trunk rivers read first.
    sym.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyStrokeWidth,
        QgsProperty.fromExpression('0.07 + 0.055 * ("ORD_STRA" - 1)'))
    rivers.setRenderer(QgsSingleSymbolRenderer(sym))

    boundary = QgsVectorLayer(_path("data", "boundary.geojson"), "District boundary", "ogr")
    boundary.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "#000000", "outline_width": "0.35"})))

    # Hollow rings: low-ranked sites often sit on a High patch smaller than a
    # filled marker, which then hides the very cell that makes them High.
    sites = QgsVectorLayer(_path("outputs", "rwh_sites.geojson"), "Candidate site (rank)", "ogr")
    sites.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "size": "1.7", "color": "0,0,0,0",
         "outline_color": "#000000", "outline_width": "0.4"})))

    for lyr in (suit, rivers, boundary, sites):
        if not lyr.isValid():
            raise RuntimeError(f"layer failed to load: {lyr.name()}")
        project.addMapLayer(lyr)
    return suit, rivers, boundary, sites


def _label_sites(sites, project, box):
    """Rank labels; sites near the inset box put their label on the far side."""
    to_utm = QgsCoordinateTransform(WGS, UTM, project)
    cx, cy = box.center().x(), box.center().y()
    near = box.buffered(4000)
    rules = []
    for f in sites.getFeatures():
        p = to_utm.transform(f.geometry().asPoint())
        # Only sites just outside the box need pushing away from its edge; a
        # site inside it (rank 1, at the centre) keeps the default placement.
        if not near.contains(QgsPointXY(p)) or box.contains(QgsPointXY(p)):
            continue
        dx, dy = p.x() - cx, p.y() - cy
        if abs(dx) * box.height() > abs(dy) * box.width():
            order = "R,TR,BR" if dx > 0 else "L,TL,BL"
        else:
            order = "T,TR,TL" if dy > 0 else "B,BR,BL"
        rules.append(f"WHEN \"rank\" = {int(f['rank'])} THEN '{order}'")
    pal = QgsPalLayerSettings()
    pal.fieldName = "rank"
    pal.placement = QgsPalLayerSettings.OrderedPositionsAroundPoint
    pal.dist = 1.15                            # clear of the ring, halo included
    pal.setFormat(_text(6.0, bold=True, buffer_mm=0.7))
    pal.displayAll = False     # forcing every label lets two collide; placement is checked instead
    pal.priority = 10
    # Elsewhere labels never go left: a left label can abut a neighbour's right
    # one, and QGIS treats touching boxes as clear ("25" + "11" read "2511").
    props = pal.dataDefinedProperties()
    props.setProperty(QgsPalLayerSettings.PredefinedPositionOrder, QgsProperty.fromExpression(
        "CASE " + " ".join(rules) + " ELSE 'TR,R,BR,T,B' END" if rules else "'TR,R,BR,T,B'"))
    pal.setDataDefinedProperties(props)
    sites.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    sites.setLabelsEnabled(True)


def _separation_circle(project, sites):
    """The 5 km separation circle around rank 1, saved so the .qgz can reopen it."""
    rank1 = next(f for f in sites.getFeatures() if int(f["rank"]) == 1)
    centre = QgsCoordinateTransform(WGS, UTM, project).transform(rank1.geometry().asPoint())
    path = os.path.join(QGZ, "fig07_separation_circle.geojson")
    mem = QgsVectorLayer("Polygon?crs=EPSG:32644", "5 km minimum separation", "memory")
    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(centre)).buffer(SEPARATION_KM * 1000, 96))
    mem.dataProvider().addFeatures([feat])
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GeoJSON"
    QgsVectorFileWriter.writeAsVectorFormatV3(mem, path, project.transformContext(), opts)
    circle = QgsVectorLayer(path, "5 km minimum separation", "ogr")
    circle.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "#000000", "outline_width": "0.35",
         "outline_style": "dash"})))
    project.addMapLayer(circle)
    return circle, centre, rank1



def fig07():
    _load_house_font()
    project = QgsProject.instance()
    project.clear()
    project.setCrs(UTM)
    os.makedirs(QGZ, exist_ok=True)
    suit, rivers, boundary, sites = _layers(project)
    circle, centre, rank1 = _separation_circle(project, sites)
    half = INSET_HALF_KM * 1000
    box = QgsRectangle(centre.x() - half, centre.y() - half, centre.x() + half, centre.y() + half)
    _label_sites(sites, project, box)

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName("Figure 7")
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(PAGE_W, PAGE_H))
    stack = [sites, circle, boundary, rivers, suit]

    _label(layout, "High-class land (6.44%) lies in a north-central belt and along the eastern "
                   "margin; 25 candidate sites, all ≥ 5 km apart",
           9, 1.5, 162, 8, size=8.2, bold=True)

    # ── (a) main map ────────────────────────────────────────────────────────
    main = QgsLayoutItemMap(layout)
    main.attemptMove(QgsLayoutPoint(9, TOP))
    main.attemptResize(QgsLayoutSize(104, 116))
    main.setCrs(UTM)
    main.setLayers(stack)
    ext = QgsCoordinateTransform(WGS, UTM, project).transformBoundingBox(boundary.extent())
    layout.addLayoutItem(main)
    main.zoomToExtent(ext.buffered(2500))
    main.setFrameEnabled(True)

    grid = QgsLayoutItemMapGrid("Graticule", main)
    grid.setCrs(WGS)
    grid.setIntervalX(0.5)
    grid.setIntervalY(0.5)
    grid.setStyle(QgsLayoutItemMapGrid.FrameAnnotationsOnly)
    grid.setFrameStyle(QgsLayoutItemMapGrid.ExteriorTicks)
    grid.setFrameWidth(1.4)
    grid.setFramePenSize(0.3)
    grid.setAnnotationEnabled(True)
    grid.setAnnotationFormat(QgsLayoutItemMapGrid.DecimalWithSuffix)
    grid.setAnnotationPrecision(1)
    grid.setAnnotationTextFormat(_text(6.0))
    for side in (QgsLayoutItemMapGrid.Right, QgsLayoutItemMapGrid.Top):
        grid.setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, side)
        grid.setFrameSideFlag(
            QgsLayoutItemMapGrid.FrameRight if side == QgsLayoutItemMapGrid.Right
            else QgsLayoutItemMapGrid.FrameTop, False)
    grid.setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)
    main.grids().addGrid(grid)

    # ── (b) inset on rank 1 ─────────────────────────────────────────────────
    inset = QgsLayoutItemMap(layout)
    inset.attemptMove(QgsLayoutPoint(118, TOP))
    inset.attemptResize(QgsLayoutSize(52, 52))
    inset.setCrs(UTM)
    inset.setLayers(stack)
    layout.addLayoutItem(inset)
    inset.setExtent(box)
    inset.setFrameEnabled(True)

    ov = QgsLayoutItemMapOverview("Inset extent", main)
    ov.setLinkedMap(inset)
    ov.setFrameSymbol(QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "#000000", "outline_width": "0.4"}))
    main.overviews().addOverview(ov)

    pt = rank1.geometry().asPoint()
    _label(layout, "(a)", 10.5, TOP + 1, 8, 5, size=8, bold=True)
    _label(layout, "(b)", 119.5, TOP + 1, 8, 5, size=8, bold=True)
    _north_arrow(layout, 21.5, TOP + 1.2)
    _label(layout, f"Rank 1 · score {float(rank1['suitability_score']):.3f}\n"
                   f"{pt.x():.4f}°E, {pt.y():.4f}°N", 118, TOP + 60.5, 52, 8, size=6.2)

    # Main bar in the empty lower-right of map (a); inset bar just below (b).
    for m, units, x, y in ((main, 10, 86, TOP + 104), (inset, 2.5, 118, TOP + 53)):
        sb = QgsLayoutItemScaleBar(layout)
        sb.setStyle("Single Box")
        sb.setLinkedMap(m)
        sb.setUnits(QgsUnitTypes.DistanceKilometers)
        sb.setUnitLabel("km")
        sb.setUnitsPerSegment(units)
        sb.setNumberOfSegments(2)
        sb.setNumberOfSegmentsLeft(0)
        sb.setHeight(1.2)
        sb.setTextFormat(_text(5.5))
        sb.setBackgroundEnabled(False)
        layout.addLayoutItem(sb)
        sb.attemptMove(QgsLayoutPoint(x, y))

    # ── legend ──────────────────────────────────────────────────────────────
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("")
    legend.setLinkedMap(main)
    legend.setAutoUpdateModel(False)
    root = legend.model().rootGroup()
    root.removeAllChildren()
    nodes = {lyr.id(): root.addLayer(lyr) for lyr in (suit, sites, circle, rivers, boundary)}
    for style in (QgsLegendStyle.Title, QgsLegendStyle.Group, QgsLegendStyle.Subgroup,
                  QgsLegendStyle.SymbolLabel):
        legend.rstyle(style).setTextFormat(_text(6.3, bold=style == QgsLegendStyle.Subgroup))
    legend.setSymbolWidth(4.5)
    legend.setSymbolHeight(2.6)
    legend.setBackgroundEnabled(False)
    legend.attemptMove(QgsLayoutPoint(118, TOP + 70))
    layout.addLayoutItem(legend)
    # After the legend joins the layout (earlier, the model refresh crashes):
    # drop the raster's "Band 1 (Gray)" entry, and draw the separation patch as
    # the circle the map shows rather than a square.
    QgsMapLayerLegendUtils.setLegendNodeOrder(nodes[suit.id()], [1, 2, 3])
    legend.model().refreshLayerLegend(nodes[suit.id()])
    ring = QgsGeometry.fromPointXY(QgsPointXY(0, 0)).buffer(1, 48)
    nodes[circle.id()].setPatchShape(QgsLegendPatchShape(QgsSymbol.Fill, ring, True))
    legend.updateLegend()
    legend.adjustBoxSize()

    _label(layout, "UTM 44N (EPSG:32644)\nRivers: HydroRIVERS · boundary: GADM",
           118, TOP + 115, 56, 7, size=5.2)

    png = os.path.join(OUT, "fig07.png")
    _export_checked(layout, png, [(main, sites, "rank")])
    project.layoutManager().addLayout(layout)
    project.write(os.path.join(QGZ, "fig07.qgz"))
    print(f"wrote {os.path.relpath(png, ROOT)} and outputs/figures/qgis/fig07.qgz")


# ── Figure 1: study area ────────────────────────────────────────────────────
INPUTS = os.path.join(QGZ, "inputs")          # written by tools/prep_map_layers.py
LCC_INDIA = QgsCoordinateReferenceSystem("EPSG:7755")   # WGS 84 / India NSF LCC
RIVER_BLUE = "#3f6f9f"   # Fig 1 has no suitability classes, so blue is free here


def _vec(project, path, name):
    lyr = QgsVectorLayer(path, name, "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"layer failed to load: {path}")
    project.addMapLayer(lyr)
    return lyr


def _style_fill(lyr, fill, outline, width, style="solid"):
    lyr.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": fill, "outline_color": outline, "outline_width": str(width),
         "outline_style": style})))


def _map_item(layout, crs, layers, x, y, w, h, extent, frame=True):
    m = QgsLayoutItemMap(layout)
    m.attemptMove(QgsLayoutPoint(x, y))
    m.attemptResize(QgsLayoutSize(w, h))
    m.setCrs(crs)
    m.setLayers(layers)
    layout.addLayoutItem(m)
    m.zoomToExtent(extent)
    m.setFrameEnabled(frame)
    return m


def _scalebar(layout, m, units, segs, x, y):
    sb = QgsLayoutItemScaleBar(layout)
    sb.setStyle("Single Box")
    sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers)
    sb.setUnitLabel("km")
    sb.setUnitsPerSegment(units)
    sb.setNumberOfSegments(segs)
    sb.setNumberOfSegmentsLeft(0)
    sb.setHeight(1.1)
    sb.setTextFormat(_text(5.5))
    sb.setBackgroundEnabled(False)
    layout.addLayoutItem(sb)
    sb.attemptMove(QgsLayoutPoint(x, y))
    return sb


def _graticule(m, interval):
    grid = QgsLayoutItemMapGrid("Graticule", m)
    grid.setCrs(WGS)
    grid.setIntervalX(interval)
    grid.setIntervalY(interval)
    grid.setStyle(QgsLayoutItemMapGrid.FrameAnnotationsOnly)
    grid.setFrameStyle(QgsLayoutItemMapGrid.ExteriorTicks)
    grid.setFrameWidth(1.4)
    grid.setFramePenSize(0.3)
    grid.setAnnotationEnabled(True)
    grid.setAnnotationFormat(QgsLayoutItemMapGrid.DecimalWithSuffix)
    grid.setAnnotationPrecision(1)
    grid.setAnnotationTextFormat(_text(6.0))
    for side, flag in ((QgsLayoutItemMapGrid.Right, QgsLayoutItemMapGrid.FrameRight),
                       (QgsLayoutItemMapGrid.Top, QgsLayoutItemMapGrid.FrameTop)):
        grid.setAnnotationDisplay(QgsLayoutItemMapGrid.HideAll, side)
        grid.setFrameSideFlag(flag, False)
    grid.setAnnotationDirection(QgsLayoutItemMapGrid.Vertical, QgsLayoutItemMapGrid.Left)
    m.grids().addGrid(grid)


def _overview(parent, child):
    ov = QgsLayoutItemMapOverview(f"Extent of {child.displayName()}", parent)
    ov.setLinkedMap(child)
    ov.setFrameSymbol(QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "#000000", "outline_width": "0.4"}))
    parent.overviews().addOverview(ov)


def _labels(lyr, field, size, colour="#222222", italic=False, placement=None, priority=5):
    pal = QgsPalLayerSettings()
    pal.fieldName = field
    if placement is not None:
        pal.placement = placement
    fmt = _text(size, buffer_mm=0.6, colour=colour)
    if italic:
        f = fmt.font()
        f.setItalic(True)
        fmt.setFont(f)
    pal.setFormat(fmt)
    pal.priority = priority
    if placement == QgsPalLayerSettings.Curved:
        pal.maxCurvedCharAngleIn = 45      # default 25° rejects winding channels
        pal.maxCurvedCharAngleOut = -45
    lyr.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    lyr.setLabelsEnabled(True)



def fig01():
    _load_house_font()
    project = QgsProject.instance()
    project.clear()
    project.setCrs(UTM)
    inp = lambda f: os.path.join(INPUTS, f)
    talukas_dir = _path("data", "raw", "talukas")

    # (a) India and (b) Maharashtra locators
    india = _vec(project, inp("india_soi.geojson"), "India (Survey of India)")
    _style_fill(india, "#ececec", "#6e6e6e", 0.2)
    mh_a = _vec(project, inp("maharashtra.geojson"), "Maharashtra")
    _style_fill(mh_a, "#a9a9a9", "#4d4d4d", 0.2)
    dist_b = _vec(project, inp("maharashtra_districts.geojson"), "Maharashtra districts")
    _style_fill(dist_b, "#ececec", "#9a9a9a", 0.12)
    chd_loc = _vec(project, _path("data", "boundary.geojson"), "Chandrapur (locator)")
    _style_fill(chd_loc, "#222222", "#000000", 0.2)

    # (c) the district
    talukas = _vec(project, os.path.join(talukas_dir, "chandrapur_talukas_filled_to_boundary.geojson"),
                   "Taluka (Census 2011)")
    # Cool grey, not beige: the #E8E4DC family means Medium in Figs 7, 10, 13.
    _style_fill(talukas, "#f3f4f6", "#8a8a8a", 0.25)
    _labels(talukas, "taluka", 6.3, colour="#2b2b2b", placement=QgsPalLayerSettings.Horizontal,
            priority=8)
    hq = _vec(project, os.path.join(talukas_dir, "chandrapur_taluka_hq.geojson"),
              "Taluka headquarters")
    hq.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "square", "size": "1.1", "color": "#222222", "outline_style": "no"})))
    # The squares must stay visible: make them label obstacles (no text of their
    # own). Without this "Erai" covered Chandrapur's square and "Sindewahi" its own.
    obst = QgsPalLayerSettings()
    obst.fieldName = "taluka_hq"
    obst.drawLabels = False
    obs = obst.obstacleSettings()
    obs.setIsObstacle(True)
    obs.setFactor(2.0)
    obst.setObstacleSettings(obs)
    hq.setLabeling(QgsVectorLayerSimpleLabeling(obst))
    hq.setLabelsEnabled(True)
    rivers = _vec(project, _path("data", "rivers.geojson"), "Rivers (HydroRIVERS)")
    sym = QgsLineSymbol.createSimple({"color": RIVER_BLUE, "width": "0.12", "capstyle": "round"})
    sym.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertyStrokeWidth,
        QgsProperty.fromExpression('0.07 + 0.075 * ("ORD_STRA" - 1)'))
    rivers.setRenderer(QgsSingleSymbolRenderer(sym))
    names = _vec(project, inp("river_labels.geojson"), "River names (OSM)")
    names.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(
        {"color": "0,0,0,0", "width": "0"})))
    _labels(names, "river", 6.6, colour=RIVER_BLUE, italic=True,
            placement=QgsPalLayerSettings.Curved, priority=10)
    boundary = _vec(project, _path("data", "boundary.geojson"), "District boundary (GADM)")
    _style_fill(boundary, "0,0,0,0", "#000000", 0.5)

    # (d) the analysis grid at true cell size
    cells_in = _vec(project, inp("grid_window.geojson"), "Grid cell inside district")
    cells_in.setSubsetString('"inside" = 1')
    _style_fill(cells_in, "#c9c2b2", "#ffffff", 0.15)
    cells_out = _vec(project, inp("grid_window.geojson"), "Grid cell outside district")
    cells_out.setSubsetString('"inside" = 0')
    _style_fill(cells_out, "#ffffff", "#c8c8c8", 0.15)

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName("Figure 1")
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(PAGE_W, TOP + 158))
    _label(layout, "Chandrapur district, eastern Maharashtra: 15 talukas, analysed on a "
                   "450-row × 422-column grid of ≈0.3 km cells", 9, 1.5, 162, 8, size=8.2, bold=True)

    to_lcc = QgsCoordinateTransform(WGS, LCC_INDIA, project)
    to_utm = QgsCoordinateTransform(WGS, UTM, project)
    m_a = _map_item(layout, LCC_INDIA, [chd_loc, mh_a, india], 9, TOP, 50, 46,
                    to_lcc.transformBoundingBox(india.extent()).buffered(90000))
    m_b = _map_item(layout, UTM, [chd_loc, dist_b], 9, TOP + 49, 50, 34,
                    to_utm.transformBoundingBox(mh_a.extent()).buffered(15000))
    cext = to_utm.transformBoundingBox(boundary.extent()).buffered(3000)
    m_c = _map_item(layout, UTM, [names, hq, boundary, rivers, talukas], 67, TOP, 103, 130, cext)
    gext = to_utm.transformBoundingBox(cells_in.extent()).buffered(250)
    gext.combineExtentWith(to_utm.transformBoundingBox(cells_out.extent()))
    m_d = _map_item(layout, UTM, [boundary, cells_in, cells_out], 9, TOP + 86, 50, 44, gext)
    # Letters run down the left column, then the large district map: (a) India,
    # (b) Maharashtra, (c) the grid window, (d) the district.
    for m, mark in ((m_a, "(a)"), (m_b, "(b)"), (m_d, "(c)"), (m_c, "(d)")):
        m.setId(mark)
    _overview(m_a, m_b)
    _overview(m_c, m_d)
    _graticule(m_c, 0.5)

    # Panel letters on a white tab, so they never sit on data.
    for x, y, t in ((9.4, TOP + 0.4, "(a)"), (9.4, TOP + 49.4, "(b)"),
                    (67.4, TOP + 0.4, "(d)"), (9.4, TOP + 86.4, "(c)")):
        tab = _label(layout, t, x, y, 6.2, 4.6, size=7.2, bold=True)
        tab.setBackgroundEnabled(True)
        tab.setBackgroundColor(QColor("#ffffff"))
        tab.setMarginX(0.8)
    _label(layout, "Chandrapur", 41, TOP + 68, 18, 4, size=5.8, bold=True)
    _north_arrow(layout, 79, TOP + 1.2)
    _scalebar(layout, m_c, 10, 2, 136, TOP + 120)
    _scalebar(layout, m_d, 1, 2, 9.5, TOP + 131)
    _label(layout, "1 cell ≈ 0.30 km E–W\n× 0.31 km N–S\n123,555 cells in the district",
           35.5, TOP + 131.2, 26, 9, size=4.9)

    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("")
    legend.setLinkedMap(m_c)
    legend.setAutoUpdateModel(False)
    root = legend.model().rootGroup()
    root.removeAllChildren()
    nodes = {lyr.id(): root.addLayer(lyr)
             for lyr in (talukas, hq, boundary, rivers)}
    for style in (QgsLegendStyle.Title, QgsLegendStyle.Group, QgsLegendStyle.Subgroup,
                  QgsLegendStyle.SymbolLabel):
        legend.rstyle(style).setTextFormat(_text(5.8))
    for lyr, text in ((talukas, "Taluka"), (hq, "Taluka headquarters"),
                      (boundary, "District boundary"), (rivers, "River")):
        nodes[lyr.id()].setName(text)
    legend.setSymbolWidth(4.2)
    legend.setSymbolHeight(2.4)
    legend.setBackgroundEnabled(False)
    # One row under the district map: inside it the legend crowded the NW
    # boundary, and no corner of the frame is free of district.
    legend.setColumnCount(4)
    legend.setSplitLayer(False)
    legend.attemptMove(QgsLayoutPoint(67, TOP + 136.5))
    layout.addLayoutItem(legend)
    legend.updateLegend()
    legend.adjustBoxSize()

    _label(layout, "Projections: (a) WGS 84 / India NSF LCC; (b)–(d) UTM 44N (EPSG:32644). "
                   "India outline: Survey of India, via DataMeet (CC BY-SA 2.5). Maharashtra and "
                   "district: GADM 4.1. Talukas and their headquarters: Census of India 2011, via "
                   "datta07/INDIAN-SHAPEFILES. Rivers: HydroRIVERS; names © OpenStreetMap "
                   "contributors.", 9, TOP + 146, 162, 8, size=5.0)

    png = os.path.join(OUT, "fig01.png")
    _export_checked(layout, png, [(m_c, talukas, "taluka"), (m_c, names, "river")])
    project.layoutManager().addLayout(layout)
    project.write(os.path.join(QGZ, "fig01.qgz"))
    print(f"wrote {os.path.relpath(png, ROOT)} and outputs/figures/qgis/fig01.qgz")


# ── Hydrology (draft Fig 18): derived_maps.py surfaces ───────────────────────
# Two independent surfaces only. Runoff depth Q and the runoff coefficient C are
# fixed functions of the Curve Number for the 100 mm design storm, so maps of
# them repeat the CN map with relabelled colours; the CN legend carries Q and C
# instead. CN takes few discrete values (soil group x land cover), so it is
# drawn as classes (tools/prep_map_layers.py writes cn_class.tif).


def _drop_band_entry(legend, node):
    """Hide the raster's "Band 1 (Gray)" legend entry, keeping its classes or ramp."""
    order = QgsMapLayerLegendUtils.legendNodeOrder(node)
    n = len(legend.model().layerOriginalLegendNodes(node))
    QgsMapLayerLegendUtils.setLegendNodeOrder(node, list(range(1, n)))
    legend.model().refreshLayerLegend(node)


def _legend_for(layout, m, lyr, x, y, size=5.8, sym_w=4.2, sym_h=2.6, horizontal_ramp=False):
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("")
    legend.setLinkedMap(m)
    legend.setAutoUpdateModel(False)
    root = legend.model().rootGroup()
    root.removeAllChildren()
    node = root.addLayer(lyr)
    for style in (QgsLegendStyle.Title, QgsLegendStyle.Group, QgsLegendStyle.Subgroup,
                  QgsLegendStyle.SymbolLabel):
        legend.rstyle(style).setTextFormat(_text(size, bold=style == QgsLegendStyle.Subgroup))
    legend.setSymbolWidth(sym_w)
    legend.setSymbolHeight(sym_h)
    legend.setBackgroundEnabled(False)
    legend.attemptMove(QgsLayoutPoint(x, y))
    layout.addLayoutItem(legend)
    _drop_band_entry(legend, node)
    legend.updateLegend()
    legend.adjustBoxSize()
    return legend


def fig_hydrology():
    import json
    from qgis.core import (QgsSingleBandPseudoColorRenderer, QgsRasterShader,
                           QgsColorRampShader, QgsStyle, QgsColorRampLegendNodeSettings,
                           QgsBasicNumericFormat)
    _load_house_font()
    project = QgsProject.instance()
    project.clear()
    project.setCrs(UTM)
    boundary = _vec(project, _path("data", "boundary.geojson"), "District boundary")
    _style_fill(boundary, "0,0,0,0", "#000000", 0.35)
    ext = QgsCoordinateTransform(WGS, UTM, project).transformBoundingBox(
        boundary.extent()).buffered(2500)
    ramp = QgsStyle.defaultStyle().colorRamp("Viridis")

    # (a) drainage density: continuous, stretched to the 2nd-98th percentile
    dd = QgsRasterLayer(_path("outputs", "drainage_density.tif"), "Drainage density (km/km²)")
    lo, hi = dd.dataProvider().cumulativeCut(1, 0.02, 0.98)
    shader = QgsColorRampShader(lo, hi, ramp.clone(), QgsColorRampShader.Interpolated)
    shader.classifyColorRamp(9, 1, QgsRectangle(), None)
    leg = QgsColorRampLegendNodeSettings()
    leg.setOrientation(1)                                   # Qt.Horizontal
    fmt = QgsBasicNumericFormat()
    fmt.setNumberDecimalPlaces(2)
    fmt.setShowTrailingZeros(True)
    leg.setNumericFormat(fmt)
    # Mark an end with ≤/≥ only where the stretch actually clips data.
    from qgis.core import QgsRasterBandStats
    st = dd.dataProvider().bandStatistics(1, QgsRasterBandStats.Min | QgsRasterBandStats.Max)
    leg.setMinimumLabel(f"{lo:.2f}" if lo <= st.minimumValue else f"≤ {lo:.2f}")
    leg.setMaximumLabel(f"{hi:.2f}" if hi >= st.maximumValue else f"≥ {hi:.2f}")
    shader.setLegendSettings(leg)
    rs = QgsRasterShader()
    rs.setRasterShaderFunction(shader)
    dd.setRenderer(QgsSingleBandPseudoColorRenderer(dd.dataProvider(), 1, rs))
    project.addMapLayer(dd)

    # (b) Curve Number classes, each labelled with its Q and C
    rows = json.load(open(os.path.join(INPUTS, "cn_classes.json"), encoding="utf8"))
    cn = QgsRasterLayer(os.path.join(INPUTS, "cn_class.tif"),
                        "CN  |  Q (mm)  |  C  |  area")
    classes = []
    for i, r in enumerate(rows):
        qlo, qhi = r["q_mm"]
        q = f"{qlo:.1f}" if qlo == qhi else f"{qlo:.1f}–{qhi:.1f}"
        c = f"{qlo / 100:.2f}" if qlo == qhi else f"{qlo / 100:.2f}–{qhi / 100:.2f}"
        colour = ramp.color(i / (len(rows) - 1))
        classes.append(QgsPalettedRasterRenderer.Class(
            r["code"], colour, f"{r['cn']}  |  {q}  |  {c}  |  {r['share_pct']:.1f}%"))
    cn.setRenderer(QgsPalettedRasterRenderer(cn.dataProvider(), 1, classes))
    project.addMapLayer(cn)

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName("Hydrology")
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(PAGE_W, TOP + 97))
    w, h = 54.0, 70.0
    m_a = _map_item(layout, UTM, [boundary, dd], 9, TOP, w, h, ext)
    m_b = _map_item(layout, UTM, [boundary, cn], 9 + w + 4, TOP, w, h, ext)
    _graticule(m_a, 0.5)
    for m, x, t in ((m_a, 9, "(a)"), (m_b, 9 + w + 4, "(b)")):
        tab = _label(layout, t, x + 0.4, TOP + 0.4, 6.2, 4.6, size=7.2, bold=True)
        tab.setBackgroundEnabled(True)
        tab.setBackgroundColor(QColor("#ffffff"))
        tab.setMarginX(0.8)
    _north_arrow(layout, 9 + w - 5, TOP + 1.2)
    # Panel (b)'s bar sits below its frame: inside, every corner holds district.
    _scalebar(layout, m_b, 20, 1, 9 + w + 4, TOP + h + 1.5)

    _legend_for(layout, m_a, dd, 9, TOP + h + 6, sym_w=w - 6, sym_h=2.6)
    _legend_for(layout, m_b, cn, 9 + 2 * w + 7, TOP + 1, size=5.5, sym_w=3.8, sym_h=3.0)

    share89 = next(r["share_pct"] for r in rows if r["cn"] == "89")
    with open(os.path.join(INPUTS, "cn_classes.json"), encoding="utf8"):
        pass
    _label(layout, f"Runoff potential is high almost everywhere: Curve Number 89 covers "
                   f"{share89:.1f}% of the district, shedding 70 mm of a 100 mm storm",
           9, 1.5, 162, 8, size=8.2, bold=True)
    _label(layout, "Q and C are for the 100 mm design storm and follow from CN alone, so they "
                   "share panel (b). Areas are area-weighted. Drainage density from HydroRIVERS "
                   "in a 2.5 km window, ramp stretched to its 2nd–98th percentile. UTM 44N "
                   "(EPSG:32644).", 9 + 2 * w + 7, TOP + 50, PAGE_W - (9 + 2 * w + 7) - 3, 22,
           size=5.0)

    png = os.path.join(OUT, "fig_hydrology.png")
    _export_checked(layout, png, [])
    project.layoutManager().addLayout(layout)
    project.write(os.path.join(QGZ, "fig_hydrology.qgz"))
    print(f"wrote {os.path.relpath(png, ROOT)}; drainage stretch {lo:.3f}-{hi:.3f}")


# ── Diagrams (Figs 3, 4, 20) ────────────────────────────────────────────────
# Built as print layouts too, so the font and export match the maps and each
# has an editable .qgz. Greys only: blue and red carry class meanings elsewhere.
INK = "#2b2b2b"


def _new_layout(name, height):
    _load_house_font()
    project = QgsProject.instance()
    project.clear()
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(name)
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(PAGE_W, height))
    return project, layout


def _box(layout, x, y, w, h, text, size=6.2, bold=False, fill="#ffffff", dashed=False,
         halign=4, radius=1.2):
    from qgis.core import QgsLayoutItemShape, QgsLayoutMeasurement
    shape = QgsLayoutItemShape(layout)
    shape.setShapeType(QgsLayoutItemShape.Rectangle)
    shape.setCornerRadius(QgsLayoutMeasurement(radius))
    shape.setSymbol(QgsFillSymbol.createSimple(
        {"color": fill, "outline_color": INK, "outline_width": "0.3",
         "outline_style": "dash" if dashed else "solid"}))
    shape.attemptMove(QgsLayoutPoint(x, y))
    shape.attemptResize(QgsLayoutSize(w, h))
    layout.addLayoutItem(shape)
    if text:
        pad = 2.2 if halign == 1 else 1.0      # left-aligned text clears arrow tips
        lab = _label(layout, text, x + pad, y + 0.6, w - 2 * pad, h - 1.2, size=size, bold=bold)
        lab.setHAlign(halign)
        lab.setVAlign(0x80)                    # Qt.AlignVCenter
    return shape


def _arrow(layout, *pts, dashed=False):
    line = QgsLayoutItemPolyline(QPolygonF([QPointF(x, y) for x, y in pts]), layout)
    line.setEndMarker(QgsLayoutItemPolyline.ArrowHead)
    line.setArrowHeadWidth(1.6)
    # The head's outline defaults to a thick stroke that fills the triangle
    # into a blob; a hairline outline keeps it a crisp arrowhead.
    line.setArrowHeadStrokeWidth(0.1)
    line.setArrowHeadFillColor(QColor(INK))
    line.setArrowHeadStrokeColor(QColor(INK))
    line.setSymbol(QgsLineSymbol.createSimple(
        {"color": INK, "width": "0.3", "line_style": "dash" if dashed else "solid"}))
    layout.addLayoutItem(line)
    return line


def _line(layout, *pts):
    line = QgsLayoutItemPolyline(QPolygonF([QPointF(x, y) for x, y in pts]), layout)
    line.setSymbol(QgsLineSymbol.createSimple({"color": INK, "width": "0.3"}))
    layout.addLayoutItem(line)
    return line


def _save_diagram(project, layout, stem):
    png = os.path.join(OUT, f"{stem}.png")
    _export_checked(layout, png, [])
    project.layoutManager().addLayout(layout)
    project.write(os.path.join(QGZ, f"{stem}.qgz"))
    print(f"wrote {os.path.relpath(png, ROOT)} and outputs/figures/qgis/{stem}.qgz")


def fig03():
    """Preprocessing chain: seven sources -> common grid -> six scored criteria.

    Wiring follows the code: the GADM outline builds the grid (and masks it);
    the five rasters are reprojected; HydroRIVERS, a vector layer, goes straight
    to the drainage-density derivation; every criterion is then scored to 0-1 by
    its own form (criteria.py), not all by fixed breakpoints.
    """
    project, layout = _new_layout("Figure 3", TOP + 92)
    _label(layout, "Seven open sources become six criteria on one grid of 450 rows × 422 "
                   "columns; two criteria are derived, not downloaded", 9, 1.5, 162, 8, size=8.2,
           bold=True)
    y0 = TOP + 6
    for x, w, t in ((9, 44, "SEVEN SOURCES"), (64, 58, "COMMON GRID"), (131, 39, "SCORED CRITERIA")):
        _label(layout, t, x, TOP, w, 5, size=6.6, bold=True)

    gap = 4.6
    steps = [
        ("Build the grid from the district's bounding box: 450 rows × 422 columns, "
         "EPSG:4326, ≈0.30 km E–W × 0.31 km N–S", 8.5),
        ("Reproject each raster onto the grid. Continuous: bilinear. Categorical: nearest "
         "neighbour (averaging class 4 and class 6 would invent class 5)", 10.5),
        ("Mask to the GADM district outline: 123,555 cells", 6.0),
        ("Fill rim gaps from the nearest valid cell: soil 2.2%, population 2.0%, slope 1.1%, "
         "land cover 0.1%, rainfall 0%", 8.5),
        ("Derive two criteria. Drainage density: river lines densified to 100 m, summed in a "
         "2.5 km circular window. Settlement proximity: exact distance to cells above "
         "400 people/km²", 11.5),
        ("Score each criterion to 0–1 (Fig. A2): fixed ramps for slope, drainage and settlement; "
         "class lookups for soil and land cover; district-relative percentile for rainfall", 10.5),
    ]
    gx, gw, y, box = 64, 58, y0, []
    for i, (t, h) in enumerate(steps):
        _box(layout, gx, y, gw, h, t, size=5.6, halign=1,
             fill="#f2f2f2" if i == 4 else "#ffffff")   # shading = derived
        box.append((y, h, y + h / 2))
        if i < len(steps) - 1:
            _arrow(layout, (gx + gw / 2, y + h), (gx + gw / 2, y + h + gap))
        y += h + gap

    # Sources, each placed beside the step it feeds.
    sx, sw = 9, 44
    _box(layout, sx, box[0][2] - 4, sw, 8, "GADM 4.1 district boundary", size=5.8)
    _arrow(layout, (sx + sw, box[0][2]), (gx, box[0][2]))

    rasters = ["CHIRPS v3.0 annual rainfall, 2014–2024", "HydroSHEDS 3″ DEM → slope (GDAL)",
               "SoilGrids250m (2017) texture class", "MODIS MCD12Q1 v6.1 land cover, 2024",
               "WorldPop 2020 population density"]
    top, bottom = box[1][0], box[3][0] + box[3][1]
    rh = 6.2
    rg = (bottom - top - len(rasters) * rh) / (len(rasters) - 1)
    mids = []
    for i, t in enumerate(rasters):
        ry = top + i * (rh + rg)
        _box(layout, sx, ry, sw, rh, t, size=5.4)
        mids.append(ry + rh / 2)
    bus = 58.5
    for m in mids:
        _line(layout, (sx + sw, m), (bus, m))
    _line(layout, (bus, mids[0]), (bus, mids[-1]))
    _arrow(layout, (bus, box[1][2]), (gx, box[1][2]))

    _box(layout, sx, box[4][2] - 4, sw, 8, "HydroRIVERS v1.0 river lines (vector)", size=5.6)
    _arrow(layout, (sx + sw, box[4][2]), (gx, box[4][2]))

    crit = [("Rainfall", "0.4285"), ("Slope", "0.2254"), ("Soil texture", "0.1535"),
            ("Drainage density*", "0.0932"), ("Land cover", "0.0597"),
            ("Settlement proximity*", "0.0397")]
    ch, cg = 7.6, 2.8
    cy0 = y0 + 14
    for i, (n, wgt) in enumerate(crit):
        _box(layout, 131, cy0 + i * (ch + cg), 39, ch, f"{n}  w = {wgt}", size=5.3, halign=1,
             fill="#f2f2f2" if n.endswith("*") else "#ffffff")
    # Every criterion leaves the scoring step.
    fan = 127
    mids = [cy0 + i * (ch + cg) + ch / 2 for i in range(6)]
    _line(layout, (gx + gw, box[5][2]), (fan, box[5][2]))
    _line(layout, (fan, min(mids)), (fan, max(max(mids), box[5][2])))
    for m in mids:
        _arrow(layout, (fan, m), (131, m))
    _label(layout, "* derived (shaded); weights: baseline AHP, CR = 0.0235", 131,
           cy0 + 6 * (ch + cg), 39, 8, size=5.0)
    _save_diagram(project, layout, "fig03")


def fig04_boxes():
    """The original box diagram, kept for a supplement; Fig 4 is now illustrated."""
    """Research framework, as the code runs it (algorithms.weights_for_algorithm,
    gis_analysis.score_stack): a scenario supplies the pairwise matrix; AHP or
    Fuzzy-AHP turns it into weights; the aggregator combines those weights with
    the cached criteria stack."""
    project, layout = _new_layout("Figure 4", TOP + 112)
    _label(layout, "Every method variant reads the same cached criteria stack, so differences "
                   "between variants come from the method alone", 9, 1.5, 162, 8, size=8.2,
           bold=True)
    # Stage 1 on the right, feeding aggregation directly.
    _box(layout, 9, TOP + 6, 30, 12, "Seven open sources", size=6)
    _arrow(layout, (39, TOP + 12), (104, TOP + 12))
    _box(layout, 104, TOP + 3, 66, 26,
         "STAGE 1 — WEIGHT-INDEPENDENT\ncomputed once, cached\n\ngrid · mask · reproject · fill · "
         "derive\nscore each criterion to 0–1", size=6.0, fill="#e6e6e6")
    # Judgements -> weights
    _box(layout, 9, TOP + 30, 52, 15,
         "Pairwise judgement matrix\nbaseline (CR = 0.0235) or one of four\nalternative scenarios, "
         "each CR < 0.10", size=5.8)
    # The same matrix feeds both weighting methods.
    _line(layout, (35, TOP + 45), (35, TOP + 47.5), (21, TOP + 47.5))
    _line(layout, (35, TOP + 47.5), (49, TOP + 47.5))
    _arrow(layout, (21, TOP + 47.5), (21, TOP + 51))
    _arrow(layout, (49, TOP + 47.5), (49, TOP + 51))
    _box(layout, 9, TOP + 51, 24, 13, "AHP\ncrisp weights", size=6)
    _box(layout, 37, TOP + 51, 24, 13, "Fuzzy-AHP\ntriangular numbers,\nBuckley", size=5.6)
    _line(layout, (21, TOP + 64), (21, TOP + 68), (49, TOP + 68), (49, TOP + 64))
    _arrow(layout, (35, TOP + 68), (35, TOP + 71.5), (60, TOP + 71.5))
    _label(layout, "weights", 37, TOP + 72.2, 20, 4, size=5.4)
    # Aggregation
    _box(layout, 60, TOP + 64, 52, 15, "Aggregation: WLC  |  TOPSIS\n"
         "2 weighting × 2 aggregation = 4 methods", size=6)
    _arrow(layout, (137, TOP + 29), (137, TOP + 71.5), (112, TOP + 71.5))
    _label(layout, "criteria stack (six 0–1 surfaces),\nidentical for every variant",
           139, TOP + 46, 31, 9, size=5.4)
    # Stage 2 and downstream
    _arrow(layout, (86, TOP + 79), (86, TOP + 85))
    _box(layout, 40, TOP + 85, 92, 14,
         "STAGE 2 — RUN PER VARIANT\ncoverage gate ≥ 80% · classify Low ≤ 0.65 < Medium ≤ 0.85 < High\n"
         "area statistics · 25 sites ≥ 5 km apart · per-site explanation", size=5.8, fill="#e6e6e6")
    _arrow(layout, (86, TOP + 99), (86, TOP + 104))
    _box(layout, 30, TOP + 104, 112, 7.5,
         "Sensitivity (three complementary analyses) · consensus (Borda ranking + agreement maps) "
         "· exports", size=5.8)
    _save_diagram(project, layout, "fig04_boxes")


CRIT_COLOUR = {"rainfall": "#009E73", "slope": "#E69F00", "soil": "#CC79A7",
               "drainage": "#56B4E9", "lulc": "#7A6A53", "population": "#5D4E8C"}
CRIT_NAME = {"rainfall": "Rainfall", "slope": "Slope", "soil": "Soil", "drainage": "Drainage",
             "lulc": "Land cover", "population": "Settlement"}
CRIT_ORDER = ["rainfall", "slope", "soil", "drainage", "lulc", "population"]


def _ramp_layer(project, path, name, ramp_name, lo=None, hi=None):
    from qgis.core import (QgsSingleBandPseudoColorRenderer, QgsRasterShader,
                           QgsColorRampShader, QgsStyle)
    lyr = QgsRasterLayer(path, name)
    if not lyr.isValid():
        raise RuntimeError(f"raster failed to load: {path}")
    if lo is None:
        lo, hi = lyr.dataProvider().cumulativeCut(1, 0.02, 0.98)
    ramp = QgsStyle.defaultStyle().colorRamp(ramp_name)
    shader = QgsColorRampShader(lo, hi, ramp, QgsColorRampShader.Interpolated)
    shader.classifyColorRamp(9, 1, QgsRectangle(), None)
    rs = QgsRasterShader()
    rs.setRasterShaderFunction(shader)
    lyr.setRenderer(QgsSingleBandPseudoColorRenderer(lyr.dataProvider(), 1, rs))
    project.addMapLayer(lyr)
    return lyr


def _grey_classes(project, path, name):
    from qgis.core import QgsStyle
    lyr = QgsRasterLayer(path, name)
    classes = QgsPalettedRasterRenderer.classDataFromRaster(
        lyr.dataProvider(), 1, QgsStyle.defaultStyle().colorRamp("Greys"))
    lyr.setRenderer(QgsPalettedRasterRenderer(lyr.dataProvider(), 1, classes))
    project.addMapLayer(lyr)
    return lyr


def _class_layer(project, path, name):
    lyr = QgsRasterLayer(path, name)
    classes = [QgsPalettedRasterRenderer.Class(v, QColor(c), lab)
               for v, (c, lab) in CLASS_COLOURS.items()]
    lyr.setRenderer(QgsPalettedRasterRenderer(lyr.dataProvider(), 1, classes))
    project.addMapLayer(lyr)
    return lyr


def _bar(layout, x, y, w, h, parts):
    """A stacked horizontal bar: parts = [(fraction, colour)]."""
    from qgis.core import QgsLayoutItemShape
    total = sum(f for f, _ in parts)
    for f, colour in parts:
        seg = w * f / total
        s = QgsLayoutItemShape(layout)
        s.setShapeType(QgsLayoutItemShape.Rectangle)
        s.setSymbol(QgsFillSymbol.createSimple(
            {"color": colour, "outline_color": "#ffffff", "outline_width": "0.15"}))
        s.attemptMove(QgsLayoutPoint(x, y))
        s.attemptResize(QgsLayoutSize(seg, h))
        layout.addLayoutItem(s)
        x += seg


def _band(layout, y, h, title):
    _box(layout, 9, y, 162, h, "", fill="#f4f4f4", radius=2.5)
    _label(layout, title, 11, y + 0.8, 150, 4.5, size=6.2, bold=True)


def fig04():
    """Illustrated research framework, built from the project's own outputs.

    Shows the system AND the paper's finding: ★ marks where the analyst's
    decisions enter (scoring, judgement matrix, classification cutoffs), and
    panel (e) is a miniature of Fig 12 showing those decisions move the High
    share far more than the two algorithm choices. Flow as the code runs it:
    the cached stack and the weights meet at aggregation, then classification;
    the scenario comparison is reported under AHP + WLC only (consensus.py).
    Scored criteria use magma, not viridis: in this figure blue means High.
    """
    import json
    from qgis.core import QgsStyle
    meta = json.load(open(os.path.join(INPUTS, "fig04.json"), encoding="utf8"))
    project, layout = _new_layout("Figure 4", TOP + 133)
    project.setCrs(UTM)
    _label(layout, "From seven open datasets to 25 explained sites, and where the analyst's "
                   "decisions enter", 9, 1.5, 162, 6, size=8.2, bold=True)
    boundary = _vec(project, _path("data", "boundary.geojson"), "District boundary")
    _style_fill(boundary, "0,0,0,0", "#000000", 0.25)
    ext = QgsCoordinateTransform(WGS, UTM, project).transformBoundingBox(
        boundary.extent()).buffered(1500)
    STAR = "★"

    def thumb(layers, x, y, w, h):
        m = _map_item(layout, UTM, [boundary] + layers, x, y, w, h, ext, frame=False)
        m.setBackgroundEnabled(False)
        return m

    def text(t, x, y, w, h, size=5.6, bold=False, centre=False):
        lab = _label(layout, t, x, y, w, h, size=size, bold=bold)
        if centre:
            lab.setHAlign(4)
        return lab

    # ── (a) STAGE 1 ────────────────────────────────────────────────────────
    T1 = TOP + 1
    _band(layout, T1, 44, "(a)  STAGE 1  ·  weight-independent  ·  computed once and cached")
    text(f"{STAR} analyst decision; these move the result most (c)", 112, T1 + 0.9, 58,
         4, size=5.6, bold=True)
    raw = [
        (_ramp_layer(project, os.path.join(INPUTS, "raw_rainfall.tif"), "Rainfall", "Greys"), "Rainfall"),
        (_ramp_layer(project, os.path.join(INPUTS, "raw_slope.tif"), "Slope", "Greys"), "Slope"),
        (_grey_classes(project, os.path.join(INPUTS, "raw_soil.tif"), "Soil"), "Soil"),
        (_grey_classes(project, os.path.join(INPUTS, "raw_lulc.tif"), "Land cover"), "Land cover"),
        (_ramp_layer(project, os.path.join(INPUTS, "raw_population.tif"), "Population", "Greys"),
         "Population"),
    ]
    rivers = _vec(project, _path("data", "rivers.geojson"), "Rivers")
    rivers.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(
        {"color": "#555555", "width": "0.12"})))
    raw.append((rivers, "Rivers"))
    text("raw inputs on the grid", 11, T1 + 5.2, 44, 3.5, size=5.6)
    tw, th = 13.6, 13.0
    for i, (lyr, cap) in enumerate(raw):
        x = 11 + (i % 3) * (tw + 1.4)
        y = T1 + 9.2 + (i // 3) * (th + 4.6)
        thumb([lyr], x, y, tw, th)
        text(cap, x - 1, y + th + 0.2, tw + 2, 3.6, size=5.6, centre=True)

    _arrow(layout, (57, T1 + 23), (61.5, T1 + 23))
    cells = _vec(project, os.path.join(INPUTS, "grid_window.geojson"), "Grid cells")
    _style_fill(cells, "#ffffff", "#9a9a9a", 0.12)
    _map_item(layout, UTM, [cells], 62, T1 + 8.5, 17, 12,
              QgsCoordinateTransform(WGS, UTM, project).transformBoundingBox(cells.extent()),
              frame=True)
    text(f"grid from the\nGADM boundary\nreproject · mask\nfill gaps · derive\nscore 0–1 {STAR}",
         60.5, T1 + 21, 20, 18, size=5.6, centre=True)
    _arrow(layout, (80.5, T1 + 23), (84, T1 + 23))

    magma = QgsStyle.defaultStyle().colorRamp("Magma")
    sw, sg = 12.6, 1.5
    for i, crit in enumerate(CRIT_ORDER):
        x = 84 + i * (sw + sg)
        lyr = _ramp_layer(project, os.path.join(INPUTS, f"score_{crit}.tif"),
                          f"{CRIT_NAME[crit]} score", "Magma", 0.0, 1.0)
        thumb([lyr], x, T1 + 8, sw, 13.5)
        _bar(layout, x + 1, T1 + 22.0, sw - 2, 1.1, [(1, CRIT_COLOUR[crit])])
        star = f" {STAR}" if crit == "rainfall" else ""
        text(f"{CRIT_NAME[crit]}{star}\nw = {meta['weights'][crit]:.2f}", x - 1.5, T1 + 23.4,
             sw + 3, 7, size=5.6, centre=True)
    _bar(layout, 84, T1 + 33.0, 26, 2.0, [(1, magma.color(k / 9).name()) for k in range(10)])
    text("0", 82.6, T1 + 35.2, 4, 3.4, size=5.6)
    text("1", 108.7, T1 + 35.2, 4, 3.4, size=5.6)
    text("score: 0 poor → 1 best", 112, T1 + 32.4, 58, 3.6, size=5.6)
    text(f"{STAR} rainfall: scored by district percentile", 112, T1 + 36.4,
         58, 3.6, size=5.6)
    text("same cached stack → every method", 89, T1 + 40.2, 50, 3.6, size=5.6, bold=True)

    # ── (b) STAGE 2 ────────────────────────────────────────────────────────
    T2 = TOP + 48
    _band(layout, T2, 54, "(b)  STAGE 2  ·  run for each method variant")
    _box(layout, 11, T2 + 6.5, 46, 8.5, f"Pairwise judgement matrix {STAR}\nbaseline CR = 0.0235",
         size=5.6)
    _line(layout, (34, T2 + 15), (34, T2 + 16.8), (22.5, T2 + 16.8))
    _line(layout, (34, T2 + 16.8), (45.5, T2 + 16.8))
    _arrow(layout, (22.5, T2 + 16.8), (22.5, T2 + 19))
    _arrow(layout, (45.5, T2 + 16.8), (45.5, T2 + 19))
    _box(layout, 11, T2 + 19, 22, 6, "AHP", size=5.8)
    _box(layout, 35, T2 + 19, 22, 6, "Fuzzy-AHP", size=5.8)
    _arrow(layout, (34, T2 + 25), (34, T2 + 27.6))
    _bar(layout, 11, T2 + 27.6, 46, 4.2,
         [(meta["weights"][c], CRIT_COLOUR[c]) for c in CRIT_ORDER])
    # No separate colour key: panel (a) already names each colour under its map.
    text("weights (baseline AHP); colours as in (a)", 11, T2 + 32.0, 46, 3.6, size=5.6)
    text("Scenarios reweight the matrix;\nreported under AHP + WLC (Fig. 8)", 11, T2 + 38.0, 46,
         7, size=5.6)

    # aggregation and classification, where weights and stack meet
    _box(layout, 62, T2 + 5.5, 50, 6.2, f"aggregate WLC | TOPSIS → classify 0.65/0.85 {STAR}",
         size=5.4, fill="#ffffff")
    _arrow(layout, (87, T1 + 40), (87, T2 + 5.5))
    _arrow(layout, (57, T2 + 29.7), (59.5, T2 + 29.7), (59.5, T2 + 8.6), (62, T2 + 8.6))
    _arrow(layout, (87, T2 + 11.7), (87, T2 + 14.0))
    # 2 x 2: columns TOPSIS | WLC, rows AHP | Fuzzy-AHP; AHP + WLC sits top-right,
    # next to the baseline map it feeds.
    names = {m["code"]: m for m in meta["methods"]}
    mw, mh = 22.5, 14.0
    cols = {"TOPSIS": 63.0, "WLC": 88.5}
    rows = {"AHP": T2 + 18.5, "Fuzzy-AHP": T2 + 36.5}
    text("TOPSIS", cols["TOPSIS"], T2 + 14.3, mw, 3.8, size=5.8, bold=True, centre=True)
    text("WLC", cols["WLC"], T2 + 14.3, mw, 3.8, size=5.8, bold=True, centre=True)
    layout_of = {1: ("AHP", "WLC"), 2: ("AHP", "TOPSIS"), 3: ("Fuzzy-AHP", "WLC"),
                 4: ("Fuzzy-AHP", "TOPSIS")}
    for code, (r, c) in layout_of.items():
        x, y = cols[c], rows[r]
        lyr = _class_layer(project, os.path.join(INPUTS, f"class_{code}.tif"),
                           names[code]["name"])
        m = thumb([lyr], x, y, mw, mh)
        if code == 1:
            m.setFrameEnabled(True)
            from qgis.core import QgsLayoutMeasurement
            m.setFrameStrokeWidth(QgsLayoutMeasurement(0.5))
        text(f"{r} · {names[code]['high_pct']:.2f}%", x - 1, y + mh + 0.9, mw + 2, 3.6,
             size=5.4, centre=True)
    _arrow(layout, (cols["WLC"] + mw, rows["AHP"] + mh / 2), (118.5, rows["AHP"] + mh / 2))

    sites = QgsVectorLayer(_path("outputs", "rwh_sites.geojson"), "Sites", "ogr")
    sites.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "size": "1.1", "color": "0,0,0,0", "outline_color": "#000000",
         "outline_width": "0.3"})))
    project.addMapLayer(sites)
    base = project.mapLayersByName(names[1]["name"])[0]
    thumb([sites, base], 120, T2 + 5, 48, 33)
    text("AHP + WLC baseline: 25 sites ≥ 5 km apart", 117, T2 + 38.6, 54, 3.8, size=5.6,
         bold=True, centre=True)
    for i, (code, lab) in enumerate(((3, "High"), (2, "Medium"), (1, "Low"))):
        x = 124 + i * 15
        _bar(layout, x, T2 + 43.6, 2.4, 2.0, [(1, CLASS_COLOURS[code][0])])
        text(lab, x + 3, T2 + 42.8, 12, 3.6, size=5.6)
    text("% = share of the district classed High", 117, T2 + 47.6, 54, 3.6, size=5.4,
         centre=True)

    # ── outputs ────────────────────────────────────────────────────────────
    T3 = TOP + 105
    for x in (34, 87, 141.5):
        _arrow(layout, (x, T2 + 54), (x, T3 + 0.2))

    # (d) consensus
    _box(layout, 64, T3, 46, 27, "", fill="#ffffff")
    text("(d) CONSENSUS", 65.5, T3 + 1, 43, 3.8, size=5.8, bold=True)
    agree = QgsRasterLayer(os.path.join(INPUTS, "agree4.tif"), "High under all four")
    agree.setRenderer(QgsPalettedRasterRenderer(agree.dataProvider(), 1, [
        QgsPalettedRasterRenderer.Class(4, QColor(CLASS_COLOURS[3][0]), "all four")]))
    project.addMapLayer(agree)
    csites = QgsVectorLayer(os.path.join(INPUTS, "consensus_sites.geojson"), "Consensus sites",
                            "ogr")
    csites.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "size": "1.1", "color": "0,0,0,0", "outline_color": "#000000",
         "outline_width": "0.3"})))
    project.addMapLayer(csites)
    thumb([csites, agree], 65, T3 + 5, 21, 21)
    text(f"{meta['consensus_sites']} sites chosen by\nall four methods\n(rings)\n\n"
         f"{meta['all4_high_km2']:.1f} km² High\nunder all four (blue)", 87, T3 + 5.5, 23, 21,
         size=5.4)

    # (e) explainability, on an absolute 0–1 score axis
    _box(layout, 113, T3, 57, 27, "", fill="#ffffff")
    r1 = meta["rank1"]
    text(f"(e) WHY RANK 1 SCORES {r1['score']:.3f}", 114.5, T3 + 1, 54, 3.8, size=5.8, bold=True)
    bx, bwid = 116, 50
    parts = [(r1["contrib"][c], CRIT_COLOUR[c]) for c in CRIT_ORDER if c in r1["contrib"]]
    total = sum(f for f, _ in parts)
    _bar(layout, bx, T3 + 9, bwid * total, 4.4, parts)
    # The paper's main caveat in miniature: rank 1 scores 1.0 on soil because it
    # sits on Loam, the only texture scored 1.00, which covers 0.38% of the district.
    pre = sum(r1["contrib"][c] for c in CRIT_ORDER[:CRIT_ORDER.index("soil")])
    sx = bx + bwid * (pre + r1["contrib"]["soil"] / 2)
    text("soil: Loam, 0.38% of district", sx - 18, T3 + 4.6, 36, 3.4, size=5.0, centre=True)
    _line(layout, (sx, T3 + 7.9), (sx, T3 + 9))
    from qgis.core import QgsLayoutItemShape
    gap = QgsLayoutItemShape(layout)
    gap.setShapeType(QgsLayoutItemShape.Rectangle)
    gap.setSymbol(QgsFillSymbol.createSimple(
        {"color": "#9a9a9a", "style": "b_diagonal", "outline_color": "#9a9a9a",
         "outline_width": "0.15"}))
    gap.attemptMove(QgsLayoutPoint(bx + bwid * total, T3 + 9))
    gap.attemptResize(QgsLayoutSize(bwid * (1 - total), 4.4))
    layout.addLayoutItem(gap)
    _line(layout, (bx, T3 + 14.2), (bx + bwid, T3 + 14.2))
    for v in (0, 0.5, 1):
        _line(layout, (bx + bwid * v, T3 + 14.2), (bx + bwid * v, T3 + 15.0))
        text(f"{v:g}", bx + bwid * v - 3, T3 + 15.2, 6, 3.4, size=5.4, centre=True)
    text(f"segment = weight × score; hatched = shortfall {1 - total:.3f}", 114.5, T3 + 19.2, 55,
         3.6, size=5.4)

    # (c) what moves the High share: miniature of Fig 12
    _box(layout, 11, T3, 50, 27, "", fill="#ffffff")
    text("(c) WHAT MOVES THE HIGH SHARE (pp)", 12.5, T3 + 1, 48, 3.8, size=5.8, bold=True)
    f12 = meta["fig12"]
    effects = [(f"cutoffs, range of 4 {STAR}", abs(f12["high_cutoff_range_pp"]), "#3a3a3a"),
               (f"rainfall scoring, 1 swap {STAR}", abs(f12["high_rainfall_pp"]), "#3a3a3a"),
               (f"judgements, range of 5 {STAR}", abs(f12["high_scenario_range_pp"]), "#3a3a3a"),
               ("aggregation, main effect", abs(f12["high_aggregation_pp"]), "#a0a0a0"),
               ("weighting, main effect", abs(f12["high_weighting_pp"]), "#a0a0a0")]
    vmax = max(v for _, v, _ in effects)
    for i, (lab, v, colour) in enumerate(effects):
        y = T3 + 5.4 + i * 4.0
        text(lab, 12.5, y - 0.3, 25, 3.6, size=5.3)
        _bar(layout, 37.5, y, max(15 * v / vmax, 0.3), 2.6, [(1, colour)])
        text(f"{v:.2f}" if v < 10 else f"{v:.1f}", 37.5 + 15 * v / vmax + 0.6, y - 0.4, 8, 3.6,
             size=5.3)
    _save_diagram(project, layout, "fig04")


def fig20():
    """Model to field: where this study stops and practice begins."""
    project, layout = _new_layout("Figure 20", TOP + 63)
    _label(layout, "The model narrows 123,555 cells to a shortlist; every step from field "
                   "reconnaissance onward remains to be done", 9, 1.5, 162, 8, size=8.2, bold=True)
    _box(layout, 9, TOP + 2, 64, 58, "", fill="#e6e6e6", radius=2)
    _label(layout, "THIS STUDY", 11, TOP + 3.5, 40, 5, size=6.6, bold=True)
    _box(layout, 12, TOP + 12, 25, 26, "GIS-MCDA\nsix criteria\nfour methods\n25 sites per method",
         size=5.8)
    _arrow(layout, (37, TOP + 25), (43, TOP + 25))
    _box(layout, 43, TOP + 12, 27, 26,
         "Consensus screening\n\n15 sites picked by\nall 4 methods\n\n528.5 km² High\nunder all 4",
         size=5.6)

    _box(layout, 79, TOP + 2, 91, 58, "", fill="#ffffff", dashed=True, radius=2)
    _label(layout, "NOT DONE", 81, TOP + 3.5, 40, 5, size=6.6, bold=True)
    _arrow(layout, (70, TOP + 25), (77, TOP + 25), (77, TOP + 20), (83, TOP + 20))
    steps = [("Field\nreconnaissance", 83, TOP + 13), ("Hydrological\nsurvey", 112, TOP + 13),
             ("Soil and\npercolation tests", 141, TOP + 13), ("Ownership and\ncost enquiry", 83, TOP + 39),
             ("Engineering\ndesign", 112, TOP + 39), ("Final siting", 141, TOP + 39)]
    for t, x, y in steps:
        _box(layout, x, y, 24, 14, t, size=5.8, dashed=True)
    for x1, x2, y in ((107, 112, TOP + 20), (136, 141, TOP + 20), (107, 112, TOP + 46),
                      (136, 141, TOP + 46)):
        _arrow(layout, (x1, y), (x2, y), dashed=True)
    _arrow(layout, (153, TOP + 27), (153, TOP + 33), (95, TOP + 33), (95, TOP + 39), dashed=True)
    # The "15 sites" definition belongs in the caption, not the image.
    _save_diagram(project, layout, "fig20")


def fig_val_map():
    """Retained MGNREGA water works over the baseline classified surface.

    Presences from outputs/validation/presences_final.gpkg (tools/validate_mgnrega.py).
    Block boundaries are drawn from the Census 2011 talukas: Chandrapur's 15
    MGNREGA blocks and 15 talukas share names and extents (an approximation).
    """
    import json
    _load_house_font()
    project = QgsProject.instance()
    project.clear()
    project.setCrs(UTM)
    summ = json.load(open(_path("outputs", "validation", "validation_summary.json")))
    g = summ["gains"]["AHP + WLC"]
    base = f"AHP + WLC|{summ['baseline']}"
    r = summ["results"][base]

    suit = QgsRasterLayer(_path("outputs", "rwh_suitability_classified.tif"), "Suitability class")
    suit.setRenderer(QgsPalettedRasterRenderer(suit.dataProvider(), 1, [
        QgsPalettedRasterRenderer.Class(v, QColor(c), lab)
        for v, (c, lab) in sorted(CLASS_COLOURS.items(), reverse=True)]))
    project.addMapLayer(suit)
    blocks = _vec(project, _path("data", "raw", "talukas",
                                 "chandrapur_talukas_filled_to_boundary.geojson"), "Block")
    _style_fill(blocks, "0,0,0,0", "#6e6e6e", 0.2)
    _labels(blocks, "taluka", 5.6, colour="#2b2b2b", placement=QgsPalLayerSettings.Horizontal)
    pres = _vec(project, _path("outputs", "validation", "presences_final.gpkg"),
                f"Water work (n = {summ['n_presence']:,})")
    pres.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "size": "0.55", "color": "#111111", "outline_style": "no"})))
    boundary = _vec(project, _path("data", "boundary.geojson"), "District boundary")
    _style_fill(boundary, "0,0,0,0", "#000000", 0.45)

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName("Validation map")
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(PAGE_W, TOP + 124))
    _label(layout, f"Recorded water works concentrate on High land: {g['High'][1]:.1f}% of works on "
                   f"{g['High'][0]:.1f}% of the area ({g['High'][2]:.2f}×)", 9, 1.5, 162, 8,
           size=8.2, bold=True)
    ext = QgsCoordinateTransform(WGS, UTM, project).transformBoundingBox(
        boundary.extent()).buffered(2500)
    m = _map_item(layout, UTM, [pres, boundary, blocks, suit], 9, TOP, 112, 112, ext)
    _graticule(m, 0.5)
    _north_arrow(layout, 112, TOP + 1.2)
    _scalebar(layout, m, 10, 2, 92, TOP + 104)

    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("")
    legend.setLinkedMap(m)
    legend.setAutoUpdateModel(False)
    root = legend.model().rootGroup()
    root.removeAllChildren()
    nodes = {l.id(): root.addLayer(l) for l in (pres, suit, blocks, boundary)}
    for st in (QgsLegendStyle.Title, QgsLegendStyle.Group, QgsLegendStyle.Subgroup,
               QgsLegendStyle.SymbolLabel):
        legend.rstyle(st).setTextFormat(_text(6.0, bold=st == QgsLegendStyle.Subgroup))
    legend.setSymbolWidth(4.2)
    legend.setSymbolHeight(2.6)
    legend.setBackgroundEnabled(False)
    legend.attemptMove(QgsLayoutPoint(125, TOP + 4))
    layout.addLayoutItem(legend)
    QgsMapLayerLegendUtils.setLegendNodeOrder(nodes[suit.id()], [1, 2, 3])
    legend.model().refreshLayerLegend(nodes[suit.id()])
    legend.updateLegend()
    legend.adjustBoxSize()

    lines = [f"{c}: {g[c][1]:.1f}% of works, {g[c][0]:.1f}% of area ({g[c][2]:.2f}×)"
             for c in ("High", "Medium", "Low")]
    _label(layout, "Baseline AHP + WLC\n\n" + "\n".join(lines) +
           f"\n\nROC AUC {r['auc']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]\n\n"
           "Works are MGNREGA category segments WC/WH, one per 3 × 3-cell "
           "neighbourhood. The photo audit found 17–50% show a harvesting "
           "structure, so these are works recorded under water categories, "
           "not verified structures.", 125, TOP + 46, 47, 64, size=5.8)
    _label(layout, "UTM 44N (EPSG:32644). Works: Bhuvan Bhugram accepted geotags (2026-10-04). "
                   "Blocks drawn from Census 2011 taluka boundaries.", 9, TOP + 119, 162, 5,
           size=5.0)
    _export_checked(layout, os.path.join(OUT, "fig_val_map.png"), [(m, blocks, "taluka")])
    project.layoutManager().addLayout(layout)
    project.write(os.path.join(QGZ, "fig_val_map.qgz"))
    print("wrote outputs/figures/fig_val_map.png")


if __name__ == "__main__":
    app = QgsApplication([], False)
    app.initQgis()
    try:
        {"fig01": fig01, "fig03": fig03, "fig04": fig04, "fig04_boxes": fig04_boxes, "fig07": fig07, "fig20": fig20,
         "hydrology": fig_hydrology, "fig_val_map": fig_val_map}[sys.argv[1] if len(sys.argv) > 1 else "fig07"]()
    finally:
        app.exitQgis()
