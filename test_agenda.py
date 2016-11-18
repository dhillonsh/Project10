from agenda import *
#import arrow


def test_noEvents():
  #8AM to 5PM on 1 day
  singleDay = agenda("2016-11-17","2016-11-17","2016-11-17T08:00:00:00", "2016-11-17T17:00:00:00", [])
  assert len(singleDay) == 1
  assert arrow.get(singleDay[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(singleDay[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  
  #8AM to 5PM over 2 days
  multipleDays = agenda("2016-11-17", "2016-11-18","2016-11-17T08:00:00:00","2016-11-18T17:00:00:00", [])
  assert len(multipleDays) == 2
  assert arrow.get(multipleDays[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(multipleDays[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  assert arrow.get(multipleDays[1]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-18 08:00"
  assert arrow.get(multipleDays[1]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-18 17:00"

def test_singleEvent():
  busyList = [{'summary': 'randomEvent', 'start': "2016-11-17T08:00:00:00", 'end': "2016-11-17T08:30:00:00"}]
  
  #Event at the start of the day and time
  startDayEvent = agenda("2016-11-17","2016-11-17","2016-11-17T08:00:00:00", "2016-11-17T17:00:00:00", busyList)
  assert len(startDayEvent) == 2
  assert arrow.get(startDayEvent[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(startDayEvent[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:30"
  assert startDayEvent[0]['summary'] == 'randomEvent'
  assert arrow.get(startDayEvent[1]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:30"
  assert arrow.get(startDayEvent[1]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  assert startDayEvent[1]['summary'] == 'Available'

  #Event at the end of the day and time
  busyList[0]['start'] = "2016-11-17T16:30:00:00"
  busyList[0]['end'] = "2016-11-17T17:00:00:00"
  endDayEvent = agenda("2016-11-17","2016-11-17","2016-11-17T08:00:00:00", "2016-11-17T17:00:00:00", busyList)
  assert len(endDayEvent) == 2
  assert arrow.get(endDayEvent[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(endDayEvent[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 16:30"
  assert endDayEvent[0]['summary'] == 'Available'
  assert arrow.get(endDayEvent[1]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 16:30"
  assert arrow.get(endDayEvent[1]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  assert endDayEvent[1]['summary'] == 'randomEvent'
  
  #Event in the middle of a day
  busyList[0]['start'] = "2016-11-17T13:30:00:00"
  busyList[0]['end'] = "2016-11-17T14:00:00:00"
  middleDayEvent = agenda("2016-11-17","2016-11-17","2016-11-17T08:00:00:00", "2016-11-17T17:00:00:00", busyList)
  assert len(middleDayEvent) == 3
  assert arrow.get(middleDayEvent[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(middleDayEvent[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 13:30"
  assert middleDayEvent[0]['summary'] == 'Available'
  assert arrow.get(middleDayEvent[1]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 13:30"
  assert arrow.get(middleDayEvent[1]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 14:00"
  assert middleDayEvent[1]['summary'] == 'randomEvent'
  assert arrow.get(middleDayEvent[2]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 14:00"
  assert arrow.get(middleDayEvent[2]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  assert middleDayEvent[2]['summary'] == 'Available'

def test_multipleEventsSingleDay():
  busyList = [{'summary': 'randomEvent1', 'start': "2016-11-17T08:00:00:00", 'end': "2016-11-17T08:30:00:00"}, {'summary': 'randomEvent2', 'start': "2016-11-17T13:21:00:00", 'end': "2016-11-17T15:55:00:00"}]
  randomEvents = agenda("2016-11-17","2016-11-17","2016-11-17T08:00:00:00", "2016-11-17T17:00:00:00", busyList)
  assert len(randomEvents) == 4
  assert arrow.get(randomEvents[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(randomEvents[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:30"
  assert randomEvents[0]['summary'] == 'randomEvent1'
  assert arrow.get(randomEvents[1]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:30"
  assert arrow.get(randomEvents[1]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 13:00"
  assert randomEvents[1]['summary'] == 'Available'
  assert arrow.get(randomEvents[2]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 13:21"
  assert arrow.get(randomEvents[2]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 15:55"
  assert randomEvents[2]['summary'] == 'randomEvent2'
  assert arrow.get(randomEvents[3]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 15:55"
  assert arrow.get(randomEvents[3]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  assert randomEvents[3]['summary'] == 'Available'

def test_noFreeTime():
  #Single Event, all day
  busyList = [{'summary': 'randomEvent1', 'start': "2016-11-17T08:00:00:00", 'end': "2016-11-17T17:00:00:00"}]
  allDayEvent = agenda("2016-11-17","2016-11-17","2016-11-17T08:00:00:00", "2016-11-17T17:00:00:00", busyList)
  assert len(allDayEvent) == 1
  assert arrow.get(allDayEvent[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(allDayEvent[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  assert allDayEvent[0]['summary'] == 'randomEvent1'
  
  #Two events, all day
  busyList = [{'summary': 'randomEvent1', 'start': "2016-11-17T08:00:00:00", 'end': "2016-11-17T11:00:00:00"}, {'summary': 'randomEvent2', 'start': "2016-11-17T11:00:00:00", 'end': "2016-11-17T17:00:00:00"}]
  assert len(allDayEvent) == 2
  assert arrow.get(allDayEvent[0]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 08:00"
  assert arrow.get(allDayEvent[0]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 11:00"
  assert allDayEvent[0]['summary'] == 'randomEvent1'
  assert arrow.get(allDayEvent[1]['start']).format('YYYY-MM-DD HH:mm') == "2016-11-17 11:00"
  assert arrow.get(allDayEvent[1]['end']).format('YYYY-MM-DD HH:mm') == "2016-11-17 17:00"
  assert allDayEvent[1]['summary'] == 'randomEvent2'
