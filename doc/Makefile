all: main.pdf

%.pdf: %.tex 
	${SH} pdflatex $<
	${SH} pgrep evince 2> /dev/null > /dev/null || evince $@ & > /dev/null 2> /dev/null


clean:
	${RM} *.aux *.log *.pdf *.out
