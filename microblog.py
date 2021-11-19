from app import create_app, db, cli
from app.models import (User, Transaction, Car, Race, Track, OwnedCar, Notification,
        Message, LapTime, Achievement, AchievementCondition, RacePerformance,
        completed_achievements, player_achievements)

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Transaction': Transaction, 'Car': Car,
            'Race': Race, 'Track': Track, 'OwnedCar': OwnedCar, 'Notification': Notification,
            'Message': Message, 'LapTime': LapTime, 'Achievement': Achievement,
            'AchievementCondition': AchievementCondition, 'RacePerformance': RacePerformance,
            'completed_achievements': completed_achievements, 'player_achievements': player_achievements}
