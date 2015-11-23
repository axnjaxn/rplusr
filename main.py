import os, random, time
import wx

from special import *

TEST_SPECIALS = False
USE_CHEAT_PROTECTION = True

class PCunit:
    counter = 1

    def __init__(self, name = ""):
        self.name = name
        self.hp = 0
        self.att = 0
        self.rcv = 0
        self.iq = 100
        self.fit = 4.0
        self.lv = 1
        self.ident = 0
        self.sp, self.spid = (None, 0)
        self.cooldown = 0

    def __str__(self):
        return "[%s Lv. %d] HP: %d ATT: %d RCV: %d IQ: %d FIT: %s" % (self.name, self.lv, self.hp, self.att, self.rcv, self.iq, self.getFitGrade())

    def getFitGrade(self):
        if self.fit >= 6.0: return 'A'
        elif self.fit >= 5.0: return 'B'
        elif self.fit >= 3.0: return 'C'
        elif self.fit >= 2.0: return 'D'
        else: return 'E'

    def checkLevelUp(self, rolls = 1):
        bonusRolls = (self.iq - 100) / 5
        if random.randint(1, 5) <= self.iq % 5: bonusRolls = bonusRolls + 1
        rolls = max(rolls + bonusRolls, 1)

        for i in range(rolls):
            if random.randint(1, 100) > self.lv: return True

        return False

    def levelUp(self):
        self.lv = self.lv + 1
        gains = 1.0 + 0.01 * self.fit
        self.hp = int(self.hp * gains + 0.5)
        self.att = int(self.att * gains + 0.5)
        self.rcv = int(self.rcv * gains + 0.5)
        
    @staticmethod
    def nextCounter():
        ident = PCunit.counter
        PCunit.counter = PCunit.counter + 1
        return ident

    @staticmethod
    def randomName():
        names = ["Adam", "Bruce", "Chris", "Dave", "Edward",
                 "Frank", "George", "Hilbert", "Ian", "John",
                 "Karl", "Lawrence", "Mark", "Neil", "Orville",
                 "Pubert", "Quincy", "Robert", "Steve", "Terrence",
                 "Ulysses", "Vincent", "William", "Xavier", "Young", "Zachary"]
        return names[random.randint(0, len(names) - 1)]

    @staticmethod
    def randomNPCName():
        names = ["Asmodeus", "Behemoth", "Cezar", "Devilot", "Egon",
                 "Fredo", "Goliath", "Haman", "Izalith", "Judas",
                 "Kappa", "Lemarche", "Mandrill", "Nosferatu", "Oz",
                 "Pell", "Quark", "Regent", "Salamander", "Trent",
                 "Uno", "Victor", "Winchester", "X-Type", "Yelgeth", "Zookeeper"]
        return names[random.randint(0, len(names) - 1)]

    @staticmethod
    def rollPC(level = 1):
        pc = PCunit(PCunit.randomName())
        pc.ident = PCunit.nextCounter()

        potential = random.randint(0, 150)
    
        pc.hp = random.randint(0, potential)
        potential = potential - pc.hp
        pc.hp = pc.hp + 50

        pc.att = random.randint(0, potential)
        potential = potential - pc.att
        pc.att = pc.att + 50

        pc.rcv = 50 + potential

        pc.iq = int(random.gauss(100, 10))

        pc.fit = random.gauss(4.0, 1.0)
        if pc.fit < 0.5: pc.fit = 0.5

        pc.spid, pc.sp = randomSpecial()

        for i in range(level - 1):
            pc.levelUp()

        return pc

    @staticmethod
    def rollNPC(pcs):
        npcs = []

        for pc in pcs:
            npc = PCunit.rollPC()
            fit = random.gauss(5.0, 1.0)
            npc.hp = npc.hp + 10
            npc.att = npc.att + 5
            npc.rcv = npc.rcv - 15
            for i in range(pc.lv): npc.levelUp()
            npcs.append(npc)

        for npc in npcs[1:]:
            npcs[0].lv = npcs[0].lv + npc.lv - 1
            npcs[0].hp = npcs[0].hp + npc.hp
            npcs[0].att = npcs[0].att + npc.att
            npcs[0].rcv = npcs[0].rcv + npc.rcv

        npcs[0].name = PCunit.randomNPCName()

        return npcs[0]

    def canBolster(self, unit):
        if self.spid != unit.spid or unit.sp.bonus >= 30 or self.lv < 5: return False
        elif self.sp.getStars() >= unit.sp.getStars(): return True
        else: return self.sp.getStars() == unit.sp.getStars() - 1 and self.sp.bonus >= 1

    # Returns True if bolstering raises level
    def bolster(self, unit):
        if not self.canBolster(unit): return False
        success = False
        rolls = self.sp.bonus + 1
        if unit.sp.getStars() > self.sp.getStars(): rolls = rolls - (unit.sp.getStars() - self.sp.getStars())
        for i in range(rolls):
            pfail = 0.75 * (unit.sp.bonus + 1) / 30.0
            if random.random() >= pfail and unit.sp.bonus < 30:
                unit.sp.bonus = unit.sp.bonus + 1
                success = True
        return success

