from __future__ import annotations

import random
import socket
from pathlib import Path
from dataclasses import asdict, dataclass

from flask import Flask, render_template, request


@dataclass
class LandingScenario:
    """Stores all values needed to evaluate a landing decision."""

    wind_speed: int
    visibility: float
    fuel_level: int
    runway_condition: str
    crosswind_speed: int
    storm_nearby: bool
    landing_gear_ready: bool
    hydraulic_pressure_ok: bool
    autopilot_ok: bool


@dataclass
class FlightDetails:
    """Stores the basic flight information entered by the pilot."""

    flight_number: str
    airline: str
    aircraft_type: str
    scheduled_time: str
    origin: str
    destination: str
    gate: str


def evaluate_landing(scenario: LandingScenario) -> tuple[str, str, list[str], int]:
    """Return a landing decision, color style, reasons, and safety score."""

    score = 100
    reasons: list[str] = []

    if scenario.wind_speed > 55:
        score -= 30
        reasons.append("Wind speed is extremely high.")
    elif scenario.wind_speed > 35:
        score -= 15
        reasons.append("Wind speed is above the preferred limit.")
    else:
        reasons.append("Wind speed is within a manageable range.")

    if scenario.crosswind_speed > 40:
        score -= 25
        reasons.append("Crosswind is dangerously high for landing.")
    elif scenario.crosswind_speed > 25:
        score -= 10
        reasons.append("Crosswind requires extra caution.")
    else:
        reasons.append("Crosswind is acceptable.")

    if scenario.visibility < 1.5:
        score -= 30
        reasons.append("Visibility is critically low.")
    elif scenario.visibility < 3:
        score -= 15
        reasons.append("Visibility is reduced.")
    else:
        reasons.append("Visibility is suitable for landing.")

    runway_penalty = {
        "Dry": 0,
        "Wet": 10,
        "Snow": 20,
        "Icy": 35,
    }
    score -= runway_penalty[scenario.runway_condition]
    reasons.append(f"Runway condition: {scenario.runway_condition}.")

    if scenario.storm_nearby:
        score -= 20
        reasons.append("Storm activity is present near the airport.")
    else:
        reasons.append("No nearby storm activity detected.")

    if scenario.fuel_level < 15:
        score -= 25
        reasons.append("Fuel level is low and limits holding time.")
    elif scenario.fuel_level < 30:
        score -= 10
        reasons.append("Fuel level is moderate.")
    else:
        reasons.append("Fuel reserve is healthy.")

    if not scenario.landing_gear_ready:
        score -= 40
        reasons.append("Landing gear is not confirmed ready.")
    else:
        reasons.append("Landing gear is confirmed ready.")

    if not scenario.hydraulic_pressure_ok:
        score -= 30
        reasons.append("Hydraulic pressure is not normal.")
    else:
        reasons.append("Hydraulic pressure is normal.")

    if not scenario.autopilot_ok:
        score -= 5
        reasons.append("Autopilot assistance is unavailable.")
    else:
        reasons.append("Autopilot systems are available.")

    critical_failure = (
        not scenario.landing_gear_ready
        or not scenario.hydraulic_pressure_ok
        or (scenario.runway_condition == "Icy" and scenario.visibility < 1.5)
    )

    score = max(0, min(score, 100))

    if critical_failure and scenario.fuel_level >= 15:
        return "Divert Immediately", "status-divert", reasons, score

    if score >= 80:
        return "Clear to Land", "status-clear", reasons, score

    if score >= 60:
        return "Land with Caution", "status-caution", reasons, score

    if scenario.fuel_level < 15:
        reasons.append("Low fuel reduces the ability to wait for better conditions.")
        return "Emergency Landing Priority", "status-emergency", reasons, score

    return "Hold Pattern", "status-hold", reasons, score


def default_form_data() -> dict:
    """Return a default form state for first load and reset."""

    return {
        "flight_number": "AI-204",
        "airline": "AeroLink",
        "aircraft_type": "Airbus A320",
        "scheduled_time": "18:45",
        "origin": "Delhi",
        "destination": "Kolkata",
        "gate": "B12",
        "wind_speed": 20,
        "crosswind_speed": 12,
        "visibility": 6.0,
        "fuel_level": 60,
        "runway_condition": "Dry",
        "storm_nearby": False,
        "landing_gear_ready": True,
        "hydraulic_pressure_ok": True,
        "autopilot_ok": True,
    }


