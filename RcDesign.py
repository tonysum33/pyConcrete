from rebar import Stirrup, TopBar, BotBar
import matplotlib.pyplot as plt
import numpy as np


class Material:
    def __init__(self, fc=280, fyb=4200, fys=4200):
        # Units : cm kgf
        self.fc = fc
        self.fyb = fyb  # Main Bar
        self.fys = fys  # Stirrup Bar
        self.Es = 2.04 * 10 ** 6


class Section:
    def __init__(self, width, height):
        # Units : cm
        self.width = width
        self.height = height


class MomentCalculate:
    def __init__(self, section: Section, material: Material, topBars, botBars, Mu: float = 0.0):
        self.__sec = section
        self.__mat = material
        self.__botBars = botBars
        self.__topBars = topBars
        self.__rebars = self.__rebars()
        self.__Mu = Mu
        self.__epsilon_c = 0.003

    def __beta1(self):
        return max(min(0.85 - 0.05 * ((self.__mat.fc - 280) / 70), 0.85), 0.65)

    def __fs(self, epsilon_s: float) -> float:
        # 拉力為正；壓力為負
        if epsilon_s > 0:
            return min(epsilon_s * self.__mat.Es, +self.__mat.fyb)
        else:
            return max(epsilon_s * self.__mat.Es, -self.__mat.fyb)

    def __factor_phi(self, epsilon_t: float, is_spiral=False) -> float:
        """
        :param epsilon_t: 最外受拉鋼筋之淨拉力應變
        :param is_spiral: 使用螺箍筋
        :return: 強度折減係數 φ
        """
        # 拉力控制
        phi_b = 0.90
        # 壓力控制
        phi_c = 0.70 if is_spiral else 0.65
        #
        epsilon_y = self.__mat.fyb / self.__mat.Es
        if epsilon_t >= 0.005:
            # 拉力控制
            return phi_b
        elif epsilon_t <= epsilon_y:
            # 壓力控制
            return phi_c
        else:
            # 過渡斷面
            return phi_c + 0.25 * (epsilon_t - epsilon_y) / (0.005 - epsilon_y)

    def __rebars(self):
        rebars = []
        for bar in self.__topBars:
            rebars.append({"area": bar.areas, "yi": +(self.__sec.height / 2 - bar.dT)})
        for bar in self.__botBars:
            rebars.append({"area": bar.areas, "yi": -(self.__sec.height / 2 - bar.dB)})
        return rebars

    def __neutral_axis_depth(self):
        nELM = 100
        ci, Fi = 0, 0
        for i in range(1, nELM + 1):
            ci_1 = ci
            Fi_1 = Fi
            ci = i * self.__sec.height / nELM
            ai = self.__beta1() * ci
            Tsi = 0  # 鋼筋合力
            asc = 0  # 混凝土壓力區內之鋼筋面積
            for rebar in self.__rebars:
                epsilon_si = self.__epsilon_c * (self.__sec.height / 2 - rebar["yi"] - ci) / ci
                Tsi += - self.__fs(epsilon_si) * rebar["area"]
                if self.__sec.height / 2 - rebar["yi"] < ai:
                    asc += rebar["area"]
            Cci = 0.85 * self.__mat.fc * (self.__beta1() * ci * self.__sec.width - asc)
            Fi = Cci + Tsi
            # print(f"ci={ci:10.3f}, Cci={Cci/1000:10.3f}, Tsi={Tsi/1000:10.3f}, Fi={Fi/1000:10.3f}")
            if Fi > 0:
                c = ci_1 + (0 - Fi_1) / (Fi - Fi_1) * (ci - ci_1)
                return c

    def __p_min(self, p_req=1.0):
        p_min11 = 0.8 * self.__mat.fc ** 0.5 / self.__mat.fyb
        p_min12 = 14 / self.__mat.fyb
        p_min1 = max(p_min11, p_min12)
        p_min2 = 4 / 3 * p_req
        p_min = min(p_min1, p_min2)
        return p_min

    def result(self):
        c = self.__neutral_axis_depth()
        a = self.__beta1() * c

        # Steel_force
        Ps = 0  # 鋼筋合力
        Ms = 0  # 鋼筋彎矩
        asc = 0  # 混凝土壓力區內之鋼筋面積
        for rebar in self.__rebars:
            ellipsis_si = self.__epsilon_c * (self.__sec.height / 2 - rebar["yi"] - c) / c
            fsi = - self.__fs(ellipsis_si)
            Ps += fsi * rebar["area"]
            Ms += fsi * rebar['area'] * rebar["yi"]
            if self.__sec.height / 2 - rebar["yi"] < a:
                asc += rebar['area']

        rebars_lowest = min(rebar["yi"] for rebar in self.__rebars)
        ellipsis_st = self.__epsilon_c * (self.__sec.height / 2 - rebars_lowest - c) / c
        phi: float = self.__factor_phi(ellipsis_st)

        # concrete_force
        Pc = 0.85 * self.__mat.fc * (a * self.__sec.width - asc)
        Mn = Pc * (self.__sec.height / 2 - a / 2) + Ms
        ratio = self.__Mu / (phi * Mn)
        return {"c": c,
                "est": ellipsis_st,
                "phi": phi,
                "Mn": Mn,
                "phiMn": phi * Mn,
                "ratio": ratio}

    def __str__(self):
        s = "--------------------------------------------------------------------\n"
        s += f"c        = {self.result()['c'] :20.3f} cm\n"
        s += f"est      = {self.result()['est'] :20.4f}\n"
        s += f"phi      = {self.result()['phi'] :20.3f}\n"
        s += f"Mn       = {self.result()['Mn'] / 100000 :20.3f} tf-m\n"
        s += f"phiMn    = {self.result()['phiMn'] / 100000 :20.3f} tf-m\n"
        s += f"phiMn    = {self.result()['phiMn'] * 9.8066 / 100000 :20.3f} kN-m\n"
        s += f"Mu       = {self.__Mu / 100000 :20.3f} tf-m\n"
        s += f"ratio    = {self.result()['ratio']:20.3f}\n"
        return s


