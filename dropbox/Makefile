SOURCES += modules/dropbox
SOURCES += modules/urllib3
SOURCES += modules/pkg_resources.py
SOURCES += icon.png
SOURCES += main.py
SOURCES += metadata.xml
SOURCES += settings.ui

ZIP = current.zip

all: $(ZIP)

$(ZIP): $(SOURCES)
	zip -r $@ $^
