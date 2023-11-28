from django.urls import include, path

from . import apis

urlpatterns = [
	path("id/getimagepath/", apis.IDGetImagePath),
	path("id/upload/", apis.IDImageUpload),
	path("id/update/result/", apis.IDResultUpload),
	path("matching/get/", apis.MatchingGet),
	path("matching/getlist/", apis.MatchingGetList),
	path("matching/upload/", apis.MatchingImageUpload),
	path("matching/update/result/", apis.MatchingResultUpload),
]