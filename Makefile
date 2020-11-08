DESTDIR=~/.local/bin

.PHONY: install

install:
	[[ -d ${DESTDIR} ]] || mkdir -p ${DESTDIR}
	install -m755 scanbro.py ${DESTDIR}/scanbro
	test -d ~/.zdir && install -m644 aliases.sh ~/.zdir/70-scanbro.zsh || true
