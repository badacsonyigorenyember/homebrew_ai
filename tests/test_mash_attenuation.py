"""Rule 10's mash model (docs/work/s5-mash-attenuation): the stored constants follow Troester's data.

The table is typed from an image and approved by the user (doc-calc.md section 2).
"""

import pytest

from loaders.db import connect

# Troester 2009, "Effects of mash parameters on attenuation and efficiency", appendix
# "Temperature series" (PDF p. 22), read from an image: sample -> (average mash °C, attenuation %).
# See docs/work/s5-mash-attenuation/doc-calc.md section 2.
TEMPERATURE_SERIES = {
    2: (70.5, 80.2), 6: (74.9, 61.6), 7: (69.3, 83.2), 8: (65.9, 86.8), 9: (65.9, 89.6),
    10: (63.3, 87.1), 11: (61.9, 83.8), 12: (59.9, 79.2), 13: (74.7, 60.5), 14: (78.6, 44.4),
    15: (71.0, 74.4),
}
PLATEAU_SAMPLES = (10, 8, 9)
FALLING_SAMPLES = (7, 2, 15, 13, 6, 14)


@pytest.fixture(scope="module")
def conn():
    connection = connect()
    yield connection
    connection.close()


@pytest.fixture(scope="module")
def limits(conn):
    return conn.execute("select app.formulation_limits()").fetchone()[0]


def fitted_line():
    temps = [TEMPERATURE_SERIES[s][0] for s in FALLING_SAMPLES]
    atts = [TEMPERATURE_SERIES[s][1] for s in FALLING_SAMPLES]
    mean_t, mean_a = sum(temps) / len(temps), sum(atts) / len(atts)
    slope = (sum((t - mean_t) * (a - mean_a) for t, a in zip(temps, atts))
             / sum((t - mean_t) ** 2 for t in temps))
    intercept = mean_a - slope * mean_t
    plateau = sum(TEMPERATURE_SERIES[s][1] for s in PLATEAU_SAMPLES) / len(PLATEAU_SAMPLES)
    return slope, intercept, plateau


def curve(limits, temp):
    """Troester's limit of attenuation: flat at the plateau, then straight down."""
    _, _, plateau = fitted_line()
    return plateau - limits["mash_slope_pct_per_c"] * max(0, temp - limits["mash_knee_c"])


@pytest.mark.stack
def test_slope_fits_the_table(limits):
    slope, _, _ = fitted_line()
    assert abs(-slope - limits["mash_slope_pct_per_c"]) <= 0.01


@pytest.mark.stack
def test_knee_meets_the_plateau(limits):
    slope, intercept, plateau = fitted_line()
    assert abs((intercept - plateau) / -slope - limits["mash_knee_c"]) <= 0.1


@pytest.mark.stack
def test_curve_reproduces_the_table(limits):
    for sample in PLATEAU_SAMPLES + FALLING_SAMPLES:
        temp, attenuation = TEMPERATURE_SERIES[sample]
        assert abs(curve(limits, temp) - attenuation) <= 2.5, f"sample {sample}"


@pytest.mark.stack
def test_function_follows_the_curve(conn, limits):
    def att(temp):
        return float(conn.execute("select app.mash_attenuation('[0,100]'::numrange, %s::numeric)", (temp,)).fetchone()[0])

    ref = limits["mash_ref_c"]
    for i in range(11):
        temp = 64 + i * 0.5
        assert att(temp) - att(ref) == pytest.approx(curve(limits, temp) - curve(limits, ref), abs=1e-6)
