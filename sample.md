# Acme Platform

**Version:** 0.3 — Q2 2026 planning cycle
**Owner:** Product team

Core platform providing user management, reporting, and notifications.
This map covers the MVP through GA releases, targeting enterprise customers
in the EU and US markets.

[Product brief](https://docs.example.com/product-brief) · [Miro board](https://miro.com/board/acme)

# Releases
## Not Planned Yet
Stories that have been identified but not yet assigned to a release.

## MVP
Core functionality required for the first public launch.
Targets [Q2 2026 milestone](https://github.com/org/repo/milestone/1).

## Beta
Invite-only beta with selected enterprise customers.
Focuses on stability, onboarding, and feedback collection.

## GA
General availability release.
Full feature set with polished UX and performance targets met.

# Personas
## Margie the Manager

- **Age:** 48
- **Location:** Suburban midwest, USA
- **Job title:** Operations Manager
- **Company size:** 200–500 employees
- **Tech level:** Low — comfortable with email and Excel, avoids unfamiliar tools
- **Device:** Primarily mobile during commute, desktop at the office

Margie manages a team of 8 and is responsible for project status reporting
to senior leadership. She needs to understand what is being built and when,
without getting lost in technical details.

**Problem she's trying to solve:** Track project progress and communicate
release timelines to her director without scheduling a meeting with the dev team.

![Margie](personas/margie.jpg){width=180px}

[Research interview transcript](https://docs.google.com/document/d/margie-interview)
[Empathy map](https://miro.com/board/margie-empathy-map)

## Dave the Developer

- **Age:** 31
- **Location:** Remote, EU
- **Job title:** Senior Software Engineer
- **Tech level:** High — API-first mindset, reads changelogs for fun
- **Device:** Desktop, multiple monitors, keyboard-driven workflow

Dave contributes to the product both as a builder and as an internal power user.
He values correctness, clear API contracts, and not being blocked by tooling.

**Problem he's trying to solve:** Understand which stories are ready to pick up,
what their acceptance criteria are, and how they relate to the broader release plan.

[LinkedIn profile](https://linkedin.com/in/dave-example)

## Nina the New User

- **Age:** 24
- **Location:** Urban, Germany
- **Job title:** Junior Marketing Analyst
- **Tech level:** Medium — uses SaaS tools daily but avoids configuration
- **Device:** Laptop, occasionally tablet

Nina has just joined her company and is onboarding onto the platform.
She needs clear guidance, forgiving error handling, and reassurance that
she hasn't broken anything.

**Problem she's trying to solve:** Get up and running quickly without
needing to ask a colleague for help every five minutes.

# Map

## User Management

### Registration

#### Create account [status:: done] [persona:: Nina the New User]
New user can register with email and password.
Includes email verification flow.
See [issue #12](https://github.com/org/repo/issues/12)

+++

#### Register via SSO [status:: in-progress] [persona:: Dave the Developer] [deadline:: 2026-04-15]
Support Google and Microsoft OAuth providers.
See [issue #34](https://github.com/org/repo/issues/34)

+++

#### Register via SAML [status:: not-started] [persona:: Margie the Manager] [deadline:: 2026-09-01]
Enterprise SAML 2.0 support for large customers.

### Authentication

#### Sign in [status:: done]
Standard email/password login with remember-me option.

+++

#### Forgot password [status:: done]
Password reset via email token.
See [issue #15](https://github.com/org/repo/issues/15)

+++

#### MFA via TOTP [status:: in-progress] [deadline:: 2026-04-30]
Time-based one-time password support (Google Authenticator, Authy).

+++

#### MFA via SMS [status:: not-started] [deadline:: 2026-09-01]

### Profile

#### View and edit profile [status:: done] [persona:: Nina the New User]

+++

#### Upload avatar [status:: blocked] [persona:: Nina the New User]
Blocked pending storage provider decision.
See [JIRA-456](https://jira.example.com/browse/JIRA-456)

+++

#### Delete account [status:: not-started] [deadline:: 2026-09-01]
Must comply with GDPR right-to-erasure requirements.
See [issue #78](https://github.com/org/repo/issues/78)

## Reporting

### Dashboard

#### View project summary [status:: done] [persona:: Margie the Manager]
High-level status cards showing release progress.

+++

#### Filter by release [status:: in-progress] [persona:: Margie the Manager] [deadline:: 2026-04-15]

+++

#### Filter by persona [status:: not-started] [deadline:: 2026-06-01]

#### Filter by status [status:: not-started] [deadline:: 2026-06-01]

### Export

#### Export to PDF [status:: in-progress] [persona:: Margie the Manager] [deadline:: 2026-04-30]
One-click PDF export of the current story map view.

+++

#### Export to CSV [status:: not-started] [persona:: Dave the Developer] [deadline:: 2026-06-01]
Machine-readable export for backlog import into Jira or GitHub.

+++

#### Export to PNG [status:: not-started] [deadline:: 2026-09-01]

## Notifications

### Email Notifications

#### Notify on story status change [status:: not-started] [persona:: Margie the Manager]

+++

#### Daily digest [status:: not-started] [persona:: Margie the Manager] [deadline:: 2026-06-01]
Optional daily summary email of changes since last digest.

+++

#### Notify on blocked stories [status:: not-started] [deadline:: 2026-09-01]
Alert assigned persona when a story is marked as blocked.

### In-app Notifications

#### Show notification badge [status:: blocked]
Blocked by front-end architecture decision on state management.
See [issue #99](https://github.com/org/repo/issues/99)

+++

#### Mark notifications as read [status:: not-started] [deadline:: 2026-06-01]

+++

#### Notification preferences [status:: not-started] [deadline:: 2026-09-01]
