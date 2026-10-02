
# RWH Suitability Analysis - AHP Process & Output Explanation

## 📋 WHAT IS AHP (Analytic Hierarchy Process)?

AHP is a **multi-criteria decision-making technique** that helps rank alternatives based on multiple factors.

### How AHP Works for RWH Suitability:

**Step 1: Define Criteria**
- **Slope** (0.208) - Lower slopes are better for water harvesting
- **Rainfall** (0.514) - Higher rainfall = more water to harvest ✅ *Highest weight*
- **Drainage** (0.076) - Proximity to rivers/water bodies
- **Soil** (0.136) - Soil infiltration capacity
- **LULC** (0.043) - Land use/land cover type (agricultural areas preferred)
- **Population** (0.023) - Lower population areas (more suitable)

**Step 2: Pairwise Comparisons**
- Creates a comparison matrix (1-9 scale)
- Expert judgment: rainfall gets highest weight (0.514) because water availability is critical
- All weights sum to 1.0

**Step 3: Consistency Check**
- Consistency Ratio (CR) < 0.1 = ✅ Acceptable
- Your CR: 0.080 = Good (indicates reliable weights)

**Step 4: Weighted Overlay**
- Each raster is normalized to 0-1 scale
- Each pixel = (Slope×0.208) + (Rainfall×0.514) + (Drainage×0.076) + ... 
- Final suitability score per pixel: 0 (unsuitable) to 1 (highly suitable)

**Step 5: Classification**
- **Low Suitability** (Red) - Bottom 33% of scores
- **Medium Suitability** (Yellow) - Middle 33%
- **High Suitability** (Green) - Top 33% ⭐

**Step 6: Extract Top Locations**
- Identifies 10 highest-scoring pixels
- Returns as candidates with coordinates

---

## 🗺️ WHAT'S NOW SHOWING ON THE MAP?

After the fixes:

### 1. **Suitability Heatmap** (Red → Yellow → Green)
- Shows entire district color-coded by suitability
- Red zones = unsuitable
- Green zones = highly suitable for RWH
- Smooth gradient showing suitability levels

### 2. **High Suitability Zones** (Green polygons)
- Contiguous areas with highest suitability (top 33%)
- These are ideal candidate regions

### 3. **Top Candidate Locations** (Gold ⭐ markers)
- Rank #1 = Gold star (best location)
- Rank #2 = Silver star (2nd best)
- Rank #3 = Bronze star (3rd best)
- Ranks 4-10 = Green dots

### 4. **Rivers/Drainage** (Blue lines)
- For reference - proximity to rivers increases suitability

### 5. **District Boundary** (Grey dashed line)
- Study area boundary

---

## 📂 HOW TO ADD YOUR LULC FILE

**You mentioned you have a LULC (Land Use/Land Cover) TIFF file ready!**

### Step 1: Copy your LULC file
```
Copy: C:\path\to\your\lulc.tif
To:   C:\Users\Personal\Documents\KJSCE\Major Project\rwh_gis_assistant\data\
Rename to: lulc.tif
```

### Step 2: Verify in the app
- Launch the app: `streamlit run app.py`
- In the sidebar "Data Status", you should see:
  - ✅ Land Use/Land Cover (Raster) 🎯 (green checkmark)
  - If ❌ (red X), the file isn't in the right place

### Step 3: Run analysis
- The LULC will now be automatically included in the weighted overlay
- LULC weight: 0.043 (looks for agricultural, open land favorable for RWH)
- Run your query to see updated results

---

## 🔄 HOW SUITABILITY SCORING WORKS

### Example: A pixel gets scored as follows:

