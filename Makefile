SUBDIRS = dropbox ftp imgur sftp shell

all: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@

.PHONY: $(SUBDIRS)

test:
	for dir in $(SUBDIRS); do \
        ./.travis-version-test.sh $$dir || exit; \
    done