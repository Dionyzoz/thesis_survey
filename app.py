from flask import Flask, redirect, render_template, request, session
import sqlite3
import logging

from data_store import (
    get_unique_key,
    handle_control_or_treamtent,
    post_allocation,
    randomize_study,
)

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import geocoder
from telegram import SendMessage

app = Flask(__name__)
app.secret_key = "3ajifs1-_asf"
respondents = sqlite3.connect("respondents.db")

# Create a logger
logger = app.logger
logger.setLevel(logging.INFO)

app.logger.propagate = False


# Initialize Flask-Limiter on the app
limiter = Limiter(
    get_remote_address,  # Function to get the client's IP address
    app=app,  # Attach Limiter to the Flask app
    default_limits=["1000 per hour"],  # Set global limits
)


@app.route("/")
def hello():
    if session.get("flow") == 4:
        return redirect("/complete")

    if session.get("flow"):
        return "<h3>You may have refreshed the survey on accident, thanks for trying the survey!</h3>"

    return render_template("index.html")


@app.route("/page_two", methods=["POST", "GET"])
def second_page():
    if not session.get("flow"):
        respondent = randomize_study(request)

        session["flow"] = 1

        session["respondent_id"] = respondent["respondent_id"]
        session["study"] = respondent["study"]

        logger.info("A new respondent has been created")

        # Implement random logic, to show either manipulation or control
    else:
        return redirect("/")

    if respondent["study"] == 1:
        return render_template("study1.html")

    else:
        return render_template("study2.html", bottom=respondent["bottom"])


@app.route("/page_three", methods=["POST", "GET"])
def time_game_allocation():
    if session["flow"] == 1:
        print(session["respondent_id"])
        handle_control_or_treamtent(session["study"], session["respondent_id"], request.form)
        session["flow"] = 2

    else:
        return redirect("/")

    # Show time dictator game rules, explain that previous participant will allocate time and they must now allocate time
    return render_template("tdg_rules.html")


@app.route("/page_four", methods=["POST"])
def time_game():
    if session["flow"] != 2:
        return redirect("/")

    session["flow"] = 3
    allocated_to = post_allocation(
        session["study"], session["respondent_id"], int(request.form["percentage"])
    )

    return render_template("tdg.html", initial_time=allocated_to)


@app.route("/complete")
def game():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.headers.get("X-Real-IP", request.remote_addr)

    if session["flow"] not in (3, 4):
        return redirect("/")

    if session["flow"] == 3:
        try:
            g = geocoder.ip(ip)
            logger.info(
                f"{session['respondent_id']} in {g.city} ({ip}) finished the survey for study {session['study']}!"
            )
            SendMessage(
                f"{session['respondent_id']} in {g.city} ({ip}) finished the survey for study {session['study']}!"
            )

        except Exception:
            logger.info(f"Failed to get city for {ip}")
            logger.info(
                f"{session['respondent_id']} ({ip}) finished the survey for study {session['study']}!"
            )
            SendMessage(
                f"{session['respondent_id']}  ({ip}) finished the survey for study {session['study']}!"
            )

    session["flow"] = 4
    unique_key = get_unique_key(session["study"], session["respondent_id"])
    return render_template("completed.html", unique_key=unique_key)


@app.errorhandler(500)
def internal_error(error):
    logger.error(
        "Server Error: %s", (error), exc_info=True
    )  # Log the exception with traceback
    SendMessage(f"Server Error: {error}")
    return "Internal server error occurred", 500


@app.errorhandler(400)
def internal_error2(error):
    logger.error(
        "Server Error: %s", (error), exc_info=True
    )  # Log the exception with traceback
    SendMessage(f"Server Error: {error}")
    return "Internal server error occurred", 500


# @app.errorhandler(Exception)
# def unhandled_exception(e):
#     logger.critical(
#         "Unhandled Exception: %s", (e), exc_info=True
#     )  # Log the unhandled exception with traceback

#     SendMessage(f"Unhandled Exception: {e}")
#     return "Unhandled exception occurred", 500
