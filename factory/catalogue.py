"""PE100 pipe dimensions transcribed from the Adafnia company profile (pages 7 and 10).

Each row is (wall S mm, weight W kg/m). None means the size is not made in that class.
Rows are seeded as *unapproved* variants: staff must check them against the factory's
engineering tables and tick "approved" in the dashboard before they appear publicly.
"""
from decimal import Decimal

DIAMETERS = [20, 25, 32, 40, 50, 63, 75, 90, 110, 125, 140, 160, 180, 200, 225]

# pressure bar -> (SDR, rows aligned with DIAMETERS)
PE100_STRAIGHT = {
    4: ('41', [None, None, None, None, None, (1.8, .364), (1.9, .457), (2.2, .643), (2.7, .943), (3.1, 1.23), (3.5, 1.54), (4.0, 2.00), (4.4, 2.49), (4.9, 3.05), (5.5, 3.86)]),
    6: ('26', [None, None, None, (1.8, .227), (2.0, .314), (2.5, .494), (2.9, .675), (3.5, .978), (4.2, 1.43), (4.8, 1.84), (5.4, 2.32), (6.2, 3.04), (6.9, 3.79), (7.7, 4.69), (8.6, 5.89)]),
    10: ('17', [None, (1.8, .137), (1.9, .187), (2.4, .295), (3.0, .453), (3.8, .721), (4.5, 1.02), (5.4, 1.46), (6.6, 2.17), (7.4, 2.76), (8.3, 3.46), (9.5, 4.52), (10.7, 5.71), (11.9, 7.05), (13.4, 8.93)]),
    16: ('11', [(1.9, .112), (2.3, .171), (2.9, .272), (3.7, .430), (4.6, .666), (5.8, 1.05), (6.8, 1.47), (8.2, 2.12), (10.0, 3.14), (11.4, 4.08), (12.7, 5.08), (14.6, 6.67), (16.4, 8.42), (18.2, 10.4), (20.5, 13.1)]),
    20: ('9', [(2.3, .133), (2.8, .200), (3.6, .327), (4.5, .509), (5.6, .788), (7.1, 1.26), (8.4, 1.76), (10.1, 2.54), (12.3, 3.78), (14.0, 4.87), (15.7, 6.11), (17.9, 7.96), (20.1, 10.1), (22.4, 12.4), (25.2, 15.8)]),
    25: ('7.4', [(2.8, .154), (3.5, .240), (4.4, .386), (5.5, .600), (6.9, .936), (8.6, 1.47), (10.3, 2.09), (12.3, 3.00), (15.1, 4.49), (17.1, 5.77), (19.2, 7.25), (21.9, 9.44), (24.6, 11.9), (27.4, 14.8), (30.8, 18.6)]),
}


def straight_pipe_rows():
    for bar, (sdr, rows) in PE100_STRAIGHT.items():
        for diameter, row in zip(DIAMETERS, rows):
            if row:
                yield {'diameter_mm': Decimal(diameter), 'pressure_bar': Decimal(bar), 'sdr': Decimal(sdr),
                       'wall_mm': Decimal(str(row[0])), 'weight_kg_m': Decimal(str(row[1]))}
