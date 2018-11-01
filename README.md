Space/activity monitor for sopel IRC bot.

Designed to operate as an activity reporting bot for common rooms, spaces.
This includes reporting change in status, taking user reports and updating channel topic based on this.
What is required from user is a method of indicating activity to the bot. Default approach is monitoring
specified filesystem file for activity, but this can be replaced rather easily with for instance signals.
