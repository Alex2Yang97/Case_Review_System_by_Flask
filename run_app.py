from project import create_app
from project.backup import make_backup
from apscheduler.schedulers.background import BackgroundScheduler

# Backup
sched = BackgroundScheduler(daemon=True)
# sched.add_job(make_backup, 'interval', seconds=5)
sched.add_job(make_backup, 'cron', hour=0, minute=10, second=0)

sched.start()

if __name__ == '__main__':
    app = create_app()
    # app.run(host="0.0.0.0", port=1000)
    app.run(debug=True)
    