class CombatEntry:
    def __init__(self, unit):
        self.unit = unit
        self.hp = self.maxhp = unit.hp * 60
        self.att = unit.att
        self.rcv = unit.rcv
        self.init = 30 + unit.iq - 110 + random.randint(-10, 10)
        self.defn = False
        self.undying = False
        self.bonusInit = False
        self.tags = set()

    def readySP(self):
        return self.init >= 90 - self.unit.sp.bonus

    def getTags(self):
        if len(self.tags) == 0: return ""
        s = "Status:"
        for tag in self.tags: s = s + " " + tag
        return s

class CombatNPCEntry:
    def __init__(self, unit):
        self.unit = unit
        self.hp = self.maxhp = unit.hp * 60
        self.att = unit.att
        self.rcv = unit.rcv
        self.tags = set()

    def getTags(self):
        if len(self.tags) == 0: return ""
        s = "Status:"
        for tag in self.tags: s = s + " " + tag
        return s

class Combat:
    def __init__(self, pcs, npc):
        self.pcs = map(CombatEntry, pcs)
        self.npc = CombatNPCEntry(npc)
        self.isRetreat = False
        self.tank = None
        self.tankTime = 0

    @staticmethod
    def displayHP(hp):
        if hp > 0: return max(hp / 60, 1)
        else: return 0

    @staticmethod
    def displayINIT(init):
        if init >= 90: return "MAX"
        elif init < 30: return "-%d%%" % (100 * (30 - init) / 30)
        else: return "%d%%" % (100 * (init - 30) / 60)

    def getDamageWeights(self):
        if self.tankTime > 0:
            if self.pcs[self.tank].hp > 0:
                dmg = [0.0] * len(self.pcs)
                dmg[self.tank] = 1.0
                return dmg
            else:
                self.tankTime = 0
        return self.getHealWeights()

    def getHealWeights(self):
        dmg = []
        for pc in self.pcs:
            if pc.hp > 0: dmg.append(1.0 / pc.unit.lv)
            else: dmg.append(0)
        s = sum(dmg)
        if s > 0.0: 
            s = 1.0 / s
            for i in range(len(dmg)): dmg[i] = dmg[i] * s
        return dmg

    def tick(self):
        att = 0
        for pc in self.pcs:
            if pc.hp > 0:
                if not pc.defn:
                    att = att + pc.att
                    pc.init = min(pc.init + 1, 90)
                    if pc.bonusInit:
                        pc.init = min(pc.init + pc.unit.sp.randomBoost(), 90)
                else:
                    pc.init = min(pc.init + random.randint(0, 1), 90)
            else:
                pc.init = 0

        dmg = self.getDamageWeights()
        if self.tankTime > 0: self.tankTime = self.tankTime - 1
        elif self.tank is not None:
            self.pcs[self.tank].tags.discard("Tanking")
            self.tank = None

        att = max(att - self.npc.rcv, 1)
        self.npc.hp = self.npc.hp - att

        if self.npc.hp <= 0: return

        for i in range(len(dmg)):
            received = max(int(self.npc.att * dmg[i]), 1)
            if self.pcs[i].defn:
                received = max(received - self.pcs[i].rcv, 0)
            self.pcs[i].hp = self.pcs[i].hp - received
            
            if self.pcs[i].hp <= 0 and self.pcs[i].undying:
                self.pcs[i].undying = False
                self.pcs[i].tags.discard("Undying")
                self.pcs[i].hp = 60 * self.pcs[i].unit.hp
                self.pcs[i].init = 30

    def heal(self, ind):
        power = min(self.pcs[ind].init - 30, 60)
        if power <= 0: return False
        self.pcs[ind].init = 0

        dmg = self.getHealWeights()
        
        for i in range(len(self.pcs)):
            if self.pcs[i].hp <= 0: continue
            self.pcs[i].hp = min(self.pcs[i].hp + int(dmg[i] * power * self.pcs[ind].rcv), self.pcs[i].maxhp)

        return True

    def special(self, ind):
        if not TEST_SPECIALS and not self.pcs[ind].readySP(): return False
        self.pcs[ind].init = 30
        self.pcs[ind].unit.sp.invoke(self, ind)
        return True

    def defend(self, ind, toDefend = True):
        self.pcs[ind].defn = toDefend

    def getRetreatChance(self):
        total = 0.0
        for pc in self.pcs:
            power = (pc.init - 30) / 60.0
            if power < 0.0: continue

            letter = pc.unit.getFitGrade()
            if letter == 'A': power *= 0.9
            elif letter == 'B': power *= 0.75
            elif letter == 'C': power *= 0.6
            elif letter == 'D': power *= 0.4
            else: power *= 0.2

            total = total + power

        return min(total, 1.0)

    def retreat(self, failureCallback = None, successCallback = None):
        p = self.getRetreatChance() 

        for pc in self.pcs:
            if pc.init > 30: pc.init = 30

        if random.random() > p:
            if failureCallback is not None: failureCallback()
        else:
            self.isRetreat = True
            if successCallback is not None: successCallback()

    def isOver(self):
        if self.npc.hp <= 0 or self.isRetreat: return True
        for pc in self.pcs:
            if pc.hp > 0: return False
        return True

