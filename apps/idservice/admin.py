from django.contrib import admin

from . import models

class IDAdmin(admin.ModelAdmin):
	def has_image(self, obj):
		return obj.image is not None
	has_image.boolean = True

	list_display = ('driver_license', 'first_name', 'last_name', 'sex', 'eyes', 'hair', 'vehicle_class', 'has_image', 'created')
	ordering = ('created',)
	list_filter = ('vehicle_class', 'sex')
	change_list_template = 'id_change_list.html'
	change_form_template = 'id_change_form.html'
admin.site.register(models.ID, IDAdmin)


class MatchingAdmin(admin.ModelAdmin):
	list_display = ('driver_license', 'creator', 'created', 'resulted', 'face_similarity' ,'is_matched')
	readonly_fields=('id','driver_license', 'creator','created','resulted','is_matched','face_similarity','result_face','result_ocr','result_matching','image')
	ordering = ('created',)
	list_filter = ('is_matched',)
	change_form_template = 'matching_change_form.html'
admin.site.register(models.Matching, MatchingAdmin)