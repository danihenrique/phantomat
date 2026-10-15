# Development expectations

Design changes for upstream review and multiple users, not only this workstation.
Keep hardware-specific settings in user configuration, with neutral defaults.
Preserve existing behavior by default for optional interaction changes.
Document new controls, lifecycle limits and configuration, and test regressions
in an isolated compositor before updating the active desktop plugin.
Keep independently reviewable changes in separate commits. Never publish or
open a PR unless the user asks.

## Upstream synchronization

Keep this personal fork current with `https://github.com/kaolti/phantomat`
(`upstream/main`). Before maintenance, fetch upstream and inspect incoming
changes. Merge compatible upstream fixes while preserving the fork's custom
controls and behavior; do not reset the fork to upstream. Validate the affected
paths in an isolated compositor before updating the active desktop plugin.
Report conflicts or incompatible changes instead of dropping personal features.
Publication still requires an explicit user request.