class Roster:
    GONE = -1
    IDLE = 0
    COMBAT = 1
    RETURNED = 2
    DEAD = 3
    COOLDOWN = 4

    def __init__(self):
        self.entries = []
        self.maxUnits = 10
        self.maxCombatSize = 5
        self.timeToRoll = self.maxTimeToRoll = 180

    def addNewUnit(self):
        self.entries.append([PCunit.rollPC(random.randint(1, 5)), Roster.IDLE])

    def randomize(self):
        self.__init__()
        for i in range(5): self.addNewUnit()            

    def setMaxUnits(self):
        for entry in self.entries:
            if entry[0].lv > self.maxUnits:
                self.maxUnits = entry[0].lv

    def tick(self, unitCallback = None, cdFinishedCallback = None):
        self.timeToRoll = self.timeToRoll - 1
        while self.timeToRoll <= 0:
            if len(self.entries) >= self.maxUnits: 
                self.setMaxUnits()
                self.timeToRoll = 0
                break
            self.addNewUnit()
            self.timeToRoll = self.timeToRoll + self.maxTimeToRoll
            if unitCallback is not None: unitCallback(self.entries[-1][0])

        for entry in self.entries:
            unit, state = entry
            if state != Roster.COOLDOWN: continue
            unit.cooldown = unit.cooldown - 1
            if unit.cooldown <= 0: 
                entry[1] = Roster.IDLE
                if cdFinishedCallback is not None: cdFinishedCallback(unit)

    def unitProgress(self):
        return float(self.maxTimeToRoll - self.timeToRoll) / self.maxTimeToRoll

    def removeUnits(self, inds):
        for ind in inds:
            if self.entries[ind][1] == Roster.IDLE:
                self.entries[ind][1] = Roster.GONE

        entries = []
        for entry in self.entries:
            if entry[1] != Roster.GONE:
                entries.append(entry)
        self.entries = entries

    def createCombat(self, inds):
        if len(inds) > self.maxCombatSize: return None
        
        pcs = []
        for i in inds:
            if self.entries[i][1] != Roster.IDLE: return None
            self.entries[i][1] = Roster.COMBAT
            pcs.append(self.entries[i][0])
        return Combat(pcs, PCunit.rollNPC(pcs))

    def getUnit(self, ind): return self.entries[ind][0]

    def getUnits(self):
        for entry in self.entries: yield entry[0]

    def inState(self, state):
        for entry in self.entries:
            if entry[1] == state: yield entry[0]

    def hasIncompleteUnits(self):
        for entry in self.entries:
            if entry[1] != Roster.IDLE: return True
        return False

    def setState(self, unit, state):
        for entry in self.entries:
            if entry[0] is unit:
                entry[1] = state

    def resolveCombat(self, combat):
        for pc in combat.pcs:
            if pc.hp > 0:
                if combat.npc.hp <= 0: self.setState(pc.unit, Roster.RETURNED)
                else: self.setState(pc.unit, Roster.IDLE)
            else: self.setState(pc.unit, Roster.DEAD)

    def completeUnits(self, deathCallback = None, successCallback = None, levelCallback = None):
        for entry in self.entries:
            unit, state = entry
            if state == Roster.RETURNED:
                entry[1] = Roster.IDLE
                if unit.checkLevelUp():
                    unit.levelUp()
                    if levelCallback is not None: levelCallback(unit)
                else:
                    if successCallback is not None: successCallback(unit)
            elif state == Roster.DEAD:
                entry[1] = Roster.COOLDOWN
                unit.cooldown = 60 * unit.lv
                if deathCallback is not None: deathCallback(unit)

