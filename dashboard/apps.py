from django.apps import AppConfig

MODULE_NAME = "dashboard"

DEFAULT_CFG = {
    "dashboard_per_hf": False,
}


class DashboardConfig(AppConfig):
    name = MODULE_NAME

    dashboard_per_hf = None

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(DashboardConfig, field):
                setattr(DashboardConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)