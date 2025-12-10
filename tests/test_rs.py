import unittest

from relation_theory import FD, FDSet, RelationSchema


class TestRelationSchemaCreation(unittest.TestCase):
    """Test cases for RelationSchema creation and initialization"""

    def test_creation_with_set(self):
        """Test creating RelationSchema with set of attributes"""
        attrs = {"A", "B", "C"}
        fds = FDSet([FD({"A"}, {"B"})])
        rs = RelationSchema(attrs, fds)

        self.assertEqual(rs.attributes, frozenset(attrs))
        self.assertEqual(len(rs.fd_set.fds), 1)

    def test_from_str_simple(self):
        """Test creating RelationSchema from string representation"""
        rs = RelationSchema.from_str("ABC", ["A->B", "B->C"])

        self.assertEqual(rs.attributes, frozenset({"A", "B", "C"}))
        self.assertEqual(len(rs.fd_set.fds), 2)

    def test_from_str_multiple_dependencies(self):
        """Test from_str with multiple FDs"""
        rs = RelationSchema.from_str("ABCD", ["A->B", "BC->D", "D->A"])

        self.assertEqual(len(rs.attributes), 4)
        self.assertEqual(len(rs.fd_set.fds), 3)

    def test_from_str_with_spaces(self):
        """Test from_str handles spaces in FD notation"""
        rs = RelationSchema.from_str("ABC", ["A -> B", "B -> C"])

        self.assertEqual(len(rs.fd_set.fds), 2)

    def test_from_str_invalid_format(self):
        """Test from_str raises error for invalid FD format"""
        with self.assertRaises(ValueError):
            RelationSchema.from_str("ABC", ["AB"])

    def test_from_str_empty_lhs(self):
        """Test from_str raises error for empty left-hand side"""
        with self.assertRaises(ValueError):
            RelationSchema.from_str("ABC", ["->A"])

    def test_repr(self):
        """Test string representation of RelationSchema"""
        rs = RelationSchema.from_str("ABC", ["A->B"])
        repr_str = repr(rs)

        self.assertIn("R(", repr_str)
        self.assertIn("F", repr_str)
        self.assertIn("→", repr_str)


class TestCandidateKeys(unittest.TestCase):
    """Test cases for candidate key identification"""

    def test_single_candidate_key(self):
        """Test relation with single candidate key"""
        rs = RelationSchema.from_str("ABC", ["A->B", "A->C"])
        keys = rs.candidate_keys()

        self.assertEqual(len(keys), 1)
        self.assertIn({"A"}, keys)

    def test_multiple_candidate_keys(self):
        """Test relation with multiple candidate keys"""
        rs = RelationSchema.from_str("ABC", ["A->B", "B->A", "B->C"])
        keys = rs.candidate_keys()

        # Both A and B can be candidate keys
        self.assertGreaterEqual(len(keys), 1)

    def test_composite_candidate_key(self):
        """Test relation with composite candidate key"""
        rs = RelationSchema.from_str("ABCD", ["AB->C", "C->D"])
        keys = rs.candidate_keys()

        self.assertTrue(any({"A", "B"} <= key for key in keys))

    def test_isolated_attributes_in_keys(self):
        """Test that isolated attributes are included in candidate keys"""
        rs = RelationSchema.from_str("ABCD", ["A->B"])
        keys = rs.candidate_keys()

        # C and D are isolated, so any candidate key must include them
        for key in keys:
            self.assertIn("C", key)
            self.assertIn("D", key)

    def test_example_abcd(self):
        """Test ABCD example from main.py"""
        rs = RelationSchema.from_str("ABCD", ["A->B", "BC->D", "D->A"])
        keys = rs.candidate_keys()

        # Should have candidate keys containing BC or equivalently ABC or BCD
        self.assertGreater(len(keys), 0)

    def test_keys_minimize(self):
        """Test that candidate keys are minimal"""
        rs = RelationSchema.from_str("ABC", ["A->B", "A->C"])
        keys = rs.candidate_keys()

        for key in keys:
            # Each candidate key should be minimal
            for attr in key:
                reduced_key = key - {attr}
                # Reduced key should not be a superkey
                closure = rs.fd_set.closure(reduced_key)
                if len(reduced_key) > 0:
                    self.assertNotEqual(closure, rs.attributes)


