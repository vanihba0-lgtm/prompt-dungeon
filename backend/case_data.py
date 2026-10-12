"""
Prompt Dungeon — Canonical Case Data: The Last Exhibition
Source of Truth: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

This module contains internal, immutable ground-truth specifications for the case.
It is NOT exposed to player-facing public API responses.
"""

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

from models import (
    EvidenceCategory,
    EvidenceId,
    RuleId,
    SuspectId,
    TargetId,
    TARGET_EVIDENCE_MAP,
)


# ============================================================================
# 1. Timeline Data Structures
# ============================================================================

@dataclass(frozen=True)
class TimelineEvent:
    """Canonical ground-truth event along the crime timeline."""
    timestamp_str: str          # e.g. "8:45 PM", "9:17:00 PM"
    location: str               # Canonical facility location
    actors: Tuple[str, ...]     # Primary participants
    description: str            # Objective historical occurrence


CANONICAL_TIMELINE: Tuple[TimelineEvent, ...] = (
    TimelineEvent(
        timestamp_str="8:45 PM",
        location="Heliodor Gallery",
        actors=("Dr. Mira Sen", "Elias Voss"),
        description="Final public seal inspection of the Obsidian Sun. Vitrine atmospheric pressure stabilized at 1.05 atm.",
    ),
    TimelineEvent(
        timestamp_str="9:00 PM",
        location="Grand Ballroom & Terrace",
        actors=("All",),
        description="Opening gala remarks begin. Celeste Ward is observed ordering a drink on the terrace.",
    ),
    TimelineEvent(
        timestamp_str="9:08 PM",
        location="Ballroom",
        actors=("Dr. Mira Sen",),
        description="Dr. Sen receives an encrypted notification on her phone from black-market appraiser Vance Sterling demanding final fee payment for the unauthorized valuation.",
    ),
    TimelineEvent(
        timestamp_str="9:10 PM",
        location="Ballroom -> Office",
        actors=("Dr. Mira Sen",),
        description="Dr. Sen slips away from gala attendees and heads up the grand staircase to her private 2nd-floor office.",
    ),
    TimelineEvent(
        timestamp_str="9:12 PM",
        location="Curator Office",
        actors=("Dr. Mira Sen",),
        description="Dr. Sen begins shredding physical appraisal notes and wiping emails on her private terminal.",
    ),
    TimelineEvent(
        timestamp_str="9:13 PM",
        location="Terrace -> West Wing",
        actors=("Celeste Ward",),
        description="Celeste Ward abandons her drink on the terrace and uses an unlocked side door to infiltrate the restricted West Archive corridor to snoop for acquisition provenance files.",
    ),
    TimelineEvent(
        timestamp_str="9:14:10 PM",
        location="Security Console",
        actors=("Noah Reed",),
        description="Noah Reed, wishing to test an unauthorized third-party camera firmware patch (for which he took a $500 forum bounty) and wipe his personal web browsing logs, queues a script.",
    ),
    TimelineEvent(
        timestamp_str="9:14:48 PM",
        location="Security Console",
        actors=("Noah Reed",),
        description="Noah executes diag_cam_restart.sh on Switch 04. The terminal hangs unexpectedly.",
    ),
    TimelineEvent(
        timestamp_str="9:15:00 PM",
        location="Gallery & East Wing",
        actors=("Cameras / System",),
        description="Video feeds for the Heliodor Gallery (Cam-03) and East Corridor (Cam-04) drop to frozen static test patterns. Noah enters a state of panic trying to reboot the port.",
    ),
    TimelineEvent(
        timestamp_str="9:15:30 PM",
        location="Service Corridor B",
        actors=("Elias Voss",),
        description="Elias Voss, monitoring security feeds via a tablet and anticipating Noah's diagnostic window, swipes his conservator keycard into Service Passage B.",
    ),
    TimelineEvent(
        timestamp_str="9:16:05 PM",
        location="Service Passage B",
        actors=("Elias Voss",),
        description="Elias reaches the concealed maintenance dumbwaiter hatch behind the 17th-century Renaissance tapestry in the Heliodor Gallery.",
    ),
    TimelineEvent(
        timestamp_str="9:16:15 PM",
        location="Heliodor Gallery",
        actors=("Elias Voss",),
        description="Elias slides through the tapestry hatch into the darkened gallery, wearing purple antistatic microfiber gloves and soft-soled lab shoes.",
    ),
    TimelineEvent(
        timestamp_str="9:16:35 PM",
        location="Heliodor Gallery Pedestal",
        actors=("Elias Voss",),
        description="Using the authorized conservator nitrogen bypass shunt tool (E-01), Elias couples the secondary gas valve, equalizing internal pressure without triggering the atmospheric drop sensor.",
    ),
    TimelineEvent(
        timestamp_str="9:17:00 PM",
        location="Heliodor Gallery Pedestal",
        actors=("Elias Voss",),
        description="THE THEFT OCCURS. Elias unlatches the dual-key mechanical cylinder, lifts the Obsidian Sun, wraps it in padded silicone sheeting, and places it into his tool satchel.",
    ),
    TimelineEvent(
        timestamp_str="9:17:35 PM",
        location="Heliodor Gallery",
        actors=("Elias Voss",),
        description="Elias re-latches the vitrine, leaves the shunt coupled to avoid pressure alarms, and exits back through the tapestry hatch into Service Corridor B.",
    ),
    TimelineEvent(
        timestamp_str="9:18:22 PM",
        location="Service Passage B",
        actors=("Elias Voss",),
        description="Elias swipes his keycard exiting Service Corridor B down into the Basement Conservation Annex.",
    ),
    TimelineEvent(
        timestamp_str="9:19:10 PM",
        location="Security Console",
        actors=("Noah Reed",),
        description="Noah's terminal reboot finally clears; video feeds reconnect. Cam-03 resumes displaying the Heliodor Gallery, but the dim ambient lighting conceals that the pedestal is vacant.",
    ),
    TimelineEvent(
        timestamp_str="9:20:05 PM",
        location="Basement Annex",
        actors=("Elias Voss",),
        description="Elias secretes the Obsidian Sun inside a modified 5-liter steel container labeled Hexane-12 Conservation Solvent in the locked Hazardous Materials cabinet.",
    ),
    TimelineEvent(
        timestamp_str="9:21:10 PM",
        location="West Archive Corridor",
        actors=("Celeste Ward",),
        description="Startled by passing security guard footsteps, Celeste flees the archive corridor, accidentally dropping her engraved gold lighter (E-05) near the archive door.",
    ),
    TimelineEvent(
        timestamp_str="9:21:45 PM",
        location="Terrace",
        actors=("Celeste Ward",),
        description="Celeste returns to the terrace, claiming she never left and ordering a second cocktail.",
    ),
    TimelineEvent(
        timestamp_str="9:22:00 PM",
        location="2nd-Floor Office",
        actors=("Dr. Mira Sen",),
        description="Dr. Sen finishes destroying appraisal paperwork and returns downstairs to check the gallery.",
    ),
    TimelineEvent(
        timestamp_str="9:22:45 PM",
        location="Heliodor Gallery",
        actors=("Dr. Mira Sen",),
        description="Dr. Sen approaches the vitrine, discovers the Obsidian Sun is missing, and triggers the emergency distress pull-station.",
    ),
    TimelineEvent(
        timestamp_str="9:23:30 PM",
        location="Entire Facility",
        actors=("Security System",),
        description="Building enters automated lockdown. External exits seal.",
    ),
)


