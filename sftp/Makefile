SOURCES += modules/ecdsa
SOURCES += modules/paramiko
SOURCES += icon.png
SOURCES += main.py
SOURCES += metadata.xml
SOURCES += settings.ui

SHORTNAME = sftp
ZIP = current.zip

all: $(ZIP)

$(ZIP): $(SOURCES)
	zip -r $@ $^

test:
	@echo "Testing version num of '$(SHORTNAME)':"
	VERSION=$(shell xmllint --xpath '//metadata/version/text()' metadata.xml)
	LIST_VERSION=$(shell xmllint --xpath 'plugins//plugin[shortname="$(SHORTNAME)"]/version/text()' ../plugin-list.xml)
ifneq "$(VERSION)" "$(LIST_VERSION)"
	exit 1
else
	@echo "Test passed!"
endif