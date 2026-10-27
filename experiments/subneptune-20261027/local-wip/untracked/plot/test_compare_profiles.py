"""Run: python -m unittest discover -s plot -p test_compare_profiles.py"""
import unittest
from compare_profiles import parse_profile

HEADER = 'Index Radius (earth) P (GPa) M (earth) Density (g cm^-3) T (K) Phase\n'
CENTRE = '0 0 400 0 14 600 Fe hcp (Smith)\n'
SURFACE = '697 0.99 1e-05 1 3.2 300 Fo/Ol (Dorogokupets)\n'


class ProfileTests(unittest.TestCase):
    def test_phase_spaces_and_trailing_blank_line(self):
        rows, phases = parse_profile(HEADER + CENTRE + SURFACE + '\n')
        self.assertEqual(rows[-1][1:4], [0.99, 1e-5, 1.0])
        self.assertEqual(phases, ['Fe hcp (Smith)', 'Fo/Ol (Dorogokupets)'])

    def test_appended_runs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'appended'):
            parse_profile((HEADER + CENTRE + SURFACE) * 2)

    def test_missing_header_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'header'):
            parse_profile(CENTRE + SURFACE)

    def test_nonfinite_number_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'finite'):
            parse_profile(HEADER + CENTRE + SURFACE.replace('3.2', 'nan'))

    def test_reversed_radius_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'ordered'):
            parse_profile(HEADER + SURFACE + CENTRE)

    def test_bad_numeric_column_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_profile(HEADER + CENTRE + SURFACE.replace('300', 'oops'))

    def test_empty_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'two'):
            parse_profile(HEADER)


if __name__ == '__main__':
    unittest.main()
