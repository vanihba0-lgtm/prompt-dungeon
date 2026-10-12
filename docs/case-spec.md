# Prompt Dungeon: The Last Exhibition
## Canonical Mystery Case Specification (v1.1.0)

---

## 1. Case Overview & Player Objective

### 1.1 Premise
On the evening of October 12, the Blackwood Museum of Antiquities hosts "The Last Exhibition," an exclusive closed-door preview gala celebrating the unveiling of the **Obsidian Sun**—a 14th-century Mesoamerican volcanic glass relic carved with astronomical glyphs, valued in excess of $4,000,000. 

At **9:17 PM**, during a four-minute security video outage, the Obsidian Sun disappears from its pressurized inert-gas display vitrine in the Heliodor Gallery. No glass is broken, no audible or silent security trip-wires are triggered, and museum perimeter security seals all exits at **9:23 PM** when the loss is discovered.

Four individuals with specialized access, motive, or suspicious proximity were present inside the museum during the crime window.

### 1.2 Player Objective
The player acts as the Lead Detective called to the scene. The player must:
1. Interrogate the four suspects and explore accessible museum zones.
2. Uncover physical and digital evidence items (`E-01` through `E-12`).
3. Expose suspect lies and contradictions using verified forensic facts.
4. Establish the exact sequence of events, identifying the true culprit, the precise technical bypass method, the true motive, and the current hiding place of the artifact.
5. Formulate a defensible accusation that satisfies the engine's deterministic proof requirements.

### 1.3 MVP Investigation Mechanics
* **No Hard Turn Limit:** To foster deliberate deduction, the investigation does not end after an arbitrary number of player turns.
* **Static Crime Timeline:** The historical timeline of the crime (8:45 PM – 9:23 PM) is fixed ground truth. Taking investigative actions during the present interrogation does not alter the historical sequence.
* **Deterministic Engine:** All case facts, evidence states, contradictions, and scoring are governed strictly by the deterministic backend engine. LLM suspect dialogues provide flavor and conversational responsiveness, but cannot alter case logic.

---

## 2. Canonical Minute-by-Minute Timeline

The timeline below represents ground-truth reality. No suspect dialogue, AI hallucination, or player assumption can alter these events.

| Time (PM) | Location | Actor(s) | Canonical Event Description |
| :--- | :--- | :--- | :--- |
| **8:45** | Heliodor Gallery | Dr. Mira Sen, Elias Voss | Final public seal inspection of the Obsidian Sun. Vitrine atmospheric pressure stabilized at 1.05 atm. |
| **9:00** | Grand Ballroom & Terrace | All | Opening gala remarks begin. Celeste Ward is observed ordering a drink on the terrace. |
| **9:08** | Ballroom | Dr. Mira Sen | Dr. Sen receives an encrypted notification on her phone from black-market appraiser Vance Sterling demanding final fee payment for the unauthorized valuation. |
| **9:10** | Ballroom $\rightarrow$ Office | Dr. Mira Sen | Dr. Sen slips away from gala attendees and heads up the grand staircase to her private 2nd-floor office. |
| **9:12** | Curator Office | Dr. Mira Sen | Dr. Sen begins shredding physical appraisal notes and wiping emails on her private terminal. |
| **9:13** | Terrace $\rightarrow$ West Wing | Celeste Ward | Celeste Ward abandons her drink on the terrace and uses an unlocked side door to infiltrate the restricted West Archive corridor to snoop for acquisition provenance files. |
| **9:14:10** | Security Console | Noah Reed | Noah Reed, wishing to test an unauthorized third-party camera firmware patch (for which he took a $500 forum bounty) and wipe his personal web browsing logs, queues a script. |
| **9:14:48** | Security Console | Noah Reed | Noah executes `diag_cam_restart.sh` on Switch 04. The terminal hangs unexpectedly. |
| **9:15:00** | Gallery & East Wing | Cameras / System | Video feeds for the Heliodor Gallery (Cam-03) and East Corridor (Cam-04) drop to frozen static test patterns. Noah enters a state of panic trying to reboot the port. |
| **9:15:30** | Service Corridor B | Elias Voss | Elias Voss, monitoring security feeds via a tablet and anticipating Noah's diagnostic window, swipes his conservator keycard into Service Passage B. |
| **9:16:05** | Service Passage B | Elias Voss | Elias reaches the concealed maintenance dumbwaiter hatch behind the 17th-century Renaissance tapestry in the Heliodor Gallery. |
| **9:16:15** | Heliodor Gallery | Elias Voss | Elias slides through the tapestry hatch into the darkened gallery, wearing purple antistatic microfiber gloves and soft-soled lab shoes. |
| **9:16:35** | Heliodor Gallery Pedestal | Elias Voss | Using the authorized conservator nitrogen bypass shunt tool (`E-01`), Elias couples the secondary gas valve, equalizing internal pressure without triggering the atmospheric drop sensor. |
| **9:17:00** | Heliodor Gallery Pedestal | Elias Voss | **THE THEFT OCCURS.** Elias unlatches the dual-key mechanical cylinder, lifts the Obsidian Sun, wraps it in padded silicone sheeting, and places it into his tool satchel. |
| **9:17:35** | Heliodor Gallery | Elias Voss | Elias re-latches the vitrine, leaves the shunt coupled to avoid pressure alarms, and exits back through the tapestry hatch into Service Corridor B. |
| **9:18:22** | Service Passage B | Elias Voss | Elias swipes his keycard exiting Service Corridor B down into the Basement Conservation Annex. |
| **9:19:10** | Security Console | Noah Reed | Noah's terminal reboot finally clears; video feeds reconnect. Cam-03 resumes displaying the Heliodor Gallery, but the dim ambient lighting conceals that the pedestal is vacant. |
| **9:20:05** | Basement Annex | Elias Voss | Elias secretes the Obsidian Sun inside a modified 5-liter steel container labeled *Hexane-12 Conservation Solvent* in the locked Hazardous Materials cabinet. |
| **9:21:10** | West Archive Corridor | Celeste Ward | Startled by a passing security guard footsteps, Celeste flees the archive corridor, accidentally dropping her engraved gold lighter (`E-05`) near the archive door. |
| **9:21:45** | Terrace | Celeste Ward | Celeste returns to the terrace, claiming she never left and ordering a second cocktail. |
| **9:22:00** | 2nd-Floor Office | Dr. Mira Sen | Dr. Sen finishes destroying appraisal paperwork and returns downstairs to check the gallery. |
| **9:22:45** | Heliodor Gallery | Dr. Mira Sen | Dr. Sen approaches the vitrine, discovers the Obsidian Sun is missing, and triggers the emergency distress pull-station. |
| **9:23:30** | Entire Facility | Security System | Building enters automated lockdown. External exits seal. |

