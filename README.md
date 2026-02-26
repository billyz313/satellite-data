# Satellite Data API - OpenET Integration
A Django REST API that fetches and analyzes satellite data (ET and NDVI) from the OpenET API with AI-powered insights and comprehensive water use analytics.

## 🌟 Features
* 📍 Point-based queries - Get satellite data for specific coordinates
* 🔷 Polygon-based queries - Analyze data for custom geographic areas
* 🤖 AI-generated summaries - Automated analysis and insights
* 💧 ET (Evapotranspiration) Analysis - Comprehensive water use metrics
* 🌱 NDVI (Vegetation) Analysis - Vegetation health and vigor assessment
* 📊 Seasonal & Yearly Trends - Long-term pattern analysis
* 🎨 Interactive Web UI - User-friendly map-based interface with drawing tools
* 🔌 RESTful API - Programmatic access with JSON responses

## 🔧 Requirements
* Python 3.8+
* Django 4.0+
* Django REST Framework 3.14+
* numpy 1.24+
* requests 2.31+

## 📦 Installation
1. Clone the repository

```bash
conda env create -f environment.yml
```

Add a file named .env in the base directory.  Add the following lines:
```bash
OPENAI_BASE_URL=https://the_url_to_your_openai_api
OPENAI_API_KEY=your_openai_api_key
OPENET_API_KEY=your_openet_api_key
```

2. Activate the environment

```bash
conda activate satellite_data
```

3. Create the database and superuser
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

At this point you should be able to start the application. From the root directory you can run the following command

```bash
python manage.py runserver
```

## 🚀 Usage
### Web Interface
Access the interactive web interface at:

```bash
http://localhost:8000/satellite-data-form/
```

### Features:

🗺️ Interactive maps with click-to-select points

✏️ Drawing tools for creating polygons

📋 Copy/paste GeoJSON support

📊 Beautiful results visualization

💻 Auto-generated cURL commands

### API
The API is available at:
http://localhost:8000/api/satellite-data/

## 📖 API Documentation
### Point Query (GET)
Fetch satellite data for a specific coordinate.

#### Parameters:

lat (float, required): Latitude (-90 to 90)
lon (float, required): Longitude (-180 to 180)
start_date (string, required): Start date (YYYY-MM-DD)
end_date (string, required): End date (YYYY-MM-DD)

#### Example:

```bash
curl "http://localhost:8000/api/satellite-data/?lat=38.057304&lon=-101.054197&start_date=2020-01-01&end_date=2024-12-31"
```

### Polygon Query (POST)
Fetch satellite data for a polygon area.

#### Request Body:
```json
{
  "polygon": <polygon_data>,
  "start_date": "2020-01-01",
  "end_date": "2024-12-31"
}
```

### Supported Polygon Formats:

* **Flat array**: [-101.058, 38.059, -101.057, 38.060, ...]
* **Coordinate pairs**: [[-101.058, 38.059], [-101.057, 38.060], ...]
* **GeoJSON Polygon**: {"type": "Polygon", "coordinates": [[[...]]]}
* **GeoJSON Feature**: {"type": "Feature", "geometry": {...}}
* **GeoJSON FeatureCollection**: {"type": "FeatureCollection", "features": [...]}

#### Example:
```json
curl -X POST http://localhost:8000/api/satellite-data/ \
  -H "Content-Type: application/json" \
  -d '{
    "polygon": {
      "type": "Polygon",
      "coordinates": [[
        [-101.058275, 38.058942],
        [-101.057374, 38.059787],
        [-101.056322, 38.060412],
        [-101.058275, 38.058942]
      ]]
    },
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
  }'
  ```

## 📦 Response Format
The API returns comprehensive JSON data:

```json
{
  "NDVI": {
    "source": "OpenET",
    "location": "38.057304, -101.054197",
    "values_found": 138,
    "date_range": "2020-01-01 to 2024-12-31",
    "ndvi_mean": 0.483,
    "data_points": [
      {"date": "2020-01-01", "NDVI": 0.221}
    ]
  },
  "ET": {
    "source": "OpenET",
    "location": "38.057304, -101.054197",
    "values_found": 138,
    "date_range": "2020-01-01 to 2024-12-31",
    "et_mean": 64.2,
    "data_points": [
      {"date": "2020-01-01", "ET": 31}
    ]
  },
  "et_analysis": {
    "total_et_mm": 4689,
    "mean_monthly_et_mm": 64.2,
    "max_monthly_et_mm": 197,
    "min_monthly_et_mm": 12,
    "peak_et_month": "2021-07-01",
    "total_et_inches": 184.61,
    "growing_season_et_mm": 3779,
    "growing_season_et_inches": 148.78,
    "observations": 73,
    "yearly_totals_mm": {
      "2020": 719,
      "2021": 900
    },
    "seasonal_totals_mm": {
      "winter": 472,
      "spring": 1152,
      "summer": 2016,
      "fall": 1049
    },
    "monthly_trend": "stable",
    "trend_slope_mm_per_month": 0.058,
    "et_variability": {
      "std_dev_mm": 48.8,
      "coefficient_of_variation": 0.76,
      "consistency": "low"
    },
    "water_use_classification": "very_high_water_use",
    "water_use_description": "Significantly high water consumption"
  },
  "vegetation_summary": {
    "total_observations": 168,
    "mean_ndvi": 0.432,
    "max_ndvi": 0.847,
    "min_ndvi": 0.101,
    "std_dev": 0.214,
    "vigor_classification": "Moderate vegetation",
    "data_sources": ["OpenET"]
  },
  "text_summary": {
    "ai_summary": "AI-generated analysis...",
    "trend_consistency": "High consistency detected...",
    "timing_alignment": "Seasonal patterns align...",
    "continuity_over_time": "Continuous data coverage..."
  }
}
```

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.