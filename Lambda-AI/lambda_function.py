import base64
import json
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pathlib import Path
import boto3
import requests

COLOR_TEXT_DETECT    = (255,0,0)
IMAGE_INPUT_PATH     = "/tmp/input.jpg"
IMAGE_INPUT_REF_PATH = "/tmp/input_ref.jpg"
IMAGE_OUTPUT_PATH    = "/tmp/output.jpg"

BACKEND_ADDRESS = "https://license.saharatss.org"

rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')

image_size = None

def getTextLocationRect(textInfo):
	frame = textInfo['Geometry']['BoundingBox']
	output = {
		'x1':int(image_size['w']*frame['Left']),
		'y1':int(image_size['h']*frame['Top']),
		'x2':int(image_size['w']*frame['Left']+image_size['w']*frame['Width']),
		'y2':int(image_size['h']*frame['Top'] +image_size['h']*frame['Height'])
	}
	output['p1'] = (output['x1'],output['y1'])
	output['p2'] = (output['x2'],output['y2'])
	return output

def getTextInfo(response,keyword):
	results = list(filter(lambda x: x['Type'] == "LINE", response["TextDetections"]))
	results = list(filter(lambda x: keyword in x['DetectedText'], results))
	if len(results) == 0: return None
	result = results[0]
	result['TextKeyword'] = keyword
	result['TextValue']   = result['DetectedText'].replace(keyword, '').strip()
	result['rect'] = getTextLocationRect(result)
	return result

def detect_text(sourceFile):
	global image_size

	print(f"Rekognition: OCR start")
	imageSource = open(sourceFile, 'rb')
	response = rekognition_client.detect_text(Image={'Bytes': imageSource.read()})
	print(f"Rekognition: OCR end -> {len(response['TextDetections'])} labels detected")

	img = Image.open(sourceFile)
	print(f"PIL: debug image loaded -> {sourceFile}")

	img.thumbnail([1000,1000])
	img = ImageOps.grayscale(img)
	img = ImageOps.colorize(img, black="black", white="white")
	img_canvas = ImageDraw.Draw(img)
	img_font   = ImageFont.truetype('font/arial_bold.ttf', size=15)

	image_size = {'w':img.width, 'h':img.height}
	result = {}
	result['california']     = getTextInfo(response,'USA')
	result['driver_license'] = getTextInfo(response,keyword='DL')
	result['vehicle_class']  = getTextInfo(response,keyword='CLASS')
	
	result['first_name']     = getTextInfo(response,keyword='FN')
	result['last_name']      = getTextInfo(response,keyword='LN')

	result['date_of_birth']  = getTextInfo(response,keyword='DOB')

	result['sex']            = getTextInfo(response,keyword='SEX')
	result['height']         = getTextInfo(response,keyword='HGT')
	result['weight']         = getTextInfo(response,keyword='WGT')
	result['eyes']           = getTextInfo(response,keyword='EYES')
	result['hair']           = getTextInfo(response,keyword='HAIR')

	result['expiration_date'] = getTextInfo(response,keyword='EXP')

	for key,textInfo in result.items():
		if textInfo is not None:
			img_canvas.rectangle([textInfo['rect']['p1'], textInfo['rect']['p2']] , outline=COLOR_TEXT_DETECT, width=2)
			img_canvas.text((textInfo['rect']['x2']+5,textInfo['rect']['y2']-15), textInfo['TextValue'], font=img_font, fill=COLOR_TEXT_DETECT)

	# img.show()

	img.save(IMAGE_OUTPUT_PATH)

	return result

def compare_faces(sourceFile, targetFile):
	imageSource = open(sourceFile, 'rb')
	imageTarget = open(targetFile, 'rb')

	response = rekognition_client.compare_faces(SimilarityThreshold=0,
		SourceImage={'Bytes': imageSource.read()},
		TargetImage={'Bytes': imageTarget.read()})

	for faceMatch in response['FaceMatches']:
		position = faceMatch['Face']['BoundingBox']
		similarity = str(faceMatch['Similarity'])
		print('The face at ' +
					str(position['Left']) + ' ' +
					str(position['Top']) +
					' matches with ' + similarity + '% confidence')

	imageSource.close()
	imageTarget.close()
	return response

def lambda_handler(event, context):
	global IMAGE_DEBUG_S3_PATH
	for record in event['Records']:
		bucket = record['s3']['bucket']['name']
		s3_obj_key  = record['s3']['object']['key']
		s3_obj_name = Path(s3_obj_key).name
		s3_debug_upload_path = f"user_upload/debug/{s3_obj_name}"
		s3_client.download_file(bucket, s3_obj_key, IMAGE_INPUT_PATH)
		print(f"S3 CLI: Image downloaded -> {s3_obj_key}")

		result_ocr = detect_text(IMAGE_INPUT_PATH)
		result_ocr['debug_image_path'] = s3_debug_upload_path
		print(f"Rekognition: OCR done")
		print(json.dumps(result_ocr))

		if '/id/' in s3_obj_key:
			response = requests.post(f'{BACKEND_ADDRESS}/api/id/id/update/result/', json={
				'id_image_name': s3_obj_name,
				'result_ocr': result_ocr
			})
			print(f"API: (ID) backend response -> {response}")

		elif '/matching/' in s3_obj_key:
			driver_license = result_ocr.get('driver_license')
			if driver_license is not None:
				driver_license = driver_license['TextValue']
				response = requests.get(f'{BACKEND_ADDRESS}/api/id/id/getimagepath/', json={
					'driver_license': driver_license,
				})
				if response.status_code == 200:
					id_ref_path = response.json()['path']
					s3_client.download_file(bucket, id_ref_path, IMAGE_INPUT_REF_PATH)
					print(f"S3 CLI: Image downloaded -> {id_ref_path}")
				
					result_face = compare_faces(IMAGE_INPUT_REF_PATH, IMAGE_INPUT_PATH)
					print(f"Rekognition: compare_faces done")
				else:
					result_face = {'FaceMatches': []}
					print(f"Rekognition: compare_faces skip")
			else:
				result_ocr['driver_license'] = {'TextValue':'(undetected)'}
				result_face = {'FaceMatches': []}

			response = requests.post(f'{BACKEND_ADDRESS}/api/id/matching/update/result/', json={
				'matching_image_name': s3_obj_name,
				'result_ocr':  result_ocr,
				'result_face': result_face
			})
			print(f"API: (matching) backend response -> {response}")

		else:
			print(f"API: (ERROR) no target API found")

		s3_client.upload_file(IMAGE_OUTPUT_PATH, bucket, s3_debug_upload_path)
		print(f"S3: Debug image uploaded -> {s3_debug_upload_path}")