class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title = "R+R", style = wx.DEFAULT_FRAME_STYLE)

        self.SetMinSize((800, 600))

        self.read()

        outerBox = wx.BoxSizer(wx.VERTICAL)

        self.mgmt = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.mgmt.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onListItemActivated)
        outerBox.Add(self.mgmt, 1, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)

        self.combatView = wx.BoxSizer(wx.VERTICAL)
        
        outerBox.Add(self.combatView, 0, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)
        
        innerBox = wx.BoxSizer(wx.HORIZONTAL)

        self.countText = wx.StaticText(self, 0, "0 / 0 units")
        innerBox.Add(self.countText, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        combatBtn = wx.Button(self, 0, "Begin combat")
        combatBtn.Bind(wx.EVT_BUTTON, lambda event: self.newCombat())
        innerBox.Add(combatBtn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        bolsterBtn = wx.Button(self, 0, "Bolster units")
        bolsterBtn.Bind(wx.EVT_BUTTON, lambda event: self.bolsterUnits())
        innerBox.Add(bolsterBtn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        removeBtn = wx.Button(self, 0, "Remove units")
        removeBtn.Bind(wx.EVT_BUTTON, lambda event: self.removeUnits())
        innerBox.Add(removeBtn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        self.unitText = wx.StaticText(self, 0, "0% to next unit")
        innerBox.Add(self.unitText, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        outerBox.Add(innerBox, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizer(outerBox)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda event: self.tickAll())
        self.timer.Start(1000)

        self.hasFocus = True
        self.Bind(wx.EVT_ACTIVATE, self.onActivate)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.refreshMgmt()
        self.Layout()

    def onClose(self, event):
        if USE_CHEAT_PROTECTION:
            for entry in self.roster.entries:
                if entry[1] == Roster.COMBAT:
                    entry[0].cooldown = 60 * entry[0].lv

        self.write()
        event.Skip()

    def onListItemActivated(self, event):
        ind = event.GetIndex()
        unit = self.roster.getUnit(ind)

        dialog = wx.TextEntryDialog(self, "Enter a new name for this unit", "Rename unit", unit.name)
        if dialog.ShowModal() == wx.ID_CANCEL: return

        unit.name = dialog.GetValue()
        self.refreshMgmt()

    def refreshMgmt(self):
        self.mgmt.ClearAll()

        self.mgmt.InsertColumn(0, "Name")
        self.mgmt.InsertColumn(1, "LV")
        self.mgmt.InsertColumn(2, "HP")
        self.mgmt.InsertColumn(3, "ATT")
        self.mgmt.InsertColumn(4, "RCV")
        self.mgmt.InsertColumn(5, "IQ")
        self.mgmt.InsertColumn(6, "FIT")
        self.mgmt.InsertColumn(7, "SP")
        self.mgmt.InsertColumn(8, "SPLV")
        self.mgmt.InsertColumn(9, "Effect")

        for i in range(len(self.roster.entries)):
            pc, status = self.roster.entries[i]
            self.mgmt.Append([pc.name, pc.lv, 
                              pc.hp, pc.att, pc.rcv, 
                              pc.iq, pc.getFitGrade(),
                              pc.sp.getName(), "*" * pc.sp.getStars(), pc.sp.summary])
            if status == Roster.COMBAT:
                self.mgmt.SetItemTextColour(i, wx.Colour(128, 128, 128))
            elif status == Roster.COOLDOWN or status == Roster.DEAD:
                self.mgmt.SetItemTextColour(i, wx.Colour(255, 0, 0))

        self.mgmt.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.mgmt.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
        self.mgmt.SetColumnWidth(2, wx.LIST_AUTOSIZE_USEHEADER)
        self.mgmt.SetColumnWidth(3, wx.LIST_AUTOSIZE_USEHEADER)
        self.mgmt.SetColumnWidth(4, wx.LIST_AUTOSIZE_USEHEADER)
        self.mgmt.SetColumnWidth(5, wx.LIST_AUTOSIZE_USEHEADER)
        self.mgmt.SetColumnWidth(6, wx.LIST_AUTOSIZE_USEHEADER)
        self.mgmt.SetColumnWidth(7, wx.LIST_AUTOSIZE)
        self.mgmt.SetColumnWidth(8, wx.LIST_AUTOSIZE_USEHEADER)
        self.mgmt.SetColumnWidth(9, wx.LIST_AUTOSIZE)

        self.mgmt.Bind(wx.EVT_LIST_COL_CLICK, self.colClicked)

        self.write()

    def colClicked(self, event):
        if event.m_col == 0: self.roster.entries.sort(key = lambda entry: entry[0].name)
        elif event.m_col == 1: self.roster.entries.sort(key = lambda entry: entry[0].lv, reverse = True)
        elif event.m_col == 2: self.roster.entries.sort(key = lambda entry: entry[0].hp, reverse = True)
        elif event.m_col == 3: self.roster.entries.sort(key = lambda entry: entry[0].att, reverse = True)
        elif event.m_col == 4: self.roster.entries.sort(key = lambda entry: entry[0].rcv, reverse = True)
        elif event.m_col == 5: self.roster.entries.sort(key = lambda entry: entry[0].iq, reverse = True)
        elif event.m_col == 6: self.roster.entries.sort(key = lambda entry: entry[0].fit, reverse = True)
        elif event.m_col == 7: self.roster.entries.sort(key = lambda entry: entry[0].sp.getName())
        elif event.m_col == 8: self.roster.entries.sort(key = lambda entry: entry[0].sp.getStars(), reverse = True)
        elif event.m_col == 9: self.roster.entries.sort(key = lambda entry: entry[0].sp.summary)
            
        self.refreshMgmt()

    def updateCombatView(self, combat):
        view = combat.view

        view.npcrow.healthText.SetLabel("%d / %d" % (Combat.displayHP(combat.npc.hp), Combat.displayHP(combat.npc.maxhp)))
        view.npcrow.statText.SetLabel("ATT: %d DEF: %d" % (combat.npc.att, combat.npc.rcv))
        if len(combat.npc.tags) > 0:
            view.npcrow.status.Show()
            view.npcrow.status.SetLabel(combat.npc.getTags())
        else:
            view.npcrow.status.Hide()

        w = combat.getDamageWeights()
        for i in range(len(combat.pcs)):
            view.pcrows[i].statText.SetLabel("ATT: %d RCV: %d" % (combat.pcs[i].att, combat.pcs[i].rcv))

            if combat.pcs[i].defn and combat.pcs[i].rcv >= w[i] * combat.npc.att and combat.pcs[i].hp > 0:
                view.pcrows[i].healthText.SetForegroundColour(wx.Colour(0, 0, 192))
            elif combat.pcs[i].hp <= w[i] * combat.npc.att * 10  or combat.pcs[i].hp <= 0:
                view.pcrows[i].healthText.SetForegroundColour(wx.Colour(192, 0, 0))
            else:
                view.pcrows[i].healthText.SetForegroundColour(wx.Colour(0, 128, 0))
            view.pcrows[i].healthText.SetLabel("%d / %d" % (Combat.displayHP(combat.pcs[i].hp), Combat.displayHP(combat.pcs[i].maxhp)))

            if combat.pcs[i].init >= 90:
                view.pcrows[i].initText.SetForegroundColour(wx.Colour(255, 0, 0))
            elif combat.pcs[i].readySP():
                view.pcrows[i].initText.SetForegroundColour(wx.Colour(255, 128, 0))
            elif combat.pcs[i].init >= 30:
                view.pcrows[i].initText.SetForegroundColour(wx.Colour(0, 0, 0))
            else:
                view.pcrows[i].initText.SetForegroundColour(wx.Colour(128, 128, 128))
            view.pcrows[i].initText.SetLabel("INIT: %s" % (Combat.displayINIT(combat.pcs[i].init)))
            
            if len(combat.pcs[i].tags) > 0:
                view.pcrows[i].status.Show()
                view.pcrows[i].status.SetLabel(combat.pcs[i].getTags())
            else:
                view.pcrows[i].status.Hide()

        view.retreatBtn.SetToolTip(wx.ToolTip("%d%% chance of escape" % (int(100 * combat.getRetreatChance() + 0.5))))

        view.Layout()

    def genCombatView(self, combat):
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        view = wx.BoxSizer(wx.VERTICAL)
        combat.view = view

        # Enemy row

        row = wx.BoxSizer(wx.VERTICAL)

        row1 = wx.BoxSizer(wx.HORIZONTAL)

        lbl = wx.StaticText(self, 0, "Enemy")
        lbl.SetForegroundColour(wx.Colour(128, 0, 0))
        row1.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        row1.Add(wx.StaticText(self, 0, "%s [Lv. %d]" % (combat.npc.unit.name, combat.npc.unit.lv)))

        row.statText = wx.StaticText(self, 0)
        row1.Add(row.statText, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        row.healthText = wx.StaticText(self, 0)
        row.healthText.SetForegroundColour(wx.Colour(0, 128, 0))
        row1.Add(row.healthText, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        row.Add(row1, 0, wx.ALIGN_CENTER)
        
        row.status = wx.StaticText(self, 0)
        row.status.SetFont(font)
        row.status.SetForegroundColour(wx.Colour(0, 0, 192))
        row.status.Hide()
        row.Add(row.status, 0, wx.ALIGN_CENTER)

        view.npcrow = row
        view.Add(row, 0, wx.ALIGN_CENTER)

        # PC rows

        view.pcrows = []
        for i in range(len(combat.pcs)):
            pc, hp, init  = (combat.pcs[i].unit, combat.pcs[i].hp, combat.pcs[i].init)

            row = wx.BoxSizer(wx.VERTICAL)

            row1 = wx.BoxSizer(wx.HORIZONTAL)
            row1.Add(wx.StaticText(self, 0, "%s [Lv. %d]" % (pc.name, pc.lv)), 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 2)
                        
            row.statText = wx.StaticText(self, 0)
            row1.Add(row.statText, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 2)

            row.healthText = wx.StaticText(self, 0)
            row.healthText.SetForegroundColour(wx.Colour(0, 128, 0))
            row1.Add(row.healthText, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 2)

            row.initText = wx.StaticText(self, 0)
            row1.Add(row.initText, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 2)

            healBtn = wx.Button(self, 0, "Recover")
            healBtn.combat = combat
            healBtn.ind = i
            healBtn.Bind(wx.EVT_BUTTON, self.healBtnCallback)
            row1.Add(healBtn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 2)

            specialBtn = wx.Button(self, 0, combat.pcs[i].unit.sp.name)
            specialBtn.SetToolTip(wx.ToolTip(combat.pcs[i].unit.sp.getText()))
            specialBtn.combat = combat
            specialBtn.ind = i
            specialBtn.Bind(wx.EVT_BUTTON, self.specialBtnCallback)
            row1.Add(specialBtn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 2)

            row.defendBox = wx.CheckBox(self, 0, "Defend")
            row.defendBox.combat = combat
            row.defendBox.ind = i
            row.defendBox.Bind(wx.EVT_CHECKBOX, self.defendCallback)
            row1.Add(row.defendBox, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 2)

            row.Add(row1, 0, wx.ALIGN_CENTER)

            row.status = wx.StaticText(self, 0)
            row.status.SetFont(font)
            row.status.SetForegroundColour(wx.Colour(0, 0, 192))
            row.status.Hide()
            row.Add(row.status, 0, wx.ALIGN_CENTER)

            view.pcrows.append(row)
            view.Add(row, 0, wx.ALIGN_CENTER)

        row = wx.BoxSizer(wx.HORIZONTAL)

        defendBtn = wx.Button(self, 0, "Defend All")
        defendBtn.combat = combat
        defendBtn.view = view
        defendBtn.Bind(wx.EVT_BUTTON, self.defendAllCallback)
        row.Add(defendBtn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        retreatBtn = wx.Button(self, 0, "Retreat")
        retreatBtn.combat = combat
        retreatBtn.Bind(wx.EVT_BUTTON, self.retreatCallback)
        view.retreatBtn = retreatBtn
        row.Add(retreatBtn, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 5)

        view.Add(row, 0, wx.ALIGN_CENTER)

        self.updateCombatView(combat)

        return view

    def healBtnCallback(self, event):
        button = event.GetEventObject()
        button.combat.heal(button.ind)

    def specialBtnCallback(self, event):
        button = event.GetEventObject()
        if button.combat.special(button.ind) and button.combat.pcs[button.ind].unit.sp.once:
            button.Disable()

    def defendCallback(self, event):
        cbox = event.GetEventObject()
        cbox.combat.defend(cbox.ind, cbox.GetValue())
        
    def defendAllCallback(self, event):
        button = event.GetEventObject()
        for i in range(len(button.combat.pcs)):
            button.view.pcrows[i].defendBox.SetValue(True)
            button.combat.defend(i, True)

    def retreatCallback(self, event):
        button = event.GetEventObject()
        button.combat.retreat()

    def tickAll(self):
        filterflag = False
        for i in range(len(self.combats)):
            combat = self.combats[i]
            if not combat.isOver():
                combat.tick()
                self.updateCombatView(combat)
            else:
                filterflag = True
                combat.view.Clear(True)
                self.combatView.Remove(i)
                self.roster.resolveCombat(combat)
                if not self.hasFocus: 
                    wx.CallAfter(lambda: wx.MessageDialog(self, "Combat has ended.", style = wx.OK | wx.CENTRE).ShowModal())

        if filterflag:
            combats = []
            for combat in self.combats:
                if not combat.isOver(): combats.append(combat)
            self.combats = combats
            if self.hasFocus: self.resolve()
            self.Layout()

        self.roster.tick(self.newUnit, self.recoveredUnit)
        self.countText.SetLabel("%d / %d units" % (len(self.roster.entries), self.roster.maxUnits))
        self.unitText.SetLabel("%d%% to next unit" % (int(100 * self.roster.unitProgress())))
        self.Layout()

    def newCombat(self):
        inds = []

        for i in range(self.mgmt.GetItemCount()):
            if self.mgmt.IsSelected(i):
                inds.append(i)
                self.mgmt.SetItemTextColour(i, wx.Colour(128, 128, 128))
                self.mgmt.Select(i, False)

        if len(inds) == 0: return
 
        self.combats.append(self.roster.createCombat(inds))
        self.combatView.Add(self.genCombatView(self.combats[-1]), 0, wx.ALIGN_CENTER)
        self.Layout()

    def bolsterUnits(self):
        inds = []

        for i in range(self.mgmt.GetItemCount()):
            if self.mgmt.IsSelected(i):
                inds.append(i)
                self.mgmt.Select(i, False)

        if len(inds) == 0: return

        success = False
        target = self.roster.entries[inds[0]][0]
        toRemove = []
        for ind in inds[1:]:
            src = self.roster.entries[ind][0]
            if src.canBolster(target): 
                success = src.bolster(target) or success
                toRemove.append(ind)

        if success:
            wx.CallAfter(lambda: wx.MessageDialog(self, "%s has been upgraded to %s" % (target.name, target.sp.getName()), style = wx.OK | wx.CENTRE).ShowModal())
        else:
            wx.CallAfter(lambda: wx.MessageDialog(self, "%s could not be upgraded" % (target.name), style = wx.OK | wx.CENTRE).ShowModal())

        self.roster.removeUnits(toRemove)
        self.refreshMgmt()

    def removeUnits(self):
        inds = []

        for i in range(self.mgmt.GetItemCount()):
            if self.mgmt.IsSelected(i):
                inds.append(i)
                self.mgmt.Select(i, False)

        if len(inds) == 0: return
 
        self.roster.removeUnits(inds)
        self.refreshMgmt()

    def onActivate(self, event):
        self.hasFocus = event.GetActive()
        if self.hasFocus and self.roster.hasIncompleteUnits():
            self.resolve()
        event.Skip()

    def newUnit(self, unit):
        self.refreshMgmt()

    def recoveredUnit(self, unit):
        self.refreshMgmt()
        wx.CallAfter(lambda: wx.MessageDialog(self, "%s has returned to fight again." % (unit.name), style = wx.OK | wx.CENTRE).ShowModal())

    def resolve(self):
        self.roster.completeUnits(self.death, self.success, self.level)
        self.refreshMgmt()

    def death(self, unit):
        wx.CallAfter(lambda: wx.MessageDialog(self, "%s has died." % (unit.name), style = wx.OK | wx.CENTRE).ShowModal())

    def success(self, unit):
        wx.CallAfter(lambda: wx.MessageDialog(self, "%s has returned unharmed." % (unit.name), style = wx.OK | wx.CENTRE).ShowModal())

    def level(self, unit):
        s = "%s grew to level %d!\n" % (unit.name, unit.lv)
        s = s + "Result:\n" + str(unit)
        wx.CallAfter(lambda: wx.MessageDialog(self, s, style = wx.OK | wx.CENTRE).ShowModal())

    def write(self):
        fp = open("rplusr.dat", "w")
        fp.write("r+rv4\n")

        fp.write("%d\n" % (self.roster.timeToRoll))
        for entry in self.roster.entries:
            unit, status = entry
            fp.write("%s %d %d %d %d %f %d %d %d %d %d\n" %
                     (unit.name, unit.hp, unit.att, unit.rcv, unit.iq, unit.fit, unit.lv,
                      unit.spid, unit.sp.lv, unit.sp.bonus, unit.cooldown))
        fp.close()

    def read(self):
        self.roster = Roster()
        self.combats = []

        if not os.path.isfile("rplusr.dat"):
            self.roster.randomize()
        else:
            fp = open("rplusr.dat", "r")

            verstr = fp.readline().strip()

            if verstr == "r+rv1":
                s = fp.readline()
                self.roster.timeToRoll = int(s)
                for line in fp:
                    unit = PCunit()
                    unit.ident = PCunit.nextCounter()
                    unit.name, unit.hp, unit.att, unit.rcv, unit.iq, unit.fit, unit.lv = line.split()

                    unit.hp = int(unit.hp)
                    unit.att = int(unit.att)
                    unit.rcv = int(unit.rcv)
                    unit.iq = int(unit.iq)
                    unit.fit = float(unit.fit)
                    unit.lv = int(unit.lv)

                    # Compatibility with r+rv2: Roll a random special for existing units
                    unit.spid, unit.sp = randomSpecial()
            
                    self.roster.entries.append([unit, Roster.IDLE])
            elif verstr == "r+rv2":
                s = fp.readline()
                self.roster.timeToRoll = int(s)
                for line in fp:
                    unit = PCunit()
                    unit.ident = PCunit.nextCounter()
                    unit.name, unit.hp, unit.att, unit.rcv, unit.iq, unit.fit, unit.lv, spid, splv = line.split()

                    unit.hp = int(unit.hp)
                    unit.att = int(unit.att)
                    unit.rcv = int(unit.rcv)
                    unit.iq = int(unit.iq)
                    unit.fit = float(unit.fit)
                    unit.lv = int(unit.lv)
                    spid = int(spid)
                    splv = int(splv)
                    unit.spid = spid
                    unit.sp = makeSpecial(spid, splv)
            
                    self.roster.entries.append([unit, Roster.IDLE])
                    self.roster.setMaxUnits()
            elif verstr == "r+rv3":
                s = fp.readline()
                self.roster.timeToRoll = int(s)
                for line in fp:
                    unit = PCunit()
                    unit.ident = PCunit.nextCounter()
                    unit.name, unit.hp, unit.att, unit.rcv, unit.iq, unit.fit, unit.lv, spid, splv, spb = line.split()

                    unit.hp = int(unit.hp)
                    unit.att = int(unit.att)
                    unit.rcv = int(unit.rcv)
                    unit.iq = int(unit.iq)
                    unit.fit = float(unit.fit)
                    unit.lv = int(unit.lv)
                    spid = int(spid)
                    splv = int(splv)
                    spb = int(spb)
                    unit.spid = spid
                    unit.sp = makeSpecial(spid, splv, spb)
            
                    self.roster.entries.append([unit, Roster.IDLE])
                    self.roster.setMaxUnits()
            elif verstr == "r+rv4":
                s = fp.readline()
                self.roster.timeToRoll = int(s)
                for line in fp:
                    unit = PCunit()
                    unit.ident = PCunit.nextCounter()
                    unit.name, unit.hp, unit.att, unit.rcv, unit.iq, unit.fit, unit.lv, spid, splv, spb, cd = line.split()

                    unit.hp = int(unit.hp)
                    unit.att = int(unit.att)
                    unit.rcv = int(unit.rcv)
                    unit.iq = int(unit.iq)
                    unit.fit = float(unit.fit)
                    unit.lv = int(unit.lv)
                    spid = int(spid)
                    splv = int(splv)
                    spb = int(spb)
                    unit.spid = int(spid)
                    unit.sp = makeSpecial(spid, splv, spb)
                    unit.cooldown = int(cd)
            
                    if unit.cooldown > 0:
                        self.roster.entries.append([unit, Roster.COOLDOWN])
                    else:
                        self.roster.entries.append([unit, Roster.IDLE])

                self.roster.setMaxUnits()
                    
app = wx.App()
frame = MainFrame(None)
frame.Center()
frame.Show()
app.MainLoop()
