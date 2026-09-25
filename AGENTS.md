# Development expectations

Design changes for upstream review and multiple users, not only this workstation.
Keep hardware-specific settings in user configuration, with neutral defaults.
Preserve existing behavior by default for optional interaction changes.
Document new controls, lifecycle limits and configuration, and test regressions
in an isolated compositor before updating the active desktop plugin.
Keep independently reviewable changes in separate commits. Never publish or
open a PR unless the user asks.
