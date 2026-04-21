---
name: scoutlens-role-intelligence
description: >
  ScoutLens's authoritative domain intelligence layer for role-aware football player
  similarity search, scouting language, and tactical classification. Use this skill
  WHENEVER generating code, API responses, UI components, scouting language, feature
  engineering, clustering logic, similarity queries, radar charts, player profile pages,
  shortlist annotations, evaluation scripts, or any output touching player roles,
  positions, stats, or scouting context within the ScoutLens project. Also trigger when
  writing dissertation sections about role classification, designing evaluation
  experiments, generating test/seed data, or explaining similarity results to users.
  If the task involves a football player in any capacity — trigger this skill. This
  skill supersedes any role-related constants in CLAUDE.md where they conflict; CLAUDE.md
  remains authoritative for architecture, tech stack, and repository structure.
---

# ScoutLens Role Intelligence Engine v2.0

> **Single source of truth** for every module that touches player data — from
> `classify_roles.py` to `RadarChart.tsx` to the dissertation methodology chapter.
> CLAUDE.md handles architecture and tech stack. This file handles football intelligence.

---

## §1 — Scouting-First Similarity Philosophy

### 1.1 What "Similar" Means

Two players are similar when a scout could realistically consider one as a
replacement or alternative for the other in the same tactical system. Three
conditions must hold simultaneously:

1. **Functional role equivalence** — they perform the same tactical job on the pitch.
   A deep-lying playmaker and a ball-winning midfielder both play "CDM" on a
   teamsheet but are not substitutable. Role, not position, is the unit of comparison.

2. **Statistical profile alignment** — per-90 output across *role-relevant* dimensions
   must cluster together. Dimensions are weighted by role: a poacher's similarity is
   dominated by attacking output; a ball-playing CB's by passing and carrying.

3. **Contextual plausibility** — league strength, age trajectory, and minutes context
   must be surfaced (not hidden). Context transforms raw numbers into actionable intelligence.

### 1.2 The Scout's Evaluation Sequence

When a scout watches a match, they evaluate in this order (first 15 minutes):
1. On-ball quality — composure, first touch, technique under pressure
2. Goal-scoring threat and positioning
3. Energy and body language — positive intent on and off the ball
4. Eye toward goal — does the player look forward every time they receive?
5. Team structure — do the players maintain shape? No line-breaking gaps through the middle?

This sequence should inform UI design: the most important information on any
player card is the information a scout would assess first.

### 1.3 Common Comparison Mistakes (Prevent in Code)

| Mistake | Failure Mechanism | ScoutLens Prevention |
|---------|-------------------|---------------------|
| Comparing across incompatible roles | A target man and false nine both play "ST" but serve different tactical functions | Role-aware pre-filter before FAISS query |
| Ignoring league context | Per-90 stats inflate/deflate by league tempo and pressing intensity | League badges + league-stratified percentiles in UI |
| Misprofiling by team style | A player's role doesn't match the team's playing style, making them look worse than they are | Role classification from event data, not from team label |
| No clear recruitment identity | No specific player type targeted for the vacancy — no vision for how the signing fits the system | Dimension weight sliders let scouts define what matters |
| Raw totals instead of rates | A 3,400-minute player looks "better" than a 1,200-minute player | All features per-90 normalised (CLAUDE.md §5) |
| Single-metric shortcuts | "Most assists" ≠ best creative player | 42-feature vector across 6 balanced dimensions |
| Shared-zeroes inflation | Both players register zero in irrelevant metrics, which cosine similarity treats as agreement | Role-conditioned dimension weights dampen irrelevant features |
| Context-stripped metrics | Same action (e.g., aerial duel) means different things in different pitch zones | Role-aware pre-filtering separates offensive from defensive aerial contexts |

### 1.4 UI Design Principle: "Would I Watch This Player on Saturday?"

Every screen must answer the scout's shortlist question:
- Similarity scores alone are insufficient → show **why** via feature contribution breakdown
- First visible on any player card: **name, age, club, league, role label, minutes played**
- Percentile bars contextualised against positional peers, not the entire population
- The UI should never display "cosine similarity: 0.91" — display "91% match" with dimensional breakdown using names scouts recognise: Attacking, Creativity, Passing, Carrying, Defending, Physicality
- Radar charts must use role-relevant axes, not a fixed generic set
- The results page must communicate **dimensional contrast** as its primary visual — where the candidate matches, exceeds, and falls short

### 1.5 The Glass Box Principle

> *"No publicly available tool currently offers this combination: role-conditional
> filtering + adjustable dimension weights + per-dimension similarity decomposition
> + scouting-language explanations."*

ScoutLens occupies the gap between black-box similarity tools (Wyscout, FBref) and
academically rigorous but inaccessible systems (PlayeRank, Player Vectors). It makes
the reasoning **visible and controllable** — turning the black box into a glass box
that respects the scout's domain expertise.

When a scout queries "players similar to Rodri," the results page should show for
each recommendation a cosine decomposition: "This player is 91% similar overall —
97% on Passing, 88% on Defending, 74% on Carrying, 62% on Aerial." The scout can
then adjust dimension weights and watch rankings re-sort in real time.

This is what Brentford does internally with proprietary tools. Lee Dykes described
their 16-position taxonomy and multi-stage filtering precisely because their edge
lies in decomposing similarity into actionable dimensions rather than collapsing it
into a single score. ScoutLens makes that workflow available transparently.

### 1.6 Professional Adoption Requirements

Three things earn a professional scout's trust:

1. **Sub-5-second workflow** — from question ("Who can replace Rodri?") to ranked,
   filterable shortlist in one interaction. One search, one results page, filters on
   the side. The FAISS-backed architecture enables sub-100ms query latency — the UX
   must match that speed.

2. **Transparency that builds trust** — every recommendation comes with reasoning
   exposed. Dimension decomposition answers "why." Role label answers "is this
   functionally comparable?" League badge answers "are these numbers inflated?"
   Age flag answers "developing or declining?"

3. **Scouting-native language throughout** — the summary sentences from §8 appear
   on player cards. Percentile bars use traffic-light colouring scouts already
   understand from Wyscout and StatsBomb IQ. Export produces a one-page PDF scouting
   report that a Head of Recruitment can read without data literacy.

---

## §2 — Hierarchical Role Taxonomy

### 2.1 Three-Level Hierarchy

```
Level 1: Position Group     (7 groups — maps to pitch zones)
  └── Level 2: Functional Role  (14 archetypes — maps to tactical jobs)
        └── Level 3: Hybrid Tag   (optional — for players straddling roles)
```

