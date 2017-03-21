# Watchdog
Watchdog is a simple utility written in Python for monitoring a hostname's uptime, and alerting predefined contacts should an issue arise.

By defualt, it requests a specified URL every 60 seconds, and logs the HTTP status code of the response. If that status is not `200 OK`, Watchdog will place a call via the Twilio API to the current contact number it has defined. This number can be defined either in a shifts.json file, or by passing a contact number as a CLI argument when Watchdog is started. 

# Prerequisties
- Python 2.7
- A Valid Twilio Account
- the `twilio` python module

# Set up
- Clone this Repository
- Install twilio python module: `pip install twilio`
- Set the proper environmental variables:
```
$ export WATCHDOG_LOG_FILE="/some/path/status.log"
$ export WATCHDOG_SHIFTS_FILE="/some/path/shifts.json"
$ export TWILIO_FROM_NUMBER="number_on_twilio_account"
$ export TWILIO_AUTH_TOKEN="twilio_auth_token"
$ export TWILIO_ACCOUNT_SID="twiliot_account_sid"
$ export WATCHDOG_URL_TO_CHECK="http://somedomain.com"
```
- (Optional) Create a shifts.json file to schedule who should be contacted on what day of the week

# Usage
To start watchdog.py with shifts.json file:

`$ python watchdog.py`

to run watchdog while specifying a contact number at runtime:

`$ python watchdog.py +15551234567`

When it executes, it should fork off a daemonized process, print the PID of the new process and other information like so:
```
$ python watchdog.py 
Daemon PID 16219
cliContact is False
monitoring https://somedomain.com/
```

Tail the log to see the status of checks:
```
$ tail -f status.log 

[Mon Mar 20 20:39:35 2017] -- [[Starting Watchdog]]
[Mon Mar 20 20:39:35 2017] -- Current Contact Number: +15551234567
[Mon Mar 20 20:40:53 2017] -- Status 200: www.google.com
```
