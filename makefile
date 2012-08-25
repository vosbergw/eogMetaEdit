

DEST=~/.config/eog/plugins
all: ${DEST}/eogMetaEdit.py ${DEST}/eogMetaEdit.plugin ${DEST}/eogMetaEdit/eogMetaEdit.glade

${DEST}/eogMetaEdit.py:
	install eogMetaEdit.py ${DEST}

${DEST}/eogMetaEdit.plugin:
	install eogMetaEdit.plugin ${DEST}

${DEST}/eogMetaEdit/eogMetaEdit.glade:
	install eogMetaEdit.glade ${DEST}/eogMetaEdit
