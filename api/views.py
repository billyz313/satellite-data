from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import logging

from .serializers import PointQuerySerializer, PolygonQuerySerializer
from .services.ai_summarizer import generate_text_summary
from .services.openet_service import OpenETService, OpenETDataProcessor

logger = logging.getLogger(__name__)


class SatelliteDataFormView(View):
    """
    Render interactive HTML form for the API
    """
    def get(self, request):
        return render(request, 'api/api_form.html')


class SatelliteDataAPIView(APIView):
    """
    API endpoint to fetch ET and NDVI data from OpenET

    Accepts either:
    - lat, lon, start_date, end_date (for point queries)
    - polygon, start_date, end_date (for polygon queries)

    Makes two separate calls to OpenET API (one for ET, one for NDVI)
    """

    def get(self, request):
        """Handle GET requests for point-based queries"""
        serializer = PointQuerySerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data

        try:
            # Fetch both ET and NDVI data (makes 2 API calls)
            raw_data = OpenETService.fetch_both_variables_point(
                lat=validated_data['lat'],
                lon=validated_data['lon'],
                start_date=validated_data['start_date'].strftime('%Y-%m-%d'),
                end_date=validated_data['end_date'].strftime('%Y-%m-%d')
            )

            # Process the data
            location = f"{validated_data['lat']}, {validated_data['lon']}"
            processed_data = OpenETDataProcessor.process_response(raw_data, location)

            # Generate text summary (call your existing function)
            try:

                processed_data['text_summary'] = generate_text_summary(processed_data)
            except ImportError:
                logger.warning("generate_text_summary function not found, skipping text summary")

            return Response(processed_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing point query: {e}", exc_info=True)
            return Response(
                {'error': f'Failed to fetch or process data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Handle POST requests for polygon-based queries"""
        if request.data and 'polygon' in request.data:
            serializer = PolygonQuerySerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'error': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            try:
                # Fetch both ET and NDVI data (makes 2 API calls)
                raw_data = OpenETService.fetch_both_variables_polygon(
                    polygon=validated_data['polygon'],
                    start_date=validated_data['start_date'].strftime('%Y-%m-%d'),
                    end_date=validated_data['end_date'].strftime('%Y-%m-%d')
                )

                # Process the data
                location = "Polygon area"
                processed_data = OpenETDataProcessor.process_response(raw_data, location)

                # Generate text summary (call your existing function)
                try:
                    processed_data['text_summary'] = generate_text_summary(processed_data)
                except ImportError:
                    logger.warning("generate_text_summary function not found, skipping text summary")

                return Response(processed_data, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Error processing polygon query: {e}", exc_info=True)
                return Response(
                    {'error': f'Failed to fetch or process data: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            serializer = PointQuerySerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'error': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            try:
                # Fetch both ET and NDVI data (makes 2 API calls)
                raw_data = OpenETService.fetch_both_variables_point(
                    lat=validated_data['lat'],
                    lon=validated_data['lon'],
                    start_date=validated_data['start_date'].strftime('%Y-%m-%d'),
                    end_date=validated_data['end_date'].strftime('%Y-%m-%d')
                )

                # Process the data
                location = f"{validated_data['lat']}, {validated_data['lon']}"
                processed_data = OpenETDataProcessor.process_response(raw_data, location)

                # Generate text summary (call your existing function)
                try:

                    processed_data['text_summary'] = generate_text_summary(processed_data)
                except ImportError:
                    logger.warning("generate_text_summary function not found, skipping text summary")

                return Response(processed_data, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Error processing point query: {e}", exc_info=True)
                return Response(
                    {'error': f'Failed to fetch or process data: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


# Optional: Create a cached version for frequently accessed locations
class CachedSatelliteDataAPIView(SatelliteDataAPIView):
    """Cached version of the API (cache for 1 hour)"""

    @method_decorator(cache_page(60 * 60))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)