class TestNormalizationForms(unittest.TestCase):
    """Test cases for normalization form judgment"""

    def test_judge_2nf_violation(self):
        """Test detection of 2NF violation"""
        rs = RelationSchema.from_str("ABCD", ["A->B", "BC->D", "D->A"])
        level, violations = rs.judge_NF()

        # This actually satisfies 2NF but violates 3NF
        self.assertEqual(level, "3NF")
        self.assertGreater(len(violations), 0)

    def test_judge_2nf_satisfied(self):
        """Test 2NF satisfied relation"""
        rs = RelationSchema.from_str("ABCD", ["AB->C", "C->D"])
        level, violations = rs.judge_NF()

        self.assertNotEqual(level, "1NF")

    def test_judge_3nf_violation(self):
        """Test detection of 3NF violation"""
        rs = RelationSchema.from_str("ABCD", ["AB->C", "C->D"])
        level, violations = rs.judge_NF()

        self.assertEqual(level, "2NF")
        self.assertGreater(len(violations), 0)

    def test_judge_3nf_satisfied(self):
        """Test 3NF satisfied relation"""
        rs = RelationSchema.from_str("ABCDE", ["A->B", "A->C", "A->D", "A->E", "B->A"])
        level, violations = rs.judge_NF()

        self.assertNotEqual(level, "2NF")

    def test_judge_bcnf_violation(self):
        """Test detection of BCNF violation"""
        rs = RelationSchema.from_str("ABC", ["AB->C", "C->A"])
        level, violations = rs.judge_NF()

        self.assertEqual(level, "3NF")
        self.assertGreater(len(violations), 0)

    def test_judge_bcnf_satisfied(self):
        """Test BCNF satisfied relation"""
        rs = RelationSchema.from_str("ABC", ["A->B", "A->C"])
        level, violations = rs.judge_NF()

        self.assertEqual(level, "BCNF")
        self.assertEqual(len(violations), 0)

    def test_judge_nf_no_violations(self):
        """Test relation with no violations"""
        rs = RelationSchema.from_str("AB", ["A->B"])
        level, violations = rs.judge_NF()

        self.assertEqual(level, "BCNF")
        self.assertEqual(len(violations), 0)


class TestLosslessDecomposition(unittest.TestCase):
    """Test cases for lossless decomposition checking"""

    def test_lossless_with_candidate_key_included(self):
        """Test decomposition is lossless when candidate key is included in subschema"""
        rs = RelationSchema.from_str("ABCD", ["A->B", "B->C"])
        sub_schemas = [{"A", "B"}, {"A", "C", "D"}]

        result = rs.is_lossless_decomposition(sub_schemas)
        self.assertTrue(result)

    def test_lossless_decomposition_example(self):
        """Test the lossless decomposition example from main.py"""
        rs = RelationSchema.from_str("ABCD", ["A->B", "B->C"])
        sub_schemas1 = [{"A", "B"}, {"A", "C", "D"}]
        sub_schemas2 = [{"A", "B"}, {"C", "D"}]

        result1 = rs.is_lossless_decomposition(sub_schemas1)
        result2 = rs.is_lossless_decomposition(sub_schemas2)

        self.assertTrue(result1)
        self.assertFalse(result2)

    def test_not_lossless_decomposition(self):
        """Test detection of lossy decomposition"""
        rs = RelationSchema.from_str("ABC", ["A->B"])
        # The candidate key is actually {A, C}, not {A, B}
        # So decomposition [AB, BC] is lossy
        sub_schemas = [{"A", "B"}, {"B", "C"}]

        result = rs.is_lossless_decomposition(sub_schemas)
        self.assertFalse(result)  # Should be lossy

    def test_single_subschema_with_all_attrs(self):
        """Test decomposition with single subschema containing all attributes"""
        rs = RelationSchema.from_str("ABC", ["A->B"])
        sub_schemas = [{"A", "B", "C"}]

        result = rs.is_lossless_decomposition(sub_schemas)
        self.assertTrue(result)

    def test_decomposition_multiple_candidate_keys(self):
        """Test decomposition when relation has multiple candidate keys"""
        rs = RelationSchema.from_str("ABC", ["A->B", "B->A", "B->C"])
        keys = rs.candidate_keys()

        # Create subschemas that include one of the candidate keys
        sub_schemas = [keys[0] if keys else {"A", "B"}, {"B", "C"}]
        result = rs.is_lossless_decomposition(sub_schemas)

        self.assertTrue(result)


