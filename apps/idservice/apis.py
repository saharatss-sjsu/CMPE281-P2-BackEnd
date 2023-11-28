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
import datetime

@csrf_exempt
@require_http_methods(["GET","POST"])
def IDGetImagePath(request):
	try:
		data = json.loads(request.body)
		driver_license = data['driver_license']
	except: return HttpResponse(status=400)
	try: id_obj = IDServiceModel.ID.objects.get(driver_license=driver_license)
	except IDServiceModel.ID.DoesNotExist: return HttpResponse(status=404)
	return JsonResponse({"path": id_obj.image.path})

@csrf_exempt
@require_http_methods(["POST"])
def IDImageUpload(request):
	if not request.user.is_authenticated: return HttpResponse(status=401)
	try:
		data = json.loads(request.body)
		file_name = data['name']
		file_type = data['type']
		file_size = data['size']
	except: return HttpResponse(status=400)
	if file_size > settings.UPLOAD_MAX_FILE_SIZE: return HttpResponse(f"{file_name} is too large", status=406)
	service = FileDirectUploadService(request.user)
	presigned_data = service.start('id', file_name, file_type, file_size)
	image_obj      = FileServiceModel.File.objects.get(id=presigned_data['file']['id'])
	id_obj         = IDServiceModel.ID(driver_license=f"$null-{image_obj.name[:10]}")
	id_obj.image   = image_obj
	id_obj.save()
	presigned_data['id'] = id_obj.dict()
	return JsonResponse(data=presigned_data)

@csrf_exempt
@require_http_methods(["POST"])
def IDResultUpload(request):
	try:
		data = json.loads(request.body)
		id_image_name = data['id_image_name']
		result_ocr    = data['result_ocr']
	except: return HttpResponse(status=400)
	try: image_obj = FileServiceModel.File.objects.get(name=id_image_name)
	except FileServiceModel.File.DoesNotExist: return HttpResponse(status=404)
	try: id_obj = IDServiceModel.ID.objects.get(image=image_obj)
	except IDServiceModel.ID.DoesNotExist: return HttpResponse(status=404)
	id_obj.driver_license = result_ocr['driver_license']['TextValue']
	id_obj.result_ocr     = result_ocr
	id_obj.vehicle_class  = result_ocr['vehicle_class']['TextValue']
	id_obj.first_name     = result_ocr['first_name']['TextValue']
	id_obj.last_name      = result_ocr['last_name']['TextValue']
	id_obj.eyes           = result_ocr['eyes']['TextValue']
	id_obj.hair           = result_ocr['hair']['TextValue']
	# id_obj.sex            = result_ocr['sex']['TextValue']

	try:
		_height = result_ocr['height']['TextValue'].replace('\'','').replace('"','').split('-')
		id_obj.height = int(_height[0])+int(_height[1])/100
	except: pass

	try: id_obj.weight = int(result_ocr['weight']['TextValue'].replace('lb',''))
	except: pass

	try:
		id_obj.date_of_birth   = datetime.datetime.strptime(result_ocr['date_of_birth']['TextValue'], "%m/%d/%Y").date()
		id_obj.expiration_date = datetime.datetime.strptime(result_ocr['expiration_date']['TextValue'], "%m/%d/%Y").date()
	except: pass

	id_obj.save()
	return JsonResponse(id_obj.dict())


@csrf_exempt
@require_http_methods(["GET","POST"])
def MatchingGet(request):
	if not request.user.is_authenticated: return HttpResponse(status=401)
	try:
		data = json.loads(request.body)
		matching_id = data['id']
	except: return HttpResponse(status=400)
	try: matching_obj = IDServiceModel.Matching.objects.get(id=matching_id)
	except IDServiceModel.Matching.DoesNotExist: return HttpResponse(status=404)
	if matching_obj.creator != request.user: return HttpResponse(status=403)
	return JsonResponse({"matching": matching_obj.dict()})

@csrf_exempt
@require_http_methods(["GET","POST"])
def MatchingGetList(request):
	if not request.user.is_authenticated: return HttpResponse(status=401)
	matching_objs = IDServiceModel.Matching.objects.filter(creator=request.user)
	return JsonResponse({"matchings": list(map(lambda x: x.dict(), matching_objs))})

@csrf_exempt
@require_http_methods(["POST"])
def MatchingImageUpload(request):
	if not request.user.is_authenticated: return HttpResponse(status=401)
	try:
		data  = json.loads(request.body)
		file_name = data['name']
		file_type = data['type']
		file_size = data['size']
	except: return HttpResponse(status=400)
	if file_size > settings.UPLOAD_MAX_FILE_SIZE: return HttpResponse(f"{file_name} is too large", status=406)
	service = FileDirectUploadService(request.user)
	presigned_data = service.start('matching',file_name, file_type, file_size)
	image_obj      = FileServiceModel.File.objects.get(id=presigned_data['file']['id'])
	matching       = IDServiceModel.Matching(driver_license=f"$null-{image_obj.name[:10]}", creator=request.user)
	matching.image = image_obj
	matching.save()
	presigned_data['matching'] = matching.dict()
	return JsonResponse(data=presigned_data)

@csrf_exempt
@require_http_methods(["POST"])
def MatchingResultUpload(request):
	try:
		data = json.loads(request.body)
		matching_image_name  = data['matching_image_name']
		matching_result_face = data['result_face']
		matching_result_ocr  = data['result_ocr']
		driver_license = matching_result_ocr['driver_license']['TextValue']
	except: return HttpResponse(status=400)
	try: image_obj = FileServiceModel.File.objects.get(name=matching_image_name)
	except FileServiceModel.File.DoesNotExist: return HttpResponse(status=404)
	try: matching = IDServiceModel.Matching.objects.get(image=image_obj)
	except IDServiceModel.Matching.DoesNotExist: return HttpResponse(status=404)
	matching.driver_license = driver_license
	matching.result_face    = matching_result_face
	matching.result_ocr     = matching_result_ocr
	matching.resulted       = datetime.datetime.utcnow()
	max_similarity = 0
	for face in matching_result_face['FaceMatches']:
		if face['Similarity'] > max_similarity:
			max_similarity = face['Similarity']
	matching.face_similarity = max_similarity
	matching.save()

	try: id_obj = IDServiceModel.ID.objects.get(driver_license=driver_license)
	except IDServiceModel.ID.DoesNotExist: return HttpResponse(status=404)
	result_matching = {}
	result_matching['face_similarity'] = matching.face_similarity >= 80
	result_matching['first_name']    = id_obj.first_name == matching_result_ocr['first_name']['TextValue']
	result_matching['last_name']     = id_obj.last_name == matching_result_ocr['last_name']['TextValue']
	result_matching['vehicle_class'] = id_obj.vehicle_class == matching_result_ocr['vehicle_class']['TextValue']

	_is_matched = True
	for value in result_matching.values():
		if value is False:
			_is_matched = False
			break
	matching.is_matched      = _is_matched
	matching.result_matching = result_matching
	matching.save()

	return JsonResponse(matching.dict())