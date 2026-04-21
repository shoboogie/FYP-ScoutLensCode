"""Central constants for ScoutLens.

This ordering MUST match the FAISS index. Any change requires a full
pipeline re-run (ingest -> features -> index -> seed).
"""

# ── Feature Vector Definition ─────────────────────────────────────────

FEATURE_NAMES: list[str] = [
    # Dim 1: Attacking Contribution (7)
    "xg_per90", "shots_per90", "shots_on_target_per90", "goals_per90",
    "npxg_per90", "touches_in_box_per90", "xg_per_shot",
    # Dim 2: Chance Creation (7)
    "xa_per90", "key_passes_per90", "assists_per90", "passes_into_box_per90",
    "through_balls_per90", "progressive_passes_per90", "crosses_per90",
    # Dim 3: Passing & Ball Control (7)
    "passes_attempted_per90", "pass_completion_pct", "progressive_pass_distance_per90",
    "long_passes_per90", "long_pass_completion_pct", "switches_per90",
    "passes_under_pressure_pct",
    # Dim 4: Ball Carrying (7)
    "progressive_carries_per90", "carry_distance_per90", "progressive_carry_distance_per90",
    "carries_into_box_per90", "dribbles_attempted_per90", "dribble_success_pct",
    "ball_receipts_per90",
    # Dim 5: Defending & Pressing (8)
    "pressures_per90", "pressure_success_pct", "tackles_per90", "tackle_success_pct",
    "interceptions_per90", "blocks_per90", "ball_recoveries_per90", "clearances_per90",
    # Dim 6: Aerial & Physical (6)
    "aerial_duels_per90", "aerial_win_pct", "ground_duels_per90",
    "ground_duel_win_pct", "fouls_won_per90", "dispossessed_per90",
]

FEATURE_COUNT = len(FEATURE_NAMES)  # 42

DIMENSION_GROUPS: dict[str, list[int]] = {
    "Attacking":        list(range(0, 7)),
    "Chance Creation":  list(range(7, 14)),
    "Passing":          list(range(14, 21)),
    "Carrying":         list(range(21, 28)),
    "Defending":        list(range(28, 36)),
    "Aerial/Physical":  list(range(36, 42)),
}

DIMENSION_NAMES: list[str] = list(DIMENSION_GROUPS.keys())

DIMENSION_KEY_MAP: dict[str, str] = {
    "ATK": "Attacking",
    "CRE": "Chance Creation",
    "PAS": "Passing",
    "CAR": "Carrying",
    "DEF": "Defending",
    "AER": "Aerial/Physical",
}


# ── Role Taxonomy (SCOUTLENS_ROLES.md §13 — authoritative) ───────────

ROLE_LABELS: list[str] = [
    "Ball-Playing CB", "Aerial/Stopper CB",
    "Attacking Full-Back", "Inverted Full-Back",
    "Deep-Lying Playmaker", "Ball-Winning Midfielder",
    "Box-to-Box Midfielder", "Advanced Playmaker",
    "Inside Forward", "Touchline Winger",
    "Complete Forward", "Poacher", "Target Forward", "Pressing Forward",
]

ROLE_COUNT = len(ROLE_LABELS)  # 14

TARGET_CLUSTER_RANGE: tuple[int, int] = (12, 16)


# ── Position Groups (SCOUTLENS_ROLES.md §2) ──────────────────────────

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
        "roles": ["Advanced Playmaker"],
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


# ── Dimension Weight Profiles per Role (SCOUTLENS_ROLES.md §3) ───────

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


# ── Dynamic Radar Chart Axes per Role (SCOUTLENS_ROLES.md §7) ────────

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


# ── Incompatible Comparison Pairs (SCOUTLENS_ROLES.md §4) ────────────

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


# ── Tactically Substitutable Pairs (SCOUTLENS_ROLES.md §5) ───────────

