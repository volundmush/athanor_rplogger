import re

from evennia.utils.ansi import ANSIString

from athanor.gamedb.scripts import AthanorOptionScript
from athanor.gamedb.models import PlotBridge, EventBridge


class AthanorPlot(AthanorOptionScript):
    re_name = re.compile(r"")
    lockstring = ""

    def create_bridge(self, key, clean_key):
        if hasattr(self, 'plot_bridge'):
            return
        bridge, created = PlotBridge.objects.get_or_create(db_script=self, db_name=clean_key,
                                                           db_iname=clean_key.lower(), db_cname=key)
        if created:
            bridge.save()

    def setup_locks(self):
        self.locks.add(self.lockstring)

    @classmethod
    def create_plot(cls, key, **kwargs):
        key = ANSIString(key)
        clean_key = str(key.clean())
        if '|' in clean_key:
            raise ValueError("Malformed ANSI in Plot Name.")
        if PlotBridge.objects.filter(db_iname=clean_key.lower()).count():
            raise ValueError("Name conflicts with another Plot.")
        script, errors = cls.create(clean_key, **kwargs)
        if script:
            script.create_bridge(key, clean_key)
            script.setup_locks()
        return script


class AthanorEvent(AthanorOptionScript):
    re_name = re.compile(r"")
    lockstring = ""

    def create_bridge(self, key, clean_key):
        if hasattr(self, 'event_bridge'):
            return
        bridge, created = EventBridge.objects.get_or_create(db_script=self, db_name=clean_key,
                                                            db_iname=clean_key.lower(), db_cname=key)
        if created:
            bridge.save()

    def setup_locks(self):
        self.locks.add(self.lockstring)

    @classmethod
    def create_event(cls, key, **kwargs):
        key = ANSIString(key)
        clean_key = str(key.clean())
        if '|' in clean_key:
            raise ValueError("Malformed ANSI in Plot Name.")
        if PlotBridge.objects.filter(db_iname=clean_key.lower()).count():
            raise ValueError("Name conflicts with another Plot.")
        script, errors = cls.create(clean_key, **kwargs)
        if script:
            script.create_bridge(key, clean_key)
            script.setup_locks()
        return script


