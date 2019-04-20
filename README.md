# Waybar NetInfo

Simple network information utility for Waybar.

### Before you ask

I wrote it in Python, then I decided it was a good idea to Cythonize it and build it as a native executable.

It's not a super-bad idea considering that it's constantly running as you use your computer, possibly draining your battery.

However, you should know that was *not* the reason I decided to do so. The *real* reason is that I couldn't find an easy way to use `pgrep` to find a pure-python script and send `SIGUSR1` to it. I found it way easier to just make it native.

Go ahead and beat me up later :kiss:

# How to use

The widget displays:

#### In the toolbar:
- Your gateway's IP address and netmask, together with the curresponding interface name
  - If the IP address starts with `192.168`, that part is removed
  - If you're connected to an interface whose name starts with `wg`, WireGuard is assumed and a nice lock emoji is added
- Alternatively, the default NetworkManager connection

You can toggle between the two by sending it `SIGUSR1`.

#### In the tooltip

- The gateway interface's IP addresses
- All active NetworkManager connections

## Sample Waybar config

```json
"custom/netinfo": {
    "format": "{}",
    "return-type": "json",
    "exec": "waybar_netinfo",
    "on-click": "killall -USR1 waybar_netinfo"
}
```

# How to build

Note: you don't have to build it, you can just run it with Python

Dependencies:

```
pydbus
pyroute2
```

If you want to build a native executable you also need

```
cython
python3-dev # or whatever your distro calls Python development headers
```

You may need to edit the `Makefile` and fix Python's include directory.

Then

```
make
```
