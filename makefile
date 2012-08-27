

DEST=~/.config/eog/plugins

all: ${DEST}/eogMetaEdit.py ${DEST}/eogMetaEdit.plugin ${DEST}/eogMetaEdit/eogMetaEdit.glade

${DEST}/eogMetaEdit.py: eogMetaEdit.py
	install eogMetaEdit.py ${DEST}
	epydoc --html -v eogMetaEdit.py -o docs

${DEST}/eogMetaEdit.plugin: eogMetaEdit.plugin
	install eogMetaEdit.plugin ${DEST}

${DEST}/eogMetaEdit/eogMetaEdit.glade: eogMetaEdit.glade
	install -d ${DEST}/eogMetaEdit
	install eogMetaEdit.glade ${DEST}/eogMetaEdit
