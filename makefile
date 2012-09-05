
# the default operation for this makefile is to copy the eogMetaEdit plugin to the
# users personal plugin directory:  ~/.config/eog/plugins (for Ubuntu 12.04)

DEST=~/.config/eog/plugins

install: ${DEST}/eogMetaEdit.py ${DEST}/eogMetaEdit.plugin ${DEST}/eogMetaEdit/eogMetaEdit.glade

${DEST}/eogMetaEdit.py: eogMetaEdit.py
	install eogMetaEdit.py ${DEST}

${DEST}/eogMetaEdit.plugin: eogMetaEdit.plugin
	install eogMetaEdit.plugin ${DEST}

${DEST}/eogMetaEdit/eogMetaEdit.glade: eogMetaEdit.glade
	install -d ${DEST}/eogMetaEdit
	install eogMetaEdit.glade ${DEST}/eogMetaEdit
