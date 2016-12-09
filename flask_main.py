import flask
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify # For AJAX transactions
import uuid
import copy

# Free Time calculation
from agenda import *

import json
import logging
import os
import codecs

# Date handling 
import arrow # Replacement for datetime, based on moment.js
from dateutil import tz  # For interpreting local times


# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services 
from apiclient import discovery

# Mongo database
from pymongo import MongoClient
import secrets.admin_secrets
import secrets.client_secrets
MONGO_CLIENT_URL = "mongodb://{}:{}@localhost:{}/{}".format(
    secrets.client_secrets.db_user,
    secrets.client_secrets.db_user_pw,
    secrets.admin_secrets.port, 
    secrets.client_secrets.db)

####
# Database connection per server process
###

try: 
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, secrets.client_secrets.db)
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)
    
###
# Globals
###
import CONFIG
import secrets.admin_secrets  # Per-machine secrets
import secrets.client_secrets # Per-application secrets

app = flask.Flask(__name__)
app.debug=CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)
app.secret_key=CONFIG.secret_key

SCOPES_MODIFY = 'https://www.googleapis.com/auth/calendar'
SCOPES_READONLY = 'https://www.googleapis.com/auth/calendar.readonly'
#SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = secrets.admin_secrets.google_key_file
APPLICATION_NAME = 'MeetMe class project'

#############################
#
#  Pages (routed from URLs)
#
#############################

@app.route("/")
@app.route("/index")
def index(extra={}):
    app.logger.debug("Entering index")
    if 'callbackURL' in flask.session and flask.session['callbackURL'] != 'index':
        flask.session.clear()
        
    if 'begin_date' not in flask.session:
        init_session_values()
    flask.session['callbackURL'] = 'index'
    return render_template('index.html')

@app.route('/arranger/<proposalID>/')
def arranger(proposalID, extra={}):
    app.logger.debug("Entering arranger")
    if 'callbackURL' in flask.session and flask.session['callbackURL'] != 'arranger':
        flask.session.clear()
        
    meetingProposal = get_records(collection, {'id': proposalID})
    if not meetingProposal:
        return flask.render_template('page_not_found.html'), 404
    flask.session['callbackURL'] = 'arranger'
    meetingProposal['daterange'] = arrow.get(meetingProposal['begin_date']).format("MM/DD/YYYY") + " - " + arrow.get(meetingProposal['end_date']).format("MM/DD/YYYY")
    meetingProposal['timerange'] = [arrow.get(meetingProposal['begin_time']).format("HH:mm"), arrow.get(meetingProposal['end_time']).format("HH:mm")]

    globalBusyTimes = []
    for key, val in meetingProposal['busyList'].items():
        meetingProposal['busyList'][key.replace('"','.')] =  meetingProposal['busyList'].pop(key)
        globalBusyTimes.extend(val)

    meetingProposal['creator'] = meetingProposal['creator'].replace('"','.')
    sortedBusyTimes = sorted(globalBusyTimes, key=lambda k: k['start'])
    fullAgenda = agenda(meetingProposal['begin_date'], meetingProposal['end_date'], meetingProposal['begin_time'], meetingProposal['end_time'], sortedBusyTimes)
    flask.g.agenda = fullAgenda
    print(fullAgenda)
    flask.session['arranger'] = meetingProposal
    flask.g.proposalID = proposalID
    flask.g.proposal = True
    return render_template('index.html')

@app.route("/setmeeting", methods=['POST'])
def setmeeting():
    print("In set meeting")
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      return flask.redirect(flask.url_for('oauth2callback'))
    gcal_service = get_gcal_service(credentials)
    meetingday = arrow.get(request.form.get('meetingday'),'MM/DD/YYYY').replace(tzinfo=tz.tzlocal())
    startTime = arrow.get(request.form.get('timepickerSTART'), 'h:mma')
    endTime = arrow.get(request.form.get('timepickerSTOP'), 'h:mma')
    
    emailList = []
    meetingProposal = get_records(collection, {'id': request.form.get('proposalID')})
    for key, val in meetingProposal['busyList'].items():
        emailList.append(key.replace('"','.'))
    collection.update({'id':request.form.get('proposalID')},{"$set":{'active':'0'}})
    event = {
      'summary': request.form.get('summary'),
      'location': request.form.get('location'),
      'description': request.form.get('description'),
      'start': {
        'dateTime': meetingday.replace(hour=startTime.hour, minute=startTime.minute).isoformat()
      },
      'end': {
        'dateTime': meetingday.replace(hour=endTime.hour, minute=endTime.minute).isoformat()
      },
      'attendees': emailList
    }
    event = gcal_service.events().insert(calendarId='primary', body=event, sendNotifications=True).execute()
    #print('Event created: %s' % (event.get('htmlLink')))
    return ""

