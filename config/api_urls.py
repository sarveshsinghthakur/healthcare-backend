from django.urls import path, include

urlpatterns = [
    path('auth/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('mappings/', include('mappings.urls')),
]