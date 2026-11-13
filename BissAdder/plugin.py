# -*- coding: utf-8 -*-
# BISS Adder - adds BISS keys (F hash 00/01 lines) for the current channel.
# Python 2 and Python 3 compatible.
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label

from Plugins.Extensions.BissAdder import hashcalc, keyfile

HEXCHARS = "0123456789ABCDEF"


class BissAdderScreen(Screen):
    skin = """
    <screen name="BissAdderScreen" position="center,center" size="900,520" title="BISS Adder">
        <widget name="chan" position="20,15" size="860,40" font="Regular;28" halign="center" />
        <widget name="hash" position="20,60" size="860,50" font="Regular;36" halign="center" foregroundColor="#00ff66" />
        <widget name="k0" position="20,135" size="860,50" font="Regular;32" halign="center" />
        <widget name="k1" position="20,200" size="860,50" font="Regular;32" halign="center" />
        <widget name="status" position="20,270" size="860,40" font="Regular;24" halign="center" foregroundColor="#ffcc00" />
        <widget name="help" position="20,325" size="860,180" font="Regular;22" halign="center" />
    </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["chan"] = Label("")
        self["hash"] = Label("")
        self["k0"] = Label("")
        self["k1"] = Label("")
        self["status"] = Label("")
        self["help"] = Label(
            "0-9: type   UP/DOWN: A-F and 0-9   LEFT/RIGHT: move\n"
            "YELLOW: switch Key00/Key01   BLUE: copy Key00 to Key01\n"
            "RED: clear field   GREEN: save   EXIT: close"
        )
        self.fields = [["_"] * 16, ["_"] * 16]
        self.cur = 0   # active field (0 = key 00, 1 = key 01)
        self.pos = 0   # cursor position
        self.hashcode = None
        self.saved_path = ""

        actions = {
            "ok": self.save, "green": self.save, "cancel": self.close,
            "red": self.clear_field, "yellow": self.switch_field, "blue": self.copy_key,
            "left": self.move_left, "right": self.move_right,
            "up": self.val_up, "down": self.val_down,
        }
        for n in range(10):
            actions[str(n)] = (lambda d=str(n): self.type_char(d))
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions", "NumberActions"],
            actions, -1)
        self.onLayoutFinish.append(self.start)

    # ---- startup: read the current channel ----
    def start(self):
        try:
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            sref = ref.toString() if ref else ""
        except Exception:
            sref = ""
        self.hashcode = hashcalc.hash_from_sref(sref) if sref else None
        if not self.hashcode:
            self["chan"].setText("No channel found")
            self["status"].setText("Tune a satellite channel first")
            return
        name = ""
        try:
            from enigma import eServiceCenter
            info = eServiceCenter.getInstance().info(ref)
            name = info.getName(ref) or ""
        except Exception:
            pass
        self["chan"].setText(name)
        self["hash"].setText("Hash: " + self.hashcode)
        try:
            k0, k1 = keyfile.read_keys(self.hashcode)
            for i, k in enumerate((k0, k1)):
                if len(k) == 16:
                    self.fields[i] = list(k)
            if k0:
                self["status"].setText("Existing key loaded - edit and save")
            else:
                self["status"].setText(keyfile.get_key_file())
        except Exception:
            pass
        self.refresh()

    # ---- display ----
    def refresh(self):
        for i in (0, 1):
            chars = self.fields[i][:]
            if i == self.cur:
                chars[self.pos] = "[" + chars[self.pos] + "]"
            txt = "".join(chars)
            label = "Key 00:  " if i == 0 else "Key 01:  "
            self["k%d" % i].setText(label + txt)

    # ---- editing ----
    def type_char(self, ch):
        if not self.hashcode:
            return
        self.fields[self.cur][self.pos] = ch
        if self.pos < 15:
            self.pos += 1
        self.refresh()

    def val_up(self):
        self._cycle(1)

    def val_down(self):
        self._cycle(-1)

    def _cycle(self, step):
        if not self.hashcode:
            return
        c = self.fields[self.cur][self.pos]
        if c == "_":
            idx = 0 if step > 0 else 15
        else:
            idx = (HEXCHARS.index(c) + step) % 16
        self.fields[self.cur][self.pos] = HEXCHARS[idx]
        self.refresh()

    def move_left(self):
        self.pos = (self.pos - 1) % 16
        self.refresh()

    def move_right(self):
        self.pos = (self.pos + 1) % 16
        self.refresh()

    def switch_field(self):
        self.cur = 1 - self.cur
        self.pos = 0
        self.refresh()

    def clear_field(self):
        self.fields[self.cur] = ["_"] * 16
        self.pos = 0
        self.refresh()

    def copy_key(self):
        self.fields[1] = self.fields[0][:]
        self.refresh()

    # ---- saving ----
    def save(self):
        if not self.hashcode:
            return
        k0 = "".join(self.fields[0])
        k1 = "".join(self.fields[1])
        if "_" in k0:
            self.session.open(MessageBox, "Key 00 must have all 16 characters", MessageBox.TYPE_ERROR, 4)
            return
        if "_" in k1:
            if k1 == "_" * 16:
                k1 = ""
            else:
                self.session.open(MessageBox, "Key 01 is incomplete (16 characters or empty)", MessageBox.TYPE_ERROR, 4)
                return
        try:
            self.saved_path = keyfile.save_keys(self.hashcode, k0, k1)
        except Exception as e:
            self.session.open(MessageBox, "Could not write file:\n%s" % e, MessageBox.TYPE_ERROR, 6)
            return
        self.session.openWithCallback(
            self.restart_answer, MessageBox,
            "Saved to %s\nRestart the softcam now?" % self.saved_path,
            MessageBox.TYPE_YESNO)

    def restart_answer(self, answer):
        if answer:
            cmd = keyfile.restart_softcam()
            if cmd:
                self.session.open(MessageBox, "Softcam restarted", MessageBox.TYPE_INFO, 3)
            else:
                self.session.open(MessageBox, "Saved, but no restart command worked.\nRestart the softcam by hand.", MessageBox.TYPE_WARNING, 6)
        self.close()


def main(session, **kwargs):
    session.open(BissAdderScreen)


def Plugins(**kwargs):
    return [
        PluginDescriptor(name="BISS Adder", description="Add BISS key to SoftCam.Key for current channel",
                         where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
        PluginDescriptor(name="BISS Adder", description="Add BISS key for current channel",
                         where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
    ]
