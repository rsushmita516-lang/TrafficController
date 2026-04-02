# Automated Aircraft Landing Decision System

This project is now a beginner-friendly Flask web application with an HTML and CSS interface.

The app lets you:

- Enter pilot flight details such as flight number, airline, aircraft type, schedule, route, and gate.
- Enter environment and aircraft safety conditions.
- Simulate random conditions for training.
- Evaluate whether the aircraft should land, hold, divert, or request emergency landing priority.
- View reasons and a safety score in a cleaner dashboard.

## Project Files

- `main.py`: Flask backend and landing decision logic.
- `templates/index.html`: Main HTML interface.
- `static/styles.css`: CSS styling for the interface.
- `requirements.txt`: Python dependencies.

## Requirements

- Python 3.x
- Flask

## Setup and Run

1. Open the folder in VS Code.
2. Activate your virtual environment:

```powershell
& .\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Start the web app:

```powershell
python main.py
```

5. Open your browser at:

http://127.0.0.1:5000

## Beginner-Friendly Architecture

The app is split into clear layers:

1. Backend logic in `main.py`.
2. UI layout in `templates/index.html`.
3. Styling in `static/styles.css`.

This separation makes it easier to edit one part without breaking the others.

## How the Decision Logic Works

The app starts from a safety score of 100 and subtracts points for risk factors:

- High wind or crosswind
- Low visibility
- Wet, snowy, or icy runway
- Storm nearby
- Low fuel
- Landing gear/hydraulic/autopilot status

Then it maps the score and critical failures to one decision:

- Clear to Land
- Land with Caution
- Hold Pattern
- Divert Immediately
- Emergency Landing Priority