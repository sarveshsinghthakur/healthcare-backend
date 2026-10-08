from django.urls import path
from .views import MappingListCreateView, MappingDetailView, PatientDoctorsView

urlpatterns = [
    path('', MappingListCreateView.as_view(), name='mapping-list-create'),
    path('patient/<int:patient_id>/', PatientDoctorsView.as_view(), name='mapping-patient-doctors'),
    path('<int:pk>/', MappingDetailView.as_view(), name='mapping-detail'),
]