class ShearCalculate:
    def __init__(self, section: Section, material: Material, stirrup_: Stirrup, dB: float, Vu: float = 0):
        self.__sec = section
        self.__mat = material
        self.__stirrup = stirrup_
        self.__Vu = Vu
        self.__d = self.__sec.height - dB
        self.__phi = 0.75

    def __Vc(self, factor=1.0):
        return 0.53 * factor * self.__mat.fc ** 0.5 * self.__sec.width * self.__d

    def __Vs(self):
        # 實際提供
        return self.__stirrup.areas * self.__mat.fys * self.__d / self.__stirrup.spacing

    def __Vn(self):
        return abs(self.__Vs()) + self.__Vc()

    def __Vs_req(self):
        return abs(self.__Vu) / self.__phi - self.__Vc()

    def __shear_reinforcement_req(self):
        # Calculate min area limits for reinforcement [4.6.6.3]

        if abs(self.__Vu) > self.__phi * self.__Vc() / 2:
            Av_spacing_min1 = 0.2 * self.__sec.width / self.__mat.fys * self.__mat.fc ** 0.5
            Av_spacing_min2 = 3.5 * self.__sec.width / self.__mat.fys
            Av_spacing_min = max(Av_spacing_min1, Av_spacing_min2)
        else:
            Av_spacing_min = 0

        # Calculate required shear strength by shear reinforcement
        if abs(self.__Vu) <= self.__phi * self.__Vc() / 2:
            str_msg = "Stirrup is not required"
            Av_spacing_req = 0  #

        elif self.__phi * self.__Vc() / 2 < abs(self.__Vu) \
                <= self.__phi * self.__Vc():
            str_msg = "Minimum stirrup is required"
            Av_spacing_req = Av_spacing_min

        elif self.__phi * self.__Vc() < abs(self.__Vu) \
                <= self.__phi * (self.__Vc() + 2.12 * self.__mat.fc ** 0.5 * self.__sec.width * self.__d):
            str_msg = "Stirrup is required"
            Av_spacing_req = max(self.__Vs_req() / (self.__mat.fys * self.__d), Av_spacing_min)

        else:
            str_msg = "Need change section"
            Av_spacing_req = max(self.__Vs_req() / (self.__mat.fys * self.__d), Av_spacing_min)
        return str_msg, Av_spacing_req

    def __max_spacing(self):
        # Maximum stirrup spacing  [4.6.5]
        if self.__Vs_req() <= 1.06 * self.__mat.fc ** 0.5 * self.__sec.width * self.__d:
            max_spacing = min(self.__d / 2, 60)
        else:
            max_spacing = min(self.__d / 4, 30)
        return max_spacing

    def __ratio_of_shear_capacity(self):
        # Calculate ratio of shear capacity
        return abs(self.__Vu) / self.__phi / self.__Vn()

    def result(self) -> dict:
        msg, av_spacing_req = self.__shear_reinforcement_req()
        return {"Vu": self.__Vu,
                "Vc": self.__Vc(),
                "Vs": self.__Vs(),
                "Vn": self.__Vn(),
                "phiVn": self.__phi * self.__Vn(),
                "Av_S_req": av_spacing_req,
                "msg": msg,
                "Smax": self.__max_spacing(),
                "ratio": self.__ratio_of_shear_capacity()}

    def __str__(self):
        s = "--------------------------------------------------------------------\n"
        s += f"msg      =   {self.result()['msg']}\n"
        s += f"Vu       =   {self.result()['Vu'] / 1000 :20.3f} tf\n"
        s += f"Vc       =   {self.result()['Vc'] / 1000 :20.3f} tf\n"
        s += f"Vs       =   {self.result()['Vs'] / 1000 :20.3f} tf\n"
        s += f"phiVn    =   {self.result()['phiVn'] / 1000 :20.3f} tf\n"
        s += f"Av/S_req =   {self.result()['Av_S_req'] * 100:20.3f} cm2/m\n"
        s += f"ratio    =   {self.result()['ratio']:20.3f}\n"
        s += f"S_max    =   {self.result()['Smax']:20.3f}\n"
        return s


