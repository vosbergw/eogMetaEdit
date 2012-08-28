eogMetaEdit
===========

Metadata Editor plugin for Eye of Gnome

Developed on Ubuntu 12.04 with EoG 3.4.   This plugin will allow you to edit the following meta
tags:

* Original Photo Date:

		+ Exif.Photo.DateTimeOriginal, Exif.Image.DateTimeOriginal and Exif.Photo.DateTimeDigitized will be set to the specified date.
		+ Xmp.exif.DateTimeOriginal, Xmp.dc.date, Iptc.Application2.DateCreated and Iptc.Application2.TimeCreated will be removed.

* Captions:

		+ Iptc.Application2.Caption will be set as specified.
		+ Exif.Image.ImageDescription, Xmp.dc.description and Xmp.acdsee.caption will be removed.

* Keywords:

		+ Iptc.Application2.Keywords will be set to the specified list of keywords.
		+ Exif.Photo.UserComment will be removed.

		