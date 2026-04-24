import wx
import os
import math
import random

from HypoModPy.hypomods import *
from HypoModPy.hypoparams import *
from HypoModPy.hypodat import *
from HypoModPy.hypogrid import *


class GhrelinMod(Mod):
    def __init__(self, mainwin, tag):
        Mod.__init__(self, mainwin, tag)

        if mainwin.modpath != "":
            self.path = mainwin.modpath + "/Ghrelin"
        else:
            self.path = "Ghrelin"

        if os.path.exists(self.path) is False:
            os.mkdir(self.path)

        self.mainwin = mainwin

        self.protobox = GhrelinProtoBox(self, "proto", "Input Protocols",
                                        wx.Point(0, 0), wx.Size(400, 660))
        self.gridbox = GridBox(self, "Data Grid",
                               wx.Point(0, 0), wx.Size(320, 500), 100, 20)
        self.ghrelinbox = GhrelinBox(self, "ghrelin", "GhrelinMod",
                                     wx.Point(0, 0), wx.Size(360, 620))

        mainwin.gridbox = self.gridbox

        self.AddTool(self.ghrelinbox)
        self.AddTool(self.gridbox)
        self.AddTool(self.protobox)

        self.ghrelinbox.Show(True)
        self.modbox = self.ghrelinbox

        self.ModLoad()
        print("Ghrelin Probabilistic Trigger-Comparison Model OK")

        self.ghrelindata = GhrelinDat()
        self.PlotData()
        self.graphload = True

    def PlotData(self):
        runtime = int(self.ghrelinbox.GetParams().get("runtime", 1440))
        
        # For standard 24 h runs, keep the x-axis in minutes.
        # For multi-day runs (e.g. Figure 3), switch the x-axis to hours.
        if runtime > 1440:
            x_max = runtime / 60.0
        else:
            x_max = runtime

        self.plotbase.AddPlot(
            PlotDat(self.ghrelindata.ghrelin, 0, x_max, 0, 160,
                    "ghrelin", "line", 1, "blue"),
            "ghrelin"
        )

        self.plotbase.AddPlot(
            PlotDat(self.ghrelindata.meal, 0, x_max, 0, 2.0,
                    "meal event", "line", 1, "red"),
            "meal"
        )

        self.plotbase.AddPlot(
            PlotDat(self.ghrelindata.circ_target, 0, x_max, 0, 160,
                    "circadian target", "line", 1, "purple"),
            "circ_target"
        )

        self.plotbase.AddPlot(
            PlotDat(self.ghrelindata.fullness, 0, x_max, 0, 18,
                    "fullness", "line", 1, "green"),
            "fullness"
        )

        self.plotbase.AddPlot(
            PlotDat(self.ghrelindata.insulin, 0, x_max, 0, 4.0,
                    "insulin", "line", 1, "purple"),
            "insulin"
        )

        self.plotbase.AddPlot(
            PlotDat(self.ghrelindata.lightdark, 0, x_max, 0, 1.2,
                    "dark phase", "line", 1, "black"),
            "lightdark"
        )

        self.plotbase.AddPlot(
            PlotDat(self.ghrelindata.trigger_prob, 0, x_max, 0, 1.0,
                    "trigger probability", "line", 1, "black"),
            "trigger_prob"
        )

    def DefaultPlots(self):
        if len(self.mainwin.panelset) > 0:
            self.mainwin.panelset[0].settag = "ghrelin"
        if len(self.mainwin.panelset) > 1:
            self.mainwin.panelset[1].settag = "meal"
        if len(self.mainwin.panelset) > 2:
            self.mainwin.panelset[2].settag = "circ_target"
        if len(self.mainwin.panelset) > 3:
            self.mainwin.panelset[3].settag = "fullness"
        if len(self.mainwin.panelset) > 4:
            self.mainwin.panelset[4].settag = "insulin"
        if len(self.mainwin.panelset) > 5:
            self.mainwin.panelset[5].settag = "lightdark"
        if len(self.mainwin.panelset) > 6:
            self.mainwin.panelset[6].settag = "trigger_prob"

    def OnModThreadComplete(self, event):
        self.mainwin.scalebox.GraphUpdateAll()

    def OnModThreadProgress(self, event):
        self.ghrelinbox.SetCount(event.GetInt())

    def RunModel(self):
        self.mainwin.SetStatusText("Ghrelin Probabilistic Trigger-Comparison Model Run")
        modthread = GhrelinModel(self)
        modthread.start()


