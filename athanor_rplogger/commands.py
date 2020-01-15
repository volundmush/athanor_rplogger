from evennia.utils.ansi import ANSIString

from athanor.commands.command import AthCommand

from athanor.utils.time import utcnow, header, subheader, separator, make_table, sanitize_string, partial_match, \
    duration_from_string, utc_from_string
from world.database.scenes.models import Event, Pot, Plot, Scene


class CmdEvents(AthCommand):
    """
    The Scheduling system allows would-be scene-runners to post notices describing the scenes they want to run and when they wish to run them.

    |cSchedule Commands|n
    These are for scene runners wanting to setup and schedule an event.
        |w+schedule/add <time>/<title>=<description>|n
            Schedules an event. <time> must be in a 24-hour format of <mon> <day> HH:MM. For instance, Apr 20 15:45. A year is also optional: Mar 31 08:30 2017. Events default to the current year if not provided. This should be entered |rAS YOUR LOCAL TIME|n. The system will use your +config setting for Timezone, convert your local time to UTC, and then use this to display it in everyone's local times.
        |w+schedule/reschedule <id>=<time>|n
            Change an event's scheduled time. Uses the same rules as /add.
        |w+schedule/delete <id>|n
            Deletes an event. Careful with this.
        |w+schedule/title <id>=<text>|n
            Change an event's title.
        |w+schedule/desc <id>=<text>|n
            Change an event's description.
        |w+schedule/plot <id>=<plot id>|n
            Link an event to a Plot. (see help +plot)
        |w+schedule/mail <id>=<message>|n
            Send a @mail message to all interested parties. (taggers)
        |w+schedule/invite <id>=<message>|n
            Send out a mass summons for interested parties to join you at your location.

        Changes to an event will be automatically reflected in its respective BBS post, including deletions.

    |cGeneral Commands|n
        |w+schedule|n
            Views a list of scheduled scene.
        |w+schedule <id>|n
            View details about a scheduled scene. The owner can see interested parties.
        |w+schedule/tag <id>|n
            'Tag' a scene to show your interest.
        |w+schedule/untag <id>|n
            Remove a tag if you change your mind.
    """
    key = "+schedule"
    aliases = ["+scene", "+event", "+schedule"]
    locks = "cmd:all()"
    help_category = "Roleplaying"
    player_switches = ['add', 'delete', 'reschedule', 'desc', 'title', 'plot', 'tag', 'untag', 'mail', 'mine', 'invite']
    admin_switches = []
    system_name = 'SCHEDULE'

    def func(self):
        rhs = self.rhs
        lhs = self.lhs
        switches = self.final_switches

        if not switches:
            self.display_events(lhs, rhs)
            return
        switch = switches[0]
        getattr(self, 'switch_%s' % switch)(lhs, rhs)

    def display_events(self, lhs, rhs):
        if lhs:
            self.display_event(lhs)
            return
        now = utcnow()
        interval = duration_from_string('6h')
        expired = now - interval
        events = Event.objects.filter(date_schedule__gte=expired).order_by('date_schedule')
        tz = self.player.settings.get('timezone')
        last_day = ''
        check_day = ''
        message = list()
        message.append(header("Current Schedule - %s" % self.caller.display_local_time(format='%Z'), viewer=self.caller))
        for event in events:
            check_day = self.caller.display_local_time(date=event.date_schedule, format='%a %b %d %Y')
            if check_day != last_day:
                message.append(subheader(check_day))
            last_day = check_day
            time = self.caller.display_local_time(date=event.date_schedule, format='%I:%M%p')
            tag_mark = ' '
            taggers = set(event.interest.all())
            alts = set(self.player.get_all_characters())
            check_set = taggers.intersection(alts)
            if len(check_set):
                tag_mark = ANSIString('|C*|n')
            if self.character in taggers:
                tag_mark = ANSIString('|r*|n')
            if event.owner == self.character:
                tag_mark = ANSIString('|g*|n')
            tag_count = event.interest.all().count()
            display_string = "{}{:<2} {:<4}{:40.40}{:23.23}{:7}".format(tag_mark, tag_count, event.id, event.title,
                                                                        event.owner, time)
            message.append(display_string)
        message.append(header(viewer=self.caller))
        self.msg_lines(message)

    def display_event(self, lhs):
        event = Event.objects.filter(id=lhs).first()
        if not event:
            raise ValueError("Event not found.")
            return
        self.msg(event.display_event(viewer=self.character))

    def switch_add(self, lhs, rhs):
        if not lhs:
            raise ValueError("What time shall it happen?")
            return
        if '/' not in lhs:
            raise ValueError("What will the scene's title be?")
            return
        time, title = lhs.split('/', 1)
        try:
            check_time = utc_from_string(time, self.character.settings.get('timezone'))
        except ValueError as err:
            raise ValueError(str(err))
            return
        if not check_time > utcnow():
            raise ValueError("No scheduling things in the past, that's just silly.")
            return
        if not title:
            raise ValueError("What will the scene's title be?")
            return
        if not rhs:
            raise ValueError("What will the scene's description be?")
            return
        new_event = Event.objects.create(owner=self.character, title=title, date_schedule=check_time, description=rhs)
        new_event.setup()
        self.sys_msg("Your new Event's ID is: %s" % new_event.id)
        return

    def switch_reschedule(self, lhs, rhs):
        if not lhs:
            raise ValueError("No scene ID entered to reschedule.")
            return
        event = Event.objects.filter(id=lhs).first()
        if not event:
            raise ValueError("Event not found.")
            return
        if not self.caller.is_admin or event.owner != self.character:
            raise ValueError("Permission denied.")
            return
        try:
            check_time = utc_from_string(rhs, self.character.settings.get('timezone'))
        except ValueError as err:
            raise ValueError(str(err))
            return
        if not check_time > utcnow():
            raise ValueError("No scheduling things in the past, that's just silly.")
            return
        event.reschedule(check_time)
        self.sys_msg("Rescheduled to: %s" % self.caller.display_local_time(date=check_time))

    def switch_delete(self, lhs, rhs):
        if not lhs:
            raise ValueError("No scene ID entered to delete.")
            return
        event = Event.objects.filter(id=lhs).first()
        if not event:
            raise ValueError("Event not found.")
            return
        if not self.caller.is_admin or event.owner != self.character:
            raise ValueError("Permission denied.")
            return
        if not self.verify('Delete Event %s' % event.id):
            self.sys_msg("WARNING: This will delete Event %s: %s. This cannot be undone! Re-enter command to verify."
                         % (event.id, event.title))
            return
        event.delete()
        self.sys_msg("Deleted!")

    def switch_desc(self, lhs, rhs):
        if not lhs:
            raise ValueError("No scene ID entered to re-describe.")
            return
        event = Event.objects.filter(id=lhs).first()
        if not event:
            raise ValueError("Event not found.")
            return
        if not self.caller.is_admin or event.owner != self.character:
            raise ValueError("Permission denied.")
            return
        if not rhs:
            raise ValueError("What will the new description be?")
            return
        event.description = rhs
        event.save()
        self.sys_msg("Description changed.")

    def switch_title(self, lhs, rhs):
        if not lhs:
            raise ValueError("No scene ID entered to re-title.")
            return
        event = Event.objects.filter(id=lhs).first()
        if not event:
            raise ValueError("Event not found.")
            return
        if not self.caller.is_admin or event.owner != self.character:
            raise ValueError("Permission denied.")
            return
        if not rhs:
            raise ValueError("What will the new title be?")
            return
        event.title = rhs
        event.save()
        self.sys_msg("Title changed.")

    def switch_tag(self, lhs, rhs):
        if not lhs:
            raise ValueError("No scene ID entered to re-title.")
            return
        event = Event.objects.filter(id=lhs).first()
        if not event:
            raise ValueError("Event not found.")
            return
        if self.character in event.interest.all():
            raise ValueError("You have already tagged that event.")
            return
        event.interest.add(self.character)
        self.sys_msg("You have tagged Event %s: %s" % (event.id, event.title))


    def switch_untag(self, lhs, rhs):
        if not lhs:
            raise ValueError("No scene ID entered to re-title.")
            return
        event = Event.objects.filter(id=lhs).first()
        if not event:
            raise ValueError("Event not found.")
            return
        if self.character not in event.interest.all():
            raise ValueError("You have not tagged that event.")
            return
        event.interest.remove(self.character)
        self.sys_msg("You have untagged Event %s: %s" % (event.id, event.title))


class CmdScene(AthCommand):
    key = "+scene"
    aliases = []
    locks = "cmd:all()"
    help_category = "Roleplaying"
    player_switches = ['create', 'loudcreate', 'title', 'desc', 'plot', 'finish', 'pause', 'continue', 'move',
                       'join', 'leave', 'undo', 'recall', 'spoof', 'old', 'who']
    admin_switches = []
    system_name = 'SCENE'

    def func(self):
        rhs = self.rhs
        lhs = self.lhs
        switches = self.final_switches

        if not switches:
            self.display_scene(lhs, rhs)
            return
        switch = switches[0]
        getattr(self, 'switch_%s' % switch)(lhs, rhs)


class CmdLog(AthCommand):
    key = "+log"
    aliases = []
    locks = "cmd:all()"
    help_category = "Roleplaying"
    player_switches = []
    admin_switches = []
    system_name = 'LOG'

    def func(self):
        rhs = self.rhs
        lhs = self.lhs
        switches = self.final_switches

        if not switches:
            self.display_log(lhs, rhs)
            return
        switch = switches[0]
        getattr(self, 'switch_%s' % switch)(lhs, rhs)