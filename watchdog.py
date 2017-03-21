import requests
import sys
import os
import time
import datetime
import json
from twilio.rest import TwilioRestClient

# Class representing a URL Check
class UrlCheck(object):

  def __init__(self, url):
   self.url = url
   self.host = url.split('//')[1].split('/')[0]
  
  #check the HTTP status code of a request
  def check(self):
    try:
      r = requests.get(self.url)
      self.status = r.status_code
      return 1
    except:
      self.status = "COULD NOT CONNECT!"
      return 0

# Class representing a Twilio Contact
class TwillioContact(object):

  def __init__(self,number):
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token =  os.environ['TWILIO_AUTH_TOKEN']
    self.from_number = os.environ['TWILIO_FROM_NUMBER']
    self.client = TwilioRestClient(account_sid, auth_token)
    self.number = number

  #place call to contact number
  def call(self):
    self.lastCall = self.client.calls.create(to=self.number,
                             from_=self.from_number, # Must be a valid Twilio number
                             url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient")

# Function to look up contacts from a shifts.json file
def getContact():
  now = datetime.datetime.now()

  # Open shift config file to see who is on-call
  shiftsFilePath =  os.environ['WATCHDOG_SHIFTS_FILE']
  with open (shiftsFilePath) as fh:
      dict =  json.load(fh)

  # check if it is before or after shift cutoff
  if datetime.time(9, 0)  >= now.time():
      dayOfWeek = now - datetime.timedelta(days=1)
  else:
      dayOfWeek = now

  contact = {
    "contact_number": dict['shifts'][dayOfWeek.strftime("%A")]['contact_number'],
     "contact_name": dict['shifts'][dayOfWeek.strftime("%A")]['contact_name']
  }
  return contact


def main():

  ###########
  # Startup #
  ###########

  # Check if a phone number has been passed via CLI  
  if len(sys.argv) > 1:
    cliContact = True
    print "cliContact is true"
  else: 
    cliContact = False
    print "cliContact is False"

  # Define URL to Check
  url = os.environ['WATCHDOG_URL_TO_CHECK']
  print "monitoring {0}".format(url)
  # Open log file, and log startup
  logFile = os.environ['WATCHDOG_LOG_FILE']
  f = open(logFile, "a")  
  logString = "[{0}] -- [[Starting Watchdog]]\n".format(time.ctime(time.time()))
  f.write(logString)
  f.flush()


  #############
  # Main Loop #
  #############

  while 1:
 
    # Create check object for pertinent URL
    c = UrlCheck(url) 

    # Define apropriate contact
    if cliContact:
      contactNumber = sys.argv[1]
    else:
       contact = getContact()
       try:
         oldNumber = contactNumber
       except:
         oldNumber = ''
       contactNumber = contact['contact_number']
       if oldNumber != contactNumber:
         logString = "[{0}] -- Current Contact Number: {1}\n".format(time.ctime(time.time()), contactNumber)
         f.write(logString)
         f.flush()  

    # Run Check and output results to log file
    if c.check():
      currentTime = time.ctime(time.time())
      logString = "[{0}] -- Status {2}: {1}\n".format(time.ctime(time.time()), c.host, c.status)
      f.write(logString)
      f.flush()

      # if the check returns in error, contact apropriate number
      if c.status != 200: 
        t = TwillioContact(contactNumber)
        logString = "[{0}] -- Calling {1}\n".format(time.ctime(time.time()), t.number)
        f.write(logString)
        f.flush()
        t.call()
        time.sleep(45)
        call = t.client.calls.get(t.lastCall.sid)

        #if the cal was answered, log such and dont call back for 5 minutes 
        if call.status == 'completed':
          logString = "[{0}] -- Call to {1} was answered\n".format(time.ctime(time.time()), t.number)
          f.write(logString)
          f.flush()
          time.sleep(300)

        # if the call was not answered, wait 1 minute then re-run check and call back
        else:
          logString = "[{0}] -- Call to {1} was NOT answered\n".format(time.ctime(time.time()), t.number)      
          f.write(logString)
          f.flush()

    #Connection Failed, contact and log
    else:
      logString = "[{0}] -- Status {2}: {1}\n".format(time.ctime(time.time()), c.host, c.status)
      f.write(logString)
      f.flush()
      t = TwillioContact(contactNumber)
      t.call()       
      logString = "[{0}] -- Calling {1}\n".format(time.ctime(time.time()), t.number)
      f.write(logString)
      f.flush()
    time.sleep(60)
    
# The __main__ definition with daemon magix
if __name__ == "__main__":
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit first parent
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 

    # do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent, print eventual PID before
            print "Daemon PID %d" % pid 
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1) 

    # start the daemon main loop
    main()
