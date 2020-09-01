from unittest.case import TestCase

from lisa import schema
from lisa.requirement import (
    IntRange,
    ListSpace,
    Node,
    SetSpace,
    _is_supported_intspace,
    _is_supported_space,
    simple,
)


class SecretTestCase(TestCase):
    def test_supported_intrange(self) -> None:
        tested_range = IntRange(min=10, max=15)
        self.assertTrue(tested_range.is_supported(10))
        self.assertTrue(tested_range.is_supported(15))
        self.assertFalse(tested_range.is_supported(20))

        tested_range = IntRange(min=10, max=15, max_inclusive=False)
        self.assertFalse(tested_range.is_supported(15))

    def test_supported_1_spec_by_1_space(self) -> None:
        min_1_space = ListSpace[Node](
            count_space=IntRange(min=1), items=[Node(core_count=IntRange(min=4, max=8))]
        )
        max_1_space = ListSpace[Node](
            count_space=IntRange(max=1), items=[Node(core_count=IntRange(min=4, max=8))]
        )
        exact_1_space = ListSpace[Node](
            count_space=1, items=[Node(core_count=IntRange(min=4, max=8))]
        )
        exact_any_1_space = ListSpace[Node](count_space=1)

        one_in_spec = [schema.NodeSpec(core_count=6)]
        # more than required condition also supported
        one_more_spec = [schema.NodeSpec(core_count=6, gpu_count=2)]
        one_out_spec = [schema.NodeSpec(core_count=10)]

        self.assertTrue(min_1_space.is_supported(one_in_spec))
        self.assertTrue(min_1_space.is_supported(one_more_spec))
        self.assertFalse(min_1_space.is_supported(one_out_spec))

        self.assertTrue(max_1_space.is_supported(one_in_spec))
        self.assertTrue(max_1_space.is_supported(one_more_spec))
        self.assertFalse(max_1_space.is_supported(one_out_spec))

        self.assertTrue(exact_1_space.is_supported(one_in_spec))
        self.assertTrue(exact_1_space.is_supported(one_more_spec))
        self.assertFalse(exact_1_space.is_supported(one_out_spec))

        self.assertTrue(exact_any_1_space.is_supported(one_in_spec))
        self.assertTrue(exact_any_1_space.is_supported(one_more_spec))
        self.assertTrue(exact_any_1_space.is_supported(one_out_spec))

    def test_supported_2_spec_by_1_space(self) -> None:
        min_1_space = ListSpace[Node](
            count_space=IntRange(min=1), items=[Node(core_count=IntRange(min=4, max=8))]
        )
        max_1_space = ListSpace[Node](
            count_space=IntRange(max=1), items=[Node(core_count=IntRange(min=4, max=8))]
        )
        exact_1_space = ListSpace[Node](
            count_space=1, items=[Node(core_count=IntRange(min=4, max=8))]
        )
        exact_any_1_space = ListSpace[Node](count_space=1)
        two_in_specs = [schema.NodeSpec(core_count=6), schema.NodeSpec(core_count=6)]
        two_out_specs = [schema.NodeSpec(core_count=6), schema.NodeSpec(core_count=10)]

        # specified min one spec
        self.assertTrue(min_1_space.is_supported(two_in_specs))
        self.assertFalse(min_1_space.is_supported(two_out_specs))

        # specified max one spec
        self.assertFalse(max_1_space.is_supported(two_in_specs))
        self.assertFalse(max_1_space.is_supported(two_out_specs))

        # specified one and only one spec
        self.assertFalse(exact_1_space.is_supported(two_in_specs))
        self.assertFalse(exact_1_space.is_supported(two_out_specs))

        # specified one and only one any spec
        self.assertFalse(exact_any_1_space.is_supported(two_in_specs))
        self.assertFalse(exact_any_1_space.is_supported(two_out_specs))

    def test_supported_set_space(self) -> None:
        default_set = set(["aa", "bb"])
        empty_allowed_space = SetSpace[str]()
        empty_denied_space = SetSpace[str]()
        allowed_space = SetSpace[str](set_=default_set, is_allow_set=True)
        denied_space = SetSpace[str](set_=default_set)

        included_single = "aa"
        excluded_single = "cc"
        included_set = ["aa"]
        excluded_set = ["cc"]
        intersection_set = ["aa", "cc"]

        # empty support all
        self.assertTrue(empty_allowed_space.is_supported(included_single))
        self.assertTrue(empty_allowed_space.is_supported(excluded_single))
        self.assertTrue(empty_allowed_space.is_supported(included_set))
        self.assertTrue(empty_allowed_space.is_supported(excluded_set))
        self.assertTrue(empty_allowed_space.is_supported(intersection_set))
        self.assertTrue(empty_denied_space.is_supported(included_single))
        self.assertTrue(empty_denied_space.is_supported(excluded_single))
        self.assertTrue(empty_denied_space.is_supported(included_set))
        self.assertTrue(empty_denied_space.is_supported(excluded_set))
        self.assertTrue(empty_denied_space.is_supported(intersection_set))

        self.assertTrue(allowed_space.is_supported(included_single))
        self.assertFalse(allowed_space.is_supported(excluded_single))
        self.assertTrue(allowed_space.is_supported(included_set))
        self.assertFalse(allowed_space.is_supported(excluded_set))
        self.assertFalse(allowed_space.is_supported(intersection_set))

        self.assertFalse(denied_space.is_supported(included_single))
        self.assertTrue(denied_space.is_supported(excluded_single))
        self.assertFalse(denied_space.is_supported(included_set))
        self.assertTrue(denied_space.is_supported(excluded_set))
        self.assertFalse(denied_space.is_supported(intersection_set))

    def test_supported_intspace(self) -> None:
        single_value = 10
        single_range = IntRange(min=10, max=15)
        multiple_range = [IntRange(min=10, max=15), IntRange(min=20, max=80)]

        self.assertTrue(_is_supported_intspace(None, 10))

        self.assertTrue(_is_supported_intspace(single_value, 10))
        self.assertFalse(_is_supported_intspace(single_value, 15))

        self.assertTrue(_is_supported_intspace(single_range, 10))
        self.assertFalse(_is_supported_intspace(single_range, 9))

        self.assertTrue(_is_supported_intspace(multiple_range, 10))
        self.assertTrue(_is_supported_intspace(multiple_range, 25))
        self.assertFalse(_is_supported_intspace(multiple_range, 18))

    def test_supported_space(self) -> None:
        default_set = set(["aa", "bb"])
        empty_allowed_space = SetSpace[str]()
        empty_denied_space = SetSpace[str]()
        allowed_space = SetSpace[str](set_=default_set, is_allow_set=True)
        denied_space = SetSpace[str](set_=default_set)

        included_single = "aa"

        # empty support all
        self.assertTrue(_is_supported_space(None, included_single))
        self.assertTrue(_is_supported_space(empty_allowed_space, included_single))
        self.assertTrue(_is_supported_space(empty_denied_space, included_single))
        self.assertTrue(_is_supported_space(allowed_space, included_single))
        self.assertFalse(_is_supported_space(denied_space, included_single))

    def test_supported_simple_requirement(self) -> None:
        one_any_space = simple()
        one_space = simple(node=Node(core_count=IntRange(4, 8)))
        two_space = simple(min_node_count=2, node=Node(core_count=IntRange(4, 8)))

        one_in_spec = [schema.NodeSpec(core_count=6)]
        # more than required condition also supported
        one_more_spec = [schema.NodeSpec(core_count=6, gpu_count=2)]
        one_out_spec = [schema.NodeSpec(core_count=10)]
        two_in_specs = [schema.NodeSpec(core_count=6), schema.NodeSpec(core_count=6)]
        two_out_specs = [schema.NodeSpec(core_count=6), schema.NodeSpec(core_count=10)]

        self.assertTrue(_is_supported_space(one_any_space.environment, one_in_spec))
        self.assertTrue(_is_supported_space(one_any_space.environment, one_more_spec))
        self.assertTrue(_is_supported_space(one_any_space.environment, one_out_spec))
        self.assertTrue(_is_supported_space(one_any_space.environment, two_in_specs))
        self.assertTrue(_is_supported_space(one_any_space.environment, two_out_specs))

        self.assertTrue(_is_supported_space(one_space.environment, one_in_spec))
        self.assertTrue(_is_supported_space(one_space.environment, one_more_spec))
        self.assertFalse(_is_supported_space(one_space.environment, one_out_spec))
        self.assertTrue(_is_supported_space(one_space.environment, two_in_specs))
        self.assertFalse(_is_supported_space(one_space.environment, two_out_specs))

        self.assertFalse(_is_supported_space(two_space.environment, one_in_spec))
        self.assertFalse(_is_supported_space(two_space.environment, one_more_spec))
        self.assertFalse(_is_supported_space(two_space.environment, one_out_spec))
        self.assertTrue(_is_supported_space(two_space.environment, two_in_specs))
        self.assertFalse(_is_supported_space(two_space.environment, two_out_specs))