SUBSTITUTABLE_ROLE_PAIRS: list[dict] = [
    {
        "pair": ("Inverted Full-Back", "Deep-Lying Playmaker"),
        "reason": (
            "In possession the IFB becomes a second No. 6. Zinchenko at Arsenal, "
            "Cancelo at City. Key shared attributes: press resistance, short passing "
            "under pressure, positional discipline in the half-space."
        ),
        "scouting_tip": (
            "When seeking an IFB, scout ball-playing DMs with lateral mobility. "
            "When replacing a No. 6, certain IFBs are viable — and cheaper."
        ),
    },
    {
        "pair": ("Pressing Forward", "Advanced Playmaker"),
        "reason": (
            "Both operate between opposition midfield and defence. Firmino converted "
            "from Hoffenheim No. 10 to Liverpool false 9 — skill set unchanged, only "
            "starting position moved. Guardiola deployed De Bruyne, Foden, Gundogan as F9s."
        ),
        "scouting_tip": (
            "Losing a false 9? Scout No. 10s with high pressing intensity. "
            "Seeking a creative No. 10? Check deep-lying forwards."
        ),
    },
    {
        "pair": ("Ball-Playing CB", "Deep-Lying Playmaker"),
        "reason": (
            "Both serve as the deepest outfield passer. Stones stepped alongside Rodri "
            "in 2022-23; Mascherano moved from DM to CB at Barcelona; Busquets regularly "
            "dropped into left CB."
        ),
        "scouting_tip": (
            "Clubs seeking a BPCB for possession: holding midfielders with aerial "
            "ability are viable and cheaper — the Brentford model."
        ),
    },
    {
        "pair": ("Attacking Full-Back", "Touchline Winger"),
        "reason": (
            "In 3-at-the-back, the WB covers the entire flank — functionally identical "
            "to a winger who tracks back. Hakimi at Inter was statistically "
            "indistinguishable from a right winger in attacking output."
        ),
        "scouting_tip": (
            "Switching to back three? Scout wingers with defensive work rate. "
            "Wing-backs in back-three systems are undervalued as wide attackers."
        ),
    },
    {
        "pair": ("Pressing Forward", "Box-to-Box Midfielder"),
        "reason": (
            "In high-press systems the pressing forward's primary job is disruption — "
            "same actions a B2B performs from a different starting position. Red Bull's "
            "multi-club model exploits this: players shift between forward and midfield."
        ),
        "scouting_tip": "Shared evaluation: PPDA contribution, high recoveries, sprint distance.",
    },
    {
        "pair": ("Inside Forward", "Advanced Playmaker"),
        "reason": (
            "Both converge on the half-space 20-30m from goal. Salah's average touch "
            "position is closer to a second striker than a winger. Inverted wingers in "
            "weaker leagues are priced as 'wingers' but functionally operate as "
            "second strikers — a market inefficiency."
        ),
        "scouting_tip": "Seeking a second striker? Scout inside forwards at winger prices.",
    },
    {
        "pair": ("Complete Forward", "Pressing Forward"),
        "reason": (
            "Both drop deep and create. Difference is pressing intensity vs goal-scoring "
            "emphasis, which varies by match context."
        ),
        "scouting_tip": "Evaluate pressures and high recoveries alongside xG to separate them.",
    },
]


# ── Scouting Report Summary Templates (SCOUTLENS_ROLES.md §8.1) ──────

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


# ── Scouting Descriptor Vocabulary (SCOUTLENS_ROLES.md §8.2) ─────────

SCOUTING_DESCRIPTORS: dict[str, dict[str, list[str]]] = {
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


# ── StatsBomb Competition IDs ─────────────────────────────────────────

BIG_FIVE_COMPETITIONS: list[dict] = [
    {"competition_id": 2,  "season_id": 27, "name": "Premier League"},
    {"competition_id": 11, "season_id": 27, "name": "La Liga"},
    {"competition_id": 9,  "season_id": 27, "name": "Bundesliga"},
    {"competition_id": 12, "season_id": 27, "name": "Serie A"},
    {"competition_id": 7,  "season_id": 27, "name": "Ligue 1"},
]


# ── Quality Filtering Thresholds ──────────────────────────────────────

MIN_MINUTES: int = 900
MIN_AGE: int = 18
AGE_CUTOFF_DATE: str = "1997-07-01"
EXCLUDED_POSITIONS: list[str] = ["Goalkeeper"]


# ── Pitch Geometry (StatsBomb 120x80 coordinate system) ───────────────

PITCH_LENGTH: float = 120.0
PITCH_WIDTH: float = 80.0
GOAL_X: float = 120.0
GOAL_Y: float = 40.0
PROGRESSIVE_THRESHOLD: float = 10.0  # Metres closer to goal for progressive actions
LONG_PASS_THRESHOLD: float = 32.0    # Metres for long pass classification
SWITCH_Y_THRESHOLD: float = 40.0     # Abs y-distance for switches of play

# Opponent penalty area boundaries (on 120x80 pitch)
OPP_BOX_X_MIN: float = 102.0
OPP_BOX_Y_MIN: float = 18.0
OPP_BOX_Y_MAX: float = 62.0
