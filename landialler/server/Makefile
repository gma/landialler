# $Id$

DESTDIR = 
BIN = $(DESTDIR)/usr/local/sbin
ETC = $(DESTDIR)/usr/local/etc
INSTALL = /usr/bin/install -c

install:
	@echo "### Installing ..."
	$(INSTALL) -d $(BIN)
	$(INSTALL) -m755 ./landiallerd.py $(BIN)
	$(INSTALL) -d $(ETC)
	$(INSTALL) -m644 ./landiallerd.conf $(ETC)

uninstall:
	@echo "### Uninstalling ..."
	rm -rf $(BIN)/landiallerd.py
	rm -rf $(MAN)/landiallerd.conf
