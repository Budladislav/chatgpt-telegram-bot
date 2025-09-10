import os, time, random, asyncio
from apscheduler.schedulers.background import BackgroundScheduler
import memory

QUIET_HOURS = os.getenv("QUIET_HOURS", "22-09")
MIN_INTERVAL_H = int(os.getenv("INITIATIVE_MIN_INTERVAL_H", "8"))

def _quiet_now():
    s, e = [int(x) for x in QUIET_HOURS.split("-")]
    h = time.localtime().tm_hour
    return (s <= h < e) if s <= e else (h >= s or h < e)

def start_scheduler(bot_send_fn):
    sched = BackgroundScheduler(timezone="Europe/Vienna")
    sched.add_job(lambda: _tick(bot_send_fn), "cron", minute=15)
    sched.start()
    return sched

def _tick(bot_send_fn):
    if _quiet_now(): return
    with memory._conn() as c:
        users = [r[0] for r in c.execute("SELECT DISTINCT user_id FROM messages").fetchall()]
    for uid in users:
        row = None
        with memory._conn() as c:
            row = c.execute("SELECT ts FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
        last_ts = row[0] if row else 0
        if int(time.time()) - last_ts < MIN_INTERVAL_H*3600: 
            continue
        text = random.choice([
            "Как ты сейчас? Было что-то приятное сегодня?",
            "Нужна поддержка в чём-то конкретном?",
            "Продвинулся по тренировкам или проекту?"
        ])
        asyncio.get_event_loop().create_task(bot_send_fn(uid, text))
