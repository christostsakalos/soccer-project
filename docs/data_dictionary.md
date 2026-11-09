# Data dictionary and audit interpretation

No production data existed in the initial workspace. Available fields and real
missingness cannot be described until genuine exports are collected. The generated
feature inventory is the field-level dictionary of observed schemas; labels do
not establish football definitions, units, or count/rate semantics.

| Requested category | Purpose suggested by category label | Coverage |
| --- | --- | --- |
| standard | General player statistics | Requested; verify manifest |
| shooting | Shooting statistics | Requested; verify manifest |
| passing | Passing statistics | Requested; not listed in current reference |
| passing_types | Passing types | Requested; not listed in current reference |
| goal_shot_creation | Goal/shot creation | Requested; not listed in current reference |
| defense | Defensive statistics | Requested; not listed in current reference |
| possession | Possession statistics | Requested; not listed in current reference |
| misc | Miscellaneous statistics | Requested; verify manifest |
| keeper | Goalkeeper statistics | Requested; verify manifest; keep separate |

This is requested scope, not a claim of actual coverage. The manifest separates
file presence, failed collection and unattempted categories. No unavailable
category receives a placeholder CSV.

Exact duplicates count repeated complete parsed rows beyond the first.
Candidate-key duplicates count repetitions across all detected player, team,
league, season and ID fields; they are not a validated entity definition. Missing
key values can also repeat. Names are candidate columns, never stable identities.
Unrecognized schemas have no candidate-key count. The heuristic recognizes
player/player_id/playerid, team/squad, league and season labels, case-insensitively.
Multi-level labels remain JSON arrays; duplicate labels remain distinguishable by
column position. External multi-header inference is explicitly marked for review;
unrecognized formats default to one header and require manual validation.

`aggregate_team_rows` counts recognizable team values such as `2 squads` or
`3 clubs`; absence of this marker does not prove absence of transfers or totals.
Team-summary rows and goalkeeper-specific field semantics need human inspection
against the source. Nothing is removed, combined, filled or normalized here.

Rows exported by soccerdata may represent player-team-season records, transfer
totals, or other source-specific granularity. Check stable IDs and source links
if present. Keep transfer totals and club rows visible to avoid later double
counting. No unit of analysis or outfield/goalkeeper merge policy is selected.