---

## 3. Suspect Profiles, Knowledge Boundaries, and Statements

### 3.1 Elias Voss — The Chief Conservator (Canonical Culprit)
* **Public Profile:** Veteran conservator of 14 years. Quiet, meticulous, highly respected for his restorations of delicate Mesoamerican ceramics and glass.
* **Motive:** Sinking under a £150,000 illicit gambling and forgery-authenticity debt to an underground syndicate ("The Grey Ledger"). Has received an ultimatum: pay in full or surrender the artifact by midnight tonight (`E-06`).
* **Secret:** Orchestrated the entire physical extraction. Exploited Noah's known habit of running unauthorized night scripts, utilized his personal conservator nitrogen-shunt key (`E-01`), and hid the artifact on-site in a solvent container (`E-11`).
* **Personality / Demeanor:** Controlled, soft-spoken, answers questions with technical pedantry to divert emotional scrutiny.
* **Strict Knowledge Boundaries:**
  * Knows the exact mechanical and pneumatic operation of the vitrine and the bypass shunt.
  * Knows the location of the maintenance dumbwaiter hatch behind the gallery tapestry.
  * Knows the location of chemical solvent stocks in Basement HazMat Locker 4.
  * Does **NOT** know why Dr. Sen was absent from the ballroom or that she had an illegal appraisal.
  * Does **NOT** know why Celeste Ward was snooping in the archive corridor.
  * Does **NOT** know Noah took a forum bounty (only observed previous switch reboots).
* **Truthful Statements:**
  * *"I checked the vitrine's atmospheric seal at 8:45 PM with Dr. Sen. The pressure was nominal."*
  * *"Breaking the glass would trigger the acoustic vibration sensors instantly."*
  * *"I was down in the basement restoration lab preparing mounting adhesives for tomorrow's exhibition."*
* **False / Misleading Statements:**
  * Lie 1: *"I never entered Service Corridor B or the gallery area after the 8:45 PM public inspection."* (Refuted by `E-03`).
  * Lie 2: *"All my specialized vitrine maintenance equipment, including the nitrogen equalizing shunts, remained locked in Cabinet 3 all evening."* (Refuted by `E-01` and `E-07`).
  * Lie 3: *"I have no financial complications whatsoever; my personal accounts are entirely in order."* (Refuted by `E-06`).

---

### 3.2 Dr. Mira Sen — Lead Curator
* **Public Profile:** Academic prodigy, ambitious curator who secured the loan of the Obsidian Sun. Publicly defends museum integrity.
* **Motive:** Suspected of orchestrating theft for insurance kickbacks or private sale. In reality, she feared academic ruin due to an unauthorized off-the-books provenance appraisal.
* **Secret:** Commissioned an unauthorized private appraisal from black-market authenticator Vance Sterling to discover the piece’s true illicit provenance and market value ($4.2M). Was frantically destroying the appraisal papers during the theft window (`E-04`, `E-12`).
* **Personality / Demeanor:** Defensive, intellectual, high-strung, irritable under direct challenge.
* **Strict Knowledge Boundaries:**
  * Knows museum provenance history, accession ledgers, and donor records.
  * Knows the vitrine requires dual keys, but has **zero** knowledge of how to bypass pneumatic pressure sensors.
  * Does **NOT** know who stole the artifact or how the vitrine was breached.
  * Does **NOT** know Noah's server script caused the camera outage.
  * Does **NOT** know Elias was inside Service Corridor B.
* **Truthful Statements:**
  * *"I did not take the artifact. It was the centerpiece of my life's academic curation."*
  * *"The museum would be bankrupted by the scandal if this piece vanished."*
* **False / Misleading Statements:**
  * Lie 1: *"I remained in the Grand Ballroom greeting patrons from 9:00 PM until I walked into the gallery at 9:22 PM."* (Refuted by `E-03`).
  * Lie 2: *"I have never discussed private commercial valuation of the Obsidian Sun with any third-party brokers."* (Refuted by `E-04` and `E-12`).

---

### 3.3 Noah Reed — Security Systems Technician
* **Public Profile:** Junior technician responsible for security network maintenance, console monitoring, and badge access hardware.
* **Motive:** Severely underpaid; has expressed bitter resentment against museum leadership on public message boards.
* **Secret:** Took a $500 cryptocurrency payment on a tech forum to live-test an unverified open-source firmware optimization patch on Switch 04 at 9:15 PM, combining it with a routine wipe of his personal web logs (`E-09`). The unverified patch crashed the video port for four minutes (`E-02`).
* **Personality / Demeanor:** Anxious, stammering, defensive, tech-jargon heavy when cornered.
* **Strict Knowledge Boundaries:**
  * Knows camera switch configuration, terminal IP logs, and badge reader hardware.
  * Has **zero** knowledge of conservation tools, vitrines, or Mesoamerican art.
  * Does **NOT** know who stole the artifact or how the vitrine was opened.
  * Does **NOT** know Elias entered Service Corridor B during the blackout.
* **Truthful Statements:**
  * *"I never left the security control booth between 8:00 PM and the alarm."*
  * *"I didn't take any relic. I wouldn't even know who to sell a rock like that to."*
* **False / Misleading Statements:**
  * Lie 1: *"The camera feeds never cut out; there was just a momentary ambient lighting flicker."* (Refuted by `E-02`).
  * Lie 2: *"I was actively monitoring live feeds the entire evening and ran no diagnostic operations or terminal commands."* (Refuted by `E-02` and `E-09`).

---

