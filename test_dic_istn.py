#!/usr/bin/env python3
"""Tests for ISTH DIC Score Calculator."""
import json
import os
import tempfile
import unittest

from dic_istn import (
    score_platelets,
    score_fibrin_marker,
    score_pt_prolongation,
    score_fibrinogen,
    calculate_overt_dic_score,
    calculate_non_overt_dic_score,
    assess_clinical_context,
    process_batch,
)


class TestScorePlatelets(unittest.TestCase):
    def test_above_100(self):
        self.assertEqual(score_platelets(150), 0)
        self.assertEqual(score_platelets(101), 0)

    def test_50_to_100(self):
        self.assertEqual(score_platelets(100), 1)
        self.assertEqual(score_platelets(75), 1)
        self.assertEqual(score_platelets(50), 1)

    def test_below_50(self):
        self.assertEqual(score_platelets(49), 2)
        self.assertEqual(score_platelets(20), 2)
        self.assertEqual(score_platelets(0), 2)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            score_platelets(-1)


class TestScoreFibrinMarker(unittest.TestCase):
    def test_no_increase(self):
        self.assertEqual(score_fibrin_marker("no_increase"), 0)
        self.assertEqual(score_fibrin_marker("none"), 0)
        self.assertEqual(score_fibrin_marker("normal"), 0)
        self.assertEqual(score_fibrin_marker("negative"), 0)

    def test_moderate_increase(self):
        self.assertEqual(score_fibrin_marker("moderate_increase"), 2)
        self.assertEqual(score_fibrin_marker("moderate"), 2)
        self.assertEqual(score_fibrin_marker("positive"), 2)

    def test_strong_increase(self):
        self.assertEqual(score_fibrin_marker("strong_increase"), 3)
        self.assertEqual(score_fibrin_marker("strong"), 3)
        self.assertEqual(score_fibrin_marker("marked"), 3)

    def test_numeric_fold(self):
        self.assertEqual(score_fibrin_marker("1.5"), 0)
        self.assertEqual(score_fibrin_marker("2.0"), 2)
        self.assertEqual(score_fibrin_marker("3.5"), 2)
        self.assertEqual(score_fibrin_marker("5.0"), 3)

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            score_fibrin_marker("invalid_value")


class TestScorePTProlongation(unittest.TestCase):
    def test_below_3(self):
        self.assertEqual(score_pt_prolongation(0), 0)
        self.assertEqual(score_pt_prolongation(2.9), 0)

    def test_3_to_6(self):
        self.assertEqual(score_pt_prolongation(3.0), 1)
        self.assertEqual(score_pt_prolongation(4.5), 1)
        self.assertEqual(score_pt_prolongation(6.0), 1)

    def test_above_6(self):
        self.assertEqual(score_pt_prolongation(6.1), 2)
        self.assertEqual(score_pt_prolongation(10.0), 2)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            score_pt_prolongation(-1)


class TestScoreFibrinogen(unittest.TestCase):
    def test_above_1(self):
        self.assertEqual(score_fibrinogen(1.5), 0)
        self.assertEqual(score_fibrinogen(2.0), 0)

    def test_at_or_below_1(self):
        self.assertEqual(score_fibrinogen(1.0), 1)
        self.assertEqual(score_fibrinogen(0.5), 1)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            score_fibrinogen(-1)


class TestOvertDICScore(unittest.TestCase):
    def test_no_dic(self):
        """All normal values → score 0."""
        result = calculate_overt_dic_score(150, "no_increase", 1.0, 2.0)
        self.assertEqual(result["total_score"], 0)
        self.assertFalse(result["overt_dic"])
        self.assertIn("Not suggestive", result["interpretation"])

    def test_overt_dic_positive(self):
        """High-risk values → score >= 5."""
        # Platelets 40 → 2, strong_increase → 3, PT 5 → 1, fibrinogen 0.8 → 1 = 7
        result = calculate_overt_dic_score(40, "strong_increase", 5.0, 0.8)
        self.assertEqual(result["total_score"], 7)
        self.assertTrue(result["overt_dic"])
        self.assertIn("Compatible", result["interpretation"])

    def test_borderline_score_5(self):
        """Score exactly 5 should be positive."""
        # Platelets 80 → 1, moderate_increase → 2, PT 4 → 1, fibrinogen 0.9 → 1 = 5
        result = calculate_overt_dic_score(80, "moderate_increase", 4.0, 0.9)
        self.assertEqual(result["total_score"], 5)
        self.assertTrue(result["overt_dic"])

    def test_borderline_score_4(self):
        """Score 4 should be negative."""
        # Platelets 120 → 0, moderate_increase → 2, PT 4 → 1, fibrinogen 0.9 → 1 = 4
        result = calculate_overt_dic_score(120, "moderate_increase", 4.0, 0.9)
        self.assertEqual(result["total_score"], 4)
        self.assertFalse(result["overt_dic"])

    def test_max_score(self):
        """Maximum possible score is 8."""
        result = calculate_overt_dic_score(10, "strong_increase", 10.0, 0.5)
        self.assertEqual(result["total_score"], 8)
        self.assertEqual(result["max_possible_score"], 8)

    def test_sepsis_scenario(self):
        """Typical sepsis DIC: low platelets, elevated D-dimer, prolonged PT, low fibrinogen."""
        result = calculate_overt_dic_score(35, "strong_increase", 5.5, 0.9)
        self.assertEqual(result["platelet_score"], 2)
        self.assertEqual(result["fibrin_marker_score"], 3)
        self.assertEqual(result["pt_score"], 1)
        self.assertEqual(result["fibrinogen_score"], 1)
        self.assertEqual(result["total_score"], 7)
        self.assertTrue(result["overt_dic"])


