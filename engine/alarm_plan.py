"""The timetable GitHub's own scheduler is supposed to follow, used by .github/workflows/alarm.yml.

GitHub stopped firing scheduled runs for this repo after Sat 21 Nov 2026 10:00 UTC (a known platform problem), so the
Monday 23 Nov morning call never ran. The alarm workflow is a chain: each run looks up the next job here, sleeps until
it (at most ~5h45m per run), starts it with workflow_dispatch, then starts the next alarm run. Stateless: every run
works the timetable out again from the clock.

Prints: <seconds to wait> <workflow file or "-">.
"""
import datetime as dt, sys

# (weekdays Mon=0..Sun=6, UTC hh:mm, workflow)
TABLE = [((0, 1, 2, 3, 4), '04:55', 'desk.yml'), ((0, 1, 2, 3, 4), '10:25', 'desk.yml'), ((0, 1, 2, 3, 4), '15:25', 'desk.yml'),
         ((0, 1, 2, 3, 4), '22:20', 'live.yml'), ((0, 1, 2, 3, 4), '22:35', 'argon.yml'), ((1, 2, 3, 4, 5), '02:35', 'live.yml')]
HOP = 345 * 60


def next_job(now):
    best = None
    for k in range(0, 8):
        day = (now + dt.timedelta(days=k)).date()
        for wds, hm, wf in TABLE:
            if day.weekday() not in wds: continue
            t = dt.datetime.combine(day, dt.time.fromisoformat(hm), dt.timezone.utc)
            if t > now and (best is None or t < best[0]): best = (t, wf)
    return best


if __name__ == '__main__':
    now = dt.datetime.now(dt.timezone.utc)
    t, wf = next_job(now)
    wait = (t - now).total_seconds()
    print(int(wait), wf) if wait <= HOP else print(HOP, '-')
