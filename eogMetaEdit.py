'''
This file is part of eogMetaEdit.

eogMetaEdit is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

eogMetaEdit is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with eogMetaEdit.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2012 Wayne Vosberg <wayne.vosberg@mindtunnel.com>
'''

from gi.repository import GObject, Gtk, Gdk, Eog, PeasGtk
from os.path import join, basename
from urlparse import urlparse
import pyexiv2
import re
import time
from string import strip



class MetaEditPlugin(GObject.Object, Eog.WindowActivatable):

	# the main EoG window
	window = GObject.property(type=Eog.Window)	
	Debug = False
	
	def __init__(self):
		GObject.Object.__init__(self)
		

	def do_activate(self):
		'''Activate the plugin - adds my dialog to the Eog Sidebar'''
		
		# the sidebar is where the eogMetaEdit dialog is added
		self.sidebar = self.window.get_sidebar()
		# need to track file changes in the EoG thumbview
		self.thumbview = self.window.get_thumb_view()		
		
		# the EogImage of the main window
		self.curImage = None
		# the EogImage selected in the thumbview
		self.thumbImage = None
		# the EogImage whose metadata has been modified
		self.changedImage = None
		# flag for selection_changed_cb to note when we made the change
		self.ignoreChange = 0
		
		# build my dialog
		builder = Gtk.Builder()
		builder.add_from_file(join(self.plugin_info.get_data_dir(),\
								"eogMetaEdit.glade"))
		pluginDialog = builder.get_object('eogMetaEdit')
		self.isChangedDialog = builder.get_object('isChangedDialog')
		
		
		# save my widgets		
		self.fileName = builder.get_object("fileName")
		
		self.newDate = builder.get_object("newDate")
		self.newDateEntry = builder.get_object("newDateEntry")
		
		self.newCaption = builder.get_object("newCaption")
		self.newCaptionEntry = builder.get_object("newCaptionEntry")
		
		self.newKeyword = builder.get_object("newKeyword")
		self.newKeywordEntry = builder.get_object("newKeywordEntry")
		
		self.commitButton = builder.get_object('commitButton')
		self.revertButton = builder.get_object('revertButton')
		
		# set the buttons disabled initially
		self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
		self.metaChanged = False
		
		self.combos =  [	self.newDate, self.newCaption, self.newKeyword ]
		self.entries = [	self.newDateEntry, self.newCaptionEntry, 
							self.newKeywordEntry ]
		
		# set up my callbacks
		
		# I'm going to create a dict of callback id's:  
		# { 'signal1': { funct1 : id, funct2 : id}, 
		#   'signal2' : { funct1 : id, funct2 : id } 
		#    ... }
		# hopefully making it easier to remove them without forgetting any.
		
		# the key-press-event callback will only be enabled when one of my 
		# comboboxes has focus
		self.cb_ids = {}
		self.cb_ids['key-press-event'] = {}
		
		self.cb_ids['key-press-event'][self.window] = \
			self.window.connect('key-press-event', self.key_press_event_cb)
		
		self.window.handler_block(self.cb_ids['key-press-event'][self.window])		
		
		
		
		for S in 'focus-in-event','focus-out-event':
			if not self.cb_ids.has_key(S):
				self.cb_ids[S]={}
			for W in self.entries:
				self.cb_ids[S][W] = W.connect(S, self.focus_event_cb, \
					self.window, self.cb_ids['key-press-event'][self.window])

		for S in 'changed',:
			if not self.cb_ids.has_key(S):
				self.cb_ids[S]={}
			for W in self.newDate, self.newCaption, self.newKeyword:
				self.cb_ids[S][W] = W.connect(S, self.combo_changed_cb, self)
		
		self.cb_ids['clicked'] = {}
		self.cb_ids['clicked'][self.commitButton] = \
			self.commitButton.connect('clicked', self.commit_clicked_cb, self)		
		self.cb_ids['clicked'][self.revertButton] = \
			self.revertButton.connect('clicked', self.revert_clicked_cb, self)
		
		self.cb_ids['selection-changed'] = {}
		self.cb_ids['selection-changed'][self.thumbview] = \
			self.thumbview.connect('selection-changed', \
				self.selection_changed_cb, self)
		
		# finally, add my dialog to the sidebar
		Eog.Sidebar.add_page(self.sidebar,"Metadata Editor", pluginDialog)

	
		
	def do_deactivate(self):
		'''remove all the callbacks stored in dict self.cb_ids '''
		
		for S in self.cb_ids:
			for W, id in self.cb_ids[S].iteritems():
				W.disconnect(id)



	# The callback functions are done statically to avoid causing additional
	# references on the window property causing eog to not quit correctly.

	@staticmethod
	def focus_event_cb(plugin,event,win,id):
		'''
		Process the change of focus for the comboboxes.  If the combobox has 
		focus, unblock the key-press-event callback on the main EogWindow so 
		that I can process the key presses.
		
		Here, plugin is the combobox this callback is set for (focus-in-event 
		and focus-out-event
		
		'''
		
		if plugin.has_focus():
			win.handler_unblock(id)
		else:
			win.handler_block(id)
		
		return True
	
	
	@staticmethod
	def key_press_event_cb(plugin, event):
		'''
		Process key events from the comboboxes.  NOTE:  this callback is set 
		for the EogWindow key-press-event.  I expected to be able to set this 
		callback for the comboboxes themselves, but no matter what I tried 
		the signal went to the main window first which caused me to miss any 
		keys acted on by the main EogWindow.  Not sure if this is a bug or if 
		I was doing something wrong but I got it working by setting the 
		callback here to perform the default key_press_event for the comboxbox 
		with focus and then throwing away the event.  This callback is only 
		enabled when one of the comboboxes has focus - otherwise the 
		key-press-event goes to the EogWindow as normal.
		
		'''
		
		# find out which widget has focus, do the default event and then
		# throw away the event
		plugin.get_focus().do_key_press_event(plugin.get_focus(),event)
		plugin.emit_stop_by_name('key-press-event')

		return True



	@staticmethod
	def combo_changed_cb(plugin,self):
		'''
		One of the comboboxes has changed.  
		Enable the revert and commit buttons and save changedImage
		
		'''
		
		if self.commitButton.get_state() == Gtk.StateType.INSENSITIVE:
			self.commitButton.set_state(Gtk.StateType.NORMAL)
			self.revertButton.set_state(Gtk.StateType.NORMAL)
			self.metaChanged = True
			#if self.changedImage == None:
			if self.thumbview.get_first_selected_image() != None:
				self.changedImage = self.thumbview.get_first_selected_image()
			elif self.changedImage == None:
				self.showImages()
				raise ValueError('combo_changed_cb called but both '+\
						'changedImage and thumbImage are None!')
			
			if self.Debug:
				print '\n--',self.showImages(),'\n--'
				print 'marking %s (%s)'%(self.changedImage,urlparse(self.changedImage.get_uri_for_display()).path)
		
		return True
			
			
			
	@staticmethod
	def commit_clicked_cb(plugin, self):
		'''Commit the changes to the file'''
		
		if self.Debug:
			print 'commit ',urlparse(self.changedImage.get_uri_for_display()).path
		
		saveDate = self.newDate.get_active_text()
		saveCaption = self.newCaption.get_active_text()
		saveKeyword = self.newKeyword.get_active_text()
		
		DTvars = [	'Exif.Photo.DateTimeOriginal',
					'Exif.Image.DateTimeOriginal',
					'Exif.Photo.DateTimeDigitized' ]
		DTrem = [	'Xmp.exif.DateTimeOriginal',
					'Xmp.dc.date',
					'Iptc.Application2.DateCreated',
					'Iptc.Application2.TimeCreated' ]
		
		for k in DTvars:
			if self.Debug:
				print "update [",k,"] to [",saveDate,"]"
			self.metadata.__setitem__(k,saveDate)
		for k in DTrem:
			if k in self.all_keys:
				if self.Debug:
					print "removing [",k,"]"
				self.metadata.__delitem__(k)
				
		CAvars = [	'Iptc.Application2.Caption' ]
		CArem = [	'Exif.Image.ImageDescription',
					'Xmp.dc.description',
					'Xmp.acdsee.caption' ]
			   
		for k in CAvars:
			if self.Debug:
				print "update [",k,"]  to [",saveCaption,"]"
			self.metadata.__setitem__(k,[saveCaption])
		for k in CArem:
			if k in self.all_keys:
				if self.Debug:
					print "removing [",k,"]"
				self.metadata.__delitem__(k)		
				
		KWrem = [	'Exif.Photo.UserComment' ]
		KWvars = [	'Iptc.Application2.Keywords' ]  
		
		for k in KWvars:
			if self.Debug:
				print "update [",k,"] to ",re.split('\W+',saveKeyword)
			self.metadata.__setitem__(k,re.split('\W+',saveKeyword))
		for k in KWrem:
			if k in self.all_keys:
				if self.Debug:
					print "removing [",k,"]"
				self.metadata.__delitem__(k)  
		
		self.metadata.write()
		
		if self.Debug:
			print 'after commit:'
			self.showImages()
			
		#self.loadMeta(urlparse(self.changedImage.get_uri_for_display()).path)		
		self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		self.revertButton.set_state(Gtk.StateType.INSENSITIVE)		
		self.metaChanged = False
		#if self.changedImage != self.thumbImage:
		#	self.changedImage.file_changed()
		#self.changedImage = None

		return True
		


	@staticmethod
	def revert_clicked_cb(plugin, self):
		'''
		Revert the three comboboxes to the values in the file itself and set 
		the buttons back to insensitive
		
		'''
		
		if self.changedImage == None:
			self.showImages()
			raise ValueError('revert clicked but there is no changedImage!')
		else:
			self.loadMeta(urlparse(self.changedImage.\
							get_uri_for_display()).path)
			self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
			self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
			self.metaChanged = False
			#self.changedImage = None

		return True
	
	
	
	def showImages(self):
		'''debug function: dump the current images paths'''
		
		if self.curImage == None:
			print 'current: None'
		else:
			print 'current: ',urlparse(self.curImage.get_uri_for_display()).path
		try:
			print 'win says: ',urlparse(self.window.get_image().get_uri_for_display()).path
		except:
			print 'none'
		if self.changedImage == None:
			print 'changed: None'
		else:
			print 'changed: ',urlparse(self.changedImage.get_uri_for_display()).path
		if self.thumbImage == None:	
			print 'thumb: None'
		else:
			print 'thumb: ',urlparse(self.thumbImage.get_uri_for_display()).path
		try:
			print 'thumb says: ',urlparse(self.thumbview.get_first_selected_image().get_uri_for_display()).path
		except:
			print 'none'
		
		
		
	@staticmethod
	def	selection_changed_cb(thumb, self):
		'''
		The file has changed.  Load the new metadata and update my dialog 
		accordingly.
		
		If this cb is hit when there are currently unsaved metadata changes
		you will be prompted as to whether to 1) cancel the selection change,
		2) throw away the unsaved changes and load the new file or 3) save
		the changes and load the new file.
		
		'''
		
		# constanst for isChangeDialog
		CANCEL=2	# cancel the file change
		NO=1		# discard the changes and load the new file
		YES=0		# save the changes and load the new file
		
		
		
		self.curImage = self.window.get_image()
		self.thumbImage = self.thumbview.get_first_selected_image()
		Event = Gtk.get_current_event()
		if self.Debug:
			print '\n\nfile changed ----------------------------------------------'
			print 'Event: ',Event
			if Event != None:
				print 'Event type: ',Event.type
			self.showImages()
			
		if Event != None and self.thumbImage == None:
			if self.Debug:
				print 'selection event received with no thumbImage.  discard it'
			return False
			#self.thumbview.set_current_image(self.changedImage,True)
		#	if self.Debug:
		#		print 'throwing event caused by loading thumbnail'
		#	return False		
		
		# check to see if this callback is from a canceled file change
		if self.ignoreChange < 0:  
			if self.Debug:
				print 'ignoring change (%d)'%self.ignoreChange
			#if self.ignoreChange == -1 and self.thumbImage != self.changedImage:
			#	self.ignoreChange -= 1
			#	self.thumbview.set_current_image(self.changedImage,True)
			#	return False
			
			self.ignoreChange += 1
			#if self.thumbImage != self.changedImage and self.thumbImage != None:
			#	#self.ignoreChange -= 1
			#	print 'resetting thumb again %s (%s)'%(self.changedImage,urlparse(self.changedImage.get_uri_for_display()).path)
			#	self.thumbview.set_current_image(self.changedImage,True)
			#	return True
			#self.thumbview.unselect_all()
			#self.thumbview.emit_stop_by_name('button-press-event')
			#self.thumbview.emit(Gtk.EventButton)
			#if self.fixME:
			#	self.fixME = False
			#	self.ignoreChange -= 1
			#	print 'resetting again %s (%s)'%(self.changedImage,urlparse(self.changedImage.get_uri_for_display()).path)
			#	self.thumbview.set_current_image(self.changedImage,True)
								
			return False	
		elif self.metaChanged:
			
			if self.Debug:
				print '\n---------------------------------------------------'
				print 'event: %s (%s) state: %s'%(Event.type,Event.get_click_count(),Event.get_state())
				print 'device: %s'%Event.get_device()
				print 'source: %s'%Event.get_source_device()
				print 'button: ',Event.get_button()
				print 'keycode: ',Event.get_keycode()
				print 'keyval: ',Event.get_keyval()
				print 'screen: ',Event.get_screen()
				print 'window stat: ',Event.window_state
			
			if Event.type == Gdk.EventType.BUTTON_PRESS:
				# we got here by clicking a thumbnail in the thumb navigator.  throw away the
				# release event or we will be left dragging the thumbnail after the dialog closes
				# (not a critical error, but forces you to click an extra time in the thumb nav
				# to release the drag
				self.thumbview.emit('button-release-event', Event)
				#E='Mouse'
			#elif Event.type == Gdk.EventType.KEY_PRESS:
				# got here by the arrow keys, no special handling seems to be required
				#E='Arrow'
			#elif Event.type == Gdk.EventType.BUTTON_RELEASE:
				#E='Toolbar'

				
				# got here by the toolbar button (next/previous)
				# if we treat this the same as the BUTTON_PRESS we are left with 2 images selected
				# in nav windows with the wrong one displayed.  selecting the arrow again will cause
				# a crash (glibc: eog double free or corruption)
				#self.fixME = True
				#pdb.set_trace()
				#Event.free()
				#self.thumbview.unselect_all()

			
			self.result = self.isChangedDialog.run()
			self.isChangedDialog.hide()

			if self.result == CANCEL or self.result < 0:
				# stay on the current file.  
				if self.changedImage != None:
					if self.Debug:
						print 'resetting thumb to %s (%s)'%(self.changedImage,urlparse(self.changedImage.get_uri_for_display()).path)
					# ignore this and the next file changed callback so that we
					# revert to the previous photo without modifying the comboboxes
					self.ignoreChange = -1
					self.thumbview.set_current_image(self.changedImage,True)
					#self.scrollview.set_property('image',self.changedImage)
					
					return False
				else:
					print 'NOTHING TO REVERT TO!!!'
					self.showImages()
				
			elif self.result == YES:
				# save the changes, as a result of the change this function will be 
				# called again with the commit button state INSENSITIVE
				self.commitButton.clicked()
				#return False
			else:
				# no was pushed.  just continue on with the normal file change
				self.metaChanged = False
				#return True		
		
		#if self.curImage != None:
		#	print 'loading current meta:',urlparse(self.curImage.get_uri_for_display()).path
		#	self.loadMeta(urlparse(self.curImage.get_uri_for_display()).path)
		if self.thumbImage == None:
			if self.changedImage != None:
				if self.Debug:
					print 'setting thumbImage to changedImage'
				self.thumbImage = self.changedImage
		
		if self.thumbImage != None:		
			if self.Debug:
				print 'loading thumb meta:',\
					urlparse(self.thumbImage.get_uri_for_display()).path
			self.loadMeta(urlparse(self.thumbImage.get_uri_for_display()).path)
		else:
			if self.Debug:
				print 'no meta to load!'
				self.showImages()
			return False
		
		# freshly set comboboxes, disable commit and revert
		self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
		self.metaChanged = False

		# return False to let any other callbacks execute as well
		return False



	def clearCombo(self,combo):
		'''clear a combobox'''
		
		combo.set_active(-1)		
		l=range(len(combo.get_model()))
		l.reverse()	   
		for i in l:
			combo.remove(i)
	
	
	
	def loadMeta(self, filePath):
		'''set the comboboxes to the current files data'''
		self.fileName.set_label(basename(filePath))
		
		self.metadata = pyexiv2.ImageMetadata(filePath)
		self.metadata.read()		
		self.all_keys = self.metadata.exif_keys+self.metadata.iptc_keys+\
			self.metadata.xmp_keys
			
		newDates = self.loadDates()			
		newCaptions = self.loadCaptions()
		newKeywords = self.loadKeywords()

		for CB in self.combos:
			self.clearCombo(CB)
		
		# clear the combobox text entry as well
		self.newDateEntry.set_text('')
		self.newCaptionEntry.set_text('')
		self.newKeywordEntry.set_text('')		
		
		# and finally set the new values and make them active
		for t in newDates:
			try:
				self.newDate.append_text(t)
			except:
				self.newDate.append_text(t[0])
		self.newDate.set_active(0)		
		
		for c in newCaptions:
			try:
				self.newCaption.append_text(c)
			except:
				try:
					self.newCaption.append_text(c[0])
				except KeyError:
					self.newCaption.append_text(c['x-default'])
				except:
					print 'error:',sys.exc_info()
		self.newCaption.set_active(0)	
		
		for k in newKeywords:  
			try:  
				self.newKeyword.append_text(k)
			except:
				self.newKeyword.append_text(k[0])
		self.newKeyword.set_active(0)



			
	def loadDates(self):
		'''
		see http://exiv2.org/tags.html
		Exif.Image.DateTime is the mod time of the image
		Exif.Photo.DateTimeOriginal, Photo.DateTimeDigitized and 
		Image.DateTimeOriginal should be create date
		The Xmp and Iptc date/time tags should be able to be deleted
		
		'''		
		
		DTvars = [	'Exif.Photo.DateTimeOriginal',
					'Exif.Image.DateTimeOriginal', 
					'Exif.Photo.DateTimeDigitized',
					'Exif.Image.DateTime' ]
		DTrem = [	'Xmp.exif.DateTimeOriginal',
					'Xmp.dc.date',
					'Iptc.Application2.DateCreated',
					'Iptc.Application2.TimeCreated' ]
		
		myTimes = []		
		for k in DTvars+DTrem:
			if k in self.all_keys:
				if self.metadata[k].raw_value not in myTimes:
					myTimes.append(self.metadata[k].raw_value)
		return myTimes
	
	
	
	def loadCaptions(self):
		'''
		see http://exiv2.org/tags.html
		Exif.Image.ImageDescription can be an ascii caption
		Exif.Photo.UserComment can contain unicode and should be interpreted 
		as keywords
		
		If zenfolio recognizes caption/keywords in Exif data then should be able to get rid of
		Iptc.Application2.Caption Xmp.acdsee.caption and Xmp.dc.description	
		'''
		
		CAvars = [	'Exif.Image.ImageDescription']
		CArem = [	'Iptc.Application2.Caption', 
					'Xmp.dc.description', 
					'Xmp.acdsee.caption' ]
		
		myCaptions=[]		
		for k in CAvars+CArem:
			if k in self.all_keys:
				if self.metadata[k].raw_value not in myCaptions:
					myCaptions.append(self.metadata[k].raw_value)				   
		return myCaptions
	
	
	
	def loadKeywords(self):
		'''
		see http://exiv2.org/tags.html
		Exif.Image.ImageDescription can be an ascii caption
		Exif.Photo.UserComment can contain unicode and should be 
		interpreted as keywords
		
		If zenfolio recognizes caption/keywords in Exif data then should 
		be able to get rid of Iptc.Application2.Caption Xmp.acdsee.caption 
		and Xmp.dc.description	
		
		'''

		myKeywords = []
		
		if 'Iptc.Application2.Keywords' in self.all_keys:
			V=self.metadata['Iptc.Application2.Keywords'].raw_value
			myKeywords.append(', '.join(V))
			for kk in V:
				myKeywords.append(kk)
		return myKeywords	


