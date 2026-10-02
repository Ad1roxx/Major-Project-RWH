"""
setup_data.py
─────────────
Helper script to prepare QGIS data files for the RWH GIS Assistant.

Converts shapefiles to GeoJSON and renames files to standard names.
Run this after placing your QGIS exports in the data/ folder.

Usage:
    python setup_data.py
"""

import os
import geopandas as gpd
from pathlib import Path

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def convert_shapefiles_to_geojson():
    """Convert any shapefiles in data/ to GeoJSON."""
    print("Looking for shapefiles to convert...")
    
    shapefile_map = {
        "Clipped_rivers": "rivers.geojson",
        "Clipper_rivers": "rivers.geojson",
        "rivers": "rivers.geojson",
        "River": "rivers.geojson",
    }
    
    for fname, target_name in shapefile_map.items():
        shp_path = os.path.join(DATA_DIR, f"{fname}.shp")
        if os.path.exists(shp_path):
            print(f"  Found: {fname}.shp")
            try:
                gdf = gpd.read_file(shp_path)
                # Ensure EPSG:4326
                if gdf.crs is None:
                    gdf = gdf.set_crs("EPSG:4326")
                elif gdf.crs.to_epsg() != 4326:
                    gdf = gdf.to_crs("EPSG:4326")
                
                output_path = os.path.join(DATA_DIR, target_name)
                gdf.to_file(output_path, driver="GeoJSON")
                print(f"  [OK] Converted to {target_name}")
            except Exception as e:
                print(f"  [ERROR] {fname}: {e}")
        else:
            print(f"  [SKIP] {fname}.shp not found")

def rename_files():
    """Rename files to standard names if they exist."""
    print("\nRenaming files to standard names...")
    
    rename_map = {
        "boundary.geojson": "boundary.geojson",  # Already correct
        "rainfall.tif": "rainfall.tif",          # Already correct
        "dem.tif": "dem.tif",                    # Already correct
        "Derived_Slope(Degrees).tif": "slope.tif",
        "Soil_Texture_Chandrapur(correct CRS).tif": "soil_texture.tif",
        "Chandrapur_population.tif": "population.tif",
        "population.tif": "population.tif",
    }
    
    for old_name, new_name in rename_map.items():
        old_path = os.path.join(DATA_DIR, old_name)
        new_path = os.path.join(DATA_DIR, new_name)
        
        if os.path.exists(old_path) and old_name != new_name:
            try:
                os.rename(old_path, new_path)
                print(f"  [OK] {old_name} -> {new_name}")
            except Exception as e:
                print(f"  [ERROR] Renaming {old_name}: {e}")

def check_data_status():
    """Print status of data files."""
    print("\nData files status:")
    
    required = {
        "boundary.geojson": "Chandrapur Boundary",
        "rivers.geojson": "Rivers / Drainage",
        "rainfall.tif": "Rainfall Raster",
        "slope.tif": "Derived Slope (Degrees)",
        "soil_texture.tif": "Soil Texture",
    }
    
    optional = {
        "dem.tif": "DEM / Elevation (optional)",
        "lulc.tif": "Land Use/Land Cover (optional)",
        "population.tif": "Population Density (optional)",
    }
    
    print("\n  Required:")
    for fname, label in required.items():
        path = os.path.join(DATA_DIR, fname)
        status = "OK" if os.path.exists(path) else "MISSING"
        print(f"    [{status}] {label:30s} ({fname})")
    
    print("\n  Optional:")
    for fname, label in optional.items():
        path = os.path.join(DATA_DIR, fname)
        status = "OK" if os.path.exists(path) else "SKIP"
        print(f"    [{status}] {label:30s} ({fname})")

if __name__ == "__main__":
    print("=" * 70)
    print("RWH GIS Assistant - Data Setup")
    print("=" * 70)
    
    convert_shapefiles_to_geojson()
    rename_files()
    check_data_status()
    
    print("\n" + "=" * 70)
    print("Setup complete! You can now run: streamlit run app.py")
    print("=" * 70)