class TestNonOvertDICScore(unittest.TestCase):
    def test_no_dynamic(self):
        """Non-overt without trends should equal base score."""
        result = calculate_non_overt_dic_score(150, "no_increase", 1.0, 2.0)
        self.assertEqual(result["base_score"], 0)
        self.assertEqual(result["dynamic_score"], 0)
        self.assertEqual(result["total_score"], 0)

    def test_worsening_trends(self):
        """Falling platelets, falling fibrinogen, rising D-dimer → +3 dynamic."""
        result = calculate_non_overt_dic_score(
            80, "moderate_increase", 3.0, 1.5,
            platelet_trend="falling",
            fibrinogen_trend="falling",
            d_dimer_trend="rising",
        )
        self.assertEqual(result["dynamic_score"], 3)

    def test_improving_trends(self):
        """Rising platelets, rising fibrinogen, falling D-dimer → -3 dynamic."""
        result = calculate_non_overt_dic_score(
            80, "moderate_increase", 3.0, 1.5,
            platelet_trend="rising",
            fibrinogen_trend="rising",
            d_dimer_trend="falling",
        )
        self.assertEqual(result["dynamic_score"], -3)

    def test_evolving_dic(self):
        """Score 2-4 should suggest evolving DIC."""
        # Base: 0+2+1+0 = 3, dynamic: 0 → total 3
        result = calculate_non_overt_dic_score(150, "moderate_increase", 3.0, 1.5)
        self.assertEqual(result["total_score"], 3)
        self.assertIn("evolving", result["interpretation"])


class TestClinicalContext(unittest.TestCase):
    def test_sepsis(self):
        result = assess_clinical_context("sepsis", 6)
        self.assertTrue(result["recognized"])
        self.assertTrue(result["score_significant"])
        self.assertIn("antimicrobials", str(result["key_considerations"]).lower())

    def test_trauma(self):
        result = assess_clinical_context("trauma", 7)
        self.assertTrue(result["recognized"])
        self.assertIn("tranexamic", str(result["key_considerations"]).lower())

    def test_obstetric(self):
        result = assess_clinical_context("obstetric", 5)
        self.assertTrue(result["recognized"])

    def test_malignancy(self):
        result = assess_clinical_context("malignancy", 4)
        self.assertTrue(result["recognized"])
        self.assertIn("apl", str(result["key_considerations"]).lower())

    def test_snakebite(self):
        result = assess_clinical_context("snakebite", 6)
        self.assertTrue(result["recognized"])
        self.assertIn("antivenom", str(result["key_considerations"]).lower())

    def test_unknown_context(self):
        result = assess_clinical_context("unknown_disease", 5)
        self.assertFalse(result["recognized"])


class TestProcessBatch(unittest.TestCase):
    def test_batch_overt(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("platelets,fibrin_marker,pt_prolongation,fibrinogen\n")
                f.write("150,no_increase,1.0,2.0\n")
                f.write("40,strong_increase,5.0,0.8\n")
            n = process_batch(inp, out)
            self.assertEqual(n, 2)
            with open(out) as f:
                content = f.read()
                self.assertIn("dic_total_score", content)
                self.assertIn("Compatible", content)

    def test_batch_non_overt(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("platelets,fibrin_marker,pt_prolongation,fibrinogen,score_type,platelet_trend\n")
                f.write("80,moderate_increase,3.0,1.5,non_overt,falling\n")
            n = process_batch(inp, out)
            self.assertEqual(n, 1)


class TestCLI(unittest.TestCase):
    def test_cli_overt(self):
        from cli import main
        ret = main(["overt", "--platelets", "80", "--fibrin-marker", "moderate_increase",
                     "--pt-prolongation", "4", "--fibrinogen", "0.9"])
        self.assertEqual(ret, 0)

    def test_cli_context(self):
        from cli import main
        ret = main(["context", "--context", "sepsis", "--dic-score", "6"])
        self.assertEqual(ret, 0)

    def test_cli_batch(self):
        from cli import main
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("platelets,fibrin_marker,pt_prolongation,fibrinogen\n")
                f.write("150,no_increase,1.0,2.0\n")
            ret = main(["batch", "-i", inp, "-o", out])
            self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
