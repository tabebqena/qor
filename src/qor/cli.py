import logging
import os
import traceback
import click

from qor.watcher import Watcher

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


def find_app():
    app = os.environ.get("KORE_APP", None)
    if not app:
        app = os.path.join(os.getcwd(), "app.py")
    if app and os.path.exists(app):
        return app
    elif app is None:
        return None
    else:
        click.echo(f"App file not found : {app}")
        return None



@click.group(name="qor")
def qor():
    """qor cli"""

@qor.command(name="run", help="run `qor` app. qor run APP\nApp is the app path. if omitted, the `KORE_APP` env variable will be used. if not set, The file named `app.py` in the current working dir will be used.")
@click.argument("app",default=None, )
def run(app):
    if not app:
        app = find_app()
    if not app:
        click.echo("can't find app, please set `KORE_APP` env variable or" 
                   "pass its path on the cmd:. `qor run src/app.py` "
                   "if you did that, ensure that path exists."
                   )
    watch_path = os.path.dirname(app)
    if app:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())
        o = Watcher(
            path=watch_path,
            command=["kore", app],
            patterns=[".*.py"],
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


@qor.command(name="routes", help="print registered routes for the ``Qor` app. ")
@click.argument("app",default=None, )
def run(app):
    if not app:
        app = find_app()
    if not app:
        click.echo("can't find app, please set `KORE_APP` env variable or" 
                   "pass its path on the cmd:. `qor run src/app.py` "
                   "if you did that, ensure that path exists."
                   )
    
    watch_path = os.path.dirname(app)
    if app:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())
        o = Watcher(
            path=watch_path,
            command=["kore", app, "print-routes-exit"],
            patterns=[".*.py"],
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
