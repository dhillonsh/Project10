import arrow
from dateutil import tz

def agenda(startDay, endDay, startTime, endTime, busyList):  
  begin_time = arrow.get(startTime)
  end_time = arrow.get(endTime)
  begin_date = arrow.get(startDay).replace(hour=begin_time.hour, minute=begin_time.minute)
  end_date = arrow.get(endDay).replace(hour=end_time.hour, minute=end_time.minute)

  cur_time = begin_date.replace(tzinfo=tz.tzlocal())
  fullAgenda = []
  #print(busyList)
  for event in busyList:
    event_start = arrow.get(event['start'])
    event_end = arrow.get(event['end'])
    
    print("")
    print("Cur_time   : " + cur_time.isoformat())
    print("Event_Start: " + event_start.isoformat())
    print("")
    if cur_time < event_start:
      #While there is a gap from now to the next event. Iterate through days until next event
      while cur_time < event_start.replace(hour=begin_time.hour,minute=begin_time.minute):
        print(" -- > Sub cur_time: " + cur_time.isoformat())
        if cur_time < cur_time.replace(hour=end_time.hour, minute=end_time.minute):
          toAppend = {'summary': 'Available', 'start': cur_time.isoformat(), 'end': cur_time.replace(hour=end_time.hour, minute=end_time.minute).isoformat()}
          print(" --  -- > Inserting in loop 2: " + toAppend['start'] + " to " + toAppend['end'])
          toAppend['formattedDate'] = formatDates(toAppend['start'], toAppend['end'])
          fullAgenda.append(toAppend)
        cur_time = cur_time.replace(hour=begin_time.hour, minute=begin_time.minute,days=+1)
      
      if cur_time < event_start:
        toAppend = {'summary': 'Available', 'start': cur_time.isoformat(), 'end': event_start.isoformat()}
        print(" --> In default loop: " + toAppend['start'] + " to " + toAppend['end'])
        toAppend['formattedDate'] = toAppend['formattedDate'] = formatDates(toAppend['start'], toAppend['end'])
        fullAgenda.append(toAppend)
          
    elif event_end > cur_time.replace(hour=end_time.hour, minute=end_time.minute):
      print("---HERE")
      
    cur_time = event_end.replace(tzinfo=tz.tzlocal())
    fullAgenda.append(event)
    
  
  #Fill in the days after the last event as `Available`
  while cur_time < end_date:
    if cur_time < cur_time.replace(hour=end_time.hour, minute=end_time.minute):
      toAppend = {'summary': 'Available', 'start': cur_time.isoformat(), 'end': cur_time.replace(hour=end_time.hour, minute=end_time.minute).isoformat()}
      toAppend['formattedDate'] = formatDates(toAppend['start'], toAppend['end'])
      fullAgenda.append(toAppend)
    cur_time = cur_time.replace(hour=begin_time.hour, minute=begin_time.minute,days=+1)
  
  return fullAgenda

def formatDates(startDate, endDate):
  startOBJ = arrow.get(startDate)
  endOBJ = arrow.get(endDate)
  if startOBJ.format("ddd MM/DD/YYYY") == endOBJ.format("ddd MM/DD/YYYY"):
    return startOBJ.format("ddd MM/DD/YYYY") + ": " + startOBJ.format("HH:mm") + " - " + endOBJ.format("HH:mm")
  return startOBJ.format("ddd MM/DD/YYYY HH:mm") + ' - ' + endOBJ.format("ddd MM/DD/YYYY HH:mm")   
