import pypsa

n = pypsa.Network()

eta = 0.1

n.add("Link",
    "CO2_capture",
    bus0 = "electricity"
    bus1 = "CO2 atmosphere",
    bus2 = "Co2 underground",

    efficiency = eta,
    efficiency2 = eta2,

    )
#Add a generator: solar--import time series