### 2.2 Position Groups → Functional Roles

```python
POSITION_GROUPS: dict[str, dict] = {
    "Centre-Back": {
        "positions": ["Center Back", "Left Center Back", "Right Center Back"],
        "roles": ["Ball-Playing CB", "Aerial/Stopper CB"],
    },
    "Full-Back": {
        "positions": ["Left Back", "Right Back", "Left Wing Back", "Right Wing Back"],
        "roles": ["Attacking Full-Back", "Inverted Full-Back"],
    },
    "Defensive Midfield": {
        "positions": [
            "Left Defensive Midfield", "Center Defensive Midfield",
            "Right Defensive Midfield",
        ],
        "roles": ["Deep-Lying Playmaker", "Ball-Winning Midfielder"],
    },
    "Central Midfield": {
        "positions": [
            "Left Center Midfield", "Center Midfield", "Right Center Midfield",
        ],
        "roles": ["Box-to-Box Midfielder", "Advanced Playmaker"],
    },
    "Attacking Midfield": {
        "positions": [
            "Left Center Attacking Midfield", "Center Attacking Midfield",
            "Right Center Attacking Midfield",
        ],
        "roles": ["Advanced Playmaker"],  # shared with Central Midfield group
    },
    "Wide Forward": {
        "positions": [
            "Left Wing", "Right Wing", "Left Midfield", "Right Midfield",
        ],
        "roles": ["Inside Forward", "Touchline Winger"],
    },
    "Centre-Forward": {
        "positions": [
            "Center Forward", "Left Center Forward", "Right Center Forward",
            "Striker", "Secondary Striker",
        ],
        "roles": ["Complete Forward", "Poacher", "Target Forward", "Pressing Forward"],
    },
}
```

### 2.3 The 14 Functional Role Archetypes

---

#### ROLE 01: Ball-Playing Centre-Back

**Tactical DNA:** The "first attacker" and deepest playmaker. No longer just a
defender in modern football. Primary objective: securely transition the ball from
the defensive third into the middle third, creating advantageous situations for
teammates. Key behaviours: (a) **Breaking lines** — vertical "laser passes" bypassing
the opponent's first press line; (b) **Provoking the press ("pausa")** — dwelling on
the ball to bait a striker's press, opening space behind; (c) **Progressive carries**
— dribbling forward into open midfield to force an opponent out of position; (d)
**Quarterbacking** — 40–50 yard diagonal switches forcing the opposition to shift.

**Exemplars:** Rio Ferdinand, Alessandro Nesta, John Stones, Virgil van Dijk, William Saliba

**Signature stats:** `progressive_passes_per90`, `progressive_carries_per90`,
`passes_under_pressure_pct`, `long_passes_per90`, `switches_per90`

**Anti-features (misleading for this role):**
- `pass_completion_pct` (raw) — inflated by safe sideways passing; elite BPCBs often
  have *lower* raw completion (85–88%) because they attempt high-risk line-breaking
  passes. A 95%+ rate often suggests a "safe" defender, not a "ball-playing" one.
- `clearances_per90` — a clearance is a failure of composure for a BPCB. Modern elite
  defenders aim to collect and control under pressure, not hoof the ball away.
- `tackles_per90` — as Paolo Maldini said: "If I have to make a tackle, I have already
  made a mistake." High tackles suggest poor positioning and recovery via slide.
- `aerial_win_pct` (in isolation) — tells nothing about playmaking; many elite BPCBs
  (Martínez, Blind) are undersized but succeed through reading and body positioning.

**Confusion boundary:**

| Feature | Traditional CB | Ball-Playing CB |
|---------|---------------|----------------|
| First instinct | Safety / clear the lines | Progress the ball / break a line |
| Pass choice | Lateral (sideways) | Vertical (forward) |
| Dribbling | Rare (only if forced) | Frequent (to provoke a press) |
| Composure | Clears ball under pressure | Retains ball under pressure |
| Main goal | Clean sheet | Clean build-up |

Confused with **Deep-Lying Playmaker** when passing volume is very high. Separate by:
BPCBs have far higher `clearances_per90`, `aerial_duels_per90`, `blocks_per90`.

**Key insight:** *"A player with 40 passes at 80% accuracy where 15 were line-breaking
is 10× more valuable than a player with 80 passes at 100% accuracy that were all lateral."*

---

#### ROLE 02: Aerial / Stopper Centre-Back

**Tactical DNA:** The physical wall. Steps out aggressively into "no-man's land"
between midfield and defence. Uses body to "pin" strikers. First-contact specialist
at defensive set pieces. Acts as the "shield" for the BPCB partner — doing the dirty
work so the playmaker stays clean and finds passing lanes.

**Exemplars:** Nemanja Vidić, Pepe, Carles Puyol, Ibrahima Konaté, Gabriel Magalhães, Antonio Rüdiger

**Signature stats:** `aerial_win_pct`, `interceptions_per90`, `blocks_per90`,
`pressures_per90` (defensive third), `ball_recoveries_per90`

**Anti-features:**
- `pass_completion_pct` — may be 95% because they only pass 2 yards to their partner
- High fouls committed isn't always negative — often indicates tactical fouling

**Confusion boundary:** Confused with the **Sweeper** — the stopper goes *toward* the
ball; the sweeper drops *away* to cover space behind. Confused with **Target Forward**
on aerial stats alone — forwards have `xg_per90` and `touches_in_box_per90` in the
opponent's box; CBs have `clearances_per90` in their own box.

---

#### ROLE 03: Attacking Full-Back

**Tactical DNA:** The team's primary source of width and lateral penetration — "hidden
wingers." Overlaps the midfield, stretches the defensive line horizontally, delivers
high-quality crosses. Allows wingers to tuck inside, creating a front five in attack.

**Exemplars:** Dani Alves, Roberto Carlos, Marcelo, Trent Alexander-Arnold, Achraf Hakimi, Andy Robertson, Nuno Mendes

**Signature stats:** `key_passes_per90`, `xa_per90`, `crosses_per90`,
`progressive_carries_per90`, `carries_into_box_per90`

**Anti-features:**
- Cross completion % — high-volume crossers have inherently low % because crosses are
  low-percentage plays; low % doesn't mean bad, it means they're trying to make things happen
- `tackles_per90` — attacking FBs often defend by jockeying or recovery pace

**Confusion boundary:** Confused with **Wing-Back** — wing-backs play in 3-at-the-back
with less defensive channel responsibility. Confused with **Touchline Winger** —
separate by: FBs have higher `tackles_per90`, `interceptions_per90`, average event
location 15–20m deeper.

