.PHONY: all reload clean

all: clean reload

clean:
	find . -iname \*.pyc -delete

reload:
	find apache -iname \*.wsgi -exec touch {} \;
