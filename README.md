# README #

### Author: Harpreet Dhillon, harpreet@uoregon.edu ###

---

### Purpose ###
* This application is for the Final Project of CIS 322 at University of Oregon.
* The purpose was to get an introduction with Google's Calendar API.
* This is a combination of projects that allows users to arrange meetings.

### Application Specifics ###
* The main [index](/templates/index.html) displays all the calendar information
* Necessary files (files not included in the repository):
  * secrets/admin_secrets.py
    * `google_key_file="PATH_TO_YOUR_google_client_key.json"`
    * The google_client_key.json can be obtained by following [this guide](https://auth0.com/docs/connections/social/google)
* There is no way to modify the date range or time range of a proposed meeting after it has been created
* There is no way to modify a meeting after the meeting invitations have been sent

### Running the Application ###
* Test deployment to other environments including Raspberry Pi.  Deployment 
  should work "out of the box" with this command sequence:
  * `git clone <yourGitRepository> <targetDirectory>`
  * `cd <targetDirectory>`
  * `./configure`
  * `make run`
  * (control-C to stop program)
* The default port is 5000, so the webserver should be reachable at http://localhost:5000 , and also through its IP address.
* Creating a meeting:
  * Navigate to http://< Host >/index
  * There is an entry for both the date range and time range in which to schedule a meeting within
  * After selecting a range of dates/times, you will be redirected to Google's authorization page. Note: The application will request for read/write permissions which is necessary to send out invitations
  * A selection of calendars will be available to use as busy times in which to schedule meetings around
  * Afterwards, a URL will be displayed which should be sent to the attendees of the meeting.
* Modifying an existing meeting:
  * It is essential to keep the unique identifier saved, as it is not obtainable any other way.
   * http://< Host >/arranger/< Unique Identifier >
  * Attendees will simply be prompted to select which calenders to block
  * The creator of the meeting will be able to:
   * See who has set their available times
   * View the available times for all users
   * Be able to specify a Summary, Description, Location for the meeting (Not necessary)
   * Be able to specify the meeting day, meeting start time, and meeting end time (necessary)

### Testing the Application ###
* There are nosetests for this application that can be run with:
  * `cd <targetDirectory>`
  * `. env/bin/activate`
  * `nosetests`
