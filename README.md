R+R
===

This is a "spreadsheet-based" low-interaction RPG I built while exploring wxPython. Excuse my awful design patterns.

In a perfect world, there would be more explanation on rules and objectives, but all I'm giving you is dependencies:

wxPython 3.x should suffice, although it was originally built on 2.8.x and Python 2.7.

The following are the notes that need to be better-organized in the future.

Notes
=====

For 1.0:

* Last revisions to Series 1 units
* Finalize UI

For 1.1:

* Release Series 2
* Save combat status
* Investigate SQLite

For 1.2:

* Raid bosses
* UI improvements
* SQLite implemented

Bugs
====

Deal with two simultaneous successes

Bolstering with a dead unit does not remove that dead unit?

v1.0 Mechanics
==============

Specials
--------

Undying needs to be revised, because the only scenario where it's useful is if the team is wiped. A reraise would be comparable in power to Series 2's Overshield, except that Overshield can be recharged. How much health should reraise generate?

Proposed fix to Undying:

(*****): Upon death, automatically revive to full health and 0% initiative.

Cover retreat is also almost useless, but it might still be worth leaving it. Not every special has to be highly useful.

v1.1 Mechanics
==============

Series 2 Specials
-----------------

*Note: Many of these only make sense if tagging units in combat view is implemented*

Lux - Show DPS / damage received for each unit and time to success/failure

Drain - Damage the enemy to heal self (how much?)

Gambler - Available special picked at random

Selfish - Heal self for ?x RCV

Fever - Increase ATT / RCV for 60s

Shuffle - Rearrange stats at random with party

Daredevil - Dramatically increase ATT, but drop RCV to 0

Power Healer - Dramatically increase RCV, but drop ATT to 0

Amorphous - Randomly redistribute base stats (lasts outside combat)

Overshield - Absorb the next ?x RCV damage

Toxic Shock - Poisons enemy for ? damage per minute (for how long?)

Regen - Recover ? HP per minute (for how long?)

Database transition
-------------------

Would need to eliminate the flat file entirely

How would ongoing combat be saved?

v1.2 Mechanics
==============

Raids
-----

Raid bosses - guaranteed rewards and stats

Some rewards that might be feasible:

SP+ increases by one

Level increases by one

UI and QoL
----------

* Better "inspect" view (double-click dialog), showing series
* Sort units or favorite
* Deal with spaces in unit names
* Better bolster UI

Future Updates
==============

Passive skills
--------------

Some specials might get both an active and a passive component

Perhaps skills that generate value over time or decrease in value over time. Others might change stat growth or odds of different random processes.

Fortuitous gain
---------------

A loot table to choose from / receive at random

+HP, +ATT, +RCV, +IQ, +FIT, +LV, +SPLV

Reroll mechanic?

Sacrifice or Reinforce
----------------------

Reinforce mechanic: This might make the "cover retreat" units worth something

Sacrifice units

Combining units - Higher unit is bolstered by smaller unit / first by second

Commit units to raise rate?
