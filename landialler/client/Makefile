# $Id$

VERS = 0.1
SRC = AUTHORS COPYING INSTALL MANIFEST README TODO \
      landialler.conf landialler.py

all: tardist zip

tardist:
	@echo "### Building landialler-$(VERS).tar.gz"
	@ls $(SRC) | sed s:^:landialler-$(VERS)/: >MANIFEST
	@(cd ..; ln -s client landialler-$(VERS))
	(cd ..; tar -czvf landialler-$(VERS).tar.gz `cat client/MANIFEST`)
	@(cd ..; rm landialler-$(VERS))

zip:
	@echo "### Building landialler-$(VERS).zip"
	@ls $(SRC) | sed s:^:landialler-$(VERS)/: >MANIFEST
	@(cd ..; ln -s client landialler-$(VERS))
	(cd ..; zip -r -9 landialler-$(VERS).zip `cat client/MANIFEST`)
	@(cd ..; rm landialler-$(VERS))