class GhrelinDat:
    def __init__(self):
        self.storesize = 40000
        self.ghrelin = datarray(self.storesize + 1)
        self.meal = pdata(self.storesize + 1)
        self.circ_target = pdata(self.storesize + 1)
        self.fullness = pdata(self.storesize + 1)
        self.insulin = pdata(self.storesize + 1)
        self.lightdark = pdata(self.storesize + 1)
        self.trigger_prob = pdata(self.storesize + 1)


class GhrelinBox(ParamBox):
    def __init__(self, mod, tag, title, position, size):
        ParamBox.__init__(self, mod, title, position, size, tag, 0, 1)

        self.autorun = True
        self.InitMenu()

        self.paramset.AddCon("runtime", "Run (min)", 1440, 10, 0)
        self.paramset.AddCon("warmup_days", "Warmup (d)", 2, 1, 0)

        self.paramset.AddCon("g_init", "G start", 100.0, 1.0, 1)
        self.paramset.AddCon("g_mean", "G base", 100.0, 1.0, 1)
        self.paramset.AddCon("circ_amp", "G circ amp", 20.0, 1.0, 1)
        self.paramset.AddCon("circ_peak", "G peak min", 1290, 10, 0)
        self.paramset.AddCon("k_relax", "G relax", 0.010, 0.001, 3)

        self.paramset.AddCon("trigger_mode", "Trig mode", 1, 1, 0)
        self.paramset.AddCon("g_threshold", "G thr", 90.0, 1.0, 1)
        self.paramset.AddCon("dg_threshold", "dG thr", 0.050, 0.005, 3)
        self.paramset.AddCon("g_prob_scale", "G rise s", 4.0, 0.5, 1)
        self.paramset.AddCon("dg_prob_scale", "dG rise s", 0.010, 0.002, 3)
        self.paramset.AddCon("random_seed", "Seed", 1, 1, 0)
        self.paramset.AddCon("refractory", "Pause min", 40, 5, 0)
        self.paramset.AddCon("fullness_cap", "F cap", 14.0, 0.5, 1)
        self.paramset.AddCon("trig_meal_size", "Trig", 1.0, 0.1, 1)
        self.paramset.AddCon("light_g_offset", "Day +G", 2.0, 0.5, 1)
        self.paramset.AddCon("light_dg_offset", "Day +dG", 0.010, 0.005, 3)

        self.paramset.AddCon("meal_buffer_gain", "Digest +", 10.5, 0.5, 1)
        self.paramset.AddCon("meal_buffer_decay", "Digest -", 0.080, 0.001, 3)
        self.paramset.AddCon("fullness_gain", "Full +", 0.040, 0.005, 3)
        self.paramset.AddCon("fullness_decay", "Full -", 0.004, 0.001, 3)
        self.paramset.AddCon("fullness_base", "F base", 1.5, 0.1, 1)

        self.paramset.AddCon("insulin_base", "I base", 0.55, 0.05, 2)
        self.paramset.AddCon("insulin_circ_amp", "I circ amp", 0.12, 0.01, 2)
        self.paramset.AddCon("insulin_circ_peak", "I circ pk", 60, 10, 0)

        self.paramset.AddCon("cephalic_width", "Ceph wid", 3, 1, 0)
        self.paramset.AddCon("cephalic_gain", "Ceph +", 0.28, 0.02, 2)
        self.paramset.AddCon("cephalic_decay", "Ceph -", 0.28, 0.01, 2)
        self.paramset.AddCon("insulin_pulse_gain", "I fast +", 0.28, 0.02, 2)
        self.paramset.AddCon("insulin_pulse_decay", "I fast -", 0.20, 0.01, 2)
        self.paramset.AddCon("insulin_pulse_sat", "I fast sat", 1.30, 0.1, 2)

        self.paramset.AddCon("insulin_gain", "I slow +", 0.110, 0.005, 3)
        self.paramset.AddCon("insulin_decay", "I slow -", 0.048, 0.001, 3)
        self.paramset.AddCon("insulin_halfmax", "I halfmax", 3.80, 0.1, 2)

        self.paramset.AddCon("g_fullness_drive", "F -> G drive", 0.035, 0.001, 3)
        self.paramset.AddCon("fullness_set", "F set", 3.2, 0.5, 1)
        self.paramset.AddCon("g_insulin_suppr", "I -> G sup", 0.070, 0.001, 3)

        self.ParamLayout(2)

        runbox = self.RunBox()
        paramfilebox = self.StoreBoxSync()

        ID_Proto = wx.NewIdRef()
        self.AddPanelButton(ID_Proto, "Proto", self.mod.protobox)
        ID_Grid = wx.NewIdRef()
        self.AddPanelButton(ID_Grid, "Grid", self.mod.gridbox)

        self.mainbox.AddSpacer(5)
        self.mainbox.Add(self.pconbox, 1,
                         wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 0)
        self.mainbox.AddStretchSpacer(5)
        self.mainbox.Add(runbox, 0,
                         wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 0)
        self.mainbox.AddSpacer(5)
        self.mainbox.Add(paramfilebox, 0,
                         wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 0)
        self.mainbox.Add(self.buttonbox, 0,
                         wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 0)
        self.mainbox.AddSpacer(5)
        self.panel.Layout()


