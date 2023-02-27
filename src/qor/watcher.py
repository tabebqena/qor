import logging
import signal
import subprocess
import sys
import time

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer


class Reloader(RegexMatchingEventHandler):
    def __init__(
        self,
        callback,
        patterns=None,
        ignore_patterns=None,
        ignore_directories=False,
        case_sensitive=False,
    ):
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.callback = callback
        self.active = True

    def on_any_event(self, event):
        # if self.is_match(event):
        # self.logger.debug(f"changes detected in {event.src_path} .")
        if event.is_directory:
            return
        if self.active:
            self.active = False
            self.callback()


class LoggerHandler(RegexMatchingEventHandler):
    def __init__(
        self,
        logger,
        patterns=None,
        ignore_patterns=None,
        ignore_directories=False,
        case_sensitive=False,
    ):
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.logger = logger

    def on_any_event(self, event):
        # what = "directory" if event.is_directory else "file"
        if not event.is_directory :
            self.logger.info("Changes %s: %s", event.src_path)


class Watcher:
    """
    run bash script, reload it when file changes
    """

    WAIT_PERIOD = 5

    def __init__(
        self,
        path,
        patterns=[".*.py"],
        command="echo 'No command specified'",
        shell=False,
        logger: logging.Logger = None,
    ) -> None:
        self.path = path
        self.command = command
        self.shell = shell
        self.logger = logger
        self.extensions = patterns
        self.reloader = Reloader(self.reload, patterns, ignore_directories=True)
        self.logger_handler = LoggerHandler(self.logger, self.extensions)
        self._reloading = False

    def log(self, message, level=logging.DEBUG):
        if self.logger:
            self.logger.log(level, message)

    def run(self):
        if not self.shell and not isinstance(self.command, list):
            raise Exception(
                "You should provide command as a list ex:. ['ls', '-a'] when the shell is False"
            )
        self.process = subprocess.Popen(
            self.command, shell=self.shell, stdout=sys.stdout, stderr=sys.stderr
        )
        self._reloading = False
        self.watch()

    def stop(self):
        self.logger.debug("stop ...")
        try:
            self.process.send_signal(signal.Signals.SIGTERM)
        except Exception as e:
            if self.logger:
                self.logger.error(e)
            else:
                self.log(e, logging.ERROR)
            raise

    def reload(self):
        time.sleep(0.5)
        self._reloading = True
        print("reload ...")
        self.stop()
        elapsed = 0

        while 1:
            if elapsed > self.WAIT_PERIOD:
                break
            if self.process.poll():
                # write message that indicates self.logger.error(f"Process is still running, time elapsed.")
                print(".", end=" ")
                time.sleep(1)
                elapsed += 1
                continue
            else:
                self.reloader.active = True
                self.run()
        self.log(f"You should kill the process manually. ", logging.ERROR)

    def should_close(self):
        return False

    def watch(self):
        self.observer = Observer()
        self.observer.schedule(self.logger_handler, self.path, recursive=True)
        self.observer.schedule(self.reloader, self.path, recursive=True)
        self.observer.start()
        logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.ERROR)
        try:
            while True:
                rv = self.process.poll()
                if rv is None:
                    time.sleep(1)
                    if self.should_close():
                        break
                if not self._reloading:
                    if rv == 0:
                        print("process closed successfully")
                        break
                    elif rv == 1:
                        print("process closed with error code:", rv)
                        break
        except KeyboardInterrupt as e:
            try:
                self.stop()
            except:
                pass
        finally:
            self.observer.stop()
            self.observer.join()