---

#### ROLE 04: Inverted Full-Back

**Tactical DNA:** Modern tactical invention (popularised by Guardiola). In possession,
moves internally into half-spaces or defensive midfield line, creating a "box midfield"
(3-2-2-3 shape). Provides extra central passing options and counter-attack protection.
Essentially becomes a second No. 6 in possession.

**Exemplars:** Philipp Lahm, Kyle Walker, Ben White, João Cancelo, Oleksandr Zinchenko, Jošk Gvardiol

**Signature stats:** `passes_attempted_per90`, `pass_completion_pct` (central),
`progressive_passes_per90`, `ball_receipts_per90`, `passes_under_pressure_pct`

**Anti-features:**
- `crosses_per90` — may finish with zero crosses; this is tactical instruction, not failure
- Wide interceptions — defensive work is central, not wide

**Confusion boundary:** Confused with **Defensive Full-Back** — defensive FBs stay deep
and wide to stop wingers; IFBs move forward and inside as playmakers. One is a "shield,"
the other a "pivot."

---

#### ROLE 05: Deep-Lying Playmaker (DLP / Regista)

**Tactical DNA:** The architect at the base of midfield. Dictates tempo through vision
and passing range — switching the point of attack, finding teammates between the lines.
The "metronome" who controls through volume, accuracy, and progressive distance, not
through running with the ball.

**Exemplars:** Andrea Pirlo, Xabi Alonso, Paul Scholes, Sergio Busquets, Toni Kroos, Rodri, Vitinha

**Signature stats:** `progressive_pass_distance_per90`, `passes_attempted_per90`,
`switches_per90`, `long_pass_completion_pct`, `pass_completion_pct`

**Anti-features:**
- `assists_per90` — since they play so deep, the "hockey assist" is more relevant;
  raw assists undervalue their contribution

**Confusion boundary:** Confused with **Ball-Winning Midfielder** — both play "CDM"
but DLPs defend through positioning and interception, not physical destroying.
Separate by: DLPs have dramatically higher passing volume and completion.

---

#### ROLE 06: Ball-Winning Midfielder (BWM / Destroyer)

**Tactical DNA:** The "engine room" enforcer. Hunts the ball, closes down space
aggressively, cleans up loose balls. Once they win it, plays a simple short pass to
a playmaker. Provides "steel" that allows creative players to stay forward.

**Exemplars:** Claude Makélélé, Gennaro Gattuso, Javier Mascherano, N'Golo Kanté, Casemiro

**Signature stats:** `tackles_per90`, `interceptions_per90`, `ball_recoveries_per90`,
`pressures_per90`, `pressure_success_pct`

**Anti-features:**
- `dribble_success_pct` — not paid to beat players; dribbling means out of tactical zone

**Confusion boundary:** Confused with **Box-to-Box Midfielder** — BWMs stay disciplined
in defensive zone; they don't crash the opponent's box. Separate by: B2B has
significantly higher `xg_per90`, `touches_in_box_per90`.

---

#### ROLE 07: Box-to-Box Midfielder (B2B)

**Tactical DNA:** The most physically demanding role. All-rounders who contribute in
both penalty areas. Help defence build out, transition through the middle, and make
"late runs" into the box. Require elite stamina and balance of defensive and offensive IQ.

**Exemplars:** Steven Gerrard, Roy Keane, Patrick Vieira, Jude Bellingham, Pedri, Declan Rice (evolved)

**Signature stats:** `progressive_carries_per90`, `touches_in_box_per90`,
`pressures_per90`, `ball_recoveries_per90`, `ground_duels_per90`

**Anti-features:**
- `pass_completion_pct` — lower than DLP because they play in congested central areas
  and take risks; expected, not a flaw
- Defined by **breadth across all dimensions**, not spikes. Absence of extreme weakness
  matters more than extreme strength.

**Confusion boundary:** Hardest role to separate cleanly. The **unique identifier:**
B2B is the only midfield role with above-median values in BOTH `pressures_per90` AND
`touches_in_box_per90`.

---

#### ROLE 08: Advanced Playmaker (CAM / Trequartista)

**Tactical DNA:** Creative hub in the "hole" (Zone 14) between opponent's midfield and
defence. Tasked with the "final ball." Elite vision, technical flair, ability to turn
in tight spaces to unlock a low block. Primary source of creativity and "magic."

**Exemplars:** Zinedine Zidane, Mesut Özil, Kevin De Bruyne, Bruno Fernandes, Jamal Musiala

**Signature stats:** `xa_per90`, `through_balls_per90`, `key_passes_per90`,
`passes_into_box_per90`, `dribbles_attempted_per90`

**Anti-features:**
- `tackles_per90`, `interceptions_per90` — judging a No. 10 on defensive output is
  irrelevant; value measured purely by offensive threat

**Confusion boundary:** Confused with **False Nine** — an AM starts in midfield and
moves up; a F9 starts as striker and drops down.

---

#### ROLE 09: Inside Forward / Wide Playmaker

**Tactical DNA:** Starts wide but operates primarily in the half-space between the
opponent's full-back and centre-back. Goal-oriented diagonal runner. Relies on
"inverted" feet (right-footer on the left) to open shooting and passing angles.
The Wide Playmaker variation prioritises creative passing over finishing, drifting
into the No. 10 zone.

**Exemplars:** Cristiano Ronaldo, Arjen Robben, Mohamed Salah, Lionel Messi, Vinícius Júnior, Bukayo Saka, Michael Olise

**Signature stats:** `progressive_carries_per90`, `touches_in_box_per90`,
`npxg_per90`, `shots_per90`, `dribbles_attempted_per90`

**Anti-features:**
- `crosses_per90` — rarely aim to whip balls into the box; low cross volume is the
  defining separation from a touchline winger

**Confusion boundary:** THE key separator from **Touchline Winger**: inside forwards
have high `xg_per90` + `shots_per90` with low `crosses_per90`; touchline wingers
have the inverse. Confused with **Inverted Winger** — inverted wingers remain wide
and cut in late; inside forwards act as a second/third striker.

---

#### ROLE 10: Touchline Winger / Traditional Winger

**Tactical DNA:** Vertical specialist providing maximum width. Hugs the touchline to
stretch the defensive line horizontally. Explosive pace, 1v1 dribbling to the byline,
delivery into the box. Plays on the side of their natural foot (right-footed on the
right) for immediate first-time crosses.

