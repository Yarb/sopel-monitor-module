# -*- coding: utf-8

#
# Monitor module for sopel IRC bot.
# Notifies channel when specified file exists in system.
# Also handles topic changing based on reported activity.
#
#   -Johan Strandman, 2017-2018


import sys
import random
import os.path
import signal
from subprocess import call
from datetime import datetime

sys.path.append("/home/ruriruri/.sopel/modules")
import htmlwrite as write_html
import sopel.module
import sopel.formatting
import sopel.tools.target


STATUSFILE = "/run/open"
SOUNDDIR = ""
DOORBELL_SND = ""

#channel to accept (most) commands from
CHANNEL = "#"

# Bot identity regexp
BOT_IDENT = "(M|m)onitor(,\s?|:\s?|\s?)"

#Lists of expressions for various occasions

COMMENTS = ["Try again.",
            "Better luck next time."
           ]

ALERTS = ["Activity detected",
          "Activity started"
         ]

UNKNOWN_COMMENTS = ["Activity started", 
                    "Something is happening" 
                   ]

#Topic variables
TOPIC_HEADER = "Current acticity: "

CLOSED = 0
OPEN = 1


opened = 0
report = ["", "", ""]

def setup(bot):
    """Sopel setup method, called when module is started. This method resets all the variables used. """
    global report
    global opened

    update_report("", "", "")
    
    set_state(CLOSED)
    print("Variable reset.")


def shutdown(bot):
    """Sopel shutdown method. Routed to setup() and thus resets all variables. """
    setup(bot)

def set_state(s):
    global opened
    opened = s
    
def get_state():
    return opened
    
def update_report(new_report, reporttime, event_count):
    """Set given report as new report. """
    global report
    
    report[0] = new_report
    report[1] = reporttime
    report[2] = event_count
    
    
def is_reported():
    return len(report) > 0:
    

    
    
@sopel.module.interval(10)
def monitor(bot):
    """Timed power status check routine. Called by Sopel on 10 second interval. """

    timestamp = datetime.now()
  
    # If the monitor status file exists, clubroom is open.
    if os.path.exists(STATUSFILE):
        if not get_state():
            print(timestamp.strftime("[%d %b, %H:%M]") + " -- Open!")
            set_state(OPEN)
            
            # Randomly choose and send alert message to channel
            alert = ALERT[random.randint(0, len(ALERTS) - 1)]
            for channel in bot.channels:
                bot.msg(channel, alert)
    else:
        if get_state():
            print(timestamp.strftime("[%d %b, %H:%M]") + " -- Closed!")
            for channel in bot.channels:
                bot.msg(channel, "Activity ended."))
            clear_topic()
            set_state(CLOSED)
        update_report("", "", "")



def parse_topic(bot, trigger, from_topic, topic_reset):
    """
    Topic process(bot, trigger, from_topic, topic_reset)
    Process only topics of given channel. Split current topic using "|" as separator. 
    We assume that first part of the split topic is reserved for current status. Thus 
    whatever is contained in this part is replaced with current status. 
    If no "|" separators exist, replace the entire topic
    """
  event_count = report[2]
  

  if trigger.args[1] == CHANNEL:
      args = trigger.args[2]
      topic = sopel.tools.target.Channel(CHANNEL).split(" | ")
      if len(topic) > 1:
          if from_topic:

              if event_count > 0:
                  event_count -= 1

              # Update report and confirm to channel
              timestamp = datetime.now()
              reporttime = timestamp.strftime("[%H:%M]")
              
              set_report(topic[1], reporttime, event_count)
              
              bot.msg(CHANNEL, "Updating status from topic")
              #Console log
              print(timestamp.strftime("[%d %b, %H:%M]") + " -- " + report)
              
              # Rebuild topic.
              if len(topic) > 2:
                  old = " | " + " | ".join(topic[2:])
              else:
                  old = ""
              from_topic = 0    
          else:
              if topic_reset:
                  #Topic reset, clear changes
                  if len(topic) > (event_count + 1):
                      old = " | " + " | ".join(topic[(event_count + 1):])
                  else:
                      old = ""
                  
                  update_report("", "", "")
              else:
                  old = " | " + " | ".join(topic[1:])
      else:
          if from_topic:
              bot.msg(CHANNEL, "Topic has no marked events.")
              report_from_topic = 0
              return
          old = ""
          if topic_reset:
              pass
      #Commit changes
      update_topic(bot, report[0], str(old))
  else:
      pass




