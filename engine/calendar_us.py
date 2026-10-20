"""Scheduled events Argon steps aside for. Fed rate decisions are released at 2:00pm New York time on the second day of
each meeting. Source: federalreserve.gov/monetarypolicy/fomccalendars.htm (checked 20 Oct 2026; 2027 dates are
tentative until confirmed at the meeting before). The 8:30am data releases (CPI, jobs, claims...) are handled by a
simple daily rule instead of a calendar: no new trades 8:25-8:40 New York on any weekday."""
FOMC_DECISIONS={
 2021:['01-27','03-17','04-28','06-16','07-28','09-22','11-03','12-15'],
 2022:['01-26','03-16','05-04','06-15','07-27','09-21','11-02','12-14'],
 2023:['02-01','03-22','05-03','06-14','07-26','09-20','11-01','12-13'],
 2024:['01-31','03-20','05-01','06-12','07-31','09-18','11-07','12-18'],
 2025:['01-29','03-19','05-07','06-18','07-30','09-17','10-29','12-10'],
 2026:['01-28','03-18','04-29','06-17','07-29','09-16','10-28','12-09'],
 2027:['01-27','03-17','04-28','06-09','07-28','09-15','10-27','12-08'],
}
FOMC=set(f'{y}-{d}' for y,ds in FOMC_DECISIONS.items() for d in ds)
FOMC_EXIT_MIN=13*60+55     # on Fed days, be flat by 1:55pm, before the 2:00pm decision
SOURCE='https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'