**Exemplars:** Joaquín, Ryan Giggs, Jesús Navas, Gareth Bale (early Spurs). Modern:
Nico Williams, Jeremy Doku, Kingsley Coman

**Signature stats:** `crosses_per90`, `dribbles_attempted_per90` (down the line),
`progressive_carries_per90`, `key_passes_per90` (from wide), `xa_per90`

**Anti-features:**
- `shots_on_target_per90` — their job isn't to score; high shot volume often means
  abandoning their tactical post

**Confusion boundary:** Confused with **Wing-Back** — wing-backs have significant
defensive responsibilities and arrive in the final third late; wingers start there.

---

#### ROLE 11: Complete Forward / Link-Up Striker

**Tactical DNA:** The "Swiss Army Knife." Physical strength to lead the line, technical
skill to drop deep and link play, clinical finishing. Acts as a fulcrum: holds up under
pressure for midfield runners, but also has mobility for channel runs. A playmaker in
a No. 9's body.

**Exemplars:** Karim Benzema, Thierry Henry, Zlatan Ibrahimović, Luis Suárez, Wayne Rooney.
Modern: Harry Kane, Robert Lewandowski

**Signature stats:** `xg_per90`, `key_passes_per90`, `progressive_passes_per90`,
`aerial_win_pct` (hold-up), `ball_receipts_per90` (midfield third)

**Anti-features:**
- `shots_per90` (total) — may have fewer shots than a poacher because they're creating;
  low shot count means playing the role correctly

**Confusion boundary:** Confused with **Target Man** — target men limited to aerial
dominance and flick-ons; complete forwards have mobility and technical floor of a
midfielder. Confused with **False Nine** — a F9 creates a vacuum; a CF maintains box presence.

**Key insight:** *"The rarest profile in football — if the data and the eye test both
confirm it, act fast because every club in Europe wants this player."*

---

#### ROLE 12: Poacher / Penalty-Box Striker

**Tactical DNA:** Specialist of efficiency and spatial awareness. Lives on the shoulder
of the last defender using blind-side runs and elite anticipation. May be invisible for
80 minutes but requires one or two touches to decide a match.

**Exemplars:** Filippo Inzaghi, Ruud van Nistelrooy, Erling Haaland, Jamie Vardy, Victor Osimhen

**Signature stats:** `goals_per90`, `xg_per_shot`, `touches_in_box_per90` (% of total),
`shots_on_target_per90`, `xg_per90`

**Anti-features:**
- `pass_completion_pct`, `progressive_passes_per90` — paid to finish moves, not start them

**Confusion boundary:** Confused with **Target Man** — target men use physical strength
to hold up for others; poachers use speed and guile. A poacher almost never moves wider
than the width of the goalposts.

**Key insight:** *"His radar will look empty outside the Attacking dimension — that's
fine, because finishing is his only job and he does it ruthlessly."*

---

#### ROLE 13: Target Forward / Aerial Striker

**Tactical DNA:** Physical focal point acting as a "backboard." Uses height,
upper-body strength, and jumping ability to win direct balls. Occupies both
centre-backs, creating space for teammates. Most important job: ball retention
through knock-downs and flick-ons to runners behind.

**Exemplars:** Didier Drogba, Luca Toni, Olivier Giroud, Erling Haaland, Benjamin Šeško,
Jean-Philippe Mateta

**Signature stats:** `aerial_duels_per90`, `aerial_win_pct`, `fouls_won_per90`,
`ball_receipts_per90`, `xg_per90`

**Anti-features:**
- `dribbles_attempted_per90` — target forwards are the destination, not the carrier
- Distance covered — high mileage is often tactically detrimental for this role

**Confusion boundary:** Confused with **Poacher** — poachers may be tall but never
contest long balls. Confused with **Deep-Lying Forward** — DLFs link via feet; TFs
link via chest-downs and headers.

---

#### ROLE 14: Pressing Forward / False Nine

**Tactical DNA:** Two merged specialisms. The **False Nine** vacates the striker
position, dropping into the hole to create midfield overloads and force CB dilemmas.
The **Pressing Forward** spearheads defensive shape — harassing ball-carriers,
screening passes, triggering high press traps. Modern systems merge both: playmaker
on the ball, defensive engine off it.

**Exemplars:** Lionel Messi (F9), Roberto Firmino, Francesco Totti, Wayne Rooney,
Antoine Griezmann, Thomas Müller, Harry Kane

**Signature stats:** `pressures_per90` (high/possession-adjusted), `ball_recoveries_per90`,
`xa_per90`, `progressive_carries_per90`, `key_passes_per90`

**Anti-features:**
- `goals_per90` — a false nine may have low goals because their job is creating space
  for wingers; judging solely on goals ignores tactical value
- `shots_per90` — spending so much time in midfield means naturally fewer shots

**Confusion boundary:** Confused with **Deep-Lying Forward** — DLF holds up back-to-goal
in a front two; F9 is typically a lone striker who turns and faces goal. Confused with
**Complete Forward** — separate by: pressing forwards have significantly higher
`pressures_per90` and `ball_recoveries_per90`.

---

## §3 — Dimension Weight Profiles per Role

Applied as **defaults** when `role_filter=True` and the user has not adjusted sliders.
Values sourced from the completed domain knowledge template (Section E) with full
justifications per role.

