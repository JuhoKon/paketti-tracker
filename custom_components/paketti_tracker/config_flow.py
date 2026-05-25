"""Config flow and options flow for Paketti Tracker."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    ACTION_ADD,
    ACTION_REMOVE,
    CONF_NAME,
    CONF_PACKAGES,
    CONF_TRACKING_ID,
    CONF_VENDOR,
    DOMAIN,
    VENDOR_NAMES,
    VENDOR_POSTI,
    VENDORS,
)


class PakettiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle initial setup of Paketti Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step — just create the config entry."""
        # Only allow a single instance.
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="Paketti Tracker",
                data={},
                options={CONF_PACKAGES: []},
            )

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> PakettiOptionsFlow:
        """Get the options flow handler."""
        return PakettiOptionsFlow(config_entry)


class PakettiOptionsFlow(OptionsFlow):
    """Handle options: add or remove tracked packages."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    @property
    def config_entry(self) -> ConfigEntry:
        """Return the config entry."""
        return self._config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show action selection: add or remove."""
        if user_input is not None:
            action = user_input.get("action")
            if action == ACTION_ADD:
                return await self.async_step_add()
            if action == ACTION_REMOVE:
                return await self.async_step_remove()

        packages = self.config_entry.options.get(CONF_PACKAGES, [])
        actions: dict[str, str] = {ACTION_ADD: "Add package"}
        if packages:
            actions[ACTION_REMOVE] = "Remove package"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Required("action"): vol.In(actions)}),
        )

    async def async_step_add(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle adding a new package."""
        errors: dict[str, str] = {}

        if user_input is not None:
            tracking_id = user_input[CONF_TRACKING_ID].strip().upper()
            vendor = user_input[CONF_VENDOR]
            name = user_input.get(CONF_NAME, "").strip() or tracking_id

            # Check for duplicates.
            packages = list(self.config_entry.options.get(CONF_PACKAGES, []))
            existing_ids = {p[CONF_TRACKING_ID] for p in packages}

            if tracking_id in existing_ids:
                errors[CONF_TRACKING_ID] = "already_tracked"
            elif not tracking_id:
                errors[CONF_TRACKING_ID] = "empty_tracking_id"
            else:
                packages.append(
                    {
                        CONF_TRACKING_ID: tracking_id,
                        CONF_VENDOR: vendor,
                        CONF_NAME: name,
                    }
                )
                return self.async_create_entry(
                    title="",
                    data={CONF_PACKAGES: packages},
                )

        vendor_options = {v: VENDOR_NAMES[v] for v in VENDORS}

        return self.async_show_form(
            step_id="add",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TRACKING_ID): str,
                    vol.Required(CONF_VENDOR, default=VENDOR_POSTI): vol.In(vendor_options),
                    vol.Optional(CONF_NAME, default=""): str,
                }
            ),
            errors=errors,
        )

    async def async_step_remove(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle removing packages."""
        packages = list(self.config_entry.options.get(CONF_PACKAGES, []))

        if user_input is not None:
            remove_ids = set(user_input.get("remove", []))
            packages = [p for p in packages if p[CONF_TRACKING_ID] not in remove_ids]
            return self.async_create_entry(
                title="",
                data={CONF_PACKAGES: packages},
            )

        # Build selection list: tracking_id -> display label.
        package_options = {
            p[CONF_TRACKING_ID]: f"{p.get(CONF_NAME, p[CONF_TRACKING_ID])} ({p[CONF_VENDOR]})"
            for p in packages
        }

        if not package_options:
            return self.async_abort(reason="no_packages")

        return self.async_show_form(
            step_id="remove",
            data_schema=vol.Schema(
                {
                    vol.Required("remove"): vol.All(vol.Coerce(list), [vol.In(package_options)]),
                }
            ),
        )
