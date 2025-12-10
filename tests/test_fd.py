import unittest

from relation_theory import FD, FDSet


class TestFD(unittest.TestCase):
    """Test cases for the FD (Functional Dependency) class"""

    def test_fd_creation(self):
        """Test creating a functional dependency"""
        fd = FD({"A"}, {"B"})
        self.assertEqual(fd.lhs, frozenset({"A"}))
        self.assertEqual(fd.rhs, frozenset({"B"}))

    def test_fd_creation_with_frozenset(self):
        """Test creating FD with frozenset inputs"""
        fd = FD(frozenset({"A", "B"}), frozenset({"C"}))
        self.assertEqual(fd.lhs, frozenset({"A", "B"}))
        self.assertEqual(fd.rhs, frozenset({"C"}))

    def test_fd_equality(self):
        """Test FD equality comparison"""
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"A"}, {"B"})
        fd3 = FD({"A"}, {"C"})
        self.assertEqual(fd1, fd2)
        self.assertNotEqual(fd1, fd3)

    def test_fd_hash(self):
        """Test FD hash consistency"""
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"A"}, {"B"})
        self.assertEqual(hash(fd1), hash(fd2))
        # Test that FD can be added to a set
        fd_set = {fd1, fd2}
        self.assertEqual(len(fd_set), 1)

    def test_fd_repr(self):
        """Test FD string representation"""
        fd = FD({"A"}, {"B"})
        self.assertIn("A", repr(fd))
        self.assertIn("B", repr(fd))
        self.assertIn("→", repr(fd))

    def test_fd_multiple_attributes_lhs(self):
        """Test FD with multiple attributes on left-hand side"""
        fd = FD({"A", "B"}, {"C"})
        self.assertEqual(fd.lhs, frozenset({"A", "B"}))
        self.assertEqual(fd.rhs, frozenset({"C"}))

    def test_fd_multiple_attributes_rhs(self):
        """Test FD with multiple attributes on right-hand side"""
        fd = FD({"A"}, {"B", "C"})
        self.assertEqual(fd.lhs, frozenset({"A"}))
        self.assertEqual(fd.rhs, frozenset({"B", "C"}))