```python
ROLE_DIMENSION_WEIGHTS: dict[str, dict[str, float]] = {
    #                              ATK    CRE    PAS    CAR    DEF    AER
    "Ball-Playing CB":           {"ATK": 0.2, "CRE": 0.3, "PAS": 2.0, "CAR": 1.2, "DEF": 1.8, "AER": 1.0},
    "Aerial/Stopper CB":         {"ATK": 0.1, "CRE": 0.1, "PAS": 0.5, "CAR": 0.3, "DEF": 2.0, "AER": 2.0},
    "Attacking Full-Back":       {"ATK": 0.6, "CRE": 1.7, "PAS": 1.2, "CAR": 1.5, "DEF": 1.2, "AER": 0.4},
    "Inverted Full-Back":        {"ATK": 0.3, "CRE": 1.0, "PAS": 1.8, "CAR": 1.0, "DEF": 1.4, "AER": 0.3},
    "Deep-Lying Playmaker":      {"ATK": 0.2, "CRE": 0.8, "PAS": 2.0, "CAR": 0.8, "DEF": 1.2, "AER": 0.5},
    "Ball-Winning Midfielder":   {"ATK": 0.2, "CRE": 0.2, "PAS": 1.0, "CAR": 0.6, "DEF": 2.0, "AER": 1.5},
    "Box-to-Box Midfielder":     {"ATK": 0.8, "CRE": 0.8, "PAS": 1.3, "CAR": 1.4, "DEF": 1.4, "AER": 1.0},
    "Advanced Playmaker":        {"ATK": 1.2, "CRE": 2.0, "PAS": 1.6, "CAR": 1.4, "DEF": 0.3, "AER": 0.2},
    "Inside Forward":            {"ATK": 2.0, "CRE": 1.4, "PAS": 0.7, "CAR": 1.7, "DEF": 0.3, "AER": 0.3},
    "Touchline Winger":          {"ATK": 1.0, "CRE": 1.8, "PAS": 0.7, "CAR": 2.0, "DEF": 0.4, "AER": 0.2},
    "Complete Forward":          {"ATK": 2.0, "CRE": 1.3, "PAS": 0.8, "CAR": 1.0, "DEF": 0.6, "AER": 1.5},
    "Poacher":                   {"ATK": 2.0, "CRE": 0.3, "PAS": 0.2, "CAR": 0.2, "DEF": 0.1, "AER": 1.0},
    "Target Forward":            {"ATK": 1.6, "CRE": 0.8, "PAS": 0.5, "CAR": 0.3, "DEF": 0.5, "AER": 2.0},
    "Pressing Forward":          {"ATK": 1.3, "CRE": 0.7, "PAS": 0.5, "CAR": 1.0, "DEF": 1.7, "AER": 1.2},
}

DIMENSION_KEY_MAP = {
    "ATK": "Attacking", "CRE": "Chance Creation", "PAS": "Passing",
    "CAR": "Carrying", "DEF": "Defending", "AER": "Aerial/Physical",
}
```

Weight justification highlights:
- **Ball-Playing CB:** PAS 2.0 is the entire differentiator; DEF remains 1.8 because
  the "ball-playing" prefix adds passing, it does not subtract defending
- **Poacher:** ATK 2.0, everything else near-zero; weighting non-attacking dimensions
  would match poachers with players doing fundamentally different jobs
- **Box-to-Box Midfielder:** Most balanced profile (no dimension above 1.4); the B2B is
  defined by breadth, and balance IS the diagnostic signal
- **Pressing Forward:** DEF 1.7 is the role's differentiator — pressures and high
  recoveries distinguish them from other forward types

---

## §4 — Incompatible Comparison Pairs (Hard Blocks)

These role pairs must **never** appear as similarity results. Each fails for one or
more of three structural reasons identified in the domain template:
1. **Shared-zeroes inflation** — both register zero in irrelevant metrics, interpreted
   as agreement
2. **Context-stripped metrics** — same action means different football in different zones
3. **Complementary output illusion** — similar aggregate output via completely different mechanisms

```python
INCOMPATIBLE_ROLE_PAIRS: set[frozenset[str]] = {
    # CB vs CF — aerial duels spatially inverted (own box vs opponent box)
    frozenset({"Aerial/Stopper CB", "Poacher"}),
    frozenset({"Aerial/Stopper CB", "Complete Forward"}),
    frozenset({"Aerial/Stopper CB", "Pressing Forward"}),
    frozenset({"Ball-Playing CB", "Poacher"}),
    frozenset({"Ball-Playing CB", "Target Forward"}),
    # CB vs CAM — passing context fundamentally different
    frozenset({"Aerial/Stopper CB", "Advanced Playmaker"}),
    frozenset({"Ball-Playing CB", "Inside Forward"}),
    # DM vs Winger — entirely different spatial territories
    frozenset({"Deep-Lying Playmaker", "Touchline Winger"}),
    frozenset({"Deep-Lying Playmaker", "Poacher"}),
    frozenset({"Ball-Winning Midfielder", "Inside Forward"}),
    frozenset({"Ball-Winning Midfielder", "Poacher"}),
    frozenset({"Ball-Winning Midfielder", "Touchline Winger"}),
    # FB vs CF — complementary output illusion
    frozenset({"Attacking Full-Back", "Target Forward"}),
    frozenset({"Attacking Full-Back", "Poacher"}),
    frozenset({"Inverted Full-Back", "Poacher"}),
    # Touchline Winger vs Stopper CB
    frozenset({"Touchline Winger", "Aerial/Stopper CB"}),
}
```

---

## §5 — Tactically Substitutable Pairs (Soft Links)

Statistically distant but tactically substitutable — surface as "alternative role"
suggestions. These represent real **market inefficiencies** that clubs exploit.

```python
SUBSTITUTABLE_ROLE_PAIRS: list[dict] = [
    {
        "pair": ("Inverted Full-Back", "Deep-Lying Playmaker"),
        "reason": "In possession the IFB becomes a second No. 6. Zinchenko at Arsenal, "
                  "Cancelo at City. Key shared attributes: press resistance, short passing "
                  "under pressure, positional discipline in the half-space.",
        "scouting_tip": "When seeking an IFB, scout ball-playing DMs with lateral mobility. "
                        "When replacing a No. 6, certain IFBs are viable — and cheaper.",
    },
    {
        "pair": ("Pressing Forward", "Advanced Playmaker"),
        "reason": "Both operate between opposition midfield and defence. Firmino converted "
                  "from Hoffenheim No. 10 to Liverpool false 9 — skill set unchanged, only "
                  "starting position moved. Guardiola deployed De Bruyne, Foden, Gündoğan as F9s.",
        "scouting_tip": "Losing a false 9? Scout No. 10s with high pressing intensity. "
                        "Seeking a creative No. 10? Check deep-lying forwards.",
    },
    {
        "pair": ("Ball-Playing CB", "Deep-Lying Playmaker"),
        "reason": "Both serve as the deepest outfield passer. Stones stepped alongside Rodri "
                  "in 2022-23; Mascherano moved from DM to CB at Barcelona; Busquets regularly "
                  "dropped into left CB.",
        "scouting_tip": "Clubs seeking a BPCB for possession: holding midfielders with aerial "
                        "ability are viable and cheaper — the Brentford model.",
    },
    {
        "pair": ("Attacking Full-Back", "Touchline Winger"),
        "reason": "In 3-at-the-back, the WB covers the entire flank — functionally identical "
                  "to a winger who tracks back. Hakimi at Inter was statistically "
                  "indistinguishable from a right winger in attacking output.",
        "scouting_tip": "Switching to back three? Scout wingers with defensive work rate. "
                        "Wing-backs in back-three systems are undervalued as wide attackers.",
    },
    {
        "pair": ("Pressing Forward", "Box-to-Box Midfielder"),
        "reason": "In high-press systems the pressing forward's primary job is disruption — "
                  "same actions a B2B performs from a different starting position. Red Bull's "
                  "multi-club model exploits this: players shift between forward and midfield.",
        "scouting_tip": "Shared evaluation: PPDA contribution, high recoveries, sprint distance.",
    },
    {
        "pair": ("Inside Forward", "Advanced Playmaker"),
        "reason": "Both converge on the half-space 20–30m from goal. Salah's average touch "
                  "position is closer to a second striker than a winger. Inverted wingers in "
                  "weaker leagues are priced as 'wingers' but functionally operate as "
                  "second strikers — a market inefficiency.",
        "scouting_tip": "Seeking a second striker? Scout inside forwards at winger prices.",
    },
    {
        "pair": ("Complete Forward", "Pressing Forward"),
        "reason": "Both drop deep and create. Difference is pressing intensity vs goal-scoring "
                  "emphasis, which varies by match context.",
        "scouting_tip": "Evaluate pressures and high recoveries alongside xG to separate them.",
    },
]
```

