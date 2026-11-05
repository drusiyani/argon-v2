---
type: lessons
written_by: Claude
updated: 2026-11-04
---
# Lessons

What Claude learned from testing on 1508 days of prices (2021-01-04 to 2026-10-30). Rewritten after every test. If you disagree with one, say why in your notes.

1. **A longer test changed the picture.** On the 64 months each version hadn't been tuned on, the old fixed rules lost +20.31R on [[The main strategy]] and -198.40R on [[The order-block strategy]].
2. **Adjusting every month helped, but didn't make it reliable.** Re-picking the best settings each month from the 6 months before cut the main strategy's loss to -13.33R and turned the order-block strategy to -17.87R. But the main strategy's rules changed in 28 of 64 months. When the "best" settings keep changing, that usually means chasing recent luck, not finding something that lasts.
3. **Hindsight is a trap.** The single best version over the whole period made +37.77R on the test months. You can only find it after the fact. Picked month by month, nothing came close.
4. **There's no magic lookback.** Looking back 3, 6, 9 or 12 months gave anything from -50.33R to -50.14R for the main strategy and -39.52R to -19.56R for the order-block one. No setting is reliably good, so we stay with 6 months, which was chosen before testing. Picking the best one now would just be overfitting again.
5. **Where the old rules lost most:** the Russell 2000 (-31.44R over 96 trades) and the London session (-2.14R).
6. **This month's rules (v1.0)** come from the last 6 months. Main strategy: +19.40R over 32 trades. Order-block strategy: +26.32R over 60 trades. Expect them to change again next month.
7. **A clock bug was hiding the result.** The free history is stamped in New York time with daylight saving, but it had been read as winter time, so for about 8 months of every year everything was an hour late: the New York window was really testing 7:30 to 10:30am. Fixed, the main strategy adjusting monthly went from losing to -13.33R over 418 trades on months it wasn't tuned on. That's encouraging, but it's roughly a 1 in 7 chance a strategy with no edge would look this good by luck, so it still needs the unseen 2021 to 2023 futures and the forward test before launch.
8. **Moving the stop to entry once a trade is +1R didn't help** in earlier tests, so it's switched off.
9. **Now trading the same markets as Kronos indices:** the Nasdaq, S&P 500, Dow and Russell 2000. Only the Nasdaq and S&P 500 have years of history for the long test; the Dow and Russell are only judged on the recent futures data until more is saved.
10. **More settings stopped helping; fixing the data did.** Before the clock fix, 24,600 versions couldn't make it profitable. The fix did. Data quality mattered more than any setting.
11. **The best idea came from published research, not from tweaking.** The opening-range breakout from Zarattini and Aziz's paper, with settings re-picked monthly and real trading costs taken off, made +157.90R on the Nasdaq over 64 months it hadn't seen. ICT's Silver Bullet hours made the sweep strategy worse, and the Judas swing looked good but only on 19 trades. On the last 50 days of real futures, the opening range lost money on the Dow and Russell, so it only runs on the Nasdaq and S&P until there's more history.
12. **Learning from mistakes cut the losses but didn't create an edge.** Tagging every losing setup and avoiding the mistakes that kept costing money took "take every setup" from -609.70R to -241.20R on months it hadn't seen. A first version of this looked like +98R, because it used losses that hadn't finished yet. Fixed, it's honest.
13. **Bottom line: no proven edge yet.** The forward test in November, on days nobody has seen, is what decides whether this goes live.

Changes are logged in the [[Changelog]]. Current rules: [[Rulebook v1.0]].

%% my notes below. Argon never changes anything under this line %%
## My notes

