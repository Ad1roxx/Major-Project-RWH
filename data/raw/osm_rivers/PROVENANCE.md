# Named rivers — OpenStreetMap — provenance

**Pulled:** 2026-10-20 (OSM data timestamp 2026-10-20T09:12:21Z), to label
rivers on the study-area figure. Display only: the model's drainage criterion
still uses HydroRIVERS (`data/rivers.geojson`), which carries no names.

**Query** (Overpass API, `https://overpass-api.de/api/interpreter`):

```
[out:json][timeout:120];(way["waterway"="river"]["name"](19.35,78.70,20.85,80.10););out geom tags;
```

The bounding box is the district plus a margin.

**Files:**

| File | Contents |
|---|---|
| `overpass_named_rivers.json` | Raw response, byte for byte, sha256 `9116bedefb7cca66966bf66dc6d5de5f6825a9357b0b359b2b4e6499e9b7993a`. 89 named river ways |
| `chandrapur_named_rivers_osm.geojson` | The ways of every named river with any length within 3 km of `data/boundary.geojson`. Columns: `osm_id`, `name`, `name_en`, `name_mr` |

**Licence:** © OpenStreetMap contributors, ODbL 1.0. Credit it in any figure
caption that uses these names.

**Notes:**
- Some rivers appear under two spellings because different OSM ways carry
  different names: "Andhari" and "Andhari river", "Erai" and "Erai river",
  "Dabha" and "Dabha Nadi".
- The Wainganga runs mostly just outside the outline: 32.9 km inside, 195 km
  within 3 km. It forms the eastern boundary. The Wardha forms the western
  boundary: 182.7 km inside, 198 km within 3 km.
- OSM names are crowd-sourced. Check the names to be labelled before a figure
  is published.
