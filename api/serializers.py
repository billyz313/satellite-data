from rest_framework import serializers


class PointQuerySerializer(serializers.Serializer):
    """Serializer for point-based queries"""
    lat = serializers.FloatField(required=True, min_value=-90, max_value=90)
    lon = serializers.FloatField(required=True, min_value=-180, max_value=180)
    start_date = serializers.DateField(required=True, format='%Y-%m-%d')
    end_date = serializers.DateField(required=True, format='%Y-%m-%d')

    def validate(self, data):
        """Validate that start_date is before end_date"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                "start_date must be before end_date"
            )
        return data


class PolygonQuerySerializer(serializers.Serializer):
    """Serializer for polygon-based queries"""
    polygon = serializers.JSONField(required=True)
    start_date = serializers.DateField(required=True, format='%Y-%m-%d')
    end_date = serializers.DateField(required=True, format='%Y-%m-%d')

    def validate_polygon(self, value):
        """
        Validate and convert polygon to OpenET format

        Accepts:
        1. Flat array: [lon1, lat1, lon2, lat2, ...]
        2. Array of pairs: [[lon1, lat1], [lon2, lat2], ...]
        3. GeoJSON Geometry: {"type": "Polygon", "coordinates": [[[lon1, lat1], ...]]}
        4. GeoJSON Feature: {"type": "Feature", "geometry": {"type": "Polygon", ...}}
        5. GeoJSON FeatureCollection: {"type": "FeatureCollection", "features": [{"type": "Feature", ...}]}

        Returns: Flat array format for OpenET API
        """

        # Case 1: Already a flat array [lon, lat, lon, lat, ...]
        if isinstance(value, list) and len(value) > 0:
            # Check if it's already flat (all items are numbers)
            if all(isinstance(x, (int, float)) for x in value):
                if len(value) < 6:  # At least 3 coordinate pairs
                    raise serializers.ValidationError(
                        "Polygon must have at least 3 coordinate pairs (6 values)"
                    )
                if len(value) % 2 != 0:
                    raise serializers.ValidationError(
                        "Polygon array must have an even number of values (lon/lat pairs)"
                    )
                return value

            # Case 2: Array of coordinate pairs [[lon, lat], [lon, lat], ...]
            elif all(isinstance(x, list) and len(x) == 2 for x in value):
                if len(value) < 3:
                    raise serializers.ValidationError(
                        "Polygon must have at least 3 coordinate pairs"
                    )
                # Flatten to OpenET format
                flat_array = []
                for coord in value:
                    flat_array.extend(coord)
                return flat_array

            else:
                raise serializers.ValidationError(
                    "Invalid polygon format. Expected flat array or array of coordinate pairs"
                )

        # Case 3, 4, 5: Dictionary (GeoJSON)
        elif isinstance(value, dict):
            # Extract coordinates based on GeoJSON type
            coords = self._extract_coordinates_from_geojson(value)

            if coords is None:
                raise serializers.ValidationError(
                    "Could not extract valid polygon coordinates from GeoJSON"
                )

            if len(coords) < 3:
                raise serializers.ValidationError(
                    "Polygon must have at least 3 coordinate pairs"
                )

            # Flatten to OpenET format
            flat_array = []
            for coord in coords:
                if not isinstance(coord, list) or len(coord) < 2:
                    raise serializers.ValidationError(
                        "Invalid coordinate in GeoJSON"
                    )
                flat_array.extend([coord[0], coord[1]])  # lon, lat

            return flat_array

        else:
            raise serializers.ValidationError(
                "Polygon must be an array or GeoJSON object"
            )

    def _extract_coordinates_from_geojson(self, geojson):
        """
        Extract polygon coordinates from various GeoJSON formats

        Args:
            geojson: GeoJSON dict (Geometry, Feature, or FeatureCollection)

        Returns:
            List of coordinate pairs [[lon, lat], ...] or None if invalid
        """
        geojson_type = geojson.get('type')

        # Case: FeatureCollection
        if geojson_type == 'FeatureCollection':
            features = geojson.get('features', [])

            if not features:
                raise serializers.ValidationError(
                    "FeatureCollection has no features"
                )

            if len(features) > 1:
                raise serializers.ValidationError(
                    "FeatureCollection contains multiple features. Only single polygon supported."
                )

            # Get the first feature
            feature = features[0]

            if not isinstance(feature, dict):
                raise serializers.ValidationError(
                    "Invalid feature in FeatureCollection"
                )

            if feature.get('type') != 'Feature':
                raise serializers.ValidationError(
                    "FeatureCollection item is not a Feature"
                )

            # Extract geometry from feature
            geometry = feature.get('geometry')

            if not geometry:
                raise serializers.ValidationError(
                    "Feature has no geometry"
                )

            # Recursively extract from geometry
            return self._extract_coordinates_from_geometry(geometry)

        # Case: Feature
        elif geojson_type == 'Feature':
            geometry = geojson.get('geometry')

            if not geometry:
                raise serializers.ValidationError(
                    "Feature has no geometry"
                )

            return self._extract_coordinates_from_geometry(geometry)

        # Case: Geometry (Polygon)
        elif geojson_type == 'Polygon':
            return self._extract_coordinates_from_geometry(geojson)

        else:
            raise serializers.ValidationError(
                f"Unsupported GeoJSON type: {geojson_type}. Expected Polygon, Feature, or FeatureCollection."
            )

    def _extract_coordinates_from_geometry(self, geometry):
        """
        Extract coordinates from a GeoJSON Geometry object

        Args:
            geometry: GeoJSON Geometry dict

        Returns:
            List of coordinate pairs [[lon, lat], ...] or None if invalid
        """
        if not isinstance(geometry, dict):
            return None

        geom_type = geometry.get('type')

        if geom_type != 'Polygon':
            raise serializers.ValidationError(
                f"Unsupported geometry type: {geom_type}. Only Polygon is supported."
            )

        coords = geometry.get('coordinates')

        if not isinstance(coords, list) or len(coords) == 0:
            raise serializers.ValidationError(
                "Invalid Polygon coordinates"
            )

        # Get the outer ring (first element)
        # GeoJSON Polygon coordinates are nested: [[[lon, lat], ...]]
        outer_ring = coords[0]

        if not isinstance(outer_ring, list):
            raise serializers.ValidationError(
                "Invalid Polygon outer ring"
            )

        return outer_ring

    def validate(self, data):
        """Validate that start_date is before end_date"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                "start_date must be before end_date"
            )
        return data