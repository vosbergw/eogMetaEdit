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

from gi.repository import GObject, Gtk, Eog, PeasGtk
from os.path import join, basename
from urlparse import urlparse
import pyexiv2
import re
from string import strip
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
	
	def __init__(self):
		GObject.Object.__init__(self)
		

	def do_activate(self):
		'''activate plugin - adds my dialog to the Eog Sidebar'''
		
		# need the sidebar to add my dialog to and the thumbview to track when the file changes.
		self.sidebar = Eog.Window.get_sidebar(self.window)
		self.thumbview = Eog.Window.get_thumb_view(self.window)
		
		# build my dialog
		builder = Gtk.Builder()
		builder.add_from_file(join(self.plugin_info.get_data_dir(),"eogMetaEdit.glade"))
		pluginDialog = builder.get_object('eogMetaEdit')
		
		
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
					
		#self.state_handler_id = self.window.connect('window-state-event', self.state_changed_cb, self)
		
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
		'''one of the comboboxes has changed.  enable the revert and commit buttons'''
		
		if self.commitButton.get_state() == Gtk.StateType.INSENSITIVE:
			self.commitButton.set_state(Gtk.StateType.NORMAL)
			self.revertButton.set_state(Gtk.StateType.NORMAL)
		
		return True
	
			
	@staticmethod
	def commitNotify(plugin, self):
		'''commit the changes to the file'''
		
		#print 'commit ',self.currentName
		
		saveDate = self.newDate.get_active_text()
		saveCaption = self.newCaption.get_active_text()
		saveKeyword = self.newKeyword.get_active_text()
		
		#print '	date: [%s]'%saveDate
		#print ' caption: [%s]'%saveCaption
		#print 'keywords: [%s]'%saveKeyword
		
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
		self.fileChanged(self.thumbview, self)
		return True
		


	@staticmethod
	def revertNotify(plugin, self):
		'''Revert the 3 comboboxes to the values in the file itself and set the buttons back to insensitive'''
		
		self.fileChanged(self.thumbview, self)
		#self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		#self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
		return True


	@staticmethod
	def	fileChanged(thumb, self):
		'''The file has changed.  Load the new metadata and update my dialog accordingly.  The Revert button will also call this function'''
	
		self.currentName = urlparse(Eog.ThumbView.get_first_selected_image(thumb).get_uri_for_display()).path
		self.fileName.set_label(basename(self.currentName))
		
		self.metadata = pyexiv2.ImageMetadata(self.currentName)
		self.metadata.read()		
		
		newDates = self.loadDates()
		#print '%d new dates'%len(newDates)
		#for l in range(len(newDates)):
		#	print 'newDates[%d]:[%s]'%(l,newDates[l])
			
		newCaptions = self.loadCaptions()
		#print '%d new captions'%len(newCaptions)
		#for l in range(len(newCaptions)):
		#	print 'newCaptions[%d]:[%s]'%(l,newCaptions[l])
			
		newKeywords = self.loadKeywords()
		#print '%d new keywords'%len(newKeywords)
		#for l in range(len(newKeywords)):
		#	print 'newKeywords[%d]:[%s]'%(l,newKeywords[l])

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
				#except KeyError:
				#captionEntry.append_text(c['x-default'])
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
				#if len(keywordEntry.get_model()) < 1:
				#keywordEntry.append_text('<keyword list>')
		self.newKeyword.set_active(0)
		
		# since we have just set the values from the file, disable the Revert and Commit buttons
		self.commitButton.set_state(Gtk.StateType.INSENSITIVE)
		self.revertButton.set_state(Gtk.StateType.INSENSITIVE)
		
		# return False to let any other callbacks execute as well
		return False
	
		
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
	
	
	
	#@staticmethod
	#def state_changed_cb(window, event, self):
	#	mode = self.window.get_mode()
	#	#print '\n>>>>>>>>>>>>>',
	#	#print ' mode:',mode.value_name,
	#	#try:
	#		print 'image:',self.window.get_image().get_uri_for_display()
	#	except:
	#		print ''
				
		#try:
		#	print "\n\nfile:",self.window.get_image().get_uri_for_display()
		#except:
		#	try:
		#		print "\n\nuri:",Eog.Image.get_uri_for_display(self.window.get_image())
		#	except:
		#		pass
		#self.show_kids(self.window)