class TestJudge2NF(unittest.TestCase):
    """Test cases for 2NF judgment method"""

    def test_2nf_partial_dependency_violation(self):
        """Test 2NF violation due to partial dependency"""
        # Use a simpler example that clearly violates 2NF with partial dependency
        rs = RelationSchema.from_str("ABCD", ["AB->C", "B->D"])
        keys = rs.candidate_keys()
        violations = rs._judge_2NF(keys)

        self.assertGreater(len(violations), 0)
        self.assertTrue(any("partial" in v.lower() for v in violations))

    def test_2nf_satisfied_no_partial_dependency(self):
        """Test 2NF satisfied when no partial dependencies exist"""
        rs = RelationSchema.from_str("ABCD", ["AB->C", "C->D"])
        keys = rs.candidate_keys()
        violations = rs._judge_2NF(keys)

        self.assertEqual(len(violations), 0)


class TestJudge3NF(unittest.TestCase):
    """Test cases for 3NF judgment method"""

    def test_3nf_transitive_dependency_violation(self):
        """Test 3NF violation due to transitive dependency"""
        rs = RelationSchema.from_str("ABCD", ["AB->C", "C->D"])
        keys = rs.candidate_keys()
        violations = rs._judge_3NF(keys)

        self.assertGreater(len(violations), 0)

    def test_3nf_satisfied_no_transitive_dependency(self):
        """Test 3NF satisfied when no transitive dependencies exist"""
        rs = RelationSchema.from_str("ABCDE", ["A->B", "A->C", "A->D", "A->E", "B->A"])
        keys = rs.candidate_keys()
        violations = rs._judge_3NF(keys)

        self.assertEqual(len(violations), 0)


class TestJudgeBCNF(unittest.TestCase):
    """Test cases for BCNF judgment method"""

    def test_bcnf_violation(self):
        """Test BCNF violation detection"""
        rs = RelationSchema.from_str("ABC", ["AB->C", "C->A"])
        keys = rs.candidate_keys()
        violations = rs._judge_BCNF(keys)

        self.assertGreater(len(violations), 0)

    def test_bcnf_satisfied(self):
        """Test BCNF satisfied"""
        rs = RelationSchema.from_str("ABC", ["A->B", "A->C"])
        keys = rs.candidate_keys()
        violations = rs._judge_BCNF(keys)

        self.assertEqual(len(violations), 0)

    def test_bcnf_all_lhs_are_superkeys(self):
        """Test BCNF when all FD left-hand sides are superkeys"""
        rs = RelationSchema.from_str("ABC", ["AB->C"])
        keys = rs.candidate_keys()
        violations = rs._judge_BCNF(keys)

        self.assertEqual(len(violations), 0)


class TestComplexScenarios(unittest.TestCase):
    """Test cases for complex scenarios"""

    def test_complex_decomposition_scenario(self):
        """Test a more complex decomposition scenario"""
        rs = RelationSchema.from_str("ABCDE", ["A->B", "B->C", "C->D", "D->E"])

        # Check candidate keys
        keys = rs.candidate_keys()
        self.assertEqual(len(keys), 1)
        self.assertIn({"A"}, keys)

        # Check normalization
        level, violations = rs.judge_NF()
        self.assertNotEqual(level, "BCNF")

    def test_all_attributes_as_candidate_key(self):
        """Test relation where all attributes form the only candidate key"""
        rs = RelationSchema.from_str("ABC", [])

        keys = rs.candidate_keys()
        self.assertEqual(len(keys), 1)
        self.assertEqual(keys[0], frozenset({"A", "B", "C"}))

    def test_multiple_composite_keys(self):
        """Test relation with multiple different composite candidate keys"""
        rs = RelationSchema.from_str("ABC", ["A->B", "B->A", "B->C"])

        keys = rs.candidate_keys()
        # Should have at least A or B as candidate keys
        self.assertGreater(len(keys), 0)

    def test_from_str_with_multi_char_attributes(self):
        """Test from_str with single-character attributes"""
        rs = RelationSchema.from_str("XYZ", ["X->Y", "Y->Z"])

        self.assertEqual(rs.attributes, frozenset({"X", "Y", "Z"}))
        keys = rs.candidate_keys()
        self.assertTrue(any({"X"} <= key for key in keys))

    def test_large_schema(self):
        """Test with larger relation schema"""
        attrs = "ABCDEFGH"
        fds = ["A->B", "B->C", "C->D", "D->E", "E->F"]
        rs = RelationSchema.from_str(attrs, fds)

        self.assertEqual(len(rs.attributes), 8)
        self.assertEqual(len(rs.fd_set.fds), 5)

        keys = rs.candidate_keys()
        self.assertGreater(len(keys), 0)


if __name__ == "__main__":
    unittest.main()
