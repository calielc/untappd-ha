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
| Recent check-in 1 to 4 | Beer and brewery of each of your latest check-ins, with rating, venue, time and picture as attributes (Strava-style cards) |
| Check-in (event) | Fires `new_checkin` for each new check-in |

### Beer-history statistics (optional, needs a session cookie)

| Entity | Description |
| --- | --- |
| Average rating / Average global rating | Your mean rating, and the community mean for the same beers |
| Rated beers | Beers you have rated (rating distribution as an attribute) |
| Average ABV / Average IBU | Means over your beer history |
| Unique breweries / Unique styles | Distinct counts |
| Top style / Top brewery | Most-checked-in, with the top 10 as attributes |
| Highest rated beer | Your top 5 as an attribute |
| Strongest beer | Highest ABV |
| New beers this year / last 30 days | Beers first checked in during the period |

These sensors stay empty until the first full sync finishes (about 1 to 2 minutes, one
page of 25 beers every 1.5 seconds). The history is cached on disk, refreshed from the
newest page on every update and fully re-synced once a day.
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

### Session cookie (optional)

Untappd's login page uses a CAPTCHA, so the integration cannot sign in for you. Instead:

1. Sign in to untappd.com in your browser.
2. Open developer tools → **Network**, reload, and click any `untappd.com` request.
3. Copy the **`Cookie`** request header value and paste it into the setup form. If
   requests get blocked, paste your browser's `User-Agent` header too.

When the cookie expires, Home Assistant shows a **Repair / re-authentication** prompt
where you paste a fresh one. The cookie is stored in your Home Assistant config, so treat
that config like a password store. It only works for your own account's history.

> This uses the website's own pages with your own session. It is more likely to run
> against Untappd's terms than the public-profile mode and can break whenever the site
> changes. Use it at your own risk.

### Multiple users

Add the integration once per username (Devices & Services → Untappd → **Add entry**).
Each user gets their own device, sensors, event entity and update interval. Every profile
must be public, and each one is a separate request to Untappd, so keep intervals gentle.

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