### 3.4 Celeste Ward — Private Antiquities Collector
* **Public Profile:** Billionaire patron of the arts, major museum donor, renowned for aggressively pursuing Mesoamerican artifacts.
* **Motive:** Made two formal multi-million-dollar acquisition bids for the Obsidian Sun that were rejected by the museum board.
* **Secret:** Trespassed into the restricted West Archive corridor between 9:13 PM and 9:21 PM attempting to photograph confidential board minutes and donor provenance records to blackmail the trustees into selling the piece (`E-05`, `E-08`).
* **Personality / Demeanor:** Aristocratic, aloof, dismissive, wields her social status and legal threats as shields.
* **Strict Knowledge Boundaries:**
  * Knows the financial value of the piece, market prices, and board politics.
  * Has **no** security system credentials, staff keys, or conservator bypass tools.
  * Does **NOT** know how the thief breached the vitrine.
  * Did not see the thief, but heard faint mechanical noises in the wall near the archive at ~9:16 PM.
* **Truthful Statements:**
  * *"I offered seven million dollars legitimately. Why would I steal something I cannot legally display in my home?"*
  * *"I heard a faint metallic clattering inside the ventilation shaft around 9:16 PM while I was... walking."*
* **False / Misleading Statements:**
  * Lie 1: *"I spent the entire evening between 9:00 PM and 9:25 PM enjoying champagne on the terrace in plain sight of the waitstaff."* (Refuted by `E-05` and `E-08`).
  * Lie 2: *"I have never stepped foot in the museum's private archive wing."* (Refuted by `E-05`).

---

## 4. Canonical Evidence Catalog (Exactly 12 Items)

| ID | Name | Location | Source | Mandatory / Optional |
| :--- | :--- | :--- | :--- | :--- |
| **E-01** | Severed Vitrine Sensor Shunt | Heliodor Gallery Pedestal Base | Physical crime scene search | **Mandatory** |
| **E-02** | Security Switch Terminal Log | Server Room Console | Digital terminal dump | **Mandatory** |
| **E-03** | Restricted Keycard Swipe Log | Security Admin Database | Access control export | **Mandatory** |
| **E-04** | Torn Appraisal Memo Fragments | Curator Office Shredder Bin | Office forensic search | Optional |
| **E-05** | Engraved Monogrammed Lighter | West Archive Hallway Floor | Physical hallway sweep | Optional |
| **E-06** | Debt Ultimatum & Pawn Ticket | Workshop Cabinet 3 | Elias Voss workspace search | **Mandatory** |
| **E-07** | Antistatic Fiber & Solvent Traces | Vitrine Locking Rim | Chemical/UV swab kit | **Mandatory** |
| **E-08** | Terrace Waitstaff Order Slip #408 | Catering Service Station | Catering records interview | Optional |
| **E-09** | Encrypted USB Drive & Forum Logs | Noah Reed's Locker Backpack | Personal locker search | Optional |
| **E-10** | Tapestry Service Hatch Scuff Marks | Service Corridor B Wall Niche | Corridor path reconstruction | **Mandatory** |
| **E-11** | Weighted Hexane-12 Solvent Canister | Basement HazMat Locker 4 | Targeted chemical storage search | **Mandatory** |
| **E-12** | Dictaphone Audio Memo #14 | Dr. Sen's Locked Desk Drawer | Office physical search | Optional |

---

### Detailed Evidence Specifications

#### `E-01`: Severed Vitrine Sensor Shunt
* **Description:** A brass micro-bore adapter equipped with a secondary pressure-relief valve and quick-release nitrogen coupling, currently attached to the intake nipple at the base of the vitrine pedestal.
* **Location:** Heliodor Gallery, recessed service panel at display pedestal base.
* **Source:** Forensic inspection of the vitrine base.
* **Discovery Conditions:** Discovered by inspecting the display pedestal or examining vitrine security mechanisms.
* **Dependencies:** None.
* **Canonical Interpretation:** Confirms that the theft did not involve brute force. The perpetrator possessed a specialized pneumatic equalizing shunt custom-built for Blackwood Museum conservation vitrines. This tool equalizes the nitrogen atmosphere to 1.05 atm during maintenance, preventing the pressure drop from triggering the central alarm.
* **Related Facts:** Excludes crude theft or external burglars; narrows technical capability to conservation personnel.
* **Status:** **Mandatory** (Required to prove Theft Method).

#### `E-02`: Security Switch Terminal Log
* **Description:** System execution log from Cisco Catalyst Switch 04 showing a bash script execution: `bash diag_cam_restart.sh -p 4 -f --force` initiated at `21:14:48` by user account `n_reed`.
* **Location:** Basement Server Room, Terminal Rack 02.
* **Source:** Digital forensic extraction of switch syslogs.
* **Discovery Conditions:** Discovered by examining the server room terminal or requesting CCTV system diagnostic logs.
* **Dependencies:** None (Can be inspected directly or prompted by questioning technician).
* **Canonical Interpretation:** Establishes the exact start and end of the camera blackout (9:14:48 PM to 9:19:10 PM). Proves the camera failure was caused internally by technician Noah Reed running an unauthorized script from his terminal, completely disproving his claim of uninterrupted live monitoring.
* **Related Facts:** Explains the video blackout without requiring a master conspirator; refutes Noah's alibi.
* **Status:** **Mandatory** (Required to establish the Blackout Window).

#### `E-03`: Restricted Keycard Swipe Log
* **Description:** Cryptographic badge access ledger for restricted service doors between 9:00 PM and 9:30 PM:
  * `21:11:04` — Card #004 (Dr. M. Sen) $\rightarrow$ Curator Office Entry
  * `21:15:30` — Card #012 (E. Voss) $\rightarrow$ Service Corridor B Entry
  * `21:18:22` — Card #012 (E. Voss) $\rightarrow$ Service Corridor B Exit (to Basement)
* **Location:** Security Administration Mainframe / Access Database.
* **Source:** Digital export of physical access logs.
* **Discovery Conditions:** Discovered by querying the electronic access database or requesting interior door records.
* **Dependencies:** None.
* **Canonical Interpretation:** Places Elias Voss inside Service Corridor B (the passage directly abutting the Heliodor Gallery) from 9:15:30 PM to 9:18:22 PM—matching the exact minute of the theft (9:17 PM). Places Dr. Sen in her office at 9:11 PM. Shows Celeste Ward has no card records.
* **Related Facts:** Destroys Elias Voss's alibi of remaining in the basement lab continuously; confirms credential presence but requires physical corroboration for guilt.
* **Status:** **Mandatory** (Required to prove Physical Proximity and Timeline).

