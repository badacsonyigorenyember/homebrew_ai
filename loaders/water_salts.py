"""The common brewing salts and the ions 1 g of each adds to 1 L of water.

The numbers are computed, never typed in: a salt's molar mass is the sum of the IUPAC standard
atomic masses of its atoms, and each ion's share of 1 g (1000 mg) is the ion's mass over that
molar mass. Water of hydration counts in the molar mass but adds no ion.
"""

from decimal import ROUND_HALF_UP, Decimal

# IUPAC standard (abridged) atomic weights, g/mol.
ATOMIC_MASS: dict[str, Decimal] = {
    "H": Decimal("1.008"),
    "C": Decimal("12.011"),
    "O": Decimal("15.999"),
    "Na": Decimal("22.990"),
    "Mg": Decimal("24.305"),
    "S": Decimal("32.06"),
    "Cl": Decimal("35.45"),
    "Ca": Decimal("40.078"),
}

# The parts a salt is built from (the brewing ions, and water of hydration) -> their atoms.
PARTS: dict[str, dict[str, int]] = {
    "Ca": {"Ca": 1},
    "Mg": {"Mg": 1},
    "Na": {"Na": 1},
    "SO4": {"S": 1, "O": 4},
    "Cl": {"Cl": 1},
    "HCO3": {"H": 1, "C": 1, "O": 3},
    "CO3": {"C": 1, "O": 3},
    "OH": {"O": 1, "H": 1},
    "H2O": {"H": 2, "O": 1},
}

# Parts that are water of hydration, not a brewing ion.
WATER = {"H2O"}

# (name, formula, composition: part -> count per formula unit)
SALTS: list[tuple[str, str, dict[str, int]]] = [
    ("gypsum", "CaSO4·2H2O", {"Ca": 1, "SO4": 1, "H2O": 2}),
    ("calcium chloride", "CaCl2·2H2O", {"Ca": 1, "Cl": 2, "H2O": 2}),
    ("epsom salt", "MgSO4·7H2O", {"Mg": 1, "SO4": 1, "H2O": 7}),
    ("magnesium chloride", "MgCl2·6H2O", {"Mg": 1, "Cl": 2, "H2O": 6}),
    ("table salt", "NaCl", {"Na": 1, "Cl": 1}),
    ("baking soda", "NaHCO3", {"Na": 1, "HCO3": 1}),
    ("chalk", "CaCO3", {"Ca": 1, "CO3": 1}),
    ("slaked lime", "Ca(OH)2", {"Ca": 1, "OH": 2}),
]


def part_mass(part: str) -> Decimal:
    """Molar mass of one part (ion or water), g/mol."""
    return sum(ATOMIC_MASS[atom] * n for atom, n in PARTS[part].items())


def ion_mg_per_l_per_g(composition: dict[str, int]) -> dict[str, Decimal]:
    """mg/L of each brewing ion from 1 g of the salt in 1 L, rounded to 0.1."""
    molar_mass = sum(part_mass(part) * n for part, n in composition.items())
    return {
        part: (1000 * part_mass(part) * n / molar_mass).quantize(Decimal("0.1"), ROUND_HALF_UP)
        for part, n in composition.items()
        if part not in WATER
    }
