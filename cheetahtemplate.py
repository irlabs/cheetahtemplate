import sys
import os

from django.http import HttpResponse
from django.template import Context, RequestContext
from django.conf import settings

from Cheetah.Template import Template

def add_template_directories_to_path():
	# get the template directories from settings
	# and add them to sys.path
	for templates_dir in settings.TEMPLATE_DIRS:
		if templates_dir not in sys.path:
			sys.path.append(templates_dir)

# When this module gets loaded add the directories to the path
add_template_directories_to_path()

def importModule(modulename, name):
	""" Import a named object from a module in the context of this function
	"""
	try:
		module = __import__(modulename, globals(), locals(), [name])
	except ImportError:
		# Report an error in the log files if the template module cannot be imported
		# Maybe this error (not able to import the module), means that we should try
		# to load the template as tmpl, instead of the compiled version . :-)
		print "ERROR. importModule couldn't import pre-compiled template"
		return None
	return getattr(module, name)

def dynamic_import( path ):
	""" Similar to importModule, but different"""
	# from http://www.djangosnippets.org/snippets/50/
	l = path.rfind('.')
	parent, child = path[:l], path[l+1:]
	base = __import__(parent, globals(), globals(), [child])
	return getattr(base, child, None)
	
def get_template(template_name):
	""" Return a DjangoCheetahTemplate object."""
	templateClass = importModule(template_name, template_name)
	if templateClass is None:
		# try to load a non-compiled .tmpl template as last resort.
		templateClassName = ".".join((template_name, "tmpl"))
		tmpl_exists = False
		for path_dir in settings.TEMPLATE_DIRS:
			templateFile = os.path.join(path_dir, templateClassName)
			if os.path.exists(templateFile):
				tmpl_exists = True
				break
		if tmpl_exists:
			t = Template(file=templateFile, searchList=[])
		else:
			error_msg = "Tried sys.path: %s looking for the template %s and failed." % (str(settings.TEMPLATE_DIRS), template_name)
			raise ValueError, error_msg
	else:
		# TODO: intially populate the searchList with Framework objects and dicts
		#		like currentYr, Django filters, and settings.
		t = templateClass(searchList = [])
	return DjangoCheetahTemplate(t)
	
class DjangoCheetahTemplate:
	def __init__(self, cheetahInstance):
		self.template = cheetahInstance
		
	def __getattr__(self, attr):
		if hasattr(self.template, attr):
			return getattr(self.template, attr)
		else:
			raise AttributeError, attr
	
	def render(self, context, *args, **kw):
		# add the context to the searchlist (only if the searchlist was empty)
		if len(self.template.searchList()) < 3:
			for dct in context.dicts:
				self.template.searchList().append(dct)
		# TODO: if the searchList is already populated, update its values with the context
		return self.template.respond()


def render_to_response(template_name, dictionary, context_instance=None):
	template = get_template(template_name)
	if context_instance:
		context_instance.update(dictionary)
	else:
		context_instance = Context(dictionary)
	return HttpResponse(template.render(context_instance))