# ============================================================================
# 2. Suspect Canonical Dossiers
# ============================================================================

@dataclass(frozen=True)
class SuspectDossier:
    """Internal canonical truth for a suspect."""
    suspect_id: SuspectId
    full_name: str
    role: str
    is_canonical_culprit: bool
    canonical_motive: str
    hidden_secret: str
    personality_demeanor: str
    strict_knowledge_boundaries: Tuple[str, ...]
    truthful_statements: Tuple[str, ...]
    false_statements: Tuple[str, ...]


SUSPECT_DOSSIERS: Dict[SuspectId, SuspectDossier] = {
    SuspectId.ELIAS_VOSS: SuspectDossier(
        suspect_id=SuspectId.ELIAS_VOSS,
        full_name="Elias Voss",
        role="Chief Conservator & Restoration Specialist",
        is_canonical_culprit=True,
        canonical_motive="Extortion debt of £150,000 to 'The Grey Ledger' criminal syndicate due by midnight tonight.",
        hidden_secret="Orchestrated the entire physical extraction. Exploited Noah's diagnostic window, utilized his personal conservator nitrogen-shunt key (E-01), and hid the artifact on-site in a solvent container (E-11).",
        personality_demeanor="Controlled, soft-spoken, answers questions with technical pedantry to divert emotional scrutiny.",
        strict_knowledge_boundaries=(
            "Knows the exact mechanical and pneumatic operation of the vitrine and the bypass shunt.",
            "Knows the location of the maintenance dumbwaiter hatch behind the gallery tapestry.",
            "Knows the location of chemical solvent stocks in Basement HazMat Locker 4.",
            "Does NOT know why Dr. Sen was absent from the ballroom or that she had an illegal appraisal.",
            "Does NOT know why Celeste Ward was snooping in the archive corridor.",
            "Does NOT know Noah took a forum bounty (only observed previous switch reboots).",
        ),
        truthful_statements=(
            "I checked the vitrine's atmospheric seal at 8:45 PM with Dr. Sen. The pressure was nominal.",
            "Breaking the glass would trigger the acoustic vibration sensors instantly.",
            "I was down in the basement restoration lab preparing mounting adhesives for tomorrow's exhibition.",
        ),
        false_statements=(
            "I never entered Service Corridor B or the gallery area after the 8:45 PM public inspection.",
            "All my specialized vitrine maintenance equipment, including the nitrogen equalizing shunts, remained locked in Cabinet 3 all evening.",
            "I have no financial complications whatsoever; my personal accounts are entirely in order.",
        ),
    ),
    SuspectId.MIRA_SEN: SuspectDossier(
        suspect_id=SuspectId.MIRA_SEN,
        full_name="Dr. Mira Sen",
        role="Lead Curator of Antiquities",
        is_canonical_culprit=False,
        canonical_motive="Suspected of commercial theft or kickbacks; in reality, feared academic ruin due to an illegal off-the-books provenance appraisal.",
        hidden_secret="Commissioned an unauthorized private appraisal from Vance Sterling to discover the piece's true market value ($4.2M). Was frantically destroying appraisal papers during the theft window.",
        personality_demeanor="Defensive, intellectual, high-strung, irritable under direct challenge.",
        strict_knowledge_boundaries=(
            "Knows museum provenance history, accession ledgers, and donor records.",
            "Knows the vitrine requires dual keys, but has zero knowledge of how to bypass pneumatic pressure sensors.",
            "Does NOT know who stole the artifact or how the vitrine was breached.",
            "Does NOT know Noah's server script caused the camera outage.",
            "Does NOT know Elias was inside Service Corridor B.",
        ),
        truthful_statements=(
            "I did not take the artifact. It was the centerpiece of my life's academic curation.",
            "The museum would be bankrupted by the scandal if this piece vanished.",
        ),
        false_statements=(
            "I remained in the Grand Ballroom greeting patrons from 9:00 PM until I walked into the gallery at 9:22 PM.",
            "I have never discussed private commercial valuation of the Obsidian Sun with any third-party brokers.",
        ),
    ),
    SuspectId.NOAH_REED: SuspectDossier(
        suspect_id=SuspectId.NOAH_REED,
        full_name="Noah Reed",
        role="Security Systems Technician",
        is_canonical_culprit=False,
        canonical_motive="Severely underpaid; bitter resentment against museum leadership.",
        hidden_secret="Took a $500 cryptocurrency payment on a tech forum to live-test an unverified open-source firmware optimization patch on Switch 04 at 9:15 PM, combining it with a routine wipe of his personal web logs.",
        personality_demeanor="Anxious, stammering, defensive, tech-jargon heavy when cornered.",
        strict_knowledge_boundaries=(
            "Knows camera switch configuration, terminal IP logs, and badge reader hardware.",
            "Has zero knowledge of conservation tools, vitrines, or Mesoamerican art.",
            "Does NOT know who stole the artifact or how the vitrine was opened.",
            "Does NOT know Elias entered Service Corridor B during the blackout.",
        ),
        truthful_statements=(
            "I never left the security control booth between 8:00 PM and the alarm.",
            "I didn't take any relic. I wouldn't even know who to sell a rock like that to.",
        ),
        false_statements=(
            "The camera feeds never cut out; there was just a momentary ambient lighting flicker.",
            "I was actively monitoring live feeds the entire evening and ran no diagnostic operations or terminal commands.",
        ),
    ),
    SuspectId.CELESTE_WARD: SuspectDossier(
        suspect_id=SuspectId.CELESTE_WARD,
        full_name="Celeste Ward",
        role="Private Antiquities Collector & Donor",
        is_canonical_culprit=False,
        canonical_motive="Obsessed with acquiring the Obsidian Sun; two multi-million-dollar acquisition bids were rejected by the board.",
        hidden_secret="Trespassed into the restricted West Archive corridor between 9:13 PM and 9:21 PM attempting to photograph confidential board minutes and donor provenance records to blackmail the trustees.",
        personality_demeanor="Aristocratic, aloof, dismissive, wields her social status and legal threats as shields.",
        strict_knowledge_boundaries=(
            "Knows the financial value of the piece, market prices, and board politics.",
            "Has no security system credentials, staff keys, or conservator bypass tools.",
            "Does NOT know how the thief breached the vitrine.",
            "Did not see the thief, but heard faint mechanical noises in the wall near the archive at ~9:16 PM.",
        ),
        truthful_statements=(
            "I offered seven million dollars legitimately. Why would I steal something I cannot legally display in my home?",
            "I heard a faint metallic clattering inside the ventilation shaft around 9:16 PM while I was... walking.",
        ),
        false_statements=(
            "I spent the entire evening between 9:00 PM and 9:25 PM enjoying champagne on the terrace in plain sight of the waitstaff.",
            "I have never stepped foot in the museum's private archive wing.",
        ),
    ),
}