---

## §6 — Hybrid Player Handling

### 6.1 Dual-Label Assignment
When silhouette score < 0.15 or second-closest centroid within defined margin,
assign both labels with confidence percentages:
> "Trent Alexander-Arnold — Attacking Full-Back (54%) / Advanced Playmaker (46%)"

### 6.2 Multi-Role FAISS Indexing
Hybrid players indexed in **multiple** per-role sub-indices with confidence weights.
A 46%-confidence Advanced Playmaker appears in AM searches but ranked lower than pure 10s.

### 6.3 Role Fluidity Detection
Compute feature vectors **per match**. If standard deviation of key features (e.g.,
progressive pass distance) across matches exceeds a threshold, flag as "role-fluid."
Phase-proxy features: ball receipt location (deep vs advanced), carry origin zones,
pressure locations approximate in-possession vs out-of-possession behaviour.

### 6.4 User-Driven Role Override
UI toggle allowing scouts to manually select which role lens to apply. A scout who
knows Stones plays as a midfielder in possession can override the CB classification.
This is the simplest and most scouting-aligned solution.

### 6.5 Known Chameleons (Validation Test Cases)

| Player | Why They Defy Classification | Expected Behaviour |
|--------|------------------------------|-------------------|
| Trent Alexander-Arnold | Output resembles Advanced Playmaker; defensive metrics too low for FB | Dual label: Attacking FB / Advanced Playmaker |
| Joshua Kimmich | Elite at RB, single pivot, and B2B across seasons | High match-level variance flag |
| John Stones (2022-23) | In-possession = No. 6; out-of-possession = CB | Dual label: Ball-Playing CB / DLP |
| Antoine Griezmann | Second striker + No. 10 + pressing forward within single matches | Multi-role distribution vector |
| Jude Bellingham (2023-24) | Started as No. 8, finished as second striker | Dual label: B2B / Inside Forward |
| Philipp Lahm | World-class at RB, LB, and CM | High match-level variance flag |

**Code requirement:** Unit tests must verify these players receive dual labels or
cross cluster boundaries when silhouette thresholds are applied.

**UI requirement:** Surface ambiguity as a feature, not a defect. A "role profile"
card showing proximity to multiple centroids. Flag multi-role players as having
broader replacement candidacy — they appear in similarity results for multiple roles.

---

## §7 — Dynamic Radar Chart Axes per Role

```python
ROLE_RADAR_AXES: dict[str, list[str]] = {
    "Ball-Playing CB": [
        "progressive_passes_per90", "passes_under_pressure_pct", "long_passes_per90",
        "progressive_carries_per90", "switches_per90",
        "tackles_per90", "aerial_win_pct", "interceptions_per90",
    ],
    "Aerial/Stopper CB": [
        "aerial_duels_per90", "aerial_win_pct", "clearances_per90",
        "blocks_per90", "interceptions_per90", "tackles_per90",
        "ball_recoveries_per90", "ground_duel_win_pct",
    ],
    "Attacking Full-Back": [
        "crosses_per90", "key_passes_per90", "xa_per90",
        "progressive_carries_per90", "carries_into_box_per90",
        "tackles_per90", "dribbles_attempted_per90", "pass_completion_pct",
    ],
    "Inverted Full-Back": [
        "passes_attempted_per90", "pass_completion_pct", "progressive_passes_per90",
        "passes_under_pressure_pct", "ball_receipts_per90",
        "tackles_per90", "interceptions_per90", "progressive_carries_per90",
    ],
    "Deep-Lying Playmaker": [
        "passes_attempted_per90", "pass_completion_pct", "progressive_pass_distance_per90",
        "long_passes_per90", "switches_per90", "passes_under_pressure_pct",
        "ball_recoveries_per90", "interceptions_per90",
    ],
    "Ball-Winning Midfielder": [
        "pressures_per90", "pressure_success_pct", "tackles_per90",
        "tackle_success_pct", "interceptions_per90", "ball_recoveries_per90",
        "ground_duels_per90", "ground_duel_win_pct",
    ],
    "Box-to-Box Midfielder": [
        "progressive_carries_per90", "pressures_per90", "ball_recoveries_per90",
        "touches_in_box_per90", "tackles_per90", "key_passes_per90",
        "ground_duels_per90", "xg_per90",
    ],
    "Advanced Playmaker": [
        "xa_per90", "key_passes_per90", "through_balls_per90",
        "passes_into_box_per90", "progressive_passes_per90",
        "xg_per90", "dribble_success_pct", "pass_completion_pct",
    ],
    "Inside Forward": [
        "xg_per90", "npxg_per90", "shots_per90",
        "dribbles_attempted_per90", "progressive_carries_per90",
        "key_passes_per90", "xg_per_shot", "carries_into_box_per90",
    ],
    "Touchline Winger": [
        "crosses_per90", "progressive_carries_per90", "carry_distance_per90",
        "dribbles_attempted_per90", "key_passes_per90",
        "dribble_success_pct", "xa_per90", "progressive_carry_distance_per90",
    ],
    "Complete Forward": [
        "xg_per90", "xa_per90", "key_passes_per90", "ball_receipts_per90",
        "progressive_passes_per90", "shots_on_target_per90",
        "touches_in_box_per90", "aerial_win_pct",
    ],
    "Poacher": [
        "goals_per90", "xg_per90", "xg_per_shot", "shots_on_target_per90",
        "npxg_per90", "touches_in_box_per90",
        "shots_per90", "aerial_duels_per90",
    ],
    "Target Forward": [
        "aerial_duels_per90", "aerial_win_pct", "fouls_won_per90",
        "xg_per90", "ball_receipts_per90", "touches_in_box_per90",
        "shots_on_target_per90", "ground_duels_per90",
    ],
    "Pressing Forward": [
        "pressures_per90", "ball_recoveries_per90", "xa_per90",
        "key_passes_per90", "progressive_carries_per90",
        "xg_per90", "pressure_success_pct", "touches_in_box_per90",
    ],
}
```