@app.route("/logout")
def logout():
  flask.session.clear()
  return ""

@app.route("/createproposal", methods=['POST'])
def createproposal():
    primaryEmail = ""
    for dic in flask.session['calendarList']:
        if 'primary' in dic and dic['primary'] == True:
            primaryEmail = dic['id']
            break
    primaryEmail = primaryEmail.replace('.','"')
    entry = {'type': "dated_calendar", 'active': '1', 'id': codecs.encode(os.urandom(32), 'hex').decode()[0:12], 'creator': primaryEmail, 'begin_date': flask.session['begin_date'], 'end_date': flask.session['end_date'], 'begin_time': flask.session['begin_time'], 'end_time': flask.session['end_time'], 'busyList': {primaryEmail: flask.session['busyList']}}
    collection.insert(entry,check_keys=False)
    return jsonify(status='ok', returnData=entry['id'])
    
@app.route("/setavailability", methods=['POST'])
def setavailability():
    app.logger.debug("Entering setavailability.")
    meetingProposal = get_records(collection, {'id': flask.session['arranger']['id']})
    primaryEmail = ""
    for dic in flask.session['calendarList']:
        if 'primary' in dic and dic['primary'] == True:
            primaryEmail = dic['id']
            break
    primaryEmail = primaryEmail.replace('.','"')
    meetingProposal['busyList'][primaryEmail] = flask.session['busyList']
    collection.update({'id':flask.session['arranger']['id']},{"$set":{'busyList':meetingProposal['busyList']}})
    return jsonify()

@app.route("/choose")
def choose():
    ## We'll need authorization to list calendars 
    ## I wanted to put what follows into a function, but had
    ## to pull it back here because the redirect has to be a
    ## 'return' 
    app.logger.debug("Checking credentials for Google calendar access")
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      if 'callbackURL' in flask.session and flask.session['callbackURL'] == 'arranger':
        return flask.redirect(flask.url_for('oauth2callback'))
      else:
        return flask.redirect(flask.url_for('oauth2callback', scopeType=SCOPES_MODIFY))

    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    flask.session['calendarList'] = list_calendars(gcal_service)
    flask.g.calendars = flask.session['calendarList']
    
    primaryEmail = ""
    for dic in flask.session['calendarList']:
        if 'primary' in dic and dic['primary'] == True:
            primaryEmail = dic['id']
            break
    flask.session['primaryEmail'] = primaryEmail
    
    if 'callbackURL' in flask.session and flask.session['callbackURL'] == 'arranger':
        return flask.redirect(flask.url_for('arranger', proposalID=flask.session['arranger']['id']))
    else:
        return flask.redirect(flask.url_for('index'))
    #return render_template('index.html')

@app.route('/selectcalendars', methods=['POST'])
def selectcalendars():
    app.logger.debug("Entering selectcalendars")
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      return flask.redirect(flask.url_for('oauth2callback'))
    gcal_service = get_gcal_service(credentials)
    
    begin_time = arrow.get(flask.session['begin_time'])
    end_time = arrow.get(flask.session['end_time'])
    
    busyTimes = []
    databaseEntry = []
    for calendar in request.form.getlist('calendarList[]'):
      eventList = gcal_service.events().list(calendarId=calendar, timeMin=arrow.get(flask.session['begin_date']).replace(hour=begin_time.hour,minute=begin_time.minute).isoformat(), timeMax=arrow.get(flask.session['end_date']).replace(hour=end_time.hour,minute=end_time.minute), singleEvents=True, orderBy='startTime').execute()
      for item in eventList['items']:
        if 'transparency' in item:
          continue

        if 'dateTime' not in item['start']:
          item['start']['dateTime'] = arrow.get(item['start']['date']).replace(hour=0, minute=0).isoformat()
        if 'dateTime' not in item['end']:
          item['end']['dateTime'] = arrow.get(item['end']['date']).replace(days=-1, hour=23, minute=59).isoformat()

        itemStart = arrow.get(item['start']['dateTime'])
        itemEnd = arrow.get(item['end']['dateTime'])
        begin_date = arrow.get(itemStart).replace(hour=begin_time.hour, minute=begin_time.minute)
        end_date = arrow.get(itemEnd).replace(hour=end_time.hour, minute=end_time.minute)
        if itemEnd <= begin_date or itemStart >= end_date:
          continue

        toAppend = {'start': item['start']['dateTime'], 'end': item['end']['dateTime']}
        databaseEntry.append(copy.copy(toAppend))
        toAppend['summary'] = item['summary']
        toAppend['calendar'] = eventList['summary']
        toAppend['formattedDate'] = formatDates(arrow.get(toAppend['start']).isoformat(), arrow.get(toAppend['end']).isoformat())
        busyTimes.append(toAppend)
              
    busyTimes = sorted(busyTimes, key=lambda k: k['start'])
    fullAgenda = agenda(flask.session['begin_date'], flask.session['end_date'], flask.session['begin_time'], flask.session['end_time'], busyTimes)
    flask.g.busyEvents = fullAgenda
    flask.session['busyList'] = databaseEntry
    flask.g.calendars = flask.session['calendarList']
    app.logger.debug("Returned from get_gcal_service")
    return jsonify(status='ok', returnData={'busyEvents': flask.g.busyEvents, 'calendars': flask.g.calendars})

