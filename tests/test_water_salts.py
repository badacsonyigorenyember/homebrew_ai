from decimal import Decimal as D

from loaders.water_salts import SALTS, ion_mg_per_l_per_g


def ions(name):
    composition = next(c for n, _, c in SALTS if n == name)
    return ion_mg_per_l_per_g(composition)


def test_gypsum():
    assert ions("gypsum") == {"Ca": D("232.8"), "SO4": D("557.9")}


def test_calcium_chloride_dihydrate():
    assert ions("calcium chloride") == {"Ca": D("272.6"), "Cl": D("482.3")}


def test_baking_soda():
    assert ions("baking soda") == {"Na": D("273.7"), "HCO3": D("726.3")}