---

## §8 — Scouting Report Language

### 8.1 Role Summary Templates

These appear at the top of player profile cards and in shortlist annotations.

```python
ROLE_SUMMARY_TEMPLATES: dict[str, str] = {
    "Ball-Playing CB": (
        "Composed, progressive centre-half who drives build-up through vertical "
        "passing from deep; comfortable carrying under pressure but must prove "
        "he can defend the box against physical strikers at the highest level."
    ),
    "Aerial/Stopper CB": (
        "Dominant, aggressive centre-half who wins the physical battle and commands "
        "his area aerially; limited on the ball — best paired with a progressive "
        "partner who handles distribution."
    ),
    "Attacking Full-Back": (
        "Dynamic, overlapping full-back who delivers quality from wide areas and "
        "provides genuine final-third output; defensive positioning can be exposed "
        "when caught high, so needs midfield cover in transition."
    ),
    "Inverted Full-Back": (
        "Technically secure full-back who tucks inside to operate as a second pivot "
        "in possession; more midfielder than traditional defender — evaluate his "
        "press resistance and central passing under pressure, not his crossing."
    ),
    "Deep-Lying Playmaker": (
        "Metronome at the base of midfield who dictates tempo, switches play, and "
        "controls the rhythm of the match; doesn't win physical battles — needs "
        "athletic partners to screen and protect him."
    ),
    "Ball-Winning Midfielder": (
        "Aggressive, high-energy disruptor who wins the ball back and recycles "
        "possession simply; limited creative output — not the player to unlock deep "
        "blocks, but invaluable against teams that want to play through the middle."
    ),
    "Box-to-Box Midfielder": (
        "High-capacity athlete who contributes at both ends and covers enormous "
        "distances; the question is whether he's genuinely good at anything rather "
        "than average at everything — check his output quality, not just volume."
    ),
    "Advanced Playmaker": (
        "Creative fulcrum who unlocks defences through vision, weight of pass, and "
        "movement between the lines; luxury player if the system doesn't protect "
        "him — needs a disciplined midfield behind him to function."
    ),
    "Inside Forward": (
        "Goal-threatening wide attacker who cuts inside to shoot and combines in "
        "the half-space; evaluate his output from central zones rather than "
        "traditional winger metrics — his xG matters more than his crossing."
    ),
    "Touchline Winger": (
        "Traditional wide player who beats his man on the outside and delivers "
        "quality into the box; specialist profile — stretches the pitch horizontally "
        "but contributes little defensively or centrally."
    ),
    "Complete Forward": (
        "All-round centre-forward who scores, creates, holds up, wins headers, and "
        "links the play; the rarest profile in football — if the data and the eye "
        "test both confirm it, act fast because every club in Europe wants this player."
    ),
    "Poacher": (
        "Instinctive penalty-box finisher who lives off scraps and converts "
        "half-chances; his radar will look empty outside the Attacking dimension — "
        "that's fine, because finishing is his only job and he does it ruthlessly."
    ),
    "Target Forward": (
        "Physically imposing aerial focal point who wins knockdowns, occupies "
        "centre-halves, and provides a direct route to goal; limited mobility — "
        "suited to systems that cross frequently and play direct."
    ),
    "Pressing Forward": (
        "High-intensity forward who leads the press, wins the ball in dangerous "
        "areas, and sets the defensive tone from the front; may not top the scoring "
        "charts but his off-ball work enables the entire attacking structure — "
        "evaluate pressures and high recoveries, not just goals."
    ),
}
```

### 8.2 Scouting Descriptor Vocabulary

Used for auto-generated scouting notes, UI chip labels, and shortlist annotations.

```python
SCOUTING_DESCRIPTORS = {
    "positive": {
        "physical": [
            "good engine", "covers the ground well", "explosive over short distances",
            "deceptive pace", "strong in the challenge", "robust frame",
            "tireless work rate", "quick feet in tight areas",
            "physically mature for his age", "clean striker of the ball",
        ],
        "technical": [
            "press-resistant", "comfortable on the half-turn",
            "silky touch under pressure", "two-footed", "clean technique",
            "excellent first touch", "composed in possession",
            "progressive passer", "picks the right pass",
            "weight of pass is outstanding", "disguises his intentions well",
            "plays with his head up",
        ],
        "tactical": [
            "clever movement", "reads the game well", "intelligent runner",
            "always scanning", "positional discipline", "anticipates danger",
            "manipulates space", "finds pockets",
            "understands pressing triggers",
            "knows when to hold and when to release",
            "switches play instinctively", "one step ahead mentally",
            "coachable", "leadership presence", "organises the backline vocally",
        ],
        "attacking": [
            "arrives late in the box", "clinical finisher",
            "ice-cold in front of goal", "creates something from nothing",
            "unpredictable in the final third", "goal threat from distance",
            "instinctive poacher", "stretches the defence with his movement",
        ],
        "defensive": [
            "wins his individual battles", "dominant in the air",
            "recovery pace to cover", "reads the passing lane",
            "aggressive without fouling", "front-foot defender",
            "commanding presence", "excellent at covering the channel",
        ],
    },
    "concern": {
        "physical": [
            "lacks a yard of pace", "leggy over long distances",
            "struggles physically against stronger opponents", "injury-prone",
            "doesn't have the engine for a high press",
            "heavy-legged in the final 20 minutes", "one-paced",
        ],
        "technical": [
            "heavy first touch", "poor under pressure",
            "limited with his weaker foot", "ball gets stuck under his feet",
            "lacks final ball", "decision-making lets him down in the final third",
            "over-dribbles", "tries too much", "gives the ball away cheaply",
            "sloppy in possession", "technique deteriorates under press",
        ],
        "tactical": [
            "ball-watcher", "switches off at set pieces",
            "poor positional discipline", "doesn't track runners",
            "naive in 1v1 defending", "struggles in transition",
            "leaves his partner exposed", "doesn't adjust to the game state",
            "goes missing in big games", "needs the game to come to him",
            "concentration lapses",
        ],
    },
    "contextual": {
        "system": [
            "system player", "product of a possession-heavy environment",
            "Guardiola-type profile", "gegenpressing forward",
            "suited to a low block", "needs the team built around him",
            "better in a two-striker system", "thrives with runners ahead of him",
        ],
        "spatial": [
            "set-piece specialist", "left-foot bias", "right-sided only",
            "plays on the shoulder", "deep-lying",
            "inverts into central areas", "hugs the touchline",
            "drops between the lines", "operates in the half-space",
        ],
        "development": [
            "raw but projectable", "late developer",
            "stats inflated by league context", "big fish in a small pond",
            "needs to prove it at a higher level",
            "Ligue 1 numbers — apply translation discount",
            "benefits from playing alongside elite teammate",
            "stats don't tell the full story — watch the tape",
        ],
    },
}
```