class GhrelinProtoBox(ParamBox):
    def __init__(self, mod, tag, title, position, size):
        ParamBox.__init__(self, mod, title, position, size, tag, 0, 1)

        self.autorun = True

        self.paramset.AddCon("meal_width", "Meal Width", 12, 2, 0)

        self.paramset.AddCon("meal1_time", "Meal 1 Time", 600, 10, 0)
        self.paramset.AddCon("meal1_size", "Meal 1 Size", 0.8, 0.1, 1)

        self.paramset.AddCon("meal2_time", "Meal 2 Time", 1170, 10, 0)
        self.paramset.AddCon("meal2_size", "Meal 2 Size", 1.0, 0.1, 1)

        self.paramset.AddCon("meal3_time", "Meal 3 Time", 1260, 10, 0)
        self.paramset.AddCon("meal3_size", "Meal 3 Size", 1.0, 0.1, 1)

        self.paramset.AddCon("meal4_time", "Meal 4 Time", 1350, 10, 0)
        self.paramset.AddCon("meal4_size", "Meal 4 Size", 0.9, 0.1, 1)

        self.paramset.AddCon("meal5_time", "Meal 5 Time", 90, 10, 0)
        self.paramset.AddCon("meal5_size", "Meal 5 Size", 1.4, 0.1, 1)

        self.paramset.AddCon("meal6_time", "Meal 6 Time", 270, 10, 0)
        self.paramset.AddCon("meal6_size", "Meal 6 Size", 1.4, 0.1, 1)

        self.paramset.AddCon("lights_on", "Lights On", 420, 10, 0)
        self.paramset.AddCon("lights_off", "Lights Off", 1140, 10, 0)

        self.ParamLayout(3)

        self.mainbox.AddSpacer(5)
        self.mainbox.Add(self.pconbox, 1,
                         wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 0)
        self.mainbox.AddStretchSpacer(5)
        self.mainbox.AddSpacer(2)
        self.panel.Layout()


