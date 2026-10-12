"""
Prompt Dungeon — Public Catalog: The Last Exhibition
Canonical Reference: docs/api-contract.md v1.1.0 & docs/case-spec.md v1.1.0

This module defines the player-safe catalog data used to initialize the client frontend.
It contains strictly non-spoiling, public information. It does NOT import or expose
canonical solution data, culprit identities, or undiscovered evidence.
"""

from typing import List

from models import (
    CaseMeta,
    ConfigResponse,
    GameRules,
    LocationProfile,
    SuspectId,
    SuspectProfile,
    TargetId,
)


# ============================================================================
# 1. Public Case Metadata
# ============================================================================

PUBLIC_CASE_META = CaseMeta(
    case_id="the_last_exhibition",
    case_title="The Last Exhibition",
    incident_time="2026-10-12T21:17:00Z",
    facility="Blackwood Museum of Antiquities",
)


# ============================================================================
# 2. Public Game Rules & Gameplay Limits
# ============================================================================

PUBLIC_GAME_RULES = GameRules(
    max_accusation_attempts=3,
    penalty_per_failed_accusation=15,
    history_window_turns=6,
    rate_limit_interrogations_per_minute=30,
    max_question_length=500,
)


# ============================================================================
# 3. Public Suspect Profiles (Non-spoiling Public Cards)
# ============================================================================

PUBLIC_SUSPECTS: List[SuspectProfile] = [
    SuspectProfile(
        suspect_id=SuspectId.ELIAS_VOSS,
        name="Elias Voss",
        role="Chief Conservator",
        avatar="/assets/suspects/elias_voss.webp",
        bio="Veteran conservator of 14 years. Meticulous specialist in Mesoamerican glass restorations.",
    ),
    SuspectProfile(
        suspect_id=SuspectId.MIRA_SEN,
        name="Dr. Mira Sen",
        role="Lead Curator",
        avatar="/assets/suspects/mira_sen.webp",
        bio="Academic prodigy who curated the loan of the Obsidian Sun and led tonight's gala exhibition.",
    ),
    SuspectProfile(
        suspect_id=SuspectId.NOAH_REED,
        name="Noah Reed",
        role="Security Systems Technician",
        avatar="/assets/suspects/noah_reed.webp",
        bio="Junior technician managing the museum's digital security consoles, switches, and badge reader hardware.",
    ),
    SuspectProfile(
        suspect_id=SuspectId.CELESTE_WARD,
        name="Celeste Ward",
        role="Antiquities Collector",
        avatar="/assets/suspects/celeste_ward.webp",
        bio="Prominent billionaire patron of the arts whose private acquisition bids for the artifact were rejected by the museum board.",
    ),
]


# ============================================================================
# 4. Public Examination Targets (Predefined Facility Directory)
# ============================================================================

PUBLIC_LOCATIONS: List[LocationProfile] = [
    LocationProfile(
        target_id=TargetId.HELIODOR_PEDESTAL,
        name="Heliodor Gallery — Pedestal Base",
        zone="Crime Scene",
    ),
    LocationProfile(
        target_id=TargetId.VITRINE_LATCH,
        name="Heliodor Gallery — Vitrine Lock Rim",
        zone="Crime Scene",
    ),
    LocationProfile(
        target_id=TargetId.GALLERY_TAPESTRY,
        name="Heliodor Gallery — South Wall Tapestry",
        zone="Crime Scene",
    ),
    LocationProfile(
        target_id=TargetId.SERVER_RACK_02,
        name="Basement Server Room — Switch 04 Console",
        zone="Security Hub",
    ),
    LocationProfile(
        target_id=TargetId.SECURITY_ACCESS_DB,
        name="Security Control Booth — Access Mainframe",
        zone="Security Hub",
    ),
    LocationProfile(
        target_id=TargetId.CURATOR_SHREDDER,
        name="Curator Office — Paper Shredder Bin",
        zone="Admin Wing",
    ),
    LocationProfile(
        target_id=TargetId.CURATOR_DESK,
        name="Curator Office — Desk Drawer",
        zone="Admin Wing",
    ),
    LocationProfile(
        target_id=TargetId.WEST_ARCHIVE_FLOOR,
        name="West Archive Corridor — Hallway Floor",
        zone="Restricted Archives",
    ),
    LocationProfile(
        target_id=TargetId.WORKSHOP_CABINET_03,
        name="Conservation Lab — Locked Tool Cabinet 3",
        zone="Conservation",
    ),
    LocationProfile(
        target_id=TargetId.BASEMENT_HAZMAT_04,
        name="Basement Annex — Flammable Storage 4",
        zone="Conservation",
    ),
    LocationProfile(
        target_id=TargetId.TERRACE_CATERING_BAR,
        name="Terrace Bar — Catering Service Log",
        zone="Public Gala",
    ),
    LocationProfile(
        target_id=TargetId.TECHNICIAN_LOCKER,
        name="Guard Quarters — Noah Reed's Locker",
        zone="Staff Facilities",
    ),
]


# ============================================================================
# 5. Public Configuration Factory
# ============================================================================

def get_public_config() -> ConfigResponse:
    """
    Constructs the static configuration bundle for GET /api/config.
    Guaranteed safe: contains zero solution keys, evidence payloads, or guilt flags.
    """
    return ConfigResponse(
        case_meta=PUBLIC_CASE_META,
        rules=PUBLIC_GAME_RULES,
        suspects=PUBLIC_SUSPECTS,
        locations=PUBLIC_LOCATIONS,
    )