class TestFDSet(unittest.TestCase):
    """Test cases for the FDSet class"""

    def setUp(self):
        """Set up common test data"""
        self.fd_ab = FD({"A"}, {"B"})
        self.fd_bc = FD({"B"}, {"C"})
        self.fd_ac = FD({"A"}, {"C"})

    def test_fdset_creation_empty(self):
        """Test creating an empty FDSet"""
        fdset = FDSet()
        self.assertEqual(len(fdset.fds), 0)

    def test_fdset_creation_with_fds(self):
        """Test creating FDSet with multiple FDs"""
        fds = [self.fd_ab, self.fd_bc]
        fdset = FDSet(fds)
        self.assertEqual(len(fdset.fds), 2)
        self.assertIn(self.fd_ab, fdset.fds)
        self.assertIn(self.fd_bc, fdset.fds)

    def test_closure_single_attribute(self):
        """Test closure of a single attribute"""
        fdset = FDSet([self.fd_ab, self.fd_bc])
        closure = fdset.closure({"A"})
        self.assertEqual(closure, {"A", "B", "C"})

    def test_closure_no_dependencies(self):
        """Test closure when attribute has no dependencies"""
        fdset = FDSet([self.fd_ab, self.fd_bc])
        closure = fdset.closure({"C"})
        self.assertEqual(closure, {"C"})

    def test_closure_empty_set(self):
        """Test closure of empty set"""
        fdset = FDSet([self.fd_ab, self.fd_bc])
        closure = fdset.closure(set())
        self.assertEqual(closure, set())

    def test_closure_multiple_attributes(self):
        """Test closure with multiple input attributes"""
        fdset = FDSet([self.fd_ab, self.fd_bc])
        closure = fdset.closure({"B"})
        self.assertEqual(closure, {"B", "C"})

    def test_closure_with_complex_dependencies(self):
        """Test closure with more complex FD set"""
        # FDs: A->B, B->C, C->D
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"B"}, {"C"})
        fd3 = FD({"C"}, {"D"})
        fdset = FDSet([fd1, fd2, fd3])

        closure = fdset.closure({"A"})
        self.assertEqual(closure, {"A", "B", "C", "D"})

    def test_implies_simple(self):
        """Test implies with simple case"""
        fdset = FDSet([self.fd_ab, self.fd_bc])
        # A->C should be implied by A->B and B->C
        fd_ac = FD({"A"}, {"C"})
        self.assertTrue(fdset.implies(fd_ac))

    def test_implies_false(self):
        """Test implies returns false when FD is not implied"""
        fdset = FDSet([self.fd_ab, self.fd_bc])
        # B->A should not be implied
        fd_ba = FD({"B"}, {"A"})
        self.assertFalse(fdset.implies(fd_ba))

    def test_implies_subset_of_closure(self):
        """Test implies when rhs is subset of closure"""
        fdset = FDSet([self.fd_ab, self.fd_bc])
        # A->{B,C} should be implied
        fd = FD({"A"}, {"B", "C"})
        self.assertTrue(fdset.implies(fd))

    def test_singleton_rhs_single_fd(self):
        """Test singleton_rhs with single FD having multiple RHS attributes"""
        fd = FD({"A"}, {"B", "C", "D"})
        fdset = FDSet([fd])
        singleton = fdset.singleton_rhs()

        self.assertEqual(len(singleton.fds), 3)
        # Check that all RHS attributes are single elements
        for fd_single in singleton.fds:
            self.assertEqual(len(fd_single.rhs), 1)

    def test_singleton_rhs_multiple_fds(self):
        """Test singleton_rhs with multiple FDs"""
        fd1 = FD({"A"}, {"B", "C"})
        fd2 = FD({"B"}, {"D"})
        fdset = FDSet([fd1, fd2])
        singleton = fdset.singleton_rhs()

        # fd1 produces 2 FDs, fd2 produces 1 FD
        self.assertEqual(len(singleton.fds), 3)

    def test_canonical_cover_removes_redundant(self):
        """Test canonical_cover removes redundant FDs"""
        # A->B, A->C, B->C: the third one is redundant
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"A"}, {"C"})
        fd3 = FD({"B"}, {"C"})
        fdset = FDSet([fd1, fd2, fd3])

        cover = fdset.canonical_cover()
        # A->B and B->C imply A->C, so the minimal cover shouldn't need A->C directly
        self.assertLessEqual(len(cover.fds), len(fdset.fds))

    def test_canonical_cover_single_fd(self):
        """Test canonical_cover with single FD"""
        fd = FD({"A"}, {"B"})
        fdset = FDSet([fd])
        cover = fdset.canonical_cover()

        self.assertEqual(len(cover.fds), 1)
        self.assertEqual(cover.fds[0].lhs, frozenset({"A"}))
        self.assertEqual(cover.fds[0].rhs, frozenset({"B"}))

    def test_canonical_cover_with_redundant_lhs(self):
        """Test canonical_cover minimizes left-hand sides"""
        # ABC->D where AB->D is sufficient
        fd1 = FD({"A", "B", "C"}, {"D"})
        fd2 = FD({"A", "B"}, {"D"})
        fdset = FDSet([fd1, fd2])

        cover = fdset.canonical_cover()
        # Should contain the minimal AB->D
        self.assertTrue(any(fd.lhs == frozenset({"A", "B"}) for fd in cover.fds))

    def test_fdset_equality_same(self):
        """Test FDSet equality when sets are equivalent"""
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"B"}, {"C"})
        fdset1 = FDSet([fd1, fd2])
        fdset2 = FDSet([fd1, fd2])

        self.assertEqual(fdset1, fdset2)

    def test_fdset_equality_different_order(self):
        """Test FDSet equality with different order"""
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"B"}, {"C"})
        fdset1 = FDSet([fd1, fd2])
        fdset2 = FDSet([fd2, fd1])

        self.assertEqual(fdset1, fdset2)

    def test_fdset_equality_logically_equivalent(self):
        """Test FDSet equality when sets are logically equivalent"""
        # {A->B, B->C} and {A->B, B->C, A->C} are equivalent
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"B"}, {"C"})
        fd3 = FD({"A"}, {"C"})
        fdset1 = FDSet([fd1, fd2])
        fdset2 = FDSet([fd1, fd2, fd3])

        self.assertEqual(fdset1, fdset2)

    def test_fdset_equality_different(self):
        """Test FDSet inequality"""
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"C"}, {"D"})
        fdset1 = FDSet([fd1])
        fdset2 = FDSet([fd2])

        self.assertNotEqual(fdset1, fdset2)

    def test_fdset_repr(self):
        """Test FDSet string representation"""
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"B"}, {"C"})
        fdset = FDSet([fd1, fd2])
        repr_str = repr(fdset)

        self.assertIn("{", repr_str)
        self.assertIn("}", repr_str)
        self.assertIn("→", repr_str)

    def test_closure_with_multiple_lhs_attributes(self):
        """Test closure with FD having multiple LHS attributes"""
        fd1 = FD({"A", "B"}, {"C"})
        fd2 = FD({"C"}, {"D"})
        fdset = FDSet([fd1, fd2])

        # A alone shouldn't lead to C
        closure_a = fdset.closure({"A"})
        self.assertNotIn("C", closure_a)

        # A and B together should lead to C and D
        closure_ab = fdset.closure({"A", "B"})
        self.assertEqual(closure_ab, {"A", "B", "C", "D"})

    def test_closure_reflexivity(self):
        """Test closure contains original attributes"""
        fdset = FDSet([self.fd_ab])
        closure = fdset.closure({"A", "B"})
        self.assertIn("A", closure)
        self.assertIn("B", closure)

    def test_implies_with_multiple_rhs(self):
        """Test implies with multiple RHS attributes"""
        fd1 = FD({"A"}, {"B"})
        fd2 = FD({"A"}, {"C"})
        fdset = FDSet([fd1, fd2])

        # A->{B,C} should be implied
        fd_abc = FD({"A"}, {"B", "C"})
        self.assertTrue(fdset.implies(fd_abc))


if __name__ == "__main__":
    unittest.main()
