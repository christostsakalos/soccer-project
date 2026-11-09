# Step 1 decisions

- Scope is restricted to organization, collection and audit. No Step 2 work.
- Initial repository contained Git metadata, ignore rules and an empty `env`;
  there were no scripts or CSVs to preserve or relocate.
- Use the existing Python 3.14 virtual environment explicitly. Package metadata
  supports Python 3.11+; actual compatibility is established by installation/tests.
- Default leagues/season copy the brief's illustrative scope, not an approved
  research population. Supervisor should confirm them.
- Original exports are immutable by default. Explicit replacement preserves a
  hash-verified backup. No synthetic data are placed in production folders.
- CSV header inference is provisional for external files. Native exports carry
  sidecars. Field positions and multi-level labels retain schema ambiguity.
- Missingness and dtypes describe pandas' parsing, not confirmed domain meaning.
- Library-supported categories and source availability may change independently.
  Failures must stay visible; no replacement source is silently substituted.
- Before Step 2: obtain supervisor approval of player-season versus
  player-team-season, stable ID policy, transfer-total handling, confirmed
  category availability, league/season coverage and goalkeeper treatment.
- Verified soccerdata 2026.43.0 supports standard, shooting, playing_time, keeper
  and misc. Passing, passing_types, goal_shot_creation, defense and possession
  are unsupported; requested scope stays visible in the manifest.
- Replaced the default browser/CAPTCHA transport with plain HTTP while retaining
  library parsing. On 9 November 2026 FBref returned 403 on the first request;
  stopped without retry or bypass. No datasets were created. The dataset portion
  of Step 1 remains blocked; no missingness or model findings can be inferred.
