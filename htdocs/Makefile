# $Id$


REMOTE_HOST=landialler.sourceforge.net
REMOTE_DIR=/home/groups/l/la/landialler/htdocs/new
REMOTE_USER=ashtong


upload: .upload-html .upload-ssi .upload-images .upload-screenshots


.upload-html: *.html .htaccess default.css
	scp $? $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)
	@touch .upload-html


.upload-news: news/*.html
	scp $? $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)
	@touch .upload-news


.upload-ssi: ssi/*.html
	scp $? $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/ssi
	@touch .upload-ssi


.upload-images: images/*.png
	scp $? $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/images
	@touch .upload-images


.upload-screenshots: images/ss/*.png images/ss/*.gif
	scp $? $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_DIR)/images/ss
	@touch .upload-screenshots