# ============================================================================
# 3. Canonical Evidence Definitions (E-01 to E-12)
# ============================================================================

@dataclass(frozen=True)
class CanonicalEvidence:
    """Canonical ground truth for a case evidence item."""
    evidence_id: EvidenceId
    title: str
    target_id: TargetId
    category: EvidenceCategory
    is_mandatory: bool
    location_description: str
    source_description: str
    discovery_conditions: str
    canonical_interpretation: str
    related_facts: str
    description: str


CANONICAL_EVIDENCE_CATALOG: Dict[EvidenceId, CanonicalEvidence] = {
    EvidenceId.E_01: CanonicalEvidence(
        evidence_id=EvidenceId.E_01,
        title="Severed Vitrine Sensor Shunt",
        target_id=TargetId.HELIODOR_PEDESTAL,
        category=EvidenceCategory.FORENSIC,
        is_mandatory=True,
        location_description="Heliodor Gallery, recessed service panel at display pedestal base.",
        source_description="Forensic inspection of the vitrine base.",
        discovery_conditions="Discovered by inspecting the display pedestal or examining vitrine security mechanisms.",
        canonical_interpretation="Confirms theft did not involve brute force. Perpetrator possessed a specialized pneumatic equalizing shunt custom-built for Blackwood Museum conservation vitrines.",
        related_facts="Excludes crude theft or external burglars; narrows technical capability to conservation personnel.",
        description="A brass micro-bore adapter equipped with a secondary pressure-relief valve and quick-release nitrogen coupling, currently attached to the intake nipple at the base of the vitrine pedestal.",
    ),
    EvidenceId.E_02: CanonicalEvidence(
        evidence_id=EvidenceId.E_02,
        title="Security Switch Terminal Log",
        target_id=TargetId.SERVER_RACK_02,
        category=EvidenceCategory.DIGITAL_LOG,
        is_mandatory=True,
        location_description="Basement Server Room, Terminal Rack 02.",
        source_description="Digital forensic extraction of switch syslogs.",
        discovery_conditions="Discovered by examining the server room terminal or requesting CCTV system diagnostic logs.",
        canonical_interpretation="Establishes exact camera blackout window (9:14:48 PM to 9:19:10 PM). Proves camera failure was caused internally by technician Noah Reed running an unauthorized script.",
        related_facts="Explains video blackout without requiring a master conspirator; refutes Noah's alibi.",
        description="System execution log from Cisco Catalyst Switch 04 showing a bash script execution: bash diag_cam_restart.sh -p 4 -f --force initiated at 21:14:48 by user account n_reed.",
    ),
    EvidenceId.E_03: CanonicalEvidence(
        evidence_id=EvidenceId.E_03,
        title="Restricted Keycard Swipe Log",
        target_id=TargetId.SECURITY_ACCESS_DB,
        category=EvidenceCategory.DIGITAL_LOG,
        is_mandatory=True,
        location_description="Security Administration Mainframe / Access Database.",
        source_description="Digital export of physical access logs.",
        discovery_conditions="Discovered by querying electronic access database or requesting interior door records.",
        canonical_interpretation="Places Elias Voss inside Service Corridor B from 9:15:30 PM to 9:18:22 PM (matching the exact minute of theft, 9:17 PM). Places Dr. Sen in her office at 9:11 PM.",
        related_facts="Destroys Elias Voss's alibi of remaining in basement lab continuously; proves presence but requires physical corroboration for guilt.",
        description="Cryptographic badge access ledger for restricted service doors: 21:11:04 Card #004 (Dr. M. Sen) -> Curator Office; 21:15:30 Card #012 (E. Voss) -> Service Corridor B; 21:18:22 Card #012 (E. Voss) -> Exit to Basement.",
    ),
    EvidenceId.E_04: CanonicalEvidence(
        evidence_id=EvidenceId.E_04,
        title="Torn Appraisal Memo Fragments",
        target_id=TargetId.CURATOR_SHREDDER,
        category=EvidenceCategory.DOCUMENT,
        is_mandatory=False,
        location_description="Dr. Mira Sen's Office, under-desk shredder bin.",
        source_description="Physical forensic recovery in curator office.",
        discovery_conditions="Discovered by searching Dr. Sen's private office.",
        canonical_interpretation="Proves Dr. Sen engaged in an illicit private appraisal with Vance Sterling ($4.2M). Demonstrates her guilty demeanor was motivated by fear of academic scandal, not theft.",
        related_facts="Disproves Dr. Sen as physical thief while explaining her deception.",
        description="Reassembled strips of 90gsm bond paper retrieved from a cross-cut paper shredder bin. Mentions: 'Confidential valuation: Obsidian Sun — $4,200,000 illicit auction ceiling. Authentication confirmed by V.S.'",
    ),
    EvidenceId.E_05: CanonicalEvidence(
        evidence_id=EvidenceId.E_05,
        title="Engraved Monogrammed Lighter",
        target_id=TargetId.WEST_ARCHIVE_FLOOR,
        category=EvidenceCategory.PHYSICAL_TRACE,
        is_mandatory=False,
        location_description="Floor of the West Archive Corridor, tucked beneath a Victorian radiator.",
        source_description="Physical search of restricted archive corridor.",
        discovery_conditions="Discovered by inspecting the West Archive Corridor floor.",
        canonical_interpretation="Conclusively places Celeste Ward in restricted West Archive wing around 9:15-9:20 PM, breaking terrace alibi. However, archive has no physical connection to gallery.",
        related_facts="Disproves Celeste Ward's alibi while clearing her of physical access to crime scene.",
        description="Solid 18k yellow-gold Dunhill lighter engraved with the cursive initials 'C.W.', smelling faintly of high-grade kerosene.",
    ),
    EvidenceId.E_06: CanonicalEvidence(
        evidence_id=EvidenceId.E_06,
        title="Debt Ultimatum & Pawn Ticket",
        target_id=TargetId.WORKSHOP_CABINET_03,
        category=EvidenceCategory.DOCUMENT,
        is_mandatory=True,
        location_description="Conservation Workshop, false bottom of locked Tool Cabinet 3.",
        source_description="Targeted search of Elias Voss's private workbench.",
        discovery_conditions="Discovered by searching Elias Voss's workshop and opening Tool Cabinet 3.",
        canonical_interpretation="Establishes real, urgent motive for theft. Elias was under imminent threat of violent extortion with a midnight deadline, specifically demanding the Obsidian Sun.",
        related_facts="Establishes Elias Voss's sole motive and urgency.",
        description="A crumpled handwritten note: 'Voss — Midnight tonight or your sister's workshop burns. £150,000 cash or the Aztec glass. No police. - Grey Ledger', clipped to a pawn ticket for an antique pocket watch.",
    ),
    EvidenceId.E_07: CanonicalEvidence(
        evidence_id=EvidenceId.E_07,
        title="Antistatic Fiber & Solvent Traces",
        target_id=TargetId.VITRINE_LATCH,
        category=EvidenceCategory.FORENSIC,
        is_mandatory=True,
        location_description="Heliodor Gallery Vitrine, upper rim and mechanical cylinder latch.",
        source_description="Forensic swab and UV luminescence analysis.",
        discovery_conditions="Discovered by swabbing the vitrine latch and lock mechanism.",
        canonical_interpretation="Links physical manipulation of vitrine directly to conservation lab supplies. Only Elias Voss wore purple antistatic gloves. Identifies Hexane-12 as the chemical breadcrumb.",
        related_facts="Directly links physical actor to Elias Voss's equipment and chemical supplies.",
        description="Microscopic trace analysis: two purple synthetic polyester fibers matching 20-denier antistatic gloves, alongside residue of Hexane-12 optical conservation solvent.",
    ),
    EvidenceId.E_08: CanonicalEvidence(
        evidence_id=EvidenceId.E_08,
        title="Terrace Waitstaff Order Slip #408",
        target_id=TargetId.TERRACE_CATERING_BAR,
        category=EvidenceCategory.DOCUMENT,
        is_mandatory=False,
        location_description="Kitchen Catering Service Station.",
        source_description="Interview with catering manager and waiter receipts.",
        discovery_conditions="Discovered by reviewing catering orders or questioning catering staff about guests.",
        canonical_interpretation="Corroborates that Celeste Ward was absent from terrace between 9:12 PM and 9:22 PM, matching timeframe of her archive excursion.",
        related_facts="Solidifies timeline of Celeste's movement.",
        description="Carbon order slip from Terrace Bar: 21:02 1x Dry Gin Martini (served table 4); 21:16 1x Dry Gin Martini (delivered, table noted vacant); 21:22 guest returned.",
    ),
    EvidenceId.E_09: CanonicalEvidence(
        evidence_id=EvidenceId.E_09,
        title="Encrypted USB Drive & Forum Logs",
        target_id=TargetId.TECHNICIAN_LOCKER,
        category=EvidenceCategory.DIGITAL_LOG,
        is_mandatory=False,
        location_description="Security Guard Locker Room, inside Noah Reed's backpack.",
        source_description="Search of security technician locker.",
        discovery_conditions="Discovered by searching Noah Reed's locker.",
        canonical_interpretation="Demonstrates Noah Reed's reboot of Switch 04 was reckless moonlighting for $500 crypto bounty rather than pre-planned criminal collusion with thief.",
        related_facts="Clears Noah Reed of active theft conspiracy.",
        description="Sandisk USB drive and printed chat transcript from overclockers-underground.net: user N_Reedy agrees to test uncompiled firmware at 9:15 PM for 0.015 BTC.",
    ),
    EvidenceId.E_10: CanonicalEvidence(
        evidence_id=EvidenceId.E_10,
        title="Tapestry Service Hatch Scuff Marks",
        target_id=TargetId.GALLERY_TAPESTRY,
        category=EvidenceCategory.PHYSICAL_TRACE,
        is_mandatory=True,
        location_description="Heliodor Gallery, South Wall behind tapestry / Service Corridor B wall recess.",
        source_description="Physical search of gallery perimeter or Service Corridor B.",
        discovery_conditions="Discovered by examining gallery walls behind tapestry or tracing wall cavity in Service Corridor B.",
        canonical_interpretation="Reveals physical bypass route used to enter and exit Heliodor Gallery without passing security guards stationed outside main gallery doors.",
        related_facts="Solves the physical ingress/egress paradox of the locked gallery.",
        description="Fresh scraping of black shoe scuffs and industrial grease on the brass rim of a 24'x36' service dumbwaiter hatch hidden behind the 17th-century tapestry on south wall.",
    ),
    EvidenceId.E_11: CanonicalEvidence(
        evidence_id=EvidenceId.E_11,
        title="Weighted Hexane-12 Solvent Canister",
        target_id=TargetId.BASEMENT_HAZMAT_04,
        category=EvidenceCategory.PHYSICAL_TRACE,
        is_mandatory=True,
        location_description="Basement Conservation Annex, Flammable Storage Cabinet 4.",
        source_description="Physical search and scale-weighing of chemical lockers.",
        discovery_conditions="Following Hexane-12 clue (E-07) to conservation chemical inventory, examining canisters reveals Canister #4 weighs 5.8 kg instead of normal 2.0 kg tare + fluid.",
        canonical_interpretation="Physical recovery of the stolen artifact. Proves item never left the building and was stashed by Elias Voss for extraction prior to midnight meeting.",
        related_facts="Unquestionable proof of the artifact's location and physical possession.",
        description="Standard 5-liter industrial steel chemical jug labeled 'Hexane-12 — Laboratory Solvent (Flammable)'. Weighs 5.8 kg (3.8 kg over tare). Contains the Obsidian Sun inside an acid-proof silicone bladder.",
    ),
    EvidenceId.E_12: CanonicalEvidence(
        evidence_id=EvidenceId.E_12,
        title="Dictaphone Audio Memo #14",
        target_id=TargetId.CURATOR_DESK,
        category=EvidenceCategory.DIGITAL_LOG,
        is_mandatory=False,
        location_description="Dr. Mira Sen's private desk drawer.",
        source_description="Office search.",
        discovery_conditions="Discovered by opening locked drawer in Dr. Sen's desk.",
        canonical_interpretation="Conclusively proves Dr. Sen was inside her private office at 9:16 PM panicking about provenance scandal while clock chimes 9:15, making physical presence in gallery impossible.",
        related_facts="Solidifies Dr. Sen's absolute physical alibi during crime minute.",
        description="Microcassette dictaphone recording timestamped 21:16:10: Dr. Sen's voice panicking about looted contraband while grandfather clock chimes 9:15 in background.",
    ),
}


