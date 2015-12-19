SUBDIRS = dropbox file ftp imgur sftp shell

all: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@

.PHONY: $(SUBDIRS)