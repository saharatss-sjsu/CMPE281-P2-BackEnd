from django.urls import include, path

from . import apis

urlpatterns = [
	path("matching/upload/", apis.MatchingImageUpload),
	path("matching/update/result/", apis.MatchingUpdateResult),
]