# ============================================================================
# 4. Examination Targets & Narrative Catalog
# ============================================================================

@dataclass(frozen=True)
class TargetNarrative:
    """Narrative text and associated evidence for an examination target."""
    target_id: TargetId
    display_name: str
    facility_zone: str
    associated_evidence_id: EvidenceId
    first_discovery_narrative: str
    repeat_inspection_narrative: str


TARGET_NARRATIVES: Dict[TargetId, TargetNarrative] = {
    TargetId.HELIODOR_PEDESTAL: TargetNarrative(
        target_id=TargetId.HELIODOR_PEDESTAL,
        display_name="Heliodor Gallery — Pedestal Base",
        facility_zone="Crime Scene",
        associated_evidence_id=EvidenceId.E_01,
        first_discovery_narrative="You inspect the recessed service panel at the base of the vitrine pedestal. A brass micro-bore adapter equipped with a secondary pressure-relief valve is coupled to the nitrogen intake nipple.",
        repeat_inspection_narrative="The recessed service panel remains open. The brass bypass shunt (E-01) has already been logged into forensic inventory.",
    ),
    TargetId.SERVER_RACK_02: TargetNarrative(
        target_id=TargetId.SERVER_RACK_02,
        display_name="Basement Server Room — Switch 04 Console",
        facility_zone="Security Hub",
        associated_evidence_id=EvidenceId.E_02,
        first_discovery_narrative="You inspect the active terminal rack for Cisco Switch 04. System execution logs show a forced camera diagnostic restart script initiated at 21:14:48 by technician account n_reed.",
        repeat_inspection_narrative="The switch terminal display still shows the execution log for diag_cam_restart.sh (E-02).",
    ),
    TargetId.SECURITY_ACCESS_DB: TargetNarrative(
        target_id=TargetId.SECURITY_ACCESS_DB,
        display_name="Security Control Booth — Access Mainframe",
        facility_zone="Security Hub",
        associated_evidence_id=EvidenceId.E_03,
        first_discovery_narrative="You query the security administration database for card swipes between 9:00 PM and 9:30 PM. Elias Voss's card swiped into Service Corridor B at 21:15:30 and exited at 21:18:22.",
        repeat_inspection_narrative="The card access ledger (E-03) has already been exported and reviewed.",
    ),
    TargetId.CURATOR_SHREDDER: TargetNarrative(
        target_id=TargetId.CURATOR_SHREDDER,
        display_name="Curator Office — Paper Shredder Bin",
        facility_zone="Admin Wing",
        associated_evidence_id=EvidenceId.E_04,
        first_discovery_narrative="You examine the cross-cut shredder bin under Dr. Sen's desk. Reassembling the topmost strips reveals an unauthorized private appraisal memo from Vance Sterling valuing the relic at $4.2M.",
        repeat_inspection_narrative="The paper shredder bin has already been sifted and the appraisal memo (E-04) reassembled.",
    ),
    TargetId.WEST_ARCHIVE_FLOOR: TargetNarrative(
        target_id=TargetId.WEST_ARCHIVE_FLOOR,
        display_name="West Archive Wing — Corridor Floor",
        facility_zone="Archives",
        associated_evidence_id=EvidenceId.E_05,
        first_discovery_narrative="You conduct a physical sweep of the restricted West Archive corridor. Beneath a cast-iron radiator, you spot an engraved 18k gold lighter with the monogram 'C.W.'",
        repeat_inspection_narrative="The floor beneath the archive radiator is bare. The gold lighter (E-05) has already been bagged.",
    ),
    TargetId.WORKSHOP_CABINET_03: TargetNarrative(
        target_id=TargetId.WORKSHOP_CABINET_03,
        display_name="Conservation Lab — Locked Tool Cabinet 3",
        facility_zone="Conservation",
        associated_evidence_id=EvidenceId.E_06,
        first_discovery_narrative="You search Elias Voss's workbench and inspect Tool Cabinet 3. Hidden beneath a false drawer bottom is a violent extortion note from the Grey Ledger syndicate demanding £150,000 or the relic by midnight.",
        repeat_inspection_narrative="Tool Cabinet 3 stands open. The debt ultimatum note and pawn ticket (E-06) have already been seized.",
    ),
    TargetId.VITRINE_LATCH: TargetNarrative(
        target_id=TargetId.VITRINE_LATCH,
        display_name="Heliodor Gallery — Vitrine Rim & Lock",
        facility_zone="Crime Scene",
        associated_evidence_id=EvidenceId.E_07,
        first_discovery_narrative="You apply a forensic swab kit and UV light to the vitrine's locking cylinder. Trace analysis reveals purple antistatic glove fibers and residue of Hexane-12 optical conservation solvent.",
        repeat_inspection_narrative="The vitrine locking cylinder shows the swab residue from forensic item E-07.",
    ),
    TargetId.TERRACE_CATERING_BAR: TargetNarrative(
        target_id=TargetId.TERRACE_CATERING_BAR,
        display_name="Terrace Bar — Catering Service Log",
        facility_zone="Public Gala",
        associated_evidence_id=EvidenceId.E_08,
        first_discovery_narrative="You review the catering order slips at the terrace bar. Slip #408 notes a Dry Martini delivered to Celeste Ward's table at 21:16 was left at an empty seat until she returned at 21:22.",
        repeat_inspection_narrative="The catering order slips (E-08) have already been cross-referenced with witness timelines.",
    ),
    TargetId.TECHNICIAN_LOCKER: TargetNarrative(
        target_id=TargetId.TECHNICIAN_LOCKER,
        display_name="Guard Quarters — Noah Reed's Locker",
        facility_zone="Staff Rooms",
        associated_evidence_id=EvidenceId.E_09,
        first_discovery_narrative="You search Noah Reed's personal backpack in the staff locker room. Inside is a USB drive containing chat logs where he agreed to test unverified switch firmware at 9:15 PM for 0.015 BTC.",
        repeat_inspection_narrative="Noah's locker has been searched; the forum chat logs and USB drive (E-09) are in custody.",
    ),
    TargetId.GALLERY_TAPESTRY: TargetNarrative(
        target_id=TargetId.GALLERY_TAPESTRY,
        display_name="Heliodor Gallery — South Tapestry & Wall",
        facility_zone="Crime Scene",
        associated_evidence_id=EvidenceId.E_10,
        first_discovery_narrative="You lift the heavy Renaissance tapestry on the south wall. Behind it is a concealed dumbwaiter service hatch leading directly into Service Corridor B, bearing fresh shoe scuffs and grease marks.",
        repeat_inspection_narrative="The tapestry remains pinned back. The dumbwaiter service hatch (E-10) is fully documented.",
    ),
    TargetId.BASEMENT_HAZMAT_04: TargetNarrative(
        target_id=TargetId.BASEMENT_HAZMAT_04,
        display_name="Basement Annex — Flammable Storage 4",
        facility_zone="Conservation",
        associated_evidence_id=EvidenceId.E_11,
        first_discovery_narrative="You search the solvent lockers in the basement annex. In Cabinet 4, a 5L steel canister labeled 'Hexane-12' feels abnormally heavy. Unscrewing the lid reveals the Obsidian Sun suspended inside a silicone bladder!",
        repeat_inspection_narrative="Cabinet 4 remains open. The weighted Hexane-12 canister (E-11) holding the relic has already been recovered.",
    ),
    TargetId.CURATOR_DESK: TargetNarrative(
        target_id=TargetId.CURATOR_DESK,
        display_name="Curator Office — Desk Drawer",
        facility_zone="Admin Wing",
        associated_evidence_id=EvidenceId.E_12,
        first_discovery_narrative="You search Dr. Sen's mahogany desk drawers and find a dictaphone. Playback reveals her frantic voice recorded at 21:16:10 worrying about looted contraband, accompanied by the 9:15 grandfather clock chime.",
        repeat_inspection_narrative="The desk drawer has been searched; Dictaphone Audio Memo #14 (E-12) is cataloged.",
    ),
}


