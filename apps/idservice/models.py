from django.db import models
from django.contrib.auth.models import User
import uuid

from apps.fileservice.models import File
from apps.fileservice.connector import s3_object_delete

SEX = (('M','Male'), ('F','Female'))
COLOR = (('SIL','Aluminum'),
('AUB','Auburn'),
('BAL','Bald'),
('BGE','Beige'),
('BLK','Black'),
('BLD','Blonde'),
('BLU','Blue'),
('DBL','Blue, Dark'),
('LBL','Blue, Light'),
('BRO','Brown'),
('MAR','Burgundy'),
('COM','Chrome'),
('CPR','Copper'),
('CRM','Cream'),
('GLD','Gold'),
('GRY','Gray'),
('GRN','Green'),
('DGR','Green, Dark'),
('LGR','Green, Light'),
('HAZ','Hazel'),
('CRM','Ivory'),
('LAV','Lavender'),
('MAR','Maroon'),
('ONG','Orange'),
('PNK','Pink'),
('PLE','Purple'),
('RED','Red'),
('SIL','Silver'),
('COM','Stainless Steel'),
('TAN','Tan'),
('TRQ','Turquoise'),
('WHI','White'),
('YEL','Yellow'))

class IDModelQuerySet(models.query.QuerySet):
	def delete(self):
		for obj in self.all():
			obj.delete()

class ID(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	driver_license  = models.CharField(max_length=20)
	first_name      = models.CharField(max_length=150, blank=True, null=True)
	last_name       = models.CharField(max_length=150, blank=True, null=True)
	address         = models.TextField(blank=True, null=True)
	date_of_birth   = models.DateField(blank=True, null=True)

	sex             = models.CharField(max_length=1, choices=SEX, blank=True, null=True)
	height          = models.FloatField(blank=True, null=True)
	weight          = models.IntegerField(blank=True, null=True)
	eyes            = models.CharField(max_length=3, choices=COLOR, blank=True, null=True)
	hair            = models.CharField(max_length=3, choices=COLOR, blank=True, null=True)
	vehicle_class   = models.CharField(max_length=1, blank=True, null=True)

	issue_date      = models.DateField(blank=True, null=True)
	expiration_date = models.DateField(blank=True, null=True)

	image           = models.ForeignKey(File, on_delete=models.CASCADE, related_name='id_image', blank=True, null=True)

	created  = models.DateTimeField(auto_now_add=True)
	updated  = models.DateTimeField(auto_now=True)

	result_ocr = models.JSONField(blank=True, null=True)

	objects = IDModelQuerySet.as_manager()

	def __str__(self):
		return self.driver_license
	class Meta:
		verbose_name = 'ID'
		verbose_name_plural = 'IDs'

	def delete(self, using=None, keep_parents=False):
		self.image.delete()
		s3_object_delete(file_path=f"user_upload/debug/{self.image.name}")
		super().delete()

	def dict(self):
		return {
			'id': self.id,
			'driver_license': self.driver_license,
			'first_name': self.first_name,
			'last_name':  self.last_name,
			'created': self.created,
			'updated': self.updated,
			'image': self.image.dict(),
		}
	

class Matching(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	# input
	driver_license   = models.CharField(max_length=20)
	image            = models.ForeignKey(File, on_delete=models.CASCADE, related_name='matching_image', blank=True, null=True)
	
	# output
	face_similarity  = models.FloatField(blank=True, null=True)
	result_face      = models.JSONField(blank=True, null=True)
	result_ocr       = models.JSONField(blank=True, null=True)
	result_matching  = models.JSONField(blank=True, null=True)
	is_matched       = models.BooleanField(blank=True, null=True)

	creator          = models.ForeignKey(User, on_delete=models.CASCADE)
	created          = models.DateTimeField(auto_now_add=True)
	resulted         = models.DateTimeField(blank=True, null=True)

	objects = IDModelQuerySet.as_manager()

	def __str__(self):
		return self.driver_license

	def delete(self, using=None, keep_parents=False):
		self.image.delete()
		s3_object_delete(file_path=f"user_upload/debug/{self.image.name}")
		super().delete()

	def dict(self):
		return {
			'id': self.id,
			'driver_license': self.driver_license,
			'image': self.image.dict(),
			'created': self.created,
		}