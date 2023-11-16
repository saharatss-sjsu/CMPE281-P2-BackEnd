from django.contrib import admin
from django.utils.html import format_html

from . import models

class FileAdmin(admin.ModelAdmin):
	def filesize(self, obj):
		input = obj.size
		if input > 10**6: return format_html(f'<span style="white-space:nowrap;">{round(input/10**6)} MB</span>');
		if input > 10**3: return format_html(f'<span style="white-space:nowrap;">{round(input/10**3)} KB</span>');
		return                   format_html(f'<span style="white-space:nowrap;">{input} bytes');
	
	list_display = ('name', 'tag', 'path', 'type', 'filesize', 'creator', 'created', 'uploaded','updated')
	ordering = ('-created',)
	list_filter = ('tag','type')
	fields = ('id','name','creator','path','type','size','note')
	readonly_fields=('id','path', 'type','size','filesize')

	change_form_template = 'file_change_form.html'

admin.site.register(models.File, FileAdmin)