"""Cross-platform version of pty"""

import platform
from threading import Thread

if platform.system().lower().startswith('win'):
    # windows

    from winpty import PtyProcess
    import os
    import sys
    import re
    import msvcrt

    # TODO CRTL+C

    def spawn(argv, win_repeat_argv0=False, **kwargs):
        # TODO: For whatever reason, Docker needs their name as padding in the arguments again.
        if win_repeat_argv0:
            argv = [argv[0]] + argv
        term_size = os.get_terminal_size()
        process = PtyProcess.spawn(argv, dimensions=(term_size[1], term_size[0]-2))

        # TODO: Is this even thread-safe?
        # TODO: "pressing up" (...in bash doesn't do what it's supposed to)
        def read():
            try:
                while True:
                    if msvcrt.kbhit():
                        process.write(msvcrt.getwch())
            except EOFError:
                pass

        ## WRITE
        t = Thread(target=read)
        t.daemon = True # thread dies with the program
        t.start()

        ## READ
        try:
            while True:
                # Remove some unprintable escape sequences when using winpty
                # TODO: FAR from perfect yet (what if sequence is on "boundary"?).
                # Source: https://stackoverflow.com/a/14693789
                ansi_escape = re.compile(r'\x1B\[\?25[hl]*[ -/]*[@-~]')
                # TODO: Little bit of a buffering issue here.
                sys.stdout.write(ansi_escape.sub('', process.read(4096)))
        except EOFError:
            pass

        process.close()
else:
    # linux and mac
    import pty

    def spawn(argv, **kwargs):
        return pty.spawn(argv)

#elif platform.system().lower().startswith('lin'):
    # import linux specific modules
#elif platform.system().lower().startswith('dar'):
    # import ...