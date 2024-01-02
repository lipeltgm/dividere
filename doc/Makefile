all: main.pdf

doc/ref.txt:
	#--remove FILE section to avoid exporting build filesystem info
	${SH} cd ..;python3 -m pydoc dividere/connection.py | sed -n '/*/,/^FILE/p' > $@
	${SH} cd ..;python3 -m pydoc dividere/messaging.py  | sed -n '/*/,/^FILE/p' >> $@
	${SH} cd ..;python3 -m pydoc dividere/registry.py  | sed -n '/*/,/^FILE/p' >> $@
	${SH} cd ..;python3 -m pydoc dividere/service.py  | sed -n '/*/,/^FILE/p' >> $@

%.pdf: %.tex doc/ref.txt
	${SH} pdflatex $<
	${SH} cp $@ ../
	${SH} pgrep evince 2> /dev/null > /dev/null || evince $@ & > /dev/null 2> /dev/null


clean:
	${RM} *.aux *.log *.pdf *.out ref.txt
