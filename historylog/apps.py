from django.apps import AppConfig


class HistorylogConfig(AppConfig):
    name = 'historylog'

    def ready(self):

        import historylog.signals