#### `E-04`: Torn Appraisal Memo Fragments
* **Description:** Reassembled strips of 90gsm bond paper retrieved from a cross-cut paper shredder bin. Mentions: *"Confidential valuation: Obsidian Sun — $4,200,000 illicit auction ceiling. Authentication confirmed by V.S."*
* **Location:** Dr. Mira Sen's Office, under-desk shredder bin.
* **Source:** Physical forensic recovery in curator office.
* **Discovery Conditions:** Discovered by searching Dr. Sen's private office.
* **Dependencies:** Unlocking or gaining entry to Dr. Sen's office (prompted by `E-03` swipe log or interviewing guests).
* **Canonical Interpretation:** Proves Dr. Sen engaged in an illicit private appraisal with Vance Sterling. Demonstrates her guilty demeanor and lies were motivated by fear of academic scandal and dismissal, not theft.
* **Related Facts:** Disproves Dr. Sen as the physical thief while explaining her deception.
* **Status:** Optional (False lead resolution).

#### `E-05`: Engraved Monogrammed Lighter
* **Description:** Solid 18k yellow-gold Dunhill lighter engraved with the cursive initials *"C.W."*, smelling faintly of high-grade kerosene.
* **Location:** Floor of the West Archive Corridor, tucked beneath a Victorian radiator.
* **Source:** Physical search of the restricted archive corridor.
* **Discovery Conditions:** Discovered by inspecting the West Archive Corridor floor.
* **Dependencies:** None (Can be searched during a general floor sweep or after noting Celeste's absence).
* **Canonical Interpretation:** Conclusively places Celeste Ward in the restricted West Archive wing around 9:15–9:20 PM, breaking her terrace alibi. However, the archive corridor has reinforced fire doors with no physical connection to the Heliodor Gallery, confirming she was snooping on donor files rather than stealing the relic.
* **Related Facts:** Disproves Celeste Ward's alibi while clearing her of physical access to the crime scene.
* **Status:** Optional (False lead resolution).

#### `E-06`: Debt Ultimatum & Pawn Ticket
* **Description:** A crumpled handwritten note on lined paper: *"Voss — Midnight tonight or your sister's workshop burns. £150,000 cash or the Aztec glass. No police. - Grey Ledger"*, clipped to a pawn ticket for an antique Patek Philippe pocket watch dated October 11.
* **Location:** Conservation Workshop, false bottom of locked Tool Cabinet 3.
* **Source:** Targeted search of Elias Voss's private workbench.
* **Discovery Conditions:** Discovered by searching Elias Voss's workshop and opening Tool Cabinet 3.
* **Dependencies:** Investigating the Conservation Workshop.
* **Canonical Interpretation:** Establishes the real, urgent motive for the theft. Elias was under imminent threat of violent extortion with a midnight deadline, specifically demanding the Obsidian Sun ("the Aztec glass").
* **Related Facts:** Establishes Elias Voss's sole motive and urgency.
* **Status:** **Mandatory** (Required to prove Motive).

#### `E-07`: Antistatic Fiber & Solvent Traces
* **Description:** Microscopic trace analysis of the vitrine's brass rim: two purple synthetic polyester fibers matching 20-denier antistatic gloves, alongside residue of *Hexane-12*, a specialized low-volatility solvent used exclusively for optical glass conservation.
* **Location:** Heliodor Gallery Vitrine, upper rim and mechanical cylinder latch.
* **Source:** Forensic swab and UV luminescence analysis.
* **Discovery Conditions:** Discovered by swabbing the vitrine latch and lock mechanism.
* **Dependencies:** Inspecting the vitrine (`E-01` provides clear reason to swab the mechanism).
* **Canonical Interpretation:** Links the physical manipulation of the vitrine directly to the chemical supplies and standard protective equipment of the museum's conservation lab. Only Elias Voss wore purple antistatic gloves during the evening. Identifies *Hexane-12* as the chemical breadcrumb.
* **Related Facts:** Directly links the physical actor to Elias Voss's specialized equipment and chemical supplies.
* **Status:** **Mandatory** (Required to link Culprit to Method and lead to `E-11`).

#### `E-08`: Terrace Waitstaff Order Slip #408
* **Description:** Carbon order slip from the Terrace Bar:
  * `21:02` — 1x Dry Gin Martini (served to table 4, Mrs. Ward)
  * `21:16` — 1x Dry Gin Martini (delivered to table 4; table noted vacant by waiter Tom P.)
  * `21:22` — Guest returned to table 4.
* **Location:** Kitchen Catering Service Station.
* **Source:** Interview with catering manager and waiter receipts.
* **Discovery Conditions:** Discovered by reviewing catering orders or questioning catering staff about guests.
* **Dependencies:** None.
* **Canonical Interpretation:** Corroborates that Celeste Ward was absent from the terrace between 9:12 PM and 9:22 PM, corroborating the timeframe of her excursion to the archive wing.
* **Related Facts:** Solidifies the timeline of Celeste's movement.
* **Status:** Optional.

#### `E-09`: Encrypted USB Drive & Forum Logs
* **Description:** A Sandisk USB drive and printed chat transcript from `overclockers-underground.net`: user `N_Reedy` agrees to test an uncompiled custom switch firmware at 9:15 PM for 0.015 BTC to benchmark packet drops.
* **Location:** Security Guard Locker Room, inside Noah Reed's backpack.
* **Source:** Search of security technician locker.
* **Discovery Conditions:** Discovered by searching Noah Reed's locker.
* **Dependencies:** Inspecting the security staff locker area (prompted by `E-02`).
* **Canonical Interpretation:** Demonstrates that Noah Reed’s reboot of Switch 04 was reckless moonlighting and gross negligence rather than pre-planned criminal collusion with the thief.
* **Related Facts:** Clears Noah Reed of active theft conspiracy.
* **Status:** Optional.

#### `E-10`: Tapestry Service Hatch Scuff Marks
* **Description:** Fresh scraping of black shoe scuffs and industrial grease on the brass rim of a 24"x36" service dumbwaiter hatch hidden behind the 17th-century tapestry on the south wall of the Heliodor Gallery, leading into Service Corridor B.
* **Location:** Heliodor Gallery, South Wall behind tapestry / Service Corridor B wall recess.
* **Source:** Physical search of gallery perimeter or Service Corridor B.
* **Discovery Conditions:** Discovered by examining the gallery walls behind the tapestry or tracing the wall cavity in Service Corridor B.
* **Dependencies:** Inspecting Service Corridor B or performing a detailed search of the Heliodor Gallery south wall.
* **Canonical Interpretation:** Reveals the physical bypass route used to enter and exit the Heliodor Gallery without passing the security guards stationed outside the main gallery double doors.
* **Related Facts:** Solves the physical ingress/egress paradox of the locked gallery.
* **Status:** **Mandatory** (Required to prove Physical Ingress/Egress Method).

#### `E-11`: Weighted Hexane-12 Solvent Canister
* **Description:** A standard 5-liter industrial steel chemical jug labeled *"Hexane-12 — Laboratory Solvent (Flammable)"*. While the fluid volume reads 2.0 liters on the gauge, the canister weighs 5.8 kilograms (3.8 kg over normal tare weight). Inside, suspended in an acid-proof silicone bladder, is the **Obsidian Sun**.
* **Location:** Basement Conservation Annex, Flammable Storage Cabinet 4.
* **Source:** Physical search and scale-weighing of chemical lockers.
* **Discovery Conditions (Fair Investigation Path):** 
  1. *Primary Forensic Trail:* Following `E-07` (which identifies *Hexane-12* residue on the vitrine latch), the player investigates the museum's chemical inventory in the Basement Conservation Annex.
  2. *Physical Examination:* Inspecting Flammable Storage Cabinet 4 reveals canisters of Hexane-12. Examining the canisters reveals that Canister #4 has an anomalous weight (5.8 kg instead of 2.0 kg tare + fluid).
  3. *Unscrewing/Inspection:* Opening Canister #4 recovers the artifact inside the silicone bladder.
* **Dependencies:** Discovering `E-07` provides the chemical clue to search for *Hexane-12*. (Does **not** require knowing the culprit or solving motive first).
* **Canonical Interpretation:** Physical recovery of the stolen artifact. Proves the stolen item never left the building and was stashed by Elias Voss for extraction prior to his midnight meeting.
* **Related Facts:** Unquestionable proof of the artifact's location and physical possession.
* **Status:** **Mandatory** (Required for Definitive Recovery & Accusation).

#### `E-12`: Dictaphone Audio Memo #14
* **Description:** A microcassette dictaphone recording timestamped `21:16:10`: Dr. Sen’s voice, breathing rapidly: *"Sterling called again. If the board discovers the 14th-century Mesoamerican provenance is looted contraband from the 1923 Oaxaca expedition... my career is finished. I have to burn the ledger."* In the background, the museum grandfather clock chimes the single quarter-hour bell (9:15 PM).
* **Location:** Dr. Mira Sen's private desk drawer.
* **Source:** Office search.
* **Discovery Conditions:** Discovered by opening the locked drawer in Dr. Sen's desk.
* **Dependencies:** Gaining access to Dr. Sen's office.
* **Canonical Interpretation:** Conclusively proves Dr. Sen was inside her private office on the second floor at 9:16 PM, listening to her own recordings and panicking about provenance scandal, making it physically impossible for her to be in the Heliodor Gallery at 9:17 PM.
* **Related Facts:** Solidifies Dr. Sen's absolute physical alibi during the crime minute.
* **Status:** Optional.

---

## 5. Theft Method and Technical Vulnerability Exploitation

### 5.1 The Security Vulnerabilities
1. **The Pneumatic/Atmospheric Alarm:** The Obsidian Sun sat on a pressure-sensitive load cell inside a hermetically sealed vitrine charged with dry nitrogen at 1.05 atmospheres. An uncoupling of the vitrine or drop in pressure below 1.02 atm instantly trips a hardwired alarm to Central Dispatch.
2. **The CCTV Monitoring:** The Heliodor Gallery is monitored by fixed camera Cam-03, transmitting 1080p video over Ethernet to Cisco Switch 04 in the basement server room.
3. **The Physical Ingress:** The double doors to the gallery were guarded by two stationary security contractors. However, an unmonitored historic dumbwaiter service hatch (used for moving heavy restoration equipment) connects Service Corridor B directly to the Heliodor Gallery behind a heavy wall tapestry.

### 5.2 The Exact Exploitation Sequence
1. **Timing the Blinding:** Elias Voss knew Noah Reed's habit of running unapproved maintenance scripts at the start of night shifts. By observing Noah's terminal activity or anticipating the scheduled diagnostic window, Elias timed his entry into Service Corridor B for **9:15:30 PM**, immediately after Noah crashed Switch 04 at **9:14:48 PM**.
2. **Hidden Ingress:** Elias entered Service Corridor B using his authorized conservator keycard (`E-03`). He crawled through the concealed maintenance hatch behind the Renaissance tapestry (`E-10`), bypassing the guards at the main doors without alerting them.
3. **Pneumatic Bypass:** Rather than prying or smashing the glass, Elias connected a customized brass nitrogen equalizing shunt (`E-01`) to the external calibration nipple at the vitrine base. This shunt maintained artificial back-pressure on the sensor while allowing the glass bell to be lifted.
4. **Physical Extraction:** Wearing purple antistatic gloves to leave no fingerprints, Elias unlocked the mechanical dual-cylinder latch with his conservator key. While doing so, residue of *Hexane-12* solvent on his gloves transferred onto the brass latch rim (`E-07`). He lifted the Obsidian Sun at **9:17:00 PM**, wrapped it in silicone, and secured the lid.
5. **Egress and Stashing:** Elias exited via the tapestry hatch back into Service Corridor B at **9:17:35 PM** and swiped out to the basement at **9:18:22 PM** (`E-03`).
6. **Concealment:** In the Basement Conservation Annex, Elias submerged the artifact inside a 5L steel canister of Hexane-12 solvent (`E-11`) in HazMat Cabinet 4, knowing chemical lockers are hazardous and unlikely to be searched during standard police bag checks.

---

## 6. Explicit Contradiction Matrix

The engine validates contradictions deterministically. When a player presents an evidence item against a suspect statement, the engine matches against the rule table below.

### 6.1 Validation Prerequisites
A contradiction rule is **only** validated when both conditions are satisfied in the session state:
1. The suspect's false statement has been elicited and recorded in the active conversation history (`statement_recorded == true`).
2. The refuting evidence has been discovered by the player (`evidence_status == DISCOVERED`) and explicitly presented during interrogation.

| Rule ID | Suspect | Disputed Statement / Claim | Refuting Evidence | Required Engine Pre-conditions | Validation State Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C-01** | **Elias Voss** | Claims he never entered Service Corridor B after 8:45 PM. | `E-03` (Keycard Swipe Log) | Elias made Lie 1; `E-03` presented. | **ALIBI_SHATTERED**: Elias admits entering corridor, claiming he was fetching cleaning rags. |
| **C-02** | **Elias Voss** | Claims vitrine tools were locked in Cabinet 3 all evening. | `E-01` (Bypass Shunt) & `E-07` (Solvent/Fiber) | Elias made Lie 2; `E-01` or `E-07` presented. | **METHOD_EXPOSED**: Elias is confronted with physical proof his tools breached the case. |
| **C-03** | **Elias Voss** | Claims he has no financial problems or outside pressures. | `E-06` (Debt Ultimatum Note) | Elias made Lie 3; `E-06` presented. | **MOTIVE_ESTABLISHED**: Elias's criminal urgency and midnight deadline are confirmed. |
| **C-04** | **Noah Reed** | Claims camera feeds never failed and live feed was uninterrupted. | `E-02` (Switch Terminal Log) | Noah made Lie 1; `E-02` presented. | **DECEPTION_BROKEN**: Noah admits switch port crashed and he hid it out of fear of firing. |
| **C-05** | **Noah Reed** | Claims he ran no scripts and was merely monitoring feeds. | `E-09` (Forum Chat & USB) | Noah made Lie 2; `E-09` presented. | **NEGLIGENCE_PROVEN**: Noah confesses to the $500 forum bounty and clearing logs; cleared of conspiracy. |
| **C-06** | **Dr. Mira Sen** | Claims she remained in the Ballroom greeting patrons 9:00–9:22 PM. | `E-03` (Card Swipe Log) | Dr. Sen made Lie 1; `E-03` presented. | **ALIBI_SHATTERED**: Dr. Sen admits retreating to her private office. |
| **C-07** | **Dr. Mira Sen** | Denies any secret appraisal or commercial valuation. | `E-04` (Torn Appraisal) & `E-12` (Dictaphone) | Dr. Sen made Lie 2; `E-04` or `E-12` presented. | **FALSE_LEAD_CLEARED**: Dr. Sen confesses to unauthorized appraisal; cleared of physical theft. |
| **C-08** | **Celeste Ward**| Claims she remained on the champagne terrace 9:00–9:25 PM. | `E-05` (Monogrammed Lighter) & `E-08` (Waiter Slip) | Celeste made Lie 1; `E-05` or `E-08` presented. | **ALIBI_SHATTERED**: Celeste admits snooping in archive wing; cleared of entering gallery. |

---

## 7. False Leads and Refutations

### 7.1 False Lead A: The Curator's Black-Market Sale (Dr. Mira Sen)
* **Suspicious Clues:** Dr. Sen slipped away from the party at 9:10 PM, lied about her whereabouts, and was caught shredding appraisal documents (`E-04`) valuing the artifact at $4.2M.
* **Why Players Bite:** Seems like the classic inside job: high-profile curator selling off museum inventory before an audit.
* **How to Disprove:**
  1. Card swipe log `E-03` records her swiping into her 2nd-floor office at 9:11 PM and staying there until 9:22 PM.
  2. Dictaphone audio memo `E-12` records her voice panicking in her office at 9:16 PM, backed by the 9:15 PM grandfather clock chime.
  3. She possesses no conservator tools to bypass the nitrogen pressure sensor (`E-01`).

### 7.2 False Lead B: The Inside Hacker / Remote Heist (Noah Reed)
* **Suspicious Clues:** The security camera feed cut out precisely between 9:14:48 PM and 9:19:10 PM. Noah's user account ran the crash script `diag_cam_restart.sh` (`E-02`). Noah lied and claimed the feed was fine.
* **Why Players Bite:** It looks like Noah disabled the cameras to steal the artifact or was paid to coordinate with an outside crew.
* **How to Disprove:**
  1. Forum chat logs and USB drive `E-09` prove Noah was acting alone for a paltry $500 forum bounty to test open-source firmware, panicking when the switch crashed.
  2. Noah never left the security booth; door logs show zero badge swipes for him during the entire evening.
  3. Noah has no access to the vitrine mechanical keys or the bypass shunt (`E-01`).

### 7.3 False Lead C: The Greedy Billionaire Collector (Celeste Ward)
* **Suspicious Clues:** Celeste had two multi-million dollar acquisition offers rejected. Her gold lighter `E-05` is found in the restricted corridor, and the terrace waiter slip `E-08` proves she went missing right during the theft.
* **Why Players Bite:** Obvious motive, aggressive personality, caught in a direct lie with physical evidence on the restricted floor.
* **How to Disprove:**
  1. The West Archive corridor where her lighter was dropped has sealed steel security doors that do not connect to the Heliodor Gallery.
  2. She had no mechanical keys, no access to Service Corridor B, and no knowledge of the tapestry dumbwaiter hatch.
  3. She was seeking paperwork (donor and provenance ledgers) rather than the physical object.

---

## 8. Optional Clue Chains and Narrative Twist

### 8.1 The Narrative Twist: The Relic Was Never Snatched to Leave the Building
* **The Assumption:** Most detectives assume an artifact stolen during a gala was passed to an accomplice out a window, thrown into a getaway car, or snuck out in a handbag before lockdown.
* **The Reality:** Elias Voss knew museum lockdown procedures would trigger the moment the theft was noticed. He never intended to walk out with it during the gala. Instead, he utilized the building's own high-hazard chemical storage (`E-11`) as a dead-drop cache.
* **The Twist Reveal:** The artifact is still inside the building, sitting 30 feet below the gallery in a bucket of toxic solvent, intended for retrieval during his regular Monday waste disposal shift.

### 8.2 Optional Clue Chains
* **Chain 1 (The Paper Trail):** `E-08` (Terrace slip) $\rightarrow$ Interrogate Celeste $\rightarrow$ Search West Archive $\rightarrow$ Discover `E-05` (Lighter) $\rightarrow$ Expose Celeste's corporate espionage without solving the main theft.
* **Chain 2 (The Academic Scandal):** `E-03` (Curator office swipe) $\rightarrow$ Search Office $\rightarrow$ Discover `E-04` (Shreds) & `E-12` (Dictaphone) $\rightarrow$ Expose Dr. Sen's fraudulent provenance records.
* **Chain 3 (The Cyber Trail):** `E-02` (Switch log) $\rightarrow$ Confront Noah $\rightarrow$ Search Locker $\rightarrow$ Discover `E-09` (USB drive) $\rightarrow$ Clear the security room of theft complicity.

---

## 9. Canonical Solution Key

The Canonical Solution Key is the ground truth against which all accusations are scored. It is stored internally by the engine and **never exposed** in player-facing API responses.

1. **The Culprit:** **Elias Voss** (Chief Conservator).
2. **The Motive:** Extortion debt of £150,000 to "The Grey Ledger" criminal syndicate due by midnight tonight (`E-06`).
3. **The Ingress/Egress Route:** Entered through the concealed service dumbwaiter hatch behind the 17th-century tapestry via Service Corridor B (`E-03`, `E-10`).
4. **The Technical Bypass:** Used a custom nitrogen atmospheric bypass shunt (`E-01`) coupled to the pedestal valve, neutralizing the pressure sensor without tripping alarms or breaking glass.
5. **The Timing Window:** Exploited Noah Reed's accidental 9:15–9:19 PM camera outage (`E-02`) to execute the theft at exactly 9:17 PM.
6. **The Current Location of the Relic:** Submerged in an acid-proof bladder inside the weighted 5L *Hexane-12* solvent canister in Basement HazMat Locker 4 (`E-11`).

---

## 10. Accusation, Scoring, and Penalty Criteria

When the player triggers the formal accusation endpoint (`POST /api/v1/case/accuse`), the game engine validates the submission across four distinct dimensions.

### 10.1 Dimension Scoring Breakdown (Base: 100 Points)

| Dimension | Points | Criteria for Full Score |
| :--- | :---: | :--- |
| **Culprit Identification** | **25 pts** | Must strictly identify `Elias Voss`. Naming any other suspect yields 0 for this category and marks the attempt as failed. |
| **Motive Explanation** | **25 pts** | Must cite his syndicate gambling/forgery debt and midnight deadline. Supported by evidence `E-06`. |
| **Method & Ingress/Egress**| **25 pts** | Must explain the nitrogen bypass shunt (`E-01`), the tapestry service hatch route (`E-10`), and the camera outage timing (`E-02`). |
| **Artifact Recovery** | **25 pts** | Must name the exact hiding location: the Hexane-12 solvent canister in the basement HazMat locker (`E-11`). |

### 10.2 Accusation Grade Scale
* **90 – 100 Points (Master Detective / S-Rank):** Perfect accusation with correct culprit, motive, method, recovery location, and minimum fair evidence set presented without unrefuted false leads.
* **75 – 89 Points (Senior Inspector / A-Rank):** Correct culprit, method, and recovery location, but minor omissions in motive or one supporting physical link.
* **50 – 74 Points (Probationary Sleuth / B-Rank):** Correct culprit and basic method, but failed to locate the artifact (`E-11`) or failed to explain the pneumatic bypass.
* **< 50 Points (Case Dismissed / Failure):** Accused wrong suspect (Mira Sen, Noah Reed, or Celeste Ward) or failed to meet minimum evidence requirements.

### 10.3 Failed Accusation Rules & Penalties
To allow learning while preventing brute-force guessing:
1. **Investigation Continues:** A failed accusation does not trigger immediate "Game Over". The player may return to the investigation, interview suspects, and discover missing evidence.
2. **Deterministic Score Penalty:** Each failed accusation deducts **15 points** from the final calculated score (minimum score clamped to 0).
3. **No Solution Leaks:** If an accusation fails, the response states that the charges were rejected by the District Magistrate due to insufficient proof or wrongful indictment. It **never** reveals which parts were correct, who the real culprit was, or what evidence was missing.
4. **Anti-Spam / Repeat Protection:** Submitting the exact same accusation without gathering new evidence or updating the theory does not re-score or reveal hints.
5. **Maximum Attempts:** A maximum of **3 accusation attempts** are permitted per case session. Upon a 3rd failed attempt, the case is officially closed as "Botched Investigation / Case Dismissed".

---

## 11. Alternative Investigation Paths & Minimum Fair Evidence Set

### 11.1 The Minimum Fair Evidence Set
A careful player does not need to collect all 12 evidence items to solve the mystery. The **Minimum Fair Evidence Set** required for an indisputable conviction consists of:

$$\text{Minimum Fair Set} = \{\mathbf{E\text{-}01}, \mathbf{E\text{-}02}, \mathbf{E\text{-}03}, \mathbf{E\text{-}06}, \mathbf{E\text{-}07}, \mathbf{E\text{-}10}, \mathbf{E\text{-}11}\}$$

* `E-01` (Bypass Shunt) — Proves conservator-grade tool used.
* `E-02` (Switch Log) — Proves camera blackout window was 9:15–9:19 PM.
* `E-03` (Keycard Swipe Log) — Proves Elias was in Service Corridor B at 9:15–9:18 PM.
* `E-06` (Debt Note) — Proves Elias's motive and midnight deadline.
* `E-07` (Solvent/Fiber) — Connects Elias's gloves and solvent to the vitrine lock.
* `E-10` (Hatch Scuffs) — Proves ingress from Service Corridor B into the gallery.
* `E-11` (Weighted Canister) — Recovers the stolen artifact in Elias's workspace locker.

Items `E-04`, `E-05`, `E-08`, `E-09`, and `E-12` are **Optional Clarifiers** used to disprove false leads and clear innocent suspects.

### 11.2 Three Viable Investigation Paths

```
                             [Crime Discovered: 9:23 PM]
                                          |
                +-------------------------+-------------------------+
                |                                                   |
      [Path A: Cyber/Log First]                                 [Path B: Forensics First]
                |                                                   |
         Inspect Server Console                              Examine Vitrine Base
             -> Find E-02                                        -> Find E-01 (Shunt)
                |                                                   |
      Export Keycard Log E-03                             Forensic Swab E-07 (Solvent/Fiber)
                |                                                   |
       Spot Voss Swipe (21:15)                               Follow Chemical Clue
                +-------------------------+-------------------------+
                                          |
                                    [Convergence]
                         Inspect Service Corridor B -> E-10
                         Search Workshop Cabinet -> E-06 (Debt)
                         Search HazMat Locker -> E-11 (Recovery)
                                          |
                              [Defensible Accusation]
```

* **Path A (The Digital Route):** Server log `E-02` $\rightarrow$ Access logs `E-03` $\rightarrow$ Corridor B hatch `E-10` $\rightarrow$ Workshop search `E-06` $\rightarrow$ HazMat solvent recovery `E-11`.
* **Path B (The Forensic Route):** Pedestal inspection `E-01` $\rightarrow$ Vitrine rim swab `E-07` $\rightarrow$ HazMat solvent search `E-11` $\rightarrow$ Workshop search `E-06` $\rightarrow$ Access logs `E-03`.
* **Path C (The Interrogation Route):** Question Noah $\rightarrow$ Catch camera lie $\rightarrow$ Uncover `E-02` $\rightarrow$ Interrogate Elias $\rightarrow$ Catch corridor lie using `E-03` $\rightarrow$ Physical search of workshop `E-06`, `E-07`, `E-10`, `E-11`.

---

## 12. Engine & Game Integrity Rules

To guarantee deterministic gameplay and prevent LLM non-determinism from undermining the game mechanics, the game engine enforces these strict boundary rules:

1. **Deterministic Truth Ledger Separation:**
   * The Truth Ledger maintains three distinct data sets:
     * `Facts`: Ground-truth states verified by evidence (immutable once discovered).
     * `Contradictions`: Engine-evaluated logical collisions between suspect statements and discovered evidence.
     * `Hypotheses`: Player-formulated theories (mutable, unverified until accusation).
2. **Dialogue Cannot Mutate Truth:**
   * LLM suspect responses are purely conversational roleplay layers conditioned on suspect knowledge boundaries.
   * An LLM suspect *cannot* generate new evidence, invalidate existing evidence, or confess to the crime unless the player has validated all mandatory contradiction requirements in the engine.
3. **Structured Action Inputs & Server Validation:**
   * All game actions (examinations, evidence presentations, theory updates, accusations, resets) must be submitted via structured API actions (`action_type`, `target_id`, `session_id`).
   * Interrogation questions remain free-form text.
   * The server validates session ownership, target validity, and whether an evidence item has been formally discovered before allowing it to be presented.
4. **Evidence Discovery Gating:**
   * A suspect mentioning an evidence item (e.g., *"Noah had an argument at the switch rack"*) does **not** unlock `E-02`.
   * Evidence can only be unlocked through explicit player actions (e.g., `inspect_location`, `analyze_item`, `request_log`) executed by the backend engine.
5. **No Guilt by Credential or Motive Alone:**
   * An access log swipe (`E-03`) proves corridor presence, not theft.
   * A motive document (`E-06` or `E-04`) proves financial distress, not guilt.
   * The engine strictly rejects accusations that do not connect motive to the physical breach and artifact recovery.
6. **Solution Key Isolation:**
   * Internal solution keys and guilt flags are never serialized in player-facing responses.
7. **Offline-Playable Authorial Fallbacks:**
   * If an LLM API call fails, times out, or lacks credentials, the engine returns pre-authored deterministic fallback dialogue.
   * The response transparently flags `is_fallback: true` and `model_status: "offline" | "fallback"`.
   * All forensic mechanics, evidence discovery, and contradiction validation function identically with or without model access.

---

## 13. Resolved Architectural Decisions & Review Approvals

Following Abhinav's review, the core architectural decisions are finalized as follows:

| # | Architecture Domain | Review Decision | Implementation Specification |
| :- | :--- | :--- | :--- |
| **1** | **Turn Limit & Clock** | **No hard turn limit in MVP** | The crime timeline remains frozen as canonical history. Player investigation turns do not increment the crime clock. No premature game over for exploring thoroughly. |
| **2** | **Dialogue Context** | **Bounded per-suspect history** | Interrogations use a sliding window of recent conversation history (last 6 turns per suspect). Fixed persona instructions and strict knowledge boundaries are injected into every prompt. Facts and evidence remain engine-managed. |
| **3** | **Failed Accusations** | **Continuable with penalty** | Players can continue investigating after a failed accusation. Each failure applies a deterministic -15 pt penalty (clamped at 0). Max 3 attempts per session. Solution is never revealed on failure. |
| **4** | **Action Input Format** | **Structured API actions** | API actions use typed request payloads (`action_type`, `target_id`, etc.). Interrogation prompt text is free-form. Server validates session ownership and evidence discovery state before processing. |
| **5** | **LLM Fallback Strategy** | **Deterministic authored fallback** | Authored fallback dialogue trees are provided for each suspect and evidence topic. Model status is reported honestly (`model_status`). Full game engine remains 100% playable offline without API keys. |

### Outstanding Design Considerations for API Contract Phase
With the core game logic locked, the following low-level implementation details will be finalized during the upcoming API contract design:
1. **Session State Storage:** In-memory dictionary with UUID session tokens vs. lightweight SQLite persistence for active sessions.
2. **Interrogation Prompt Payload Size:** Maximum token allocation for per-suspect sliding history windows.
3. **Evidence Presentation Format:** Whether presenting evidence is an explicit endpoint (`POST /interrogate/present-evidence`) or a field on the general interrogation payload (`{ "message": "...", "presented_evidence_id": "E-03" }`).

---
*End of Canonical Specification — The Last Exhibition (v1.1.0)*
