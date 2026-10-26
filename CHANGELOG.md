# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-10-26

### Added
- Brand icon, as required by the HACS brands check.

## [0.1.0] - 2026-10-26

### Added
- Sensors for total check-ins, unique beers, badges, friends, last check-in, last beer and last rating.
- Event entity that fires `new_checkin`.
- Config flow with username validation, and an options flow for the update interval.
- Recent check-in 1 to 4 sensors.
- Optional session-cookie mode with beer-history statistics, a disk cache, and re-authentication.
- Diagnostics.
