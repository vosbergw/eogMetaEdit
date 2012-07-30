
from gi.repository import GObject, Gtk, Eog
import pdb
from os.path import join

class MetaEditPlugin(GObject.Object, Eog.WindowActivatable):

	class Handler:
		def __init__(self):
			pass
		
	#pdb.set_trace()
	# Override EogWindowActivatable's window property
	window = GObject.property(type=Eog.Window)
	
	#print 'properties:',GObject.Object.get_properties()
	
	#pdb.set_trace()
	
	def __init__(self):
		#print 'init self'
		GObject.Object.__init__(self)

	
	
	#plugin->gtkbuilder_widget = GTK_WIDGET (gtk_builder_get_object (plugin->sidebar_builder, "viewport1"));	
	#eog_sidebar_add_page (EOG_SIDEBAR (sidebar), "Details",
	#		      plugin->gtkbuilder_widget);
	'''
	builder = Gtk.Builder()
	builder.add_from_file("/home/wayne/.config/plugins/eogMetaEdit.glade")
    #builder.connect_signals(Handler())
    
	#window = builder.get_object("metaEditDialog")
    
	dateEntry = builder.get_object("dateEntry")
	captionEntry = builder.get_object("captionEntry")
	keywordEntry = builder.get_object("keywordEntry")
	builder.connect_signals(Handler())
	window.show_all()  
	'''

	'''
	def update_ui(self):
		print 'update_ui'
		plugin = Gtk.Builder()
		plugin.add_from_file("/home/wayne/.config/plugins/eogMetaEdit.glade")
		plugin.connect_signals(Handler())
		pluginWidget = plugin.get_object('viewport1')
		pdb.set_trace()
	'''
	
	#def __init__(self):
	#	GObject.Object.__init__(self)

	def do_activate(self):
		'''activate plugin - adds my dialog to the Eog Sidebar'''

		sidebar = Eog.Window.get_sidebar(self.window)
		if sidebar:
			#print 'sidebar:',sidebar
			#print "\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
			#self.show_kids(sidebar)
			plugin = Gtk.Builder()
			plugin.add_from_file(join(self.plugin_info.get_data_dir(),"eogMetaEdit.glade"))
			plugin.connect_signals(self.Handler())
			pluginWidget = plugin.get_object('viewport1')	
			
			#print "\n\nEOG",dir(Eog)
			#print "\n\nIMAGE",dir(Eog.Image)
			#print "\n\nIMAGECLASS",dir(Eog.ImageClass)
			#print "\n\nIMAGEDATA",dir(Eog.ImageData)
			#print "\n\nExifDetails",dir(Eog.ExifDetails)
			#print "\n\nSIDEBAR",dir(Eog.Sidebar)
			
			#try:
			#	print "\n\nfile:",self.window.get_image().get_uri_for_display()
			#except:
			#	try:
			#		print "\n\nuri:",Eog.Image.get_uri_for_display(self.window.get_image())
			#	except:
			#		pass
			
			Eog.Sidebar.add_page(sidebar,"My MetaEditor", pluginWidget)
			
			self.state_handler_id = \
				self.window.connect('window-state-event', self.state_changed_cb, self)
		else:
			raise AttributeError('EogSidebar not found!')
		
		

	def do_deactivate(self):
		print "I'm de-Activated!"
		self.window.disconnect(self.state_handler_id)



	# The callback functions are done statically to avoid causing additional
	# references on the window property causing eog to not quit correctly.
	
	
	def find_sidebar(self,A):
		'''return the sidebar GObject'''
		try:
			for a in A.get_children():
				try:
					n=a.get_name()
				except:
					n=''
				if n == 'EogSidebar':
					return a 
				else:
					t = self.find_sidebar(a)
					if t:
						return t
		except:
			return False
			
	def show_kids(self,A,pre='',dump=False,level=0):
		'''looking for get_name()="EogSidebar"  '''
		
		#print '\n%s>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'%pre
		try:
			for a in A.get_children():
				print '%s%d %s'%(pre,level,a),
				try:
					print 'label(%s)'%a.get_label(),
				except:
					print 'label()',
				try:
					print 'name(%s)'%a.get_name()
					#if a.get_name() == 'EogSidebar':
					#	dump=True
				except:
					print 'name()'
					
				if dump:
					print '\ndir:%s\n'%dir(a)
				try:
					self.show_kids(a,pre+'  ',dump,level=level+1)					
				except:
					pass
					#print '%sI guess no children'%pre+'  '
		except:
			pass
			#print '%sMaybe Not'%pre
		
	@staticmethod
	def state_changed_cb(window, event, self):
		mode = self.window.get_mode()
		print '\n\n###########################################################'
		print 'mode:',mode.value_name
		print 'image:',self.window.get_image()
		
		print "state changed!"
		
		try:
			print "\n\nfile:",self.window.get_image().get_uri_for_display()
		except:
			try:
				print "\n\nuri:",Eog.Image.get_uri_for_display(self.window.get_image())
			except:
				pass
		#self.show_kids(self.window)
		
		
		#sidebar = self.find_sidebar(self.window)
		#if sidebar:
		#	#print 'sidebar:',sidebar
		#	print "\n\n==================================================="
		#	self.show_kids(sidebar)
		#else:
		#	print 'sidebar not found'
		
		#pdb.set_trace()
		


