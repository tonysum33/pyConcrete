# Rebar Table CNS 560
rebar_table = {"D10": {"area": 0.7133, "db": 0.953, "weight": 0.560, "l": 3.00},
               "D13": {"area": 1.2670, "db": 1.270, "weight": 0.994, "l": 4.00},
               "D16": {"area": 1.9860, "db": 1.590, "weight": 1.560, "l": 5.00},
               "D19": {"area": 2.8650, "db": 1.910, "weight": 2.250, "l": 6.00},
               "D22": {"area": 3.8710, "db": 2.220, "weight": 3.040, "l": 7.00},
               "D25": {"area": 5.0670, "db": 2.540, "weight": 3.980, "l": 8.00},
               "D29": {"area": 6.4690, "db": 2.870, "weight": 5.080, "l": 9.00},
               "D32": {"area": 8.1430, "db": 3.220, "weight": 6.390, "l": 10.1},
               "D36": {"area": 10.070, "db": 3.580, "weight": 7.900, "l": 11.3},
               "D43": {"area": 14.520, "db": 4.300, "weight": 11.40, "l": 13.5}}


class Rebar:
    def __init__(self,  size):
        self.__size = size

    @property
    def area(self) -> float:
        return rebar_table[self.__size]["area"]

    @property
    def weight(self) -> float:
        return rebar_table[self.__size]["weight"]


class TopBar(Rebar):
    def __init__(self, qty, size, dT):
        super().__init__(size)
        self.n = qty
        self.dT = dT
        self.areas = self.n * self.area


class BotBar(Rebar):
    def __init__(self, qty, size, dB):
        super().__init__(size)
        self.n = qty
        self.dB = dB
        self.areas = self.n * self.area


class Stirrup(Rebar):
    def __init__(self, n_leg, size, spacing):
        super().__init__(size)
        self.n_leg = n_leg
        self.spacing = spacing
        self.areas = self.n_leg * self.area


if __name__ == "__main__":
    top_bar = [TopBar(3, "D22", 6.0),
               TopBar(2, "D22", 11.0)]
    print(top_bar[0].areas)