```
Normalized Values (0-1 scale):
  Slope:       0.85 (low slope - good)
  Rainfall:    0.92 (high rainfall - excellent)
  Drainage:    0.60 (moderate distance - average)
  Soil:        0.70 (good infiltration)
  LULC:        0.80 (agricultural land - good)
  Population:  0.95 (sparse - excellent)

Weighted Sum:
  (0.85 × 0.208) + (0.92 × 0.514) + (0.60 × 0.076) + (0.70 × 0.136) + (0.80 × 0.043) + (0.95 × 0.023)
  = 0.177 + 0.473 + 0.046 + 0.095 + 0.034 + 0.022
  = 0.847 ← HIGH SUITABILITY (85%)
```

This pixel would be classified as **HIGH** (top 33%) ✅

---

## 📊 UNDERSTANDING THE INSIGHTS SECTION

### Top Contributing Factors
Shows which criteria influenced the result most:
- **Rainfall: 0.514** - Highest weight (water availability critical)
- **Slope: 0.208** - Terrain accessibility
- **Soil: 0.136** - Infiltration capacity

### Analysis Notes
- ✅ Green checkmark = Layer successfully loaded
- ⚠️ Yellow warning = Missing file (uses default weight)
- 🔴 Red error = Critical issue

---

## 🎯 INTERPRETING THE OUTPUT

### Map Visualization
- **Red zones** → Avoid these areas (low suitability)
- **Yellow zones** → Secondary priority (medium suitability)
- **Green zones** → Focus here (high suitability) 🎯
- **Gold star ⭐** → Best single location for RWH structure

### Top Candidate Locations
Each shows:
- **Rank #1** - Best single-point location
- **Score: 0.847** - Suitability score (0-1)
- **Coordinates** - Latitude/Longitude for GPS/field visit

### Use Cases
- **Bulk water harvesting**: Focus on green zones
- **Community tanks**: Place at Rank #1 location
- **Check dams**: Distribute across high-suitability areas
- **Farm-level RWH**: Consider your specific farm characteristics

---

## 🔧 CUSTOMIZING WEIGHTS (Optional)

To prioritize specific criteria, modify `ahp.py`:

```python
# In AHP matrix, increase rainfall row relative to others
self.matrix = np.array([
    [1, 1/5, 3, 2, 4, 5],      # slope (decreased from 1/3)
    [5, 1, 5, 3, 6, 7],        # rainfall (increased from 3) ← PRIORITIZE
    [1/3, 1/5, 1, 1/2, 2, 3],  # drainage
    # ...
])
```

Then recalculate weights using consistency check.

---

## ✅ CHECKLIST TO VERIFY EVERYTHING WORKS

- [ ] All required files in `data/` folder:
  - ✅ boundary.geojson
  - ✅ rivers.geojson
  - ✅ dem.tif
  - ✅ rainfall.tif
  - ✅ population.tif
  - ✅ **lulc.tif** (your new file)
  - ⚠️ soil.tif (optional - uses default if missing)

- [ ] Streamlit app runs without errors
- [ ] Map shows:
  - [ ] Suitability heatmap (red/yellow/green colors)
  - [ ] Top location markers with gold/silver/bronze stars
  - [ ] Rivers in blue
  - [ ] District boundary outline

- [ ] Results section shows:
  - [ ] AHP weights table with consistency ratio < 0.1
  - [ ] Top candidate coordinates
  - [ ] Analysis notes with ✅ for loaded files

---

## 📌 COMMON ISSUES & FIXES

| Issue | Cause | Fix |
|-------|-------|-----|
| Only rivers showing | Suitability raster not rendering | Ensure rainfall.tif exists in data/ |
| No markers on map | top_locations not generated | Check if rasters have valid data |
| ❌ LULC in data status | File not copied | Copy lulc.tif to data/ folder |
| Red warnings in notes | Missing raster file | Add file or ignore (uses defaults) |
| High inconsistency (CR > 0.1) | AHP matrix out of balance | Review expert judgments in ahp.py |

---

## 📞 NEXT STEPS

1. **Copy your LULC file** to `data/lulc.tif`
2. **Restart the app**
3. **Run the analysis** with your query
4. **Check the map** for suitability visualization
5. **Review top 5 locations** for field verification

The suitability map and heatmap should now display correctly! 🎉
