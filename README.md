eogMetaEdit
===========

Metadata Editor plugin for Eye of Gnome.

Developed on Ubuntu 12.04 with EoG 3.4.   This plugin allows you to  modify various
Title, Date, Caption and Keyword image metadata for Zenfolio and Darktable compatibility.

The eogMetaEdit form modifies the following metadata:

<table>
	<tr>
		<td>Title</td><td>Exif.Application2.Headline, Exif.Image.ImageDescription, 
		Xmp.dc.title NOTE: The title will be prefixed by Iptc.Application2.DateCreated 
		to allow for sorting on Zenfolio of images with dates prior to 1914.</td>
	</tr>
	<tr>
		<td>Date</td><td>Exif.Photo.DateTimeOriginal, Exif.Image.DateTimeOriginal, 
		Exif.Photo.DateTimeDigitized, Exif.Image.DateTime, Iptc.Application2.DateCreated, 
		Iptc.Application2.TimeCreated</td>
	</tr>
	<tr>
		<td>Caption</td><td>Exif.Photo.UserComment,	Iptc.Application2.Caption, 
		Xmp.dc.description</td>
	</tr>
	<tr>
		<td>Keywords</td><td>Iptc.Application2.Keywords, Xmp.dc.subject</td>
	</tr>
</table>

For the above, the tags will be read from the file in the order given and the first
valid, non null, entry will be used as the default (i.e. displayed in the form field).
Any other valid entries will be available for selection in the pull-down.

If any changes are made the following will also be modified automatically:

<table>
	<tr>
		<td>Make</td><td>Exif.Image.Make will be set to "eogMetaEdit" if it is not already set</td>
	</tr>
	<tr>
		<td>Model</td><td>Exif.Image.Model will be set to "eogMetaEdit vX.X" if it is not already set</td>
	</tr>
	<tr>
		<td>Removed</td><td>Xmp.exif.DateTimeOriginal, Xmp.dc.date, Xmp.acdsee.caption</td>
	</tr>
</table>


If "Set default values?" is checked, then when an image is loaded default values will be set
if required, and the image will be marked as modified (Revert and Commit enabled) if any changes
are required to make it Zenfolio/Darktable compatible.

If "Set default values?" is not checked, no checks are done on the existing metadata on load.  The
image will only be marked as modified if the user modifies one of Title, Date, Caption or Keyword.


Note, valid date strings are:

* YYYY-MM-DD HH:MM:SS
* YYYY-MM-DDTHH:MM:SS
* YYYY:MM:DD HH:MM:SS
* YYYY:MM:DDTHH:MM:SS