def phiMn(section: Section, material: Material, topbars: list[TopBar], botbars: list[BotBar]) -> float:
    cal = MomentCalculate(section, material, topbars, botbars)
    return cal.result()["phiMn"]


def phiVn(section: Section, material: Material, stirrup: Stirrup, dB) -> float:
    cal = ShearCalculate(section, material, stirrup, dB)
    return cal.result()["phiVn"]


sec = Section(width=40, height=60)
mat = Material(fc=280, fyb=4200, fys=4200)

# 剪力計算
V_u = 10 * 1000  # kgf-cm
stirrup = Stirrup(n_leg=2, size="D13", spacing=20)
shear_cal = ShearCalculate(sec, mat, stirrup, 5, V_u)
shear_cal.result()
#
ret = phiVn(sec, mat, stirrup, dB=5)
print(f"phiVn= {ret / 1000:.3f} tf")

# 彎矩計算
M_u = 20 * 100000  # kgf-cm
top_bars = [TopBar(0, "D22", 6)]
bot_bars = [BotBar(4, "D22", 6), BotBar(4, "D22", 11)]
moment_cal = MomentCalculate(sec, mat, top_bars, bot_bars, M_u)
moment_cal.result()
#
ret = phiMn(sec, mat, top_bars, bot_bars)
print(f"phiMn= {ret / 100000:.3f} tf-m")

# --------------------------------------
def step(t, a):
    if t < a:
        return 0
    else:
        return 1            

def pulse(t, s, e, scale):
    return scale * (step(t, s) - step(t, e))

class mx:
    def __init__(self,p1,p2,s):
        self.p1 = p1
        self.p2 = p2
        self.s = s
        
def envelope(*items):
    pt1 = min([i.p1 for i in items])
    pt2 = max([i.p2 for i in items])
    num = 500
    x = np.linspace(pt1, pt2, num)
    x = np.delete(x,-1)
    y = np.zeros(num-1)
    for item in items:
        y += np.array([pulse(i,item.p1,item.p2,item.s) for i in x]) 
    return x,y
    
moments =[mx(0,1,10),mx(0.2,0.8,5)]
x,y = envelope(*moments)

fig, ax = plt.subplots()
ax.plot(x, y,  color='red', linestyle="--")
ax.set_xlabel('x')
ax.set_ylabel('Moment (t-m)')
plt.show()
