from __future__ import annotations

from ckan import plugins
import ckan.plugins.toolkit as tk
from ckan import types

from ckanext.ap_main.types import ConfigurationItem, SectionConfig


@tk.blanket.helpers
@tk.blanket.actions
@tk.blanket.auth_functions
@tk.blanket.blueprints
@tk.blanket.validators
@tk.blanket.config_declarations
class TourPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ISignal)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "tour")

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("ap_main:collect_config_sections"): [self.collect_config_sections_subs],
            tk.signals.ckanext.signal("ap_main:collect_config_schemas"): [self.collect_config_schemas_subs],
        }

    @staticmethod
    def collect_config_sections_subs(sender: None):
        return SectionConfig(
            name="Tour",
            configs=[
                ConfigurationItem(
                    name="List of tours",
                    blueprint="tour.list",
                    info="Manage existing tours",
                ),
                ConfigurationItem(
                    name="Add tour",
                    blueprint="tour.add",
                    info="Add new tour",
                ),
                ConfigurationItem(
                    name="Settings",
                    blueprint="tour.config",
                    info="Extension settings",
                ),
            ],
        )

    @staticmethod
    def collect_config_schemas_subs(sender: None):
        return ["ckanext.tour:config_schema.yaml"]