class GhrelinModel(ModThread):
    def __init__(self, mod):
        ModThread.__init__(self, mod.modbox, mod.mainwin)

        self.mod = mod
        self.ghrelinbox = mod.ghrelinbox
        self.mainwin = mod.mainwin
        self.scalebox = mod.mainwin.scalebox

    def run(self):
        self.Model()
        wx.QueueEvent(self.mod, ModThreadEvent(ModThreadCompleteEvent))

    def is_dark_phase(self, time_of_day, lights_on, lights_off):
        if lights_on <= lights_off:
            return not (lights_on <= time_of_day < lights_off)
        else:
            return lights_off <= time_of_day < lights_on

    def circadian_target(self, time_of_day, g_mean, circ_amp, circ_peak):
        angle = 2.0 * math.pi * (time_of_day - circ_peak) / 1440.0
        return g_mean + circ_amp * math.cos(angle)

    def time_in_window(self, time_of_day, start_time, width):
        if width <= 0:
            return False
        end_time = (start_time + width) % 1440
        if start_time <= end_time:
            return start_time <= time_of_day < end_time
        else:
            return time_of_day >= start_time or time_of_day < end_time

    def get_meal_schedule(self, proto):
        schedule = []
        for idx in range(1, 7):
            t_key = f"meal{idx}_time"
            s_key = f"meal{idx}_size"
            meal_time = int(proto.get(t_key, -1))
            meal_size = float(proto.get(s_key, 0.0))
            if 0 <= meal_time < 1440 and meal_size > 0:
                schedule.append((meal_time, meal_size))
        schedule.sort(key=lambda x: x[0])
        return schedule

    def trigger_probability(self, signal_value, threshold, scale):
        if signal_value <= threshold:
            return 0.0
        if scale <= 0:
            return 1.0
        z = (signal_value - threshold) / scale
        if z > 60:
            z = 60
        return 1.0 - math.exp(-z)

    def Model(self):
        data = self.mod.ghrelindata
        ghrelinbox = self.mod.ghrelinbox
        params = self.mod.ghrelinbox.GetParams()
        proto = self.mod.protobox.GetParams()

        runtime = int(params.get("runtime", 1440))
        warmup_days = int(params.get("warmup_days", 2))

        g_init = float(params.get("g_init", 100.0))
        g_mean = float(params.get("g_mean", 100.0))
        circ_amp = float(params.get("circ_amp", 20.0))
        circ_peak = int(params.get("circ_peak", 1290))
        k_relax = float(params.get("k_relax", 0.010))

        trigger_mode = int(params.get("trigger_mode", 1))
        g_threshold = float(params.get("g_threshold", 100.0))
        dg_threshold = float(params.get("dg_threshold", 0.030))
        g_prob_scale = float(params.get("g_prob_scale", 4.0))
        dg_prob_scale = float(params.get("dg_prob_scale", 0.010))
        random_seed = int(params.get("random_seed", 1))
        refractory = int(params.get("refractory", 70))
        fullness_cap = float(params.get("fullness_cap", 14.0))
        trig_meal_size = float(params.get("trig_meal_size", 1.3))
        light_g_offset = float(params.get("light_g_offset", 14.0))
        light_dg_offset = float(params.get("light_dg_offset", 0.010))

        meal_buffer_gain = float(params.get("meal_buffer_gain", 10.5))
        meal_buffer_decay = float(params.get("meal_buffer_decay", 0.080))
        fullness_gain = float(params.get("fullness_gain", 0.060))
        fullness_decay = float(params.get("fullness_decay", 0.004))
        fullness_base = float(params.get("fullness_base", 1.5))

        insulin_base = float(params.get("insulin_base", 0.55))
        insulin_circ_amp = float(params.get("insulin_circ_amp", 0.12))
        insulin_circ_peak = int(params.get("insulin_circ_peak", 60))

        cephalic_width = int(params.get("cephalic_width", 3))
        cephalic_gain = float(params.get("cephalic_gain", 0.28))
        cephalic_decay = float(params.get("cephalic_decay", 0.28))
        insulin_pulse_gain = float(params.get("insulin_pulse_gain", 0.28))
        insulin_pulse_decay = float(params.get("insulin_pulse_decay", 0.20))
        insulin_pulse_sat = float(params.get("insulin_pulse_sat", 1.3))

        insulin_gain = float(params.get("insulin_gain", 0.110))
        insulin_decay = float(params.get("insulin_decay", 0.048))
        insulin_halfmax = float(params.get("insulin_halfmax", 3.8))

        g_fullness_drive = float(params.get("g_fullness_drive", 0.020))
        fullness_set = float(params.get("fullness_set", 4.0))
        g_insulin_suppr = float(params.get("g_insulin_suppr", 0.070))

        meal_width = int(proto.get("meal_width", 12))
        lights_on = int(proto.get("lights_on", 420))
        lights_off = int(proto.get("lights_off", 1140))
        meal_schedule = self.get_meal_schedule(proto)

        if runtime < 1:
            runtime = 1
        if warmup_days < 0:
            warmup_days = 0
        if meal_width <= 0:
            meal_width = 1
        if cephalic_width <= 0:
            cephalic_width = 1
        if refractory < 0:
            refractory = 0

        if k_relax < 0:
            k_relax = 0
        if meal_buffer_decay < 0:
            meal_buffer_decay = 0
        if fullness_decay < 0:
            fullness_decay = 0
        if cephalic_decay < 0:
            cephalic_decay = 0
        if insulin_pulse_decay < 0:
            insulin_pulse_decay = 0
        if insulin_pulse_sat <= 0:
            insulin_pulse_sat = 1e-6
        if insulin_decay < 0:
            insulin_decay = 0
        if insulin_halfmax <= 0:
            insulin_halfmax = 1e-6
        if insulin_circ_amp < 0:
            insulin_circ_amp = 0
        if g_prob_scale <= 0:
            g_prob_scale = 1e-6
        if dg_prob_scale <= 0:
            dg_prob_scale = 1e-6
        rng = random.Random(random_seed)

        meal_step_gain = meal_buffer_gain / meal_width
        total_steps = warmup_days * 1440 + runtime

        G = g_init
        G_prev = g_init
        D = 0.0
        F = 0.0
        C = 0.0
        I_fast = 0.0
        I_slow = 0.0
        I = insulin_base

        meal_timer = 0
        meal_age = 0
        active_meal_size = 0.0
        refractory_timer = 0
        recorded_index = 0

        data.ghrelin.clear()
        data.meal.clear()
        data.circ_target.clear()
        data.fullness.clear()
        data.insulin.clear()
        data.lightdark.clear()
        data.trigger_prob.clear()

        initial_target = self.circadian_target(0, g_mean, circ_amp, circ_peak)
        initial_dark = 1 if self.is_dark_phase(0, lights_on, lights_off) else 0

        # Temporary placeholders; after warmup we overwrite index 0 with the
        # actual warmed-up state so the plotted day starts from the true state,
        # not from the pre-warmup initial condition.
        data.ghrelin[0] = G
        data.meal[0] = 0
        data.circ_target[0] = initial_target
        data.fullness[0] = F
        data.insulin[0] = I
        data.lightdark[0] = initial_dark
        data.trigger_prob[0] = 0.0

        for global_step in range(1, total_steps + 1):
            if global_step % 100 == 0:
                ghrelinbox.SetCount(int(global_step * 100 / total_steps))

            time_of_day = global_step % 1440
            dark_phase = 1 if self.is_dark_phase(time_of_day, lights_on, lights_off) else 0

            G_target = self.circadian_target(time_of_day, g_mean, circ_amp, circ_peak)

            dG_current = G - G_prev
            G_prev = G

            eff_g_threshold = g_threshold if dark_phase else g_threshold + light_g_offset
            eff_dg_threshold = dg_threshold if dark_phase else dg_threshold + light_dg_offset

            can_trigger = (meal_timer <= 0) and (refractory_timer <= 0) and (F < fullness_cap)

            p_trigger = 0.0
            if can_trigger:
                if trigger_mode == 1:
                    p_trigger = self.trigger_probability(G, eff_g_threshold,
                                                         g_prob_scale)
                elif trigger_mode == 2:
                    p_trigger = self.trigger_probability(dG_current, eff_dg_threshold,
                                                         dg_prob_scale)

            trigger_now = (p_trigger > 0.0) and (rng.random() < p_trigger)

            meal_marker = 0.0
            meal_drive = 0.0
            cephalic_drive = 0.0

            if trigger_mode == 0:
                for meal_time, meal_size in meal_schedule:
                    if self.time_in_window(time_of_day, meal_time, meal_width):
                        meal_marker += meal_size
                        meal_drive += meal_step_gain * meal_size
                    if self.time_in_window(time_of_day, meal_time, cephalic_width):
                        cephalic_drive += meal_size / cephalic_width
            else:
                if trigger_now:
                    meal_timer = meal_width
                    meal_age = 0
                    active_meal_size = trig_meal_size
                    refractory_timer = refractory

                if meal_timer > 0:
                    meal_marker = active_meal_size
                    meal_drive = meal_step_gain * active_meal_size
                    if meal_age < cephalic_width:
                        cephalic_drive = active_meal_size / cephalic_width
                    meal_timer -= 1
                    meal_age += 1

            if refractory_timer > 0:
                refractory_timer -= 1

            D = D + meal_drive - meal_buffer_decay * D
            if D < 0:
                D = 0.0

            F = F + fullness_gain * D - fullness_decay * (F - fullness_base)
            if F < 0:
                F = 0.0

            ceph_signal = cephalic_drive / (insulin_pulse_sat + cephalic_drive)
            C = C + cephalic_gain * ceph_signal - cephalic_decay * C
            if C < 0:
                C = 0.0

            slow_drive = F / (insulin_halfmax + F)

            I_fast = I_fast + insulin_pulse_gain * C - insulin_pulse_decay * I_fast
            if I_fast < 0:
                I_fast = 0.0

            I_slow = I_slow + insulin_gain * slow_drive - insulin_decay * I_slow
            if I_slow < 0:
                I_slow = 0.0

            circ_angle = 2.0 * math.pi * (time_of_day - insulin_circ_peak) / 1440.0
            I_base_dynamic = insulin_base * (1.0 + insulin_circ_amp * math.cos(circ_angle))
            if I_base_dynamic < 0:
                I_base_dynamic = 0.0

            I = I_base_dynamic + I_fast + I_slow
            if I < 0:
                I = 0.0

            fullness_effect = g_fullness_drive * (fullness_set - F)
            G = G + k_relax * (G_target - G) + fullness_effect - g_insulin_suppr * I
            if G < 0:
                G = 0.0

            # Overwrite the displayed t=0 point with the true warmed-up state.
            if global_step == warmup_days * 1440:
                data.ghrelin[0] = G
                data.meal[0] = 0.0
                data.circ_target[0] = G_target
                data.fullness[0] = F
                data.insulin[0] = I
                data.lightdark[0] = dark_phase
                data.trigger_prob[0] = p_trigger

            if global_step > warmup_days * 1440 and recorded_index < data.storesize:
                recorded_index += 1
                data.ghrelin[recorded_index] = G
                data.meal[recorded_index] = meal_marker
                data.circ_target[recorded_index] = G_target
                data.fullness[recorded_index] = F
                data.insulin[recorded_index] = I
                data.lightdark[recorded_index] = dark_phase
                data.trigger_prob[recorded_index] = p_trigger