def random_form_data() -> dict:
    """Generate a random scenario and flight details for practice."""

    routes = [
        ("AT-118", "AeroLink", "Boeing 737", "Mumbai", "Kolkata", "A4"),
        ("NX-452", "Nimbus Air", "Airbus A321", "Bengaluru", "Delhi", "C9"),
        ("SR-307", "SkyRoute", "ATR 72", "Hyderabad", "Chennai", "B2"),
        ("VT-990", "VistaJet", "Boeing 787", "Dubai", "Mumbai", "D6"),
    ]
    flight_number, airline, aircraft_type, origin, destination, gate = random.choice(routes)

    return {
        "flight_number": flight_number,
        "airline": airline,
        "aircraft_type": aircraft_type,
        "scheduled_time": f"{random.randint(0, 23):02d}:{random.choice([0, 15, 30, 45]):02d}",
        "origin": origin,
        "destination": destination,
        "gate": gate,
        "wind_speed": random.randint(5, 75),
        "crosswind_speed": random.randint(0, 50),
        "visibility": round(random.uniform(0.5, 10.0), 1),
        "fuel_level": random.randint(5, 100),
        "runway_condition": random.choice(["Dry", "Wet", "Snow", "Icy"]),
        "storm_nearby": random.choice([True, False]),
        "landing_gear_ready": random.choice([True, True, True, False]),
        "hydraulic_pressure_ok": random.choice([True, True, False]),
        "autopilot_ok": random.choice([True, True, True, False]),
    }


def parse_form(form_data) -> dict:
    """Convert posted form values into the app's expected Python types."""

    data = {
        "flight_number": form_data.get("flight_number", "").strip() or "Unknown Flight",
        "airline": form_data.get("airline", "").strip() or "Unknown Airline",
        "aircraft_type": form_data.get("aircraft_type", "").strip() or "Unknown Aircraft",
        "scheduled_time": form_data.get("scheduled_time", "").strip() or "Not Set",
        "origin": form_data.get("origin", "").strip() or "Unknown Origin",
        "destination": form_data.get("destination", "").strip() or "Unknown Destination",
        "gate": form_data.get("gate", "").strip() or "Unassigned",
        "wind_speed": int(form_data.get("wind_speed", 20)),
        "crosswind_speed": int(form_data.get("crosswind_speed", 12)),
        "visibility": float(form_data.get("visibility", 6.0)),
        "fuel_level": int(form_data.get("fuel_level", 60)),
        "runway_condition": form_data.get("runway_condition", "Dry"),
        "storm_nearby": form_data.get("storm_nearby") == "on",
        "landing_gear_ready": form_data.get("landing_gear_ready") == "on",
        "hydraulic_pressure_ok": form_data.get("hydraulic_pressure_ok") == "on",
        "autopilot_ok": form_data.get("autopilot_ok") == "on",
    }
    return data


app = Flask(__name__)


def choose_open_port(start_port: int = 5000, max_checks: int = 20) -> int:
    """Return the first available localhost TCP port from a small range."""

    for port in range(start_port, start_port + max_checks):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def get_styles_version() -> str:
    """Return a cache-busting version based on styles.css modified time."""

    css_file = Path(app.root_path) / "static" / "styles.css"
    if css_file.exists():
        return str(int(css_file.stat().st_mtime))
    return "1"


@app.route("/", methods=["GET", "POST"])
def index():
    """Render page and process Evaluate/Simulate/Reset actions."""

    form = default_form_data()
    result = None

    if request.method == "POST":
        action = request.form.get("action", "evaluate")

        if action == "simulate":
            form = random_form_data()
        elif action == "reset":
            form = default_form_data()
            return render_template(
                "index.html",
                form=form,
                result=None,
                styles_version=get_styles_version(),
            )
        else:
            form = parse_form(request.form)

        flight = FlightDetails(
            flight_number=form["flight_number"],
            airline=form["airline"],
            aircraft_type=form["aircraft_type"],
            scheduled_time=form["scheduled_time"],
            origin=form["origin"],
            destination=form["destination"],
            gate=form["gate"],
        )

        scenario = LandingScenario(
            wind_speed=form["wind_speed"],
            visibility=form["visibility"],
            fuel_level=form["fuel_level"],
            runway_condition=form["runway_condition"],
            crosswind_speed=form["crosswind_speed"],
            storm_nearby=form["storm_nearby"],
            landing_gear_ready=form["landing_gear_ready"],
            hydraulic_pressure_ok=form["hydraulic_pressure_ok"],
            autopilot_ok=form["autopilot_ok"],
        )

        decision, badge_class, reasons, score = evaluate_landing(scenario)

        result = {
            "decision": decision,
            "badge_class": badge_class,
            "score": score,
            "reasons": reasons,
            "flight": asdict(flight),
            "scenario": asdict(scenario),
        }

    return render_template(
        "index.html",
        form=form,
        result=result,
        styles_version=get_styles_version(),
    )


if __name__ == "__main__":
    port = choose_open_port(5000, 20)
    print(f"Starting web server at http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)