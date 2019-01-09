DESTDIR=~/.local/bin

.PHONY: install

install:
	install -m755 scanbro.py ${DESTDIR}/scanbro
