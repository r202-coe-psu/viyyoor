import optparse
import pathlib

from flask import Flask

from .. import models
from . import views
from . import acl
from . import caches
from . import oauth2
from . import redis_rq

app = Flask(__name__)


def create_app():
    app.config.from_object("viyyoor.default_settings")
    app.config.from_envvar("VIYYOOR_SETTINGS", silent=True)

    VIYYOOR_CACHE_DIR = app.config.get("VIYYOOR_CACHE_DIR")
    p = pathlib.Path(VIYYOOR_CACHE_DIR)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)

    models.init_db(app)
    views.register_blueprint(app)
    acl.init_acl(app)
    caches.init_cache(app)
    oauth2.init_oauth(app)
    redis_rq.init_rq(app)

    return app


def get_program_options(default_host="127.0.0.1", default_port="8080"):

    """
    Takes a flask.Flask instance and runs it. Parses
    command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option(
        "-H",
        "--host",
        help="Hostname of the Flask app " + "[default %s]" % default_host,
        default=default_host,
    )
    parser.add_option(
        "-P",
        "--port",
        help="Port for the Flask app " + "[default %s]" % default_port,
        default=default_port,
    )

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_option(
        "-c", "--config", dest="config", help=optparse.SUPPRESS_HELP, default=None
    )
    parser.add_option(
        "-d", "--debug", action="store_true", dest="debug", help=optparse.SUPPRESS_HELP
    )
    parser.add_option(
        "-p",
        "--profile",
        action="store_true",
        dest="profile",
        help=optparse.SUPPRESS_HELP,
    )

    options, _ = parser.parse_args()

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if options.profile:
        from werkzeug.middleware.profiler import ProfilerMiddleware

        app.config["PROFILE"] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
        options.debug = True

    return options
