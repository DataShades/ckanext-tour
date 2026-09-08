from __future__ import annotations

from ckan import plugins
import ckan.plugins.toolkit as tk
from ckan import types

from ckanext.tour import config


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
        tk.add_resource("assets", "tour")

    def update_config_schema(self, schema):
        ignore_missing = tk.get_validator("ignore_missing")
        unicode_safe = tk.get_validator("unicode_safe")
        boolean_validator = tk.get_validator("boolean_validator")
        one_of = tk.get_validator("one_of")

        schema.update(
            {
                config.CONF_COLLAPSE_STEPS: [ignore_missing, boolean_validator],
                config.CONF_LAUNCHER_POSITION: [
                    ignore_missing,
                    unicode_safe,
                    one_of(list(config.LAUNCHER_POSITIONS)),
                ],
            }
        )

        return schema

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("ap_main:collect_config_sections"): [self.collect_config_sections_subs],
        }

    @staticmethod
    def collect_config_sections_subs(sender: None):
        from ckanext.ap_main.types import ConfigurationItem, SectionConfig  # noqa

        return SectionConfig(
            name="Tour",
            configs=[
                ConfigurationItem(
                    name="List of tours",
                    blueprint="tour.list",
                    info=tk._("Manage existing tours"),
                ),
                ConfigurationItem(
                    name="Add tour",
                    blueprint="tour.add",
                    info=tk._("Add new tour"),
                ),
                ConfigurationItem(
                    name="Settings",
                    blueprint="tour.config",
                    info=tk._("Extension settings"),
                ),
            ],
        )