@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html'), 404

####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
#  Protocol for use ON EACH REQUEST: 
#     First, check for valid credentials
#     If we don't have valid credentials
#         Get credentials (jump to the oauth2 protocol)
#         (redirects back to /choose, this time with credentials)
#     If we do have valid credentials
#         Get the service object
#
#  The final result of successful authorization is a 'service'
#  object.  We use a 'service' object to actually retrieve data
#  from the Google services. Service objects are NOT serializable ---
#  we can't stash one in a cookie.  Instead, on each request we
#  get a fresh serivce object from our credentials, which are
#  serializable. 
#
#  Note that after authorization we always redirect to /choose;
#  If this is unsatisfactory, we'll need a session variable to use
#  as a 'continuation' or 'return address' to use instead. 
#
####

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value. 
    """
    if 'credentials' not in flask.session:
      return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
        credentials.access_token_expired):
      return None
    return credentials


def get_gcal_service(credentials):
  """
  We need a Google calendar 'service' object to obtain
  list of calendars, busy times, etc.  This requires
  authorization. If authorization is already in effect,
  we'll just return with the authorization. Otherwise,
  control flow will be interrupted by authorization, and we'll
  end up redirected back to /choose *without a service object*.
  Then the second call will succeed without additional authorization.
  """
  app.logger.debug("Entering get_gcal_service")
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http_auth)
  app.logger.debug("Returning service")
  return service

@app.route('/oauth2callback')
def oauth2callback(scopeType=SCOPES_READONLY):
  """
  The 'flow' has this one place to call back to.  We'll enter here
  more than once as steps in the flow are completed, and need to keep
  track of how far we've gotten. The first time we'll do the first
  step, the second time we'll skip the first step and do the second,
  and so on.
  """
  app.logger.debug("Entering oauth2callback")
  flow =  client.flow_from_clientsecrets(
      CLIENT_SECRET_FILE,
      scope= SCOPES_MODIFY,
      redirect_uri=flask.url_for('oauth2callback', _external=True))
  ## Note we are *not* redirecting above.  We are noting *where*
  ## we will redirect to, which is this function. 
  
  ## The *second* time we enter here, it's a callback 
  ## with 'code' set in the URL parameter.  If we don't
  ## see that, it must be the first time through, so we
  ## need to do step 1. 
  app.logger.debug("Got flow")
  if 'code' not in flask.request.args:
    app.logger.debug("Code not in flask.request.args")
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
    ## This will redirect back here, but the second time through
    ## we'll have the 'code' parameter set
  else:
    ## It's the second time through ... we can tell because
    ## we got the 'code' argument in the URL.
    app.logger.debug("Code was in flask.request.args")
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    ## Now I can build the service and execute the query,
    ## but for the moment I'll just log it and go back to
    ## the main screen
    app.logger.debug("Got credentials")
    return flask.redirect(flask.url_for('choose'))

@app.route('/setrange', methods=['POST'])
def setrange():
    """
    User chose a date range with the bootstrap daterange
    widget.
    """
    app.logger.debug("Entering setrange")
    flask.flash("Setrange gave us '" + request.form.get('daterange') + "' and [from: " + request.form.get('fromTime') + " to " + request.form.get('toTime') + "]")
    daterange = request.form.get('daterange')
    flask.session['daterange'] = daterange
    daterange_parts = daterange.split()
    flask.session['begin_date'] = interpret_date(daterange_parts[0])
    flask.session['end_date'] = interpret_date(daterange_parts[2])
    app.logger.debug("Setrange parsed {} - {}  dates as {} - {}".format(
      daterange_parts[0], daterange_parts[1], 
      flask.session['begin_date'], flask.session['end_date']))

    flask.session["begin_time"] = interpret_time(request.form.get('fromTime'))
    flask.session["end_time"] = interpret_time(request.form.get('toTime'))
    
    flask.session["timerange"] = [request.form.get('fromTime'), request.form.get('toTime')]
    return flask.redirect(flask.url_for("choose"))

####
#
#   Initialize session variables 
#
####
  
def init_session_values():
    """
    Start with some reasonable defaults for date and time ranges.
    Note this must be run in app context ... can't call from main. 
    """
    app.logger.debug('--- In here')
    # Default date span = tomorrow to 1 week from now
    now = arrow.now('local')
    tomorrow = now.replace(days=+1)
    nextweek = now.replace(days=+7)
    flask.session["begin_date"] = tomorrow.floor('day').isoformat()
    flask.session["end_date"] = nextweek.ceil('day').isoformat()
    flask.session["daterange"] = "{} - {}".format(
        tomorrow.format("MM/DD/YYYY"),
        nextweek.format("MM/DD/YYYY"))
    # Default time span each day, 8 to 5
    flask.session["begin_time"] = interpret_time("8am")
    flask.session["end_time"] = interpret_time("5pm")
    flask.session["timerange"] = ["08:00", "17:00"]

def interpret_time( text ):
    """
    Read time in a human-compatible format and
    interpret as ISO format with local timezone.
    May throw exception if time can't be interpreted. In that
    case it will also flash a message explaining accepted formats.
    """
    app.logger.debug("Decoding time '{}'".format(text))
    time_formats = ["ha", "h:mma",  "h:mm a", "H:mm"]
    try: 
        as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
        as_arrow = as_arrow.replace(year=2016) #HACK see below
        app.logger.debug("Succeeded interpreting time")
    except:
        app.logger.debug("Failed to interpret time")
        flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
              .format(text))
        raise
    return as_arrow.isoformat()
    #HACK #Workaround
    # isoformat() on raspberry Pi does not work for some dates
    # far from now.  It will fail with an overflow from time stamp out
    # of range while checking for daylight savings time.  Workaround is
    # to force the date-time combination into the year 2016, which seems to
    # get the timestamp into a reasonable range. This workaround should be
    # removed when Arrow or Dateutil.tz is fixed.
    # FIXME: Remove the workaround when arrow is fixed (but only after testing
    # on raspberry Pi --- failure is likely due to 32-bit integers on that platform)


def interpret_date( text ):
    """
    Convert text of date to ISO format used internally,
    with the local time zone.
    """
    try:
      as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
          tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()

def next_day(isotext):
    """
    ISO date + 1 day (used in query to Google calendar)
    """
    as_arrow = arrow.get(isotext)
    return as_arrow.replace(days=+1).isoformat()

####
#
#  Functions (NOT pages) that return some information
#
####
  
def list_calendars(service):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict.
    The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")  
    calendar_list = service.calendarList().list().execute()["items"]
    result = [ ]
    for cal in calendar_list:
        kind = cal["kind"]
        id = cal["id"]
        if "description" in cal: 
            desc = cal["description"]
        else:
            desc = "(no description)"
        summary = cal["summary"]
        # Optional binary attributes with False as default
        selected = ("selected" in cal) and cal["selected"]
        primary = ("primary" in cal) and cal["primary"]
        

        result.append(
          { "kind": kind,
            "id": id,
            "summary": summary,
            "selected": selected,
            "primary": primary
            })
    return sorted(result, key=cal_sort_key)


def cal_sort_key( cal ):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
       selected_key = " "
    else:
       selected_key = "X"
    if cal["primary"]:
       primary_key = " "
    else:
       primary_key = "X"
    return (primary_key, selected_key, cal["summary"])

def get_records(collection, searchType):
    search = { "type": "dated_calendar" }
    search.update(searchType)
    for record in collection.find(search, {'_id': False}):
        return record
    return {} 

#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"

@app.template_filter( 'fmttime' )
def format_arrow_time( time ):
    try:
        normal = arrow.get( time )
        return normal.format("HH:mm")
    except:
        return "(bad time)"
    
#############


if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running under green unicorn)
  app.run(port=CONFIG.PORT,host="0.0.0.0")
    