---

## §9 — League Context Intelligence

Key data for dissertation Chapter 2 and cross-league similarity warnings:

- La Liga pressing intensity: 9.9 PPDA (highest); Ligue 1: 11.82 (lowest)
- Premier League: 15.9 high turnovers per match (highest); Serie A: 13.5
- Bundesliga chance conversion: 12.2%; La Liga: 10.7%
- Bundesliga: most shots and long balls; Serie A: fewer touches, lower pass accuracy
- Ligue 1→PL translation: defenders and midfielders translate better than attackers

**Adjustment methodology hierarchy:**
1. Possession-adjusted defensive stats (PAdj) — Ted Knutson / StatsBomb
2. Club-level match adjustment — Analytics FC ClubStrength+
3. Gemini Plus-Minus with league translation coefficients (academic gold standard)

**ScoutLens implementation:** League-stratified percentiles + league badge on UI +
contextual warning on cross-league results.

---

## §10 — Age-Adjusted Interpretation

Position-specific peaks (GAM analysis, Europe's top five, 2014/15–2020/21):
- Wingers: ~26.1 years (earliest), decline to 50% by ~31 (fastest)
- Centre-backs: ~28+ years, decline to 50% by ~35.2 (slowest outfield)
- Strikers: ~28.5 years; Overall average: ~27.4 years

Skill-specific curves:
- Dribbling: continuous decline from late teens (1.6/90 at 20–21 → 1.1 at 26)
- Sprint speed: peaks ~25.7, significant decline after 32
- Passing accuracy: improves with age, especially for CMs and CBs
- Game intelligence: develops well into the 30s

**ScoutLens implementation:** Age as contextual flag, never compare raw output between
age brackets without surfacing the context.

---

## §11 — Clustering Validation Rules

1. **Centroid fingerprint matching:** z-score profile per cluster; match to roles by
   checking signature stats show z > +0.5 and anti-features show z < -0.5
2. **Position sanity check:** ≥60% of cluster members from expected position group
3. **Minimum cluster size:** no cluster below 30 players; merge small ones
4. **Exemplar spot-check:** at least one named exemplar per role in expected cluster
5. **Chameleon verification:** §6.5 players should receive dual labels or ambiguous assignment

---

## §12 — Similarity Engine Rules

### 12.1 Default (role_filter=True)
1. Identify query player's role → apply dimension weights (§3)
2. Search within role's FAISS sub-index
3. Post-filter: league, age, minutes
4. Return top-k with per-feature contribution breakdown

### 12.2 Expanded (role_filter=False)
1. Global FAISS index, uniform weights (all 1.0)
2. Flag incompatible pair results (§4) with warning badge
3. Surface substitutable role suggestions (§5) when results cross role boundaries

### 12.3 Custom Weights (user sliders)
1. User adjusts 6 sliders (0.0–2.0), replaces role defaults
2. Re-normalise to sum 6.0, search per 12.1 or 12.2

### 12.4 Formation Context (COULD-HAVE)
Store formation from StatsBomb lineups as contextual badge. Optional filter:
"Show Wide Attackers in back-three systems."

---

## §13 — Updated Constants (Supersedes CLAUDE.md ROLE_LABELS)

```python
ROLE_LABELS: list[str] = [
    "Ball-Playing CB", "Aerial/Stopper CB",
    "Attacking Full-Back", "Inverted Full-Back",
    "Deep-Lying Playmaker", "Ball-Winning Midfielder",
    "Box-to-Box Midfielder", "Advanced Playmaker",
    "Inside Forward", "Touchline Winger",
    "Complete Forward", "Poacher", "Target Forward", "Pressing Forward",
]
ROLE_COUNT = 14
TARGET_CLUSTER_RANGE = (12, 16)
```

---

## §14 — Dissertation Section Mapping

| Skill Section | Dissertation Chapter | Content |
|--------------|---------------------|---------|
| §1 Philosophy + Glass Box | Ch.2 Literature Review | Problem framing, gap analysis |
| §2 Taxonomy | Ch.4 Design | Role classification justification |
| §3 Dimension Weights | Ch.5 Implementation | Weighted similarity methodology |
| §4–§5 Compatibility | Ch.4 Design | Domain constraints, edge cases |
| §6 Hybrid Players | Ch.5 + Ch.7 Limitations | Dual-label, known limitations |
| §7 Radar Axes | Ch.5 Implementation | Role-adaptive visualisation |
| §8 Scouting Language | Ch.5 Implementation | Domain-appropriate UX |
| §9 League Context | Ch.2 + Ch.7 | Cross-league methodology |
| §10 Age Curves | Ch.2 Literature Review | Position-specific aging |
| §11 Clustering | Ch.6 Evaluation | Validation methodology |
| §12 Similarity Engine | Ch.5 Implementation | Decision logic |

---

## §15 — Quick Reference

| Task | Read |
|------|------|
| `classify_roles.py` | §2, §3, §6, §11 |
| `similarity_service.py` | §3, §4, §5, §12 |
| `explain_service.py` | §3, §8.1 |
| `constants.py` | §2, §3, §4, §5, §7, §8, §13 |
| `RadarChart.tsx` | §7 |
| `PlayerCard.tsx` | §1.4, §8 |
| `FeatureWeightSliders.tsx` | §3, §12.3 |
| `SimilarPlayerCard.tsx` | §1.4, §1.5, §8.1 |
| Evaluation scripts | §11 |
| Dissertation Ch.2 | §1, §9, §10 |
| Dissertation Ch.4 | §2, §4, §5, §6 |
| Dissertation Ch.5 | §3, §7, §8, §12 |
| Dissertation Ch.6 | §11 |
| Dissertation Ch.7 | §6.5, §9, §10 |
