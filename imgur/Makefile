SOURCES += modules/certifi
SOURCES += modules/chardet
SOURCES += modules/idna
SOURCES += modules/pyimgur
SOURCES += modules/requests
SOURCES += modules/urllib3
SOURCES += icon.png
SOURCES += main.py
SOURCES += metadata.xml
SOURCES += settings.ui

ZIP = current.zip

all: $(ZIP)

$(ZIP): $(SOURCES)
	zip -r $@ $^
