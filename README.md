# Untappd for Home Assistant

Shows your [Untappd](https://untappd.com) stats and latest check-in in Home Assistant.

Untappd no longer gives out public API access without a commercial agreement, so this
integration reads your **public profile page** (`untappd.com/user/<username>`). No login
or credentials are needed.

> **Heads up:** this scrapes a web page. It can break if Untappd changes its HTML, and it
> may go against Untappd's terms of service. Use it for your own account at a low polling
> rate. This project is not affiliated with Untappd.

## Entities

| Entity | Description |
| --- | --- |
| Total check-ins | All-time check-ins |
| Unique beers | Distinct beers |
| Badges | Badges earned |
| Friends | Friend count |
| Last check-in | Timestamp, with beer, brewery, venue, rating, comment and links as attributes |
| Last beer | Name of the last beer checked in |
| Last rating | Rating on the last check-in |
| Check-in (event) | Fires `new_checkin` for each new check-in |

## Installation

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/calielc/untappd-ha` as category **Integration**.
3. Install **Untappd**, then restart Home Assistant.

### Manual

Copy `custom_components/untappd` into your config's `custom_components` folder and restart.

## Setup

Settings → Devices & Services → **Add Integration** → **Untappd**, then enter your
username. Your profile must be public.

The update interval defaults to 30 minutes (minimum 15). Change it in the integration's
options.

## Automation example

```yaml
triggers:
  - trigger: state
    entity_id: event.untappd_caliel_check_in
actions:
  - action: notify.notify
    data:
      message: >
        {{ trigger.to_state.attributes.beer }} by
        {{ trigger.to_state.attributes.brewery }}
        ({{ trigger.to_state.attributes.rating }}★)
```

## Limitations

- The profile page lists only the 5 most recent check-ins, so more than 5 between polls
  means missed events.
- Only your own public profile is read.

## License

MIT
