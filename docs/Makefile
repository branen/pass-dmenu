#!/usr/bin/make -f

reqs=filter.py build

.PHONY: all
all: build/man1/pass-dmenu.1 build/html/pass-dmenu.html

build:
	mkdir -p build/man1 build/html

build/man1/pass-dmenu.1: MANUAL.md $(reqs)
	# Pandoc wants every chunk of text to be wrapped in a paragraph, but
	# this is not idiomatic in the NAME section of a manpage and may confuse
	# indexers (e.g. dwww-index++), so we strip out the first ".PP" after
	# ".SH NAME"
	pandoc -f markdown -t man --filter panflute -s $< |\
	  awk '/^\.SH NAME$$/{x=1}(x==1&&/^\.PP$$/){x=0; next}{print}' > $@

build/html/pass-dmenu.html: MANUAL.md pass-dmenu.css $(reqs)
	cp pass-dmenu.css build/html
	pandoc -f markdown -t html5 -c pass-dmenu.css --filter panflute -s -o $@ $<

.PHONY: clean
clean:
	rm -rf build __pycache__
