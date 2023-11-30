from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import serializers, viewsets

from apps.idservice import models as IDServiceModel
from apps.fileservice import models as FileServiceModel
from apps.fileservice.services import FileDirectUploadService

import json
import datetime

def getTextValueIfExist(result_ocr, key, forceUppercase=True):
	output = result_ocr.get(key)
	if output is None: return None
	output = output.get('TextValue')
	return output.upper() if forceUppercase else output

@csrf_exempt
@require_http_methods(["GET","POST"])
def IDGetImagePath(request):
	try:
		data = json.loads(request.body)
		driver_license = data['driver_license']
	except: return HttpResponse(status=400)
	id_obj = IDServiceModel.ID.objects.filter(driver_license=driver_license)
	if id_obj.count() == 0: return HttpResponse(status=404)
	else: id_obj = id_obj[0]
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
	if file_type not in ['image/jpeg','image/png']: return HttpResponse(f"Only jpg, png are supported but received \"{file_type}\".", status=406)
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
	id_obj.result_ocr     = result_ocr
	id_obj.driver_license = getTextValueIfExist(result_ocr, 'driver_license')
	id_obj.vehicle_class  = getTextValueIfExist(result_ocr, 'vehicle_class')
	id_obj.first_name     = getTextValueIfExist(result_ocr, 'first_name')
	id_obj.last_name      = getTextValueIfExist(result_ocr, 'last_name')
	id_obj.eyes           = getTextValueIfExist(result_ocr, 'eyes')
	id_obj.hair           = getTextValueIfExist(result_ocr, 'hair')
	id_obj.sex            = getTextValueIfExist(result_ocr, 'sex')

	try:
		_height = getTextValueIfExist(result_ocr,'height').replace('\'','').replace('"','').split('-')
		id_obj.height = int(_height[0])+int(_height[1])/100
	except: pass

	try: id_obj.weight = int(getTextValueIfExist(result_ocr,'weight').replace('LB',''))
	except: pass

	try:
		id_obj.date_of_birth   = datetime.datetime.strptime(getTextValueIfExist(result_ocr,'date_of_birth'), "%m/%d/%Y").date()
		id_obj.expiration_date = datetime.datetime.strptime(getTextValueIfExist(result_ocr,'expiration_date'), "%m/%d/%Y").date()
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
@require_http_methods(["DELETE"])
def MatchingDelete(request):
	if not request.user.is_authenticated: return HttpResponse(status=401)
	try:
		data = json.loads(request.body)
		matching_id = data['id']
	except: return HttpResponse(status=400)
	try: matching_obj = IDServiceModel.Matching.objects.get(id=matching_id)
	except IDServiceModel.Matching.DoesNotExist: return HttpResponse(status=404)
	if matching_obj.creator != request.user: return HttpResponse(status=403)
	matching_obj.delete()
	return JsonResponse({"matching": {"id":matching_id}})


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
	if file_type not in ['image/jpeg','image/png']: return HttpResponse(f"Only jpg, png are supported but received \"{file_type}\".", status=406)
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
		driver_license       = getTextValueIfExist(matching_result_ocr, 'driver_license')
	except: return HttpResponse(status=400)
	try: image_obj = FileServiceModel.File.objects.get(name=matching_image_name)
	except FileServiceModel.File.DoesNotExist: return HttpResponse(status=404)
	try: matching = IDServiceModel.Matching.objects.get(image=image_obj)
	except IDServiceModel.Matching.DoesNotExist: return HttpResponse(status=404)
	matching.driver_license = driver_license
	matching.result_face    = matching_result_face
	matching.result_ocr     = matching_result_ocr
	matching.resulted       = timezone.now()

	max_similarity = 0
	for face in matching_result_face['FaceMatches']:
		if face['Similarity'] > max_similarity:
			max_similarity = face['Similarity']
	matching.face_similarity = max_similarity
	matching.save()

	result_matching = {}
	id_obj = IDServiceModel.ID.objects.filter(driver_license=driver_license)
	if id_obj.count() > 0: # found
		id_obj = id_obj[0]
		result_matching['driver_license']  = True
		result_matching['face_similarity'] = matching.face_similarity >= 80
		result_matching['first_name']      = id_obj.first_name    == getTextValueIfExist(matching_result_ocr, 'first_name')
		result_matching['last_name']       = id_obj.last_name     == getTextValueIfExist(matching_result_ocr, 'last_name')
		result_matching['vehicle_class']   = id_obj.vehicle_class == getTextValueIfExist(matching_result_ocr, 'vehicle_class')
		result_matching['eyes']            = id_obj.eyes          == getTextValueIfExist(matching_result_ocr, 'eyes')
		result_matching['hair']            = id_obj.hair          == getTextValueIfExist(matching_result_ocr, 'hair')
		result_matching['sex']             = id_obj.sex           == getTextValueIfExist(matching_result_ocr, 'sex')

		try:
			_height = getTextValueIfExist(matching_result_ocr,'height').replace('\'','').replace('"','').split('-')
			result_matching['height'] = id_obj.height == int(_height[0])+int(_height[1])/100
		except: pass

		try:
			_weight = int(getTextValueIfExist(matching_result_ocr,'weight').replace('LB',''))
			result_matching['weight'] = id_obj.weight == _weight
		except: pass

		try:
			result_matching['date_of_birth']   = id_obj.date_of_birth   == datetime.datetime.strptime(getTextValueIfExist(matching_result_ocr,'date_of_birth'), "%m/%d/%Y").date()
			result_matching['expiration_date'] = id_obj.expiration_date == datetime.datetime.strptime(getTextValueIfExist(matching_result_ocr,'expiration_date'), "%m/%d/%Y").date()
		except: pass

	else:
		result_matching['driver_license']  = False
		result_matching['face_similarity'] = False
		result_matching['first_name']      = False
		result_matching['last_name']       = False
		result_matching['vehicle_class']   = False
		result_matching['eyes']            = False
		result_matching['hair']            = False
		result_matching['sex']             = False
		result_matching['height']          = False
		result_matching['weight']          = False
		result_matching['date_of_birth']   = False
		result_matching['expiration_date'] = False


	_is_matched = True
	for value in result_matching.values():
		if value is False:
			_is_matched = False
			break
	matching.is_matched      = _is_matched
	matching.result_matching = result_matching
	matching.save()

	return JsonResponse(matching.dict())