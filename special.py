import random

class Special:
    def __init__(self, name = "", lv = 0, bonus = 0, summary = "", textFn = None, callback = None, series = 0, stars = None, once = False):
        self.name = name
        self.lv = lv
        self.bonus = bonus
        self.summary = summary
        self.textFn = textFn # must be of the form fn(sp)
        self.callback = callback # must be of form fn(sp, combat, ind)
        self.series = series
        self.stars = stars
        self.once = once

    def __str__(self):
        return self.name + " " + ("*" * self.getStars())

    def atLevel(self, lv, bonus = 0):
        return Special(self.name, lv, bonus, self.summary, self.textFn, self.callback, self.series, self.stars, self.once)

    @staticmethod
    def randomLevel(): return random.choice([0] + [1] * 4 + [2] * 6 + [3] * 4 + [4])

    def getName(self):
        if self.bonus < 1: return self.name
        elif self.bonus < 30: return self.name + " [+%d]" % (self.bonus)
        else: return self.name + " [MAX]"

    def getStars(self): 
        if self.stars is None: return self.lv + 1
        else: return self.stars

    def getText(self):
        if self.textFn is None: return self.name
        else: return self.textFn(self)

    def invoke(self, combat, ind):
        if self.callback is not None: self.callback(self, combat, ind)

    def multiplier(self): return [0.5, 0.75, 1.0, 1.25, 1.5][self.lv]
    def mxName(self): return ["0.5x", "0.75x", "1x", "1.25x", "1.5x"][self.lv]
    def nxName(self): return ["1.5x", "1.75x", "2x", "2.25x", "2.5x"][self.lv]

    def seconds(self): return [10, 20, 30, 40, 50][self.lv]
    def secName(self): return ["10s", "20s", "30s", "40s", "50s"][self.lv]

    def randomBoost(self):
        if self.lv == 4: return 1 + random.randint(0, 1)
        elif self.lv == 3: return 1 + max(random.randint(-1, 1), 0)
        elif self.lv == 2: return 1
        elif self.lv == 1: return min(random.randint(0, 2), 1)
        else: return random.randint(0, 1)
    def boostName(self): return ["50%", "67%", "100%", "133%", "150%"][self.lv]

    def levelMultiplier(self): return [5, 8, 10, 12, 15][self.lv]
    def levelMultiplierName(self): return "%dx" % (self.levelMultiplier())

def doBerserk(sp, combat, ind):
    pc = combat.pcs[ind]
    health = float(pc.hp) / pc.maxhp
    pc.maxhp = 60 * int((sp.multiplier() + 1) * pc.unit.hp + 0.5)
    pc.hp = int(health * pc.maxhp + 0.5)
    pc.tags.add("Berserk")

def doOverdrive(sp, combat, ind):
    combat.pcs[ind].att = int((sp.multiplier() + 1) * combat.pcs[ind].unit.att + 0.5)
    combat.pcs[ind].tags.add("Overdrive")

def doThaumaturgy(sp, combat, ind):
    combat.pcs[ind].rcv = int((sp.multiplier() + 1) * combat.pcs[ind].unit.rcv + 0.5)
    combat.pcs[ind].tags.add("Thaumaturgy")

def doTank(sp, combat, ind):
    combat.tank = ind
    combat.tankTime = sp.seconds()
    for pc in combat.pcs:
        pc.tags.discard("Tanking")
    combat.pcs[ind].tags.add("Tanking")

def doSniper(sp, combat, ind):
    combat.npc.hp = combat.npc.hp - 60 * sp.levelMultiplier() * combat.pcs[ind].unit.lv

def doGuardCrush(sp, combat, ind):
    combat.npc.rcv = max(int(combat.npc.unit.rcv - combat.pcs[ind].unit.att * sp.multiplier()), 0)
    combat.npc.tags.add("Guard Crushed")

def doCoverRetreat(sp, combat, ind):
    combat.isRetreat = True

def doRaise(sp, combat, ind):
    candidates = []
    for pc in combat.pcs:
        if pc.hp <= 0:
            if len(candidates) < 1 or pc.unit.lv == candidates[0].unit.lv:
                candidates.append(pc)
            elif len(candidates) > 0 and pc.unit.lv > candidates[0].unit.lv:
                candidates = [pc]
    if len(candidates) > 0:
        pc = random.choice(candidates)
        pc.hp = min(int(60 * combat.pcs[ind].rcv * sp.multiplier() + 0.5), pc.maxhp)
        pc.init = 30

def doUndying(sp, combat, ind):
    combat.pcs[ind].undying = True
    combat.pcs[ind].tags.add("Undying")

def doMantra(sp, combat, ind):
    combat.pcs[ind].bonusInit = True
    combat.pcs[ind].tags.add("Mantra")

def doBlitz(sp, combat, ind):
    lowest = None
    for pc in combat.pcs:
        if pc is not combat.pcs[ind] and (lowest is None or pc.init < lowest.init): lowest = pc
    if lowest is not None: lowest.init = 90

allSpecials = [
    Special("Berserk",
            summary = "Raises Max HP",
            textFn = lambda sp: "Max HP %s for the rest of the fight" % (sp.nxName()),
            callback = doBerserk,
            series = 1,
            once = True),
    Special("Overdrive",
            summary = "Raises ATT",
            textFn = lambda sp: "ATT %s for the rest of the fight" % (sp.nxName()),
            callback = doOverdrive,
            series = 1,
            once = True),
    Special("Thaumaturgy",
            summary = "Raises RCV",
            textFn = lambda sp: "RCV %s for the rest of the fight" % (sp.nxName()),
            callback = doThaumaturgy,
            series = 1,
            once = True),
    Special("Tank",
            summary = "Redirects damage to unit",
            textFn = lambda sp: "Take 100%% of the damage for %s" % (sp.secName()),
            callback = doTank,
            series = 1),
    Special("Sniper",
            summary = "Deals fixed damage",
            textFn = lambda sp: "Disregard enemy DEF to do %s LV damage" % (sp.levelMultiplierName()), 
            callback = doSniper,
            series = 1),
    Special("Guard Crush",
            summary = "Reduces enemy DEF",
            textFn = lambda sp: "Decrease enemy DEF by %s ATT" % (sp.mxName()), 
            callback = doGuardCrush,
            series = 1),
    Special("Cover Retreat",
            summary = "Guaranteed retreat",
            textFn = lambda sp: "Guaranteed retreat",
            callback = doCoverRetreat,
            series = 1,
            stars = 3),
    Special("Raise",
            summary = "Raises a dead unit",
            textFn = lambda sp: "Raise a dead unit and heal up to %s RCV" % (sp.mxName()),
            callback = doRaise,
            series = 1),
    Special("Undying",
            summary = "Avoids losing unit",
            textFn = lambda sp: "Unit is not lost, even if defeated in combat",
            callback = doUndying,
            series = 1,
            stars = 5),
    Special("Mantra",
            summary = "Raises initiative rate",
            textFn = lambda sp: "+%s to initiative rate" % (sp.boostName()),
            callback = doMantra,
            series = 1,
            once = True),
    Special("Blitz",
            summary = "Boosts a unit's initiative",
            textFn = lambda sp: "Boost lowest party member's initiative",
            callback = doBlitz,
            series = 1,
            stars = 4)
    ]

def makeSpecial(index, level, bonus = 0):
    return allSpecials[index].atLevel(level, bonus)

# Returns index, special
def randomSpecial():
    index = random.randint(0, len(allSpecials) - 1)
    sp = makeSpecial(index, Special.randomLevel())
    return (index, sp)
