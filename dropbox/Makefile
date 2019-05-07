SOURCES += modules/dropbox
SOURCES += modules/urllib3
SOURCES += modules/requests
SOURCES += modules/pkg_resources
SOURCES += modules/certifi
SOURCES += modules/chardet
SOURCES += modules/idna
SOURCES += modules/packaging
SOURCES += modules/appdirs.py
SOURCES += modules/pyparsing.py
SOURCES += modules/six.py


SOURCES += icon.png
SOURCES += main.py
SOURCES += metadata.xml
SOURCES += settings.ui

ZIP = current.zip

all: $(ZIP)

$(ZIP): $(SOURCES)
	zip -r $@ $^