# ============================================================================
# 5. Contradiction Rules Matrix (C-01 to C-08)
# ============================================================================

@dataclass(frozen=True)
class ContradictionRule:
    """Deterministic contradiction rule."""
    rule_id: RuleId
    suspect_id: SuspectId
    disputed_claim: str
    refuting_evidence_ids: Tuple[EvidenceId, ...]
    validation_state: str
    suspect_reaction_dialogue: str


CONTRADICTION_RULES: Dict[RuleId, ContradictionRule] = {
    RuleId.C_01: ContradictionRule(
        rule_id=RuleId.C_01,
        suspect_id=SuspectId.ELIAS_VOSS,
        disputed_claim="Claims he never entered Service Corridor B after 8:45 PM.",
        refuting_evidence_ids=(EvidenceId.E_03,),
        validation_state="ALIBI_SHATTERED",
        suspect_reaction_dialogue="Elias blinks, his composure faltering. 'I... well, yes. I swiped into the corridor for two minutes to fetch specialized lint-free cleaning rags from the auxiliary bin. That is hardly a crime.'",
    ),
    RuleId.C_02: ContradictionRule(
        rule_id=RuleId.C_02,
        suspect_id=SuspectId.ELIAS_VOSS,
        disputed_claim="Claims vitrine tools were locked in Cabinet 3 all evening.",
        refuting_evidence_ids=(EvidenceId.E_01, EvidenceId.E_07),
        validation_state="METHOD_EXPOSED",
        suspect_reaction_dialogue="Elias stares at the nitrogen shunt. His voice drops to a whisper: 'That is my custom brass calibration shunt. Someone must have taken it from my workshop... I did not leave it there.'",
    ),
    RuleId.C_03: ContradictionRule(
        rule_id=RuleId.C_03,
        suspect_id=SuspectId.ELIAS_VOSS,
        disputed_claim="Claims he has no financial problems or outside pressures.",
        refuting_evidence_ids=(EvidenceId.E_06,),
        validation_state="MOTIVE_ESTABLISHED",
        suspect_reaction_dialogue="Elias turns pale as you reveal the debt ultimatum note. 'Where did you find that? You don't understand... they threatened my family. The Grey Ledger doesn't make empty threats.'",
    ),
    RuleId.C_04: ContradictionRule(
        rule_id=RuleId.C_04,
        suspect_id=SuspectId.NOAH_REED,
        disputed_claim="Claims camera feeds never failed and live feed was uninterrupted.",
        refuting_evidence_ids=(EvidenceId.E_02,),
        validation_state="DECEPTION_BROKEN",
        suspect_reaction_dialogue="Noah grabs his hair, sweating. 'Okay! Okay, I lied! Switch 4 crashed at 9:15 PM! The screens were completely black for four minutes! I panicked because I thought I'd get fired!'",
    ),
    RuleId.C_05: ContradictionRule(
        rule_id=RuleId.C_05,
        suspect_id=SuspectId.NOAH_REED,
        disputed_claim="Claims he ran no scripts and was merely monitoring feeds.",
        refuting_evidence_ids=(EvidenceId.E_09,),
        validation_state="NEGLIGENCE_PROVEN",
        suspect_reaction_dialogue="Noah looks terrified. 'I took five hundred bucks on a forum to benchmark a firmware patch! I didn't steal the relic! I was just trying to pay my rent! Please believe me!'",
    ),
    RuleId.C_06: ContradictionRule(
        rule_id=RuleId.C_06,
        suspect_id=SuspectId.MIRA_SEN,
        disputed_claim="Claims she remained in the Ballroom greeting patrons 9:00–9:22 PM.",
        refuting_evidence_ids=(EvidenceId.E_03,),
        validation_state="ALIBI_SHATTERED",
        suspect_reaction_dialogue="Dr. Sen sighs sharply and crosses her arms. 'Very well. I left the gala at 9:10 PM. I went upstairs to my office because I had urgent private correspondence to handle.'",
    ),
    RuleId.C_07: ContradictionRule(
        rule_id=RuleId.C_07,
        suspect_id=SuspectId.MIRA_SEN,
        disputed_claim="Denies any secret appraisal or commercial valuation.",
        refuting_evidence_ids=(EvidenceId.E_04, EvidenceId.E_12),
        validation_state="FALSE_LEAD_CLEARED",
        suspect_reaction_dialogue="Dr. Sen slumps in her chair. 'Vance Sterling appraised the relic off-the-books. He discovered it was looted contraband from 1923. If anyone found out, my career was finished. I was destroying the appraisal, not stealing the piece!'",
    ),
    RuleId.C_08: ContradictionRule(
        rule_id=RuleId.C_08,
        suspect_id=SuspectId.CELESTE_WARD,
        disputed_claim="Claims she remained on the champagne terrace 9:00–9:25 PM.",
        refuting_evidence_ids=(EvidenceId.E_05, EvidenceId.E_08),
        validation_state="ALIBI_SHATTERED",
        suspect_reaction_dialogue="Celeste's icy composure breaks for an instant. 'Fine. My lighter. I slipped into the archive wing to inspect provenance ledgers the board refused to show me. But I never went near the Heliodor Gallery!'",
    ),
}


