from app import create_app, db, cli, apsched
from app.models import (User, Transaction, Car, Race, Track, OwnedCar, Notification,
        Message, LapTime, Achievement, AchievementCondition, RacePerformance,
        completed_achievements, player_achievements, CalendarEvent)
from app.main.utils import background_jobs
import os

app = create_app()
cli.register(app)

@app.before_first_request
def start_tasks():
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
                apsched.add_job(func=background_jobs, args=[app], trigger='interval',seconds=60, id="do_job_1")

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Transaction': Transaction, 'Car': Car,
            'Race': Race, 'Track': Track, 'OwnedCar': OwnedCar, 'Notification': Notification,
            'Message': Message, 'LapTime': LapTime, 'Achievement': Achievement,
            'AchievementCondition': AchievementCondition, 'RacePerformance': RacePerformance,
            'completed_achievements': completed_achievements, 'player_achievements': player_achievements}
