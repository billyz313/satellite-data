from django.urls import path
from .views import SatelliteDataAPIView, CachedSatelliteDataAPIView, SatelliteDataFormView

app_name = 'satellite_data'

urlpatterns = [
    path('api/satellite-data/', SatelliteDataAPIView.as_view(), name='satellite-data'),
    path('api/satellite-data/cached/', CachedSatelliteDataAPIView.as_view(), name='satellite-data-cached'),
    path('satellite-data-form/', SatelliteDataFormView.as_view(), name='satellite-data-form'),
]