# ============================================================================
# 6. Canonical Solution Key & Recovery Truth
# ============================================================================

@dataclass(frozen=True)
class CanonicalCaseSolution:
    """Ground truth solution key for The Last Exhibition."""
    culprit_id: SuspectId
    culprit_name: str
    canonical_motive_summary: str
    motive_evidence_id: EvidenceId
    mechanical_bypass_tool_id: EvidenceId
    ingress_egress_route_id: EvidenceId
    timing_window_evidence_id: EvidenceId
    physical_link_evidence_id: EvidenceId
    recovery_evidence_id: EvidenceId
    recovery_location_summary: str
    theft_minute_exact: str


CANONICAL_SOLUTION: CanonicalCaseSolution = CanonicalCaseSolution(
    culprit_id=SuspectId.ELIAS_VOSS,
    culprit_name="Elias Voss",
    canonical_motive_summary="Extortion debt of £150,000 to 'The Grey Ledger' syndicate due by midnight tonight.",
    motive_evidence_id=EvidenceId.E_06,
    mechanical_bypass_tool_id=EvidenceId.E_01,
    ingress_egress_route_id=EvidenceId.E_10,
    timing_window_evidence_id=EvidenceId.E_02,
    physical_link_evidence_id=EvidenceId.E_07,
    recovery_evidence_id=EvidenceId.E_11,
    recovery_location_summary="Submerged in an acid-proof silicone bladder inside a 5L steel canister labeled Hexane-12 Conservation Solvent in Basement HazMat Locker 4.",
    theft_minute_exact="9:17 PM",
)


