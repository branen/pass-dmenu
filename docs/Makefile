#!/usr/bin/make -f

reqs=filter.py build

.PHONY: all
all: build/man1/pass-dmenu.1 build/html/pass-dmenu.html

build:
	mkdir -p build/man1 build/html

build/man1/pass-dmenu.1: MANUAL.md $(reqs)
	pandoc -f markdown -t man --filter panflute -s -o $@ $<

build/html/pass-dmenu.html: MANUAL.md pass-dmenu.css $(reqs)
	cp pass-dmenu.css build/html
	pandoc -f markdown -t html5 -c pass-dmenu.css --filter panflute -s -o $@ $<

.PHONY: clean
clean:
	rm -rf build __pycache__
