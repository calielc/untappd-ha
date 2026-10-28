# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.3] - 2026-10-28

### Added
- Happy-hour polling: a faster interval (default 15 min, 17:00 to 01:00) with the normal interval (30 min) the rest of the day. All four values are in the options.

### Fixed
- New check-ins no longer wait up to 4 hours: the profile request skips Untappd's CDN cache.

## [0.1.2] - 2026-10-26

### Changed
- Recent check-in sensors now cover all 5 check-ins the public profile lists (was 4).

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
