

from gi.repository import GObject, Gtk, Eog
from os.path import join
#import pdb

def dumpMe(A):
	nm=""
	lb=""
	im=""
	fi=""
	
	if 	hasattr(A,'get_name'):
		nm=A.get_name()
	if hasattr(A,'get_label'):
		lb=A.get_label()
	if hasattr(A,'get_image'):
		im=A.get_image()
	#if im != None:
	#	fi=Eog.Image.get_uri_for_display(im)
	print "%s : %s : %s : %s"%(nm,lb,im,fi)
	if hasattr(A,'get_parent'):		
		dumpMe(A.get_parent())


def	find_EogWindow(A):
	if A.get_name() == 'EogWindow':
		return A
	else:
		if hasattr(A,'get_parent'):
			return find_EogWindow(A.get_parent())
		else:
			return None
		






class MetaEditPlugin(GObject.Object, Eog.WindowActivatable):

	window = GObject.property(type=Eog.Window)

	#class Handler:
	#	def __init__(self):
	#		pass
		
	def myFile(self):
		return self.window.get_image().get_uri_for_display()
	
	
			
	@staticmethod
	def revertNotify(self, *args):
		print 'revert()',args
		EogWin=find_EogWindow(self)
		print 'image:',EogWin.get_image().get_uri_for_display()
	
	@staticmethod
	def commitNotify(self, *args):
		print 'commit()',args
		EogWin=find_EogWindow(self)
		print 'image:',EogWin.get_image().get_uri_for_display()
		
		#pdb.set_trace()
		#print 'instance:',Instance(self)
		#print 'super():',Instance(super(MetaEditPlugin))
		#print 'image:',super(MetaEditPlugin).window.get_image().get_uri_for_display()
		
	
	def __init__(self):
		GObject.Object.__init__(self)


	def do_activate(self):
		'''activate plugin - adds my dialog to the Eog Sidebar'''

		sidebar = Eog.Window.get_sidebar(self.window)
		if sidebar:
			plugin = Gtk.Builder()
			plugin.add_from_file(join(self.plugin_info.get_data_dir(),"eogMetaEdit.glade"))
			#plugin.connect_signals(self.Handler())
			plugin.connect_signals(self)
			pluginWidget = plugin.get_object('viewport1')	
			
			#try:
			#	print "\n\nfile:",self.window.get_image().get_uri_for_display()
			#except:
			#	try:
			#		print "\n\nuri:",Eog.Image.get_uri_for_display(self.window.get_image())
			#	except:
			#		pass
			
			self.thumbview = Eog.Window.get_thumb_view(self.window)
			print 'thumb:',self.thumbview
			print 'dir:',dir(self.thumbview)
			
			Eog.Sidebar.add_page(sidebar,"Metadata Editor", pluginWidget)
			
			self.selection_changed_id = \
				self.thumbview.connect('selection-changed', self.selection_changed_cb, self)
			self.state_handler_id = \
				self.window.connect('window-state-event', self.state_changed_cb, self)
		else:
			raise AttributeError('EogSidebar not found!')
		
		
	def do_deactivate(self):
		print "I'm de-Activated!"
		self.thumbview.disconnect(self.selection_changed_id)
		self.window.disconnect(self.state_handler_id)
		



	# The callback functions are done statically to avoid causing additional
	# references on the window property causing eog to not quit correctly.

	@staticmethod
	def	selection_changed_cb(thumb, self):
		print "file changed!",Eog.ThumbView.get_first_selected_image(thumb).get_uri_for_display()
		
			
	@staticmethod
	def state_changed_cb(window, event, self):
		mode = self.window.get_mode()
		print '\n>>>>>>>>>>>>>',
		print ' mode:',mode.value_name,
		try:
			print 'image:',self.window.get_image().get_uri_for_display()
		except:
			print ''
				
		#try:
		#	print "\n\nfile:",self.window.get_image().get_uri_for_display()
		#except:
		#	try:
		#		print "\n\nuri:",Eog.Image.get_uri_for_display(self.window.get_image())
		#	except:
		#		pass
		#self.show_kids(self.window)



