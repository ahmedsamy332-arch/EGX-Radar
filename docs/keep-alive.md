# Streamlit keep-alive workflow

`Keep Streamlit App Alive` sends a best-effort HTTP request to the existing
Streamlit app URL. Its schedule remains `0 0 */3 * *`: 00:00 UTC on calendar days
1, 4, 7, ..., 31 where those dates exist. This pattern restarts each month; it is
not a fixed 72-hour interval. GitHub runs schedules from the default branch
(`main`) and may delay or drop scheduled runs during periods of high load.

## Why the schedule stopped

On November 6, 2026, the GitHub API reported workflow `311286163` as
`disabled_inactivity`. The latest commit on `main` was from September 4, and the
last scheduled run, on November 4, completed successfully. GitHub automatically
disables scheduled workflows in public repositories after 60 days without
repository activity. Successful scheduled pings do not prevent this disablement.

The cron expression is valid. The prepared change preserves it and adds bounded
requests, retries for transient failures, visible HTTP errors, and no GitHub token
permissions. It does not add automated commits or a self-re-enabling mechanism.

## Restore and verify

1. Merge the workflow change into `main` after review.
2. Open [the workflow's Actions page](https://github.com/ahmedsamy332-arch/EGX-Radar/actions/workflows/keep_alive.yml)
   and click **Enable workflow** if it is disabled. A YAML edit alone is not the
   same as explicitly enabling the existing schedule.
3. Choose **Run workflow** on branch `main` for a manual check. Confirm the `ping`
   job succeeds, then verify that a later run has event `schedule`.

With GitHub CLI authenticated as a user with write access, the equivalent is:

```sh
gh workflow enable keep_alive.yml --repo ahmedsamy332-arch/EGX-Radar
gh api repos/ahmedsamy332-arch/EGX-Radar/actions/workflows/keep_alive.yml --jq .state
# Expect: active
gh workflow run keep_alive.yml --ref main --repo ahmedsamy332-arch/EGX-Radar
gh run list --workflow keep_alive.yml --repo ahmedsamy332-arch/EGX-Radar --limit 5
```

The manual run checks the request; it does not prove the scheduler has resumed.
The inactivity rule still applies, so monitor GitHub's notices and re-enable the
workflow if needed after another inactive period.

## Limits

An HTTP success response does not prove that the Streamlit application is awake
or healthy. Streamlit Community Cloud can hibernate apps after 12 hours without
traffic, and waking a sleeping app may require visiting it and clicking
**Yes, get this app back up!** This three-day schedule cannot guarantee continuous
availability.

References: [GitHub enable/disable guidance](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows),
[GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[Streamlit app hibernation](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#app-hibernation).
