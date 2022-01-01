# whale_tracker_telebot
Python Based telegram bot to track whale movements on block explorer (updated as of 01/01/2022)

## Future works:
1. add tables for whales from different chains
2. add transaction information in tele msg?
3. enable backup of db files as heroku has flaw, files gone after instance restarts from idle, redeploy

## Things to note:
1. Host on local server with whaletrackerbot.py
2. Host on Heroku with whaletrackerbotheroku.py
3. db file not included as it contains secret alphas 😉
4. If host on heroku, remember to employ some service to ping heroku periodically or it will become idle and stop tracker (e.g. cron job)

## Usage:
```/start``` to start tracker, can set intervals within the code at ```job_queue.run_repeating```

```/end``` to end tracker

```/new``` to add new record

```/update``` to update record

```/delete``` to delete record
