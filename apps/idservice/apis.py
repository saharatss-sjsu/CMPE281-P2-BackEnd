from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import serializers, viewsets

from apps.idservice import models as IDServiceModel
from apps.fileservice import models as FileServiceModel
from apps.fileservice.services import FileDirectUploadService

import json

@csrf_exempt
@require_http_methods(["POST"])
def MatchingImageUpload(request):
	if not request.user.is_authenticated: return HttpResponse(status=401)
	try:
		data  = json.loads(request.body)
		driver_license = data['driver_license']
		image          = data['image']
	except: return HttpResponse(status=400)
	file_name = image.get('name')
	file_type = image.get('type')
	file_size = image.get('size')
	if file_size > settings.UPLOAD_MAX_FILE_SIZE: return HttpResponse(f"{file_name} is too large", status=406)
	try: IDServiceModel.ID.objects.get(driver_license=driver_license)
	except IDServiceModel.ID.DoesNotExist: return HttpResponse(status=404, content="Driver license number missed match")
	matching = IDServiceModel.Matching(driver_license=driver_license, creator=request.user)
	service = FileDirectUploadService(request.user)
	presigned_data = service.start('matching',file_name, file_type, file_size)
	matching.image = FileServiceModel.File.objects.get(id=presigned_data['file']['id'])
	matching.save()
	presigned_data['matching'] = matching.dict()
	return JsonResponse(data=presigned_data)

@csrf_exempt
@require_http_methods(["POST"])
def MatchingUpdateResult(request):
	try:
		data = json.loads(request.body)
		matching_image_name = data['matching_image_name']
		matching_result_face = data.get('result_face')
	except: return HttpResponse(status=400)
	try: image = FileServiceModel.File.objects.get(name=matching_image_name)
	except FileServiceModel.File.DoesNotExist: return HttpResponse(status=404)
	try: matching = IDServiceModel.Matching.objects.get(image=image)
	except IDServiceModel.Matching.DoesNotExist: return HttpResponse(status=404)
	matching.result_face = matching_result_face
	max_similarity = 0
	for face in matching_result_face['FaceMatches']:
		if face['Similarity'] > max_similarity:
			max_similarity = face['Similarity']
	matching.face_similarity = max_similarity
	matching.save()
	return JsonResponse(matching.dict())