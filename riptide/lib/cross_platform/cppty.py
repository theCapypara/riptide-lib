"""Cross-platform version of pty"""

import platform
from threading import Thread
from typing import TYPE_CHECKING

if platform.system().lower().startswith("win") and not TYPE_CHECKING:
    # windows

    import msvcrt
    import os
    import re
    import sys

    from winpty import PtyProcess

    # TODO CRTL+C

    def spawn(argv, win_repeat_argv0=False, **kwargs):
        # TODO: For whatever reason, Docker needs their name as padding in the arguments again.
        if win_repeat_argv0:
            argv = [argv[0]] + argv
        term_size = os.get_terminal_size()
        process = PtyProcess.spawn(argv, dimensions=(term_size[1], term_size[0] - 2))

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
        t.daemon = True  # thread dies with the program
        t.start()

        ## READ
        try:
            while True:
                # Remove some unprintable escape sequences when using winpty
                # TODO: FAR from perfect yet (what if sequence is on "boundary"?).
                # Source: https://stackoverflow.com/a/14693789
                ansi_escape = re.compile(r"\x1B\[\?25[hl]*[ -/]*[@-~]")
                # TODO: Little bit of a buffering issue here.
                sys.stdout.write(ansi_escape.sub("", process.read(4096)))
        except EOFError:
            pass

        process.close()
        return process.exitstatus()
else:
    # linux and mac
    import contextlib
    import errno
    import fcntl
    import os
    import pty
    import select
    import signal
    import struct
    import sys
    import termios
    import time
    import tty

    def spawn(argv, win_repeat_argv0=False, **kwargs):
        # Fork of pty.spawn to support streams and sginals better (no duplictae output etc.)
        # Does not use pty if the current terminal is not a TTY, instead uses standard os.fork.

        if isinstance(argv, str):
            argv = (argv,)

        is_tty = sys.stdin.isatty()

        def _read(fd):
            return os.read(fd, 1024)

        def _write(fd, data):
            while data != b"" and child_is_running:
                n = os.write(fd, data)
                data = data[n:]

        status = None
        child_is_running = True

        def _handle_chld(signum, frame):
            nonlocal status, child_is_running
            try:
                status = os.waitpid(child_pid, os.P_NOWAIT)[1]
                child_is_running = False
            except ChildProcessError:
                child_is_running = False

        def _handle_winch(signum, frame):
            try:
                tc = struct.pack("HHHH", 0, 0, 0, 0)
                tc = fcntl.ioctl(pty.STDIN_FILENO, termios.TIOCGWINSZ, tc)
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, tc)
            except Exception:
                pass

        def _handle_int(signum, frame):
            os.kill(child_pid, signal.SIGINT)

        # In parts taken from pexpect (ISC LICENSE, see https://github.com/pexpect/pexpect/blob/master/LICENSE)
        def _copy():
            while child_is_running:
                r, w, e = select_ignore_interrupts([master_fd, pty.STDIN_FILENO], [], [])
                if master_fd in r:
                    try:
                        data = _read(master_fd)
                    except OSError as err:
                        if err.args[0] == errno.EIO:
                            # Linux-style EOF
                            break
                        raise
                    if data == b"":
                        # BSD-style EOF
                        break
                    os.write(pty.STDOUT_FILENO, data)
                if pty.STDIN_FILENO in r:
                    data = _read(pty.STDIN_FILENO)
                    _write(master_fd, data)

        with contextlib.ExitStack() as stack:
            sys.stdout.flush()
            sys.stderr.flush()
            if is_tty:
                try:
                    mode = termios.tcgetattr(pty.STDIN_FILENO)
                    stack.callback(termios.tcsetattr, pty.STDIN_FILENO, termios.TCSANOW, mode)
                    tty.setraw(pty.STDIN_FILENO)
                except termios.error:
                    pass  # probably not supported

                child_pid, master_fd = pty.fork()
            else:
                child_pid = os.fork()
            if child_pid == pty.CHILD:
                os.execlp(argv[0], *argv)

            handler = signal.signal(signal.SIGINT, _handle_int)
            stack.callback(signal.signal, signal.SIGINT, handler)

            if is_tty:
                stack.callback(os.close, master_fd)

                handler = signal.signal(signal.SIGCHLD, _handle_chld)
                stack.callback(signal.signal, signal.SIGCHLD, handler)
                handler = signal.signal(signal.SIGWINCH, _handle_winch)
                stack.callback(signal.signal, signal.SIGWINCH, handler)
                _handle_winch(0, None)

                _copy()

            if status is None:
                return os.waitpid(child_pid, 0)[1] >> 8

            return status >> 8

    # from pexpect, license info see above;
    # see https://github.com/pexpect/pexpect/blob/fc8f062518b40bd0862aae870cdedf5d9c0c7fc3/pexpect/utils.py#L130
    def select_ignore_interrupts(iwtd, owtd, ewtd, timeout=None):
        """This is a wrapper around select.select() that ignores signals. If
        select.select raises a select.error exception and errno is an EINTR
        error then it is ignored. Mainly this is used to ignore sigwinch
        (terminal resize)."""

        # if select() is interrupted by a signal (errno==EINTR) then
        # we loop back and enter the select() again.
        if timeout is not None:
            end_time = time.time() + timeout
        while True:
            try:
                return select.select(iwtd, owtd, ewtd, timeout)
            except InterruptedError:
                err = sys.exc_info()[1]
                if err.args[0] == errno.EINTR:  # type: ignore
                    # if we loop back we have to subtract the
                    # amount of time we already waited.
                    if timeout is not None:
                        timeout = end_time - time.time()
                        if timeout < 0:
                            return ([], [], [])
                else:
                    # something else caused the select.error, so
                    # this actually is an exception.
                    raise
