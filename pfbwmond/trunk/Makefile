PARTS = pfbwmond.o

CFLAGS = -g3

all:	pfbwmond

pfbwmond:	$(PARTS)
		$(CC) $(CFLAGS) $(PARTS) -o pfbwmond

pfbwmond.o:	pfbwmond.h

clean:
	rm -f *.o *.core pfbwmond
