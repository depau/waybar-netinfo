CC = gcc
CFLAGS = -fPIC -I/usr/include/python3.8  -lpython3.8
CYTHON  = cython

all: waybar_netinfo

waybar_netinfo: waybar_netinfo.c
				$(CC) $(CFLAGS) waybar_netinfo.c -o waybar_netinfo

waybar_netinfo.c: waybar_netinfo.py
				$(CYTHON) -v -3 --embed waybar_netinfo.py

clean:
				rm *.c waybar_netinfo
