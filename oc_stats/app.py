from flask import Flask, render_template

from oc_stats.context import BaseContextBuilder
from oc_stats.jinja_env import setup_jinja_env
from oc_stats.repo import ContextBuilderRepository

app = Flask(__name__)
setup_jinja_env(app.jinja_env)

context_builders = [cls() for cls in BaseContextBuilder.__subclasses__()]


@app.route("/")
@app.route("/index.html")
def app_home() -> str:
    repo = ContextBuilderRepository()
    repo.load_data()
    context = repo.build_context()
    return render_template("home.html", **context)
