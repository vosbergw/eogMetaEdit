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
#import sys
#import pdb

'''
def showParents(A,pref=""):
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
	print "%s%s : %s : %s : %s"%(pref,nm,lb,im,repr(A))
	if hasattr(A,'get_parent'):		
		showParents(A.get_parent(),pref+" ")
		
def showChildren(A,pref=""):
	nm=""
	lb=""
	im=""
	fi=""
	
	if hasattr(A,'get_name'):
		nm=A.get_name()
	if hasattr(A,'get_label'):
		lb=A.get_label()
	if hasattr(A,'get_image'):
		im=A.get_image()
	print "%s%s : %s : %s : %s"%(pref,nm,lb,im,repr(A))
	if hasattr(A,'get_children'):
		for B in A.get_children():
			showChildren(B,pref+" ")
'''




class MetaEditPlugin(GObject.Object, Eog.WindowActivatable):

	window = GObject.property(type=Eog.Window)	
	Debug = False
	
	def __init__(self):
		GObject.Object.__init__(self)
		

	def do_activate(self):
		'''activate plugin - adds my dialog to the Eog Sidebar'''
		
		# need the sidebar to add my dialog to and the thumbview to track when the file changes.
		
		self.sidebar = self.window.get_sidebar()
		self.thumbview = self.window.get_thumb_view()
		#self.scrollview = self.window.get_view()
		
		#self.image = Eog.Window.get_image(self.window)
		#self.scrollview = Eog.Window.get_view(self.window)
		
		
		self.curImage = None
		#self.curName = None
		#self.oldImage = None
		#self.oldName = None
		self.changedImage = None
		self.ignoreChange = 0
		#self.fixME = False
		
		# build my dialog
		builder = Gtk.Builder()
		builder.add_from_file(join(self.plugin_info.get_data_dir(),"eogMetaEdit.glade"))
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
		self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
		self.metaChanged = False
		
		# set up my callbacks
		
		# the key-press-event callback will only be enabled when one of my comboboxes has focus
		self.window_keyIn_id = self.window.connect('key-press-event', self.inKey)
		self.window.handler_block(self.window_keyIn_id)		
		
		# I'm going to create a dict of callback id's:  { 'signal1': { funct1 : id, funct2 : id}, 'signal2' : { funct1 : id, funct2 : id } ... }
		# hopefully making it easier to remove them without forgetting any.
		
		self.cb_ids = {}
		for S in 'focus-in-event','focus-out-event':
			if not self.cb_ids.has_key(S):
				self.cb_ids[S]={}
			for W in self.newDateEntry,self.newCaptionEntry,self.newKeywordEntry :
				self.cb_ids[S][W] = W.connect(S, self.doFocus, self.window, self.window_keyIn_id)

		for S in 'changed',:
			if not self.cb_ids.has_key(S):
				self.cb_ids[S]={}
			for W in self.newDate, self.newCaption, self.newKeyword:
				self.cb_ids[S][W] = W.connect(S, self.Changed, self)
		
		self.cb_ids['clicked'] = {}
		self.cb_ids['clicked'][self.commitButton] = self.commitButton.connect('clicked', self.commitNotify, self)		
		self.cb_ids['clicked'][self.revertButton] = self.revertButton.connect('clicked', self.revertNotify, self)
		
		self.cb_ids['selection-changed'] = {}
		self.cb_ids['selection-changed'][self.thumbview] = self.thumbview.connect('selection-changed', self.fileChanged, self)
		
		# finally, add my dialog to the sidebar
		Eog.Sidebar.add_page(self.sidebar,"Metadata Editor", pluginDialog)

	
		
		
	def do_deactivate(self):
		'''remove all the callbacks stored in dict self.cb_ids '''
		
		for S in self.cb_ids:
			for W, id in self.cb_ids[S].iteritems():
				W.disconnect(id)
				
		self.window.disconnect(self.window_keyIn_id)



	# The callback functions are done statically to avoid causing additional
	# references on the window property causing eog to not quit correctly.

	@staticmethod
	def doFocus(plugin,event,win,id):
		'''Process the change of focus on for the combobox.  If the combobox has focus, unblock the
		key-press-event callback on the main EogWindow so that I can process the key presses.
		
		Here, plugin is the combobox this call back is set for (focus-in-event and focus-out-event
		'''
		
		if plugin.has_focus():
			win.handler_unblock(id)
		else:
			win.handler_block(id)
		
		return True
	
	
	@staticmethod
	def inKey(plugin, event):
		'''Process key events from the comboboxes.  NOTE:  this callback is set for the EogWindow key-press-event.  I expected to 
		be able to set this callback for the comboboxes themselves, but no matter what I tried the signal went to the main window
		first which caused me to miss any keys acted on by the main EogWindow.  Not sure if this is a bug or if I was doing something
		wrong but I got it working by setting the callback here to perform the default key_press_event for the comboxbox with focus
		and then throwing away the event.  This callback is only enabled when one of the comboboxes has focus - otherwise the key-press-event
		goes to the EogWindow as normal.
		
		
		Here, plugin here is the main EogWindow.  get_focus() returns a handle to the combobox that currently has focus.
		This just calls the comboboxes default callback function and then throws away the event 
		'''
		
		plugin.get_focus().do_key_press_event(plugin.get_focus(),event)
		plugin.emit_stop_by_name('key-press-event')

		return True


	@staticmethod
	def Changed(plugin,self):
		'''one of the comboboxes has changed.  enable the revert and commit buttons and save the current image in changedImage'''
		
		if self.commitButton.get_state() == Gtk.StateType.INSENSITIVE:
			self.commitButton.set_state(Gtk.StateType.NORMAL)
			self.revertButton.set_state(Gtk.StateType.NORMAL)
			#self.changedImage = self.window.get_image()
			self.changedImage = self.thumbview.get_first_selected_image()
			#self.changedImage = self.scrollview.get_property('image')
			if self.changedImage != None:
				if self.Debug:
					print 'marking %s (%s)'%(self.changedImage,urlparse(self.changedImage.get_uri_for_display()).path)
				self.metaChanged = True
		
		return True
			
			
			
	@staticmethod
	def commitNotify(plugin, self):
		'''commit the changes to the file'''
		
		#print 'commit ',self.curName
		
		saveDate = self.newDate.get_active_text()
		saveCaption = self.newCaption.get_active_text()
		saveKeyword = self.newKeyword.get_active_text()
		
		DTvars = [ 'Exif.Photo.DateTimeOriginal', 'Exif.Image.DateTimeOriginal', 'Exif.Photo.DateTimeDigitized' ]
		DTrem = [ 'Xmp.exif.DateTimeOriginal', 'Xmp.dc.date', 'Iptc.Application2.DateCreated', 'Iptc.Application2.TimeCreated' ]
		
		for k in DTvars:
			#print "update [",k,"] to [",saveDate,"]"
			self.metadata.__setitem__(k,saveDate)
		for k in DTrem:
			if k in self.metadata.exif_keys+self.metadata.iptc_keys+self.metadata.xmp_keys:
				#print "removing [",k,"]"
				self.metadata.__delitem__(k)
				
		#CAvars = ['Exif.Image.ImageDescription']
		CAvars = ['Iptc.Application2.Caption']
		#CArem = ['Iptc.Application2.Caption', 'Xmp.dc.description', 'Xmp.acdsee.caption' ] 
		CArem = ['Exif.Image.ImageDescription', 'Xmp.dc.description', 'Xmp.acdsee.caption' ]
			   
		for k in CAvars:
			#print "update [",k,"]  to [",saveCaption,"]"
			self.metadata.__setitem__(k,[saveCaption])
		for k in CArem:
			if k in self.metadata.exif_keys+self.metadata.iptc_keys+self.metadata.xmp_keys:
				#print "removing [",k,"]"
				self.metadata.__delitem__(k)		
				
		KWrem = ['Exif.Photo.UserComment']
		KWvars = ['Iptc.Application2.Keywords']  
		
		for k in KWvars:
			#print "update [",k,"] to ",re.split('\W+',saveKeyword)
			self.metadata.__setitem__(k,re.split('\W+',saveKeyword))
		for k in KWrem:
			if k in self.metadata.exif_keys+self.metadata.iptc_keys+self.metadata.xmp_keys:
				#print "removing [",k,"]"
				self.metadata.__delitem__(k)  
		
		self.metadata.write()
		
		# reset the comboboxes to what was just written
		
		#if self.thumbImage != None:
		#	self.loadMeta(urlparse(self.thumbImage.get_uri_for_display()).path)
		#elif self.curImage != None:
		#	self.loadMeta(urlparse(self.curImage.get_uri_for_display()).path)
		if self.Debug:
			print 'after commit:'
			self.showImages()
			
		#self.loadMeta(urlparse(self.changedImage.get_uri_for_display()).path)		
		self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		self.revertButton.set_state(Gtk.StateType.INSENSITIVE)		
		self.metaChanged = False
		#if self.changedImage != self.thumbImage:
		#	self.changedImage.file_changed()
		self.changedImage = None

		return True
		


	@staticmethod
	def revertNotify(plugin, self):
		'''Revert the 3 comboboxes to the values in the file itself and set the buttons back to insensitive'''
		
		if self.changedImage == None:
			print 'warning: revert selected but nothing to revert to!'
			self.showImages()
		else:
			self.loadMeta(urlparse(self.changedImage.get_uri_for_display()).path)
			self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
			self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
			self.metaChanged = False
			self.changedImage = None

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
	def	fileChanged(thumb, self):
		'''The file has changed.  Load the new metadata and update my dialog accordingly.  The Revert button will also call this function'''
		CANCEL=2
		NO=1
		YES=0
		
		
		
		self.curImage = self.window.get_image()
		#self.curImage = Eog.Window.get_image(self.window)
		#print 'window.get_image: ',self.window.get_image()
		#print dir(self.scrollview)
		#self.viewImage = self.scrollview.get_property('image')
		self.thumbImage = self.thumbview.get_first_selected_image()
		
		if self.Debug:
			print '\n\nfile changed ----------------------------------------------'
			self.showImages()		
		
		if self.ignoreChange < 0:  # check to see if this callback is from a canceled file change
			# let other callbacks run
			if self.Debug:
				print 'ignoring change (%d)'%self.ignoreChange
			if self.ignoreChange == -1 and self.thumbImage != self.changedImage:
				self.ignoreChange -= 1
				self.thumbview.set_current_image(self.changedImage,True)
				return False
			
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
			Event = Gtk.get_current_event()
			if self.Debug:
				print '\n\n---------------------------------------------------'
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
					self.ignoreChange = -2
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
		if self.thumbImage != None:
			if self.Debug:
				print 'loading thumb meta:',urlparse(self.thumbImage.get_uri_for_display()).path
			self.loadMeta(urlparse(self.thumbImage.get_uri_for_display()).path)
		else:
			if self.Debug:
				print 'no meta to load!'
				self.showImages()
			return False
		
		# freshly set comboboxes, disable commit and revert
		self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
		#self.changedImage = None
		self.metaChanged = False

		# return False to let any other callbacks execute as well
		return False


	
	def loadMeta(self, filePath):
		'''set the comboboxes to the current files data'''
		self.fileName.set_label(basename(filePath))
		
		self.metadata = pyexiv2.ImageMetadata(filePath)
		self.metadata.read()		
		
		newDates = self.loadDates()			
		newCaptions = self.loadCaptions()
		newKeywords = self.loadKeywords()

		# set the combobox to no active selection
		self.newDate.set_active(-1)
		self.newCaption.set_active(-1)
		self.newKeyword.set_active(-1)
		
		# for each combobox, get the current settings and clear them in reverse order
		l=range(len(self.newDate.get_model()))
		l.reverse()	   
		for i in l:
			self.newDate.remove(i)
			
		l=range(len(self.newCaption.get_model()))
		l.reverse()
		for i in l:
			self.newCaption.remove(i)
		
		l=range(len(self.newKeyword.get_model()))
		l.reverse()
		for i in l:
			self.newKeyword.remove(i)
		
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
		Exif.Photo.DateTimeOriginal, Photo.DateTimeDigitized and Image.DateTimeOriginal should be
		create date
		The Xmp and Iptc date/time tags should be able to be deleted
		'''		
		DTvars = [ 'Exif.Photo.DateTimeOriginal', 'Exif.Image.DateTimeOriginal', 
				'Exif.Photo.DateTimeDigitized', 'Exif.Image.DateTime' ]
		DTrem = [ 'Xmp.exif.DateTimeOriginal', 'Xmp.dc.date', 'Iptc.Application2.DateCreated',
				'Iptc.Application2.TimeCreated' ]
		
		myTimes = []		
		for k in DTvars+DTrem:
			if k in self.metadata.exif_keys+self.metadata.iptc_keys+self.metadata.xmp_keys:
				if self.metadata[k].raw_value not in myTimes:
					myTimes.append(self.metadata[k].raw_value)
		return myTimes
	
	
	def loadCaptions(self):
		'''
		see http://exiv2.org/tags.html
		Exif.Image.ImageDescription can be an ascii caption
		Exif.Photo.UserComment can contain unicode and should be interpreted as keywords
		
		If zenfolio recognizes caption/keywords in Exif data then should be able to get rid of
		Iptc.Application2.Caption Xmp.acdsee.caption and Xmp.dc.description	
		'''
		
		CAvars = ['Exif.Image.ImageDescription']
		CArem = ['Iptc.Application2.Caption', 'Xmp.dc.description', 'Xmp.acdsee.caption' ]
		
		myCaptions=[]		
		for k in CAvars+CArem:
			if k in self.metadata.exif_keys+self.metadata.iptc_keys+self.metadata.xmp_keys:
				if self.metadata[k].raw_value not in myCaptions:
					myCaptions.append(self.metadata[k].raw_value)				   
		return myCaptions
	
	
	def loadKeywords(self):
		'''
		see http://exiv2.org/tags.html
		Exif.Image.ImageDescription can be an ascii caption
		Exif.Photo.UserComment can contain unicode and should be interpreted as keywords
		
		If zenfolio recognizes caption/keywords in Exif data then should be able to get rid of
		Iptc.Application2.Caption Xmp.acdsee.caption and Xmp.dc.description	
		'''
		
		#KWvars = ['Exif.Photo.UserComment']
		#KWrem = ['Iptc.Application2.Keywords']
		
		myKeywords = []
		
		#for k in KWvars+KWrem:
		if 'Iptc.Application2.Keywords' in self.metadata.exif_keys+self.metadata.iptc_keys+self.metadata.xmp_keys:
			V=self.metadata['Iptc.Application2.Keywords'].raw_value
			myKeywords.append(', '.join(V))
			for kk in V:
				myKeywords.append(kk)
				#myKeywords.append(self.metadata[k].raw_value)
		return myKeywords	