# ============================================================================
# 7. Minimum Fair Evidence Set & Documented Investigation Routes
# ============================================================================

MINIMUM_FAIR_EVIDENCE_SET: FrozenSet[EvidenceId] = frozenset({
    EvidenceId.E_01,  # Bypass Shunt
    EvidenceId.E_02,  # Switch Terminal Log
    EvidenceId.E_03,  # Keycard Swipe Log
    EvidenceId.E_06,  # Debt Note & Pawn Ticket
    EvidenceId.E_07,  # Solvent & Fiber Traces
    EvidenceId.E_10,  # Tapestry Hatch Scuffs
    EvidenceId.E_11,  # Weighted Canister / Artifact Recovery
})

INVESTIGATION_ROUTE_A_DIGITAL: Tuple[EvidenceId, ...] = (
    EvidenceId.E_02,  # Switch log
    EvidenceId.E_03,  # Keycard swipe
    EvidenceId.E_10,  # Tapestry hatch
    EvidenceId.E_06,  # Workshop debt note
    EvidenceId.E_11,  # HazMat solvent canister
)

INVESTIGATION_ROUTE_B_FORENSIC: Tuple[EvidenceId, ...] = (
    EvidenceId.E_01,  # Pedestal bypass shunt
    EvidenceId.E_07,  # Vitrine swab solvent/fiber
    EvidenceId.E_11,  # HazMat solvent canister
    EvidenceId.E_06,  # Workshop debt note
    EvidenceId.E_03,  # Keycard swipe log
)

INVESTIGATION_ROUTE_C_INTERROGATION: Tuple[EvidenceId, ...] = (
    EvidenceId.E_02,  # Confront Noah -> find switch log
    EvidenceId.E_03,  # Confront Elias -> find keycard log
    EvidenceId.E_06,  # Workshop search -> debt note
    EvidenceId.E_07,  # Vitrine swab
    EvidenceId.E_10,  # Tapestry hatch search
    EvidenceId.E_11,  # HazMat locker recovery
)
