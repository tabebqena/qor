import logging
import os
import signal
import subprocess
import sys
import time
import traceback

import click

from qor.watcher import Watcher

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass


DEFAULT_IGNORE_REJEXES = [".*\.venv.*", ".*venv.*", ".*env.*", ".*\.env.*", ".*\.pyc"]


def find_app():
    app = os.environ.get("KORE_APP", None)
    if not app:
        app = os.path.join(os.getcwd(), "app.py")
    return app


@click.group(name="qor")
def qor():
    """qor cli"""


@qor.command(name="run", help="run `qor` app. `qor run --app <PATH>`")
@click.option(
    "-a",
    "--app",
    default=None,
    help="app path. if omitted, the `KORE_APP` env variable will be used. if not set, The file named `app.py` in the current working dir will be used.",
)
@click.option(
    "-w", "--watch", default=True, help="Whether to watch the files changes or not."
)
def run(app, watch):
    if not app:
        app = find_app()

    if not app:
        click.secho(
            "can't find app, please set `KORE_APP` env variable or "
            "pass its path on the cmd:. `qor run src/app.py` "
            "if you did that, ensure that path exists.",
            err=True,
            fg="red"
        )
        return
    app = os.path.abspath(app)

    if not os.path.exists(app):
        click.secho(message=f"app not found, {app},", err=True, fg="red")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    if watch:
        watch_path = os.path.dirname(app)
        o = Watcher(
            path=watch_path,
            command=["kore", app],
            regexes=[".*.py"],
            ignore_regexes=DEFAULT_IGNORE_REJEXES,
            logger=logger,
            shell=False,
        )
        logging.getLogger("watchdog.observers.inotify_buffer").setLevel(logging.ERROR)

        try:
            o.run()
        except KeyboardInterrupt as e:
            o.stop()
            traceback.print_exception(KeyboardInterrupt, e, e.__traceback__)
        except Exception as e:
            traceback.print_exception(KeyboardInterrupt, e, e.__traceback__)
            o.stop()
        return
    else:
        process = subprocess.Popen(
            ["kore", app], shell=False, stdout=sys.stdout, stderr=sys.stderr
        )
        while True:
            try:
                time.sleep(2)
                if process.poll():
                    process.send_signal(signal.Signals.SIGTERM)
                    break

            except RuntimeError:
                process.kill()
        click.secho(
            f"Stopped by code: {str(process.poll())}", fg="yellow"
        )


@qor.command(name="routes", help="print registered routes for the ``Qor` app. ")
@click.option(
    "-a",
    "--app",
    default=None,
    help="app path. if omitted, the `KORE_APP` env variable will be used. if not set, The file named `app.py` in the current working dir will be used.",
)
def routes(app):
    if not app:
        app = find_app()
    if not app:
        click.secho(
            "can't find app, please set `KORE_APP` env variable or"
            "pass its path on the cmd:. `qor run src/app.py` "
            "if you did that, ensure that path exists."
            ,err=True, fg="red"
        )

    watch_path = os.path.dirname(app)
    if app:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())
        o = Watcher(
            path=watch_path,
            command=["kore", app, "print-routes-exit"],
            regexes=[".*\.py$"],
            logger=logger,
            shell=False,
        )

        try:
            o.run()

        except KeyboardInterrupt as e:
            o.stop()
            traceback.print_exception(KeyboardInterrupt, e, e.__traceback__)
        except Exception as e:
            traceback.print_exception(KeyboardInterrupt, e, e.__traceback__)
            o.stop()


if __name__ == "__main__":
    qor()
