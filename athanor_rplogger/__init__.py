INSTALLED_APPS = ["athanor_rplogger"]

GLOBAL_SCRIPTS = dict()

GLOBAL_SCRIPTS['roleplay'] = {
    'typeclass': 'athanor_rplogger.controllers.AthanorRoleplayController',
    'repeats': -1, 'interval': 50, 'desc': 'Event Controller for RP Logger System'
}