def report_handler(bot, new_report):
    """report_handler(bot, new_report)
    Process new report into topic.
    """
    event_count = report[2]
    
    # Count events and take report & time
    if event_count == 0:
        event_count = new_report.count("|")
    else:
        event_count += new_report.count("|")

    timestamp = datetime.now()
    reporttime = timestamp.strftime("[%H:%M]")

    #Console log
    print(timestamp.strftime("[%d %b, %H:%M]") + " -- " + report)

    update_report(new_report, reporttime, event_count)
    
    bot.say("Understood.")
    
    update_topic(bot, new_report, sopel.tools.target.Channel(CHANNEL))


@sopel.module.commands(BOT_IDENT + "(C|c)le(an|ar)\stopic[!.]*")
@sopel.module.nickname_commands("Clean\stopic[!.]*", "Clear\stopic[!.]*")
def reset_topic(bot, trigger):
    """reset_topic(bot, trigger)
    Used to clear changes made to the topic by the bot. Also clears current report.
    """
    global report

    if get_state():
        if is_reported():
            for channel in bot.channels:
                bot.msg(channel, "Clearing my changes from topic")
                print("TOPIC RESET")
                parse_topic(bot, trigger, 0, 1)

        else:
            bot.msg(CHANNEL, "No changes made.")




@sopel.module.nickname_commands("Report[:]?", "Reporting[:]?")
def take_report(bot, trigger):
    """take_report(bot, trigger)
    Preliminary sanity checks on new report after which the report
    is passed to handler.
    """
    # Check preliminaries and then call report handler
    if trigger.sender == CHANNEL:
        if get_state():
            if trigger.group(2) is None:
                # Oh boy...
                bot.reply("Information content zero..")
            else:
                # Take report and count events in it, if any
                report_handler(bot, trigger.group(2))
        else:
            # Really...
            bot.reply("Room is not open ")
    else:
        # Sigh...
        bot.reply("You have to do this from " + CHANNEL)



@sopel.module.commands(BOT_IDENT + "(R|r)eporting:")
def take_report_tg(bot, trigger):
    """take_report_tg(bot, trigger)
    Take report from telegram users.
    """
    new_report = trigger.group(0).split("eporting: ")[1]

    # Check preliminaries and then call report handler
    if trigger.sender == CHANNEL:
        if get_state():
            if new_report is None:
                # Silly...
                bot.reply("Information content zero..")
            else:
                # Take report and count events in it, if any
                report_handler(bot, new_report)
        else:
            # How hard can it be...
            bot.reply("Room is not open")
    else:
        # Seriously...
        bot.reply("You have to do this from " + CHANNEL)



@sopel.module.commands(BOT_IDENT + "(T|t)opic\sevent\sstarted[!?.]*")
@sopel.module.nickname_commands("Topic\sevent\sstarted[!?.]*")
def take_report_from_topic(bot, trigger):
    """tale_report_from_topic(bot, trigger)
    Process a report request from topic.
    """
    if trigger.sender == CHANNEL:
        if get_state():
            bot.write(('TOPIC',), CHANNEL)
            parse_topic(bot, trigger, 1, 0)
        else:
            bot.reply("Sensors indicate that you must be mistaken.")
    else:
        bot.reply("You have to do this from " + CHANNEL)




def update_topic(bot, new, old):
    """update_topic(bot, new_topic, old_topic)"""
    bot.write(('TOPIC', CHANNEL + " :" + TOPIC_HEADER +": "+ new + old))



@sopel.module.commands(BOT_IDENT + "(room\s)?(S|s)tatus[?!.]*")
@sopel.module.nickname_commands("room\sstatus[?!.]*", "Status[?!.]*")
def status(bot, trigger):
    """status(bot, trigger)
    Status command, report current status to channel.
    """
    if get_state():
        if is_reported():
            bot.say("Last report was: " + report[0] + " at " + report[1])
        else:
            response = random.randint(0, len(UNKNOWN_COMMENTS) - 1)
            bot.say(UNKNOWN_COMMENTS[response])
    else:
        bot.say("Nothing is currently happening")



#-----------------------------------------------------------------------------#
# Some simple helper functions
#-----------------------------------------------------------------------------#



def play(sound):
    """play(sound)
    Play given sound from defined SOUNDDIR.
    If not specified, does nothing"""
    if SOUNDDIR != "":
      call(["aplay", SOUNDDIR + sound])


def alert_signal(signum, stack):
    """alert_signal(signum, stack)
    Function to be called when signal is received from doorbell"""
    if get_state():
        play(DOORBELL_SND)

# Doorbell signal
signal.signal(signal.SIGUSR2, alert_signal)

