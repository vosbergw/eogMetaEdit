eogMetaEdit
===========

Metadata Editor plugin for Eye of Gnome

Developed on Ubuntu 12.04 with EoG 3.4.   This plugin will modify image
metadata for Zenfolio and Darktable (pre-import).


When an image is loaded into EoG, the following will be checked:

* Exif.Image.Make, if not set or Null, will be set to "eogMetaEdit"
* Exif.Image.Model, if not set or Null, will be set to "eogMetaEdit v0.2b"
* Exif.Application2.Headline and Xmp.dc.title will be set to the image title.  
* Exif.Photo.DateTimeOriginal, Exif.Image.DateTimeOriginal, 
Exif.Photo.DateTimeDigitized and Exif.Image.DateTime will all be set to the
photo creation date.
* Exif.Image.ImageDescription, Iptc.Application2.Caption and
Xmp.dc.description will all be set to the caption.
* Iptc.Application2.Keywords and Xmp.dc.subject will set to the list of
keywords.
* Iptc.Application2.DateCreated will be set to the photo creation date (YYYY-MM-DD)
* Iptc.Application2.TimeCreated will be set to the photo creation time (HH:MM:SS)


In the above, where multiple tags are being set the same, the default value
is determined when the file is loaded by reading the keys from the file
in the given order.  The fist valid entry will be the default (the remaining
will be available in the combobox pulldown).  

For the date variables, if no valid one is found the current date will be used.
For the others, if no valid entry is found they will be set to "N/A"

If the Commit and Revert buttons are enabled when a file is initially loaded
it means that some of the required variables were not set or not equal.

The following metadata will be removed from the image:

* Xmp.exif.DateTimeOriginal
* Xmp.dc.date
* Xmp.acdsee.caption
* Exif.Photo.UserComment

Note, valid date strings are:

* YYYY-MM-DD HH:MM:SS
* YYYY-MM-DDTHH:MM:SS
* YYYY:MM:DD HH:MM:SS
* YYYY:MM:DDTHH:MM:SS

