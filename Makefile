SUBDIRS = dropbox file ftp imgur sftp shell

all: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@

.PHONY: $(SUBDIRS)

test:
	for dir in $(SUBDIRS); do \
        $(MAKE) test -C $$dir; \
    done