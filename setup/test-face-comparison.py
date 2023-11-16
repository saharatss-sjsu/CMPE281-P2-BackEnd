# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

import boto3
import json
import requests

def s3_get_client():
	return boto3.client(
		service_name="s3",
		aws_access_key_id="AKIATLOLONNQTN6JNR5W",
		aws_secret_access_key="VYz3m/4QhVUgcwpLJIU/ECOiNNg6Dk+DvfR7dw07",
		region_name="us-west-1"
	)

def rekognition_get_client():
	return boto3.client(
		service_name="rekognition",
		aws_access_key_id="AKIATLOLONNQSFPFXHKO",
		aws_secret_access_key="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",
		region_name="us-west-1"
	)

def compare_faces(sourceFile, targetFile):
	rekognition_client = rekognition_get_client()

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

def main():
	s3_client = s3_get_client()
	matching_image_name = '9b3da35e4ff0458aaece20e7813e722b.jpg'
	s3_client.download_file("cmpe281-p2", f"user_upload/id/3d5ef76cd5cc421ebf753ec692186e2d.jpeg", "image1.jpeg")
	s3_client.download_file("cmpe281-p2", f"user_upload/matching/{matching_image_name}", "image2.jpeg")
	result_face = compare_faces('image1.jpeg', 'image2.jpeg')
	response = requests.post(f'http://localhost:8000/api/id/matching/update/result/', json={
		'matching_image_name': matching_image_name,
		'result_face': result_face
	})
	print(response)

if __name__ == "__main__":
	main()