from evennia.utils.utils import class_from_module
from evennia.utils.logger import log_trace

from athanor.gamedb.scripts import AthanorGlobalScript
from athanor_rplogger.gamedb import AthanorPlot, AthanorEvent
from athanor_rplogger.models import PlotBridge, EventBridge


class AthanorRoleplayController(AthanorGlobalScript):
    system_name = "ROLEPLAY"

    def at_start(self):
        from django.conf import settings
        try:
            self.ndb.plot_typeclass = class_from_module(settings.BASE_PLOT_TYPECLASS,
                                                         defaultpaths=settings.TYPECLASS_PATHS)
        except Exception:
            log_trace()
            self.ndb.plot_typeclass = AthanorPlot

        try:
            self.ndb.event_typeclass = class_from_module(settings.BASE_EVENT_TYPECLASS,
                                                         defaultpaths=settings.TYPECLASS_PATHS)
        except Exception:
            log_trace()
            self.ndb.event_typeclass = AthanorEvent

    def plots(self):
        return AthanorPlot.objects.filter_family().order_by('plot_bridge__id')

    def events(self):
        return AthanorEvent.objects.filter_family().order_by('event_bridge__id')
