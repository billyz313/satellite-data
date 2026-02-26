import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging
import numpy as np
from collections import defaultdict

from django.conf import settings

logger = logging.getLogger(__name__)


class OpenETService:
    """Service for interacting with OpenET API"""

    BASE_URL = 'https://openet-api.org'

    @staticmethod
    def fetch_point_data(lat: float, lon: float, start_date: str, end_date: str, variable: str) -> Dict:
        """
        Fetch data for a single variable at a point location

        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            variable: Variable to fetch ('et' or 'ndvi')

        Returns:
            Dictionary containing the requested variable data
        """
        url = f"{OpenETService.BASE_URL}/raster/timeseries/point"

        params = {
            'geometry': [lon,lat ],
            'date_range': [start_date, end_date],
            "file_format": "JSON",
            "interval": "monthly",
            "model": "Ensemble",
            "reference_et": "gridMET",
            "units": "mm",
            'variable': variable.lower(),
            "version": 2.1
        }

        try:
            logger.info(f"Fetching {variable} data for point ({lat}, {lon})")

            logger.info(f"OPENET_API_KEY  {settings.OPENET_API_KEY}")

            header = {"Authorization": settings.OPENET_API_KEY}
            response = requests.post(url, headers=header, json=params, timeout=300)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched {variable} data")
            return data
        except requests.RequestException as e:
            logger.error(f"Error fetching {variable} point data from OpenET: {e}")
            raise

    @staticmethod
    def fetch_polygon_data(polygon: List, start_date: str, end_date: str, variable: str) -> Dict:
        """
        Fetch data for a single variable for a polygon

        Args:
            polygon: GeoJSON polygon or list of coordinates
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            variable: Variable to fetch ('et' or 'ndvi')

        Returns:
            Dictionary containing the requested variable data
        """
        url = f"{OpenETService.BASE_URL}/raster/timeseries/polygon"

        payload = {
            'geometry': polygon,
            'date_range': [start_date, end_date],
            "file_format": "JSON",
            "interval": "monthly",
            "model": "Ensemble",
            "reference_et": "gridMET",
            "reducer": "mean",
            "units": "mm",
            'variable': variable.lower(),
            "version": 2.1
        }

        logger.info(f"payload {payload}")

        try:
            logger.info(f"Fetching {variable} data for polygon")
            header = {"Authorization": settings.OPENET_API_KEY}
            response = requests.post(url, headers=header, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched {variable} data")
            return data
        except requests.RequestException as e:
            logger.error(f"Error fetching {variable} polygon data from OpenET: {e}")
            raise

    @staticmethod
    def fetch_both_variables_point(lat: float, lon: float, start_date: str, end_date: str) -> Dict:
        """
        Fetch both ET and NDVI data for a point location
        Makes two separate API calls

        Returns:
            Dictionary with 'et' and 'ndvi' keys containing raw API responses
        """
        et_data = OpenETService.fetch_point_data(lat, lon, start_date, end_date, 'et')
        ndvi_data = OpenETService.fetch_point_data(lat, lon, start_date, end_date, 'ndvi')

        return {
            'et': et_data,
            'ndvi': ndvi_data
        }

    @staticmethod
    def fetch_both_variables_polygon(polygon: Union[List, Dict], start_date: str, end_date: str) -> Dict:
        """
        Fetch both ET and NDVI data for a polygon
        Makes two separate API calls

        Returns:
            Dictionary with 'et' and 'ndvi' keys containing raw API responses
        """
        et_data = OpenETService.fetch_polygon_data(polygon, start_date, end_date, 'et')
        ndvi_data = OpenETService.fetch_polygon_data(polygon, start_date, end_date, 'ndvi')

        return {
            'et': et_data,
            'ndvi': ndvi_data
        }


class OpenETDataProcessor:
    """Process OpenET API responses into structured format"""

    @staticmethod
    def process_response(raw_data: Dict, location: str) -> Dict:
        """
        Process OpenET API responses into structured format

        Args:
            raw_data: Dictionary containing 'et' and 'ndvi' raw responses
            location: Location string (lat,lon or polygon description)

        Returns:
            Processed dictionary with NDVI, ET, analysis, and summaries
        """
        # Extract NDVI and ET data from separate responses
        ndvi_data = OpenETDataProcessor._extract_variable_data(
            raw_data['ndvi'], 'ndvi', location
        )
        et_data = OpenETDataProcessor._extract_variable_data(
            raw_data['et'], 'et', location
        )

        # Perform ET analysis
        et_analysis = OpenETDataProcessor._analyze_et_data(et_data['data_points'])

        # Generate vegetation summary
        vegetation_summary = OpenETDataProcessor._generate_vegetation_summary(
            ndvi_data['data_points']
        )

        return {
            'NDVI': ndvi_data,
            'ET': et_data,
            'et_analysis': et_analysis,
            'vegetation_summary': vegetation_summary
        }

    @staticmethod
    def _extract_variable_data(raw_data: Dict, variable: str, location: str) -> Dict:
        """
        Extract and format data for a specific variable (NDVI or ET)

        Args:
            raw_data: Raw API response for single variable (list of dicts with 'time' and variable keys)
            variable: Variable name ('ndvi' or 'et')
            location: Location string

        Returns:
            Formatted dictionary with variable data
        """
        data_points = []
        values = []

        # OpenET API returns a list of dicts with 'time' and the variable name
        # Example: [{"time": "2020-01-01", "et": 31}, ...]

        if isinstance(raw_data, list):
            for item in raw_data:
                date = item.get('time')
                value = item.get(variable.lower())

                if date and value is not None:
                    data_points.append({
                        'date': date,
                        variable.upper(): value
                    })
                    values.append(value)
        else:
            logger.error(f"Unexpected data format for {variable}. Expected list, got {type(raw_data)}")
            return {
                'source': 'OpenET',
                'location': location,
                'values_found': 0,
                'date_range': 'N/A',
                f'{variable}_mean': 0,
                'data_points': []
            }

        # Filter out None values
        valid_values = [v for v in values if v is not None]

        if not data_points:
            logger.warning(f"No {variable} data found in response")

        date_range = "N/A"
        if data_points:
            start_date = data_points[0]['date']
            end_date = data_points[-1]['date']
            date_range = f"{start_date} to {end_date}"

        mean_value = round(np.mean(valid_values), 3) if valid_values else 0

        result = {
            'source': 'OpenET',
            'location': location,
            'values_found': len(valid_values),
            'date_range': date_range,
            'data_points': data_points
        }

        # Add the mean with the appropriate key name
        if variable.lower() == 'ndvi':
            result['ndvi_mean'] = mean_value
        elif variable.lower() == 'et':
            result['et_mean'] = mean_value

        return result

    @staticmethod
    def _analyze_et_data(data_points: List[Dict]) -> Dict:
        """Perform comprehensive ET analysis"""
        if not data_points:
            return {}

        # Extract ET values and dates
        et_values = []
        dates = []
        for point in data_points:
            if 'ET' in point and point['ET'] is not None:
                et_values.append(point['ET'])
                try:
                    # Now using 'date' key (already transformed in _extract_variable_data)
                    dates.append(datetime.strptime(point['date'], '%Y-%m-%d'))
                except ValueError:
                    logger.warning(f"Invalid date format: {point['date']}")
                    continue

        if not et_values:
            return {}

        et_array = np.array(et_values)

        # Calculate basic statistics
        total_et_mm = round(np.sum(et_array), 0)
        mean_monthly_et_mm = round(np.mean(et_array), 1)
        max_et = round(np.max(et_array), 0)
        min_et = round(np.min(et_array), 0)

        # Find peak ET month
        max_idx = np.argmax(et_array)
        peak_month = dates[max_idx].strftime('%Y-%m-%d')

        # Convert to inches
        mm_to_inches = 0.0393701
        total_et_inches = round(total_et_mm * mm_to_inches, 2)

        # Calculate growing season ET (April-October)
        growing_season_et = []
        for date, et_val in zip(dates, et_values):
            if 4 <= date.month <= 10:
                growing_season_et.append(et_val)

        growing_season_et_mm = round(sum(growing_season_et), 0) if growing_season_et else 0
        growing_season_et_inches = round(growing_season_et_mm * mm_to_inches, 2)

        # Calculate yearly totals
        yearly_totals = defaultdict(float)
        for date, et_val in zip(dates, et_values):
            yearly_totals[date.year] += et_val

        yearly_totals_mm = {year: round(total, 0) for year, total in sorted(yearly_totals.items())}

        # Calculate seasonal totals
        seasonal_totals = {
            'winter': 0,  # Dec, Jan, Feb
            'spring': 0,  # Mar, Apr, May
            'summer': 0,  # Jun, Jul, Aug
            'fall': 0  # Sep, Oct, Nov
        }

        for date, et_val in zip(dates, et_values):
            month = date.month
            if month in [12, 1, 2]:
                seasonal_totals['winter'] += et_val
            elif month in [3, 4, 5]:
                seasonal_totals['spring'] += et_val
            elif month in [6, 7, 8]:
                seasonal_totals['summer'] += et_val
            else:
                seasonal_totals['fall'] += et_val

        seasonal_totals_mm = {season: round(total, 0) for season, total in seasonal_totals.items()}

        # Calculate trend
        if len(et_values) > 1:
            x = np.arange(len(et_values))
            slope, _ = np.polyfit(x, et_array, 1)
            trend_slope = round(slope, 3)

            if abs(slope) < 0.1:
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
        else:
            trend = "stable"
            trend_slope = 0.0

        # Calculate variability
        std_dev = round(np.std(et_array), 1)
        cv = round(std_dev / mean_monthly_et_mm, 2) if mean_monthly_et_mm > 0 else 0

        if cv < 0.3:
            consistency = "high"
        elif cv < 0.6:
            consistency = "moderate"
        else:
            consistency = "low"

        # Classify water use
        if mean_monthly_et_mm < 30:
            water_class = "low_water_use"
            water_desc = "Low water consumption"
        elif mean_monthly_et_mm < 50:
            water_class = "moderate_water_use"
            water_desc = "Moderate water consumption"
        elif mean_monthly_et_mm < 70:
            water_class = "high_water_use"
            water_desc = "High water consumption"
        else:
            water_class = "very_high_water_use"
            water_desc = "Significantly high water consumption"

        return {
            'total_et_mm': int(total_et_mm),
            'mean_monthly_et_mm': mean_monthly_et_mm,
            'max_monthly_et_mm': int(max_et),
            'min_monthly_et_mm': int(min_et),
            'peak_et_month': peak_month,
            'total_et_inches': total_et_inches,
            'growing_season_et_mm': int(growing_season_et_mm),
            'growing_season_et_inches': growing_season_et_inches,
            'observations': len(et_values),
            'date_range': {
                'start': dates[0].strftime('%Y-%m-%d'),
                'end': dates[-1].strftime('%Y-%m-%d')
            },
            'yearly_totals_mm': yearly_totals_mm,
            'seasonal_totals_mm': seasonal_totals_mm,
            'monthly_trend': trend,
            'trend_slope_mm_per_month': trend_slope,
            'et_variability': {
                'std_dev_mm': std_dev,
                'coefficient_of_variation': cv,
                'consistency': consistency
            },
            'water_use_classification': water_class,
            'water_use_description': water_desc
        }

    @staticmethod
    def _generate_vegetation_summary(data_points: List[Dict]) -> Dict:
        """Generate vegetation summary from NDVI data"""
        if not data_points:
            return {}

        # Extract NDVI values
        ndvi_values = []
        for point in data_points:
            if 'NDVI' in point and point['NDVI'] is not None:
                ndvi_values.append(point['NDVI'])

        if not ndvi_values:
            return {}

        ndvi_array = np.array(ndvi_values)

        mean_ndvi = round(np.mean(ndvi_array), 3)
        max_ndvi = round(np.max(ndvi_array), 3)
        min_ndvi = round(np.min(ndvi_array), 3)
        std_dev = round(np.std(ndvi_array), 3)

        # Classify vegetation vigor
        if mean_ndvi < 0.2:
            vigor = "Sparse or no vegetation"
        elif mean_ndvi < 0.4:
            vigor = "Low vegetation"
        elif mean_ndvi < 0.6:
            vigor = "Moderate vegetation"
        elif mean_ndvi < 0.8:
            vigor = "Healthy vegetation"
        else:
            vigor = "Very healthy/dense vegetation"

        return {
            'total_observations': len(ndvi_values),
            'mean_ndvi': mean_ndvi,
            'max_ndvi': max_ndvi,
            'min_ndvi': min_ndvi,
            'std_dev': std_dev,
            'vigor_classification': vigor,
            'data_sources': ['OpenET']
        }