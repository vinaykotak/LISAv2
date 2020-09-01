from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, List, Optional, Set, Type, TypeVar, Union

from lisa import schema
from lisa.platform_ import Platform as PlatformType
from lisa.util import LisaException


class RequirementMixin:
    @abstractmethod
    def is_supported(self, value: Any) -> bool:
        raise NotImplementedError()


_MAX = 2147483647

T_SPACE = TypeVar("T_SPACE", bound=RequirementMixin)
T = TypeVar("T")


@dataclass
class IntRange(RequirementMixin):
    min: int = 0
    max: int = field(default=_MAX)
    max_inclusive: bool = True

    def __post_init__(self, *args: Any, **kwargs: Any) -> None:
        if self.min > self.max:
            raise LisaException(
                f"min: {self.min} shouldn't be greater than max: {self.max}"
            )
        elif self.min == self.max and self.max_inclusive is False:
            raise LisaException(
                "min shouldn't be equal to max, if max_includes is False."
            )

    def is_supported(self, value: int) -> bool:
        supported: bool = True
        if value < self.min:
            supported = False
        elif value > self.max:
            supported = False
        elif value == self.max and not self.max_inclusive:
            supported = False
        return supported


IntSpace = Union[int, List[IntRange], IntRange, None]
BoolSpace = Union[bool, None]


@dataclass
class ListSpace(Generic[T_SPACE], RequirementMixin):
    count_space: IntSpace = IntRange(min=0)
    items: Optional[List[T_SPACE]] = None

    def is_supported(self, value: List[T]) -> bool:
        supported: bool = True
        supported = _is_supported_intspace(self.count_space, len(value))
        if supported and self.items is not None:
            if len(self.items) == 1:
                item = self.items[0]
                supported = all(item.is_supported(x) for x in value)
            else:
                supported = len(value) == len(self.items)
                if supported:
                    supported = all(
                        self.items[index].is_supported(value[index])
                        for index in range(len(value))
                    )

        return supported


@dataclass
class SetSpace(Generic[T], RequirementMixin):
    set_: Optional[Set[T]] = None
    is_allow_set: bool = False

    def is_supported(self, value: Union[T, List[T]]) -> bool:
        supported: bool = True
        if self.set_ is not None:
            if isinstance(value, list):
                if self.is_allow_set:
                    if self.set_.issuperset(value):
                        supported = True
                    else:
                        supported = False
                else:
                    if len(self.set_.intersection(value)) > 0:
                        supported = False
                    else:
                        supported = True
            else:
                supported = (value in self.set_) == self.is_allow_set
        return supported


def _is_supported_intspace(space: IntSpace, value: int) -> bool:
    supported = True
    if space is not None:
        if isinstance(space, int):
            supported = space == value
        elif isinstance(space, IntRange):
            supported = space.is_supported(value)
        else:
            assert isinstance(space, list)
            supported = False
            for space_item in space:
                supported = space_item.is_supported(value)
                if supported:
                    break
    return supported


def _is_supported_space(space: Optional[T_SPACE], value: T) -> bool:
    supported = True
    if space is not None:
        supported = space.is_supported(value)
    return supported


@dataclass
class Node(RequirementMixin):
    core_count: IntSpace = IntRange(min=1)
    memory_mb: IntSpace = IntRange(min=512)
    nic_count: IntSpace = IntRange(min=1)
    gpu_count: IntSpace = None
    features: Optional[SetSpace[schema.Feature]] = None

    @classmethod
    def default_factory(cls: Type[T_SPACE]) -> ListSpace[T_SPACE]:
        result = ListSpace(items=[cls()])
        result.count_space = IntRange(min=1)
        return result

    def is_supported(self, value: schema.NodeSpec) -> bool:
        assert isinstance(
            value, schema.NodeSpec
        ), f"expect type: {schema.NodeSpec}, actual {type(value)}"
        supported: bool = True
        supported = (
            _is_supported_intspace(self.core_count, value.core_count)
            and _is_supported_intspace(self.memory_mb, value.memory_mb)
            and _is_supported_intspace(self.nic_count, value.nic_count)
            and _is_supported_intspace(self.gpu_count, value.gpu_count)
            and _is_supported_space(self.features, value.features)
        )

        return supported


@dataclass
class Environment(RequirementMixin):
    nodes: Optional[ListSpace[Node]] = field(default_factory=Node.default_factory)

    def is_supported(self, value: List[schema.NodeSpec]) -> bool:
        return _is_supported_space(self.nodes, value)


@dataclass
class TestCase:
    environment: Optional[Environment] = None
    platform_type: Optional[SetSpace[PlatformType]] = None


def simple(
    min_node_count: int = 1,
    node: Optional[Node] = None,
    platform_type: Optional[SetSpace[PlatformType]] = None,
) -> TestCase:
    """
    define a simple requirement to support most test cases.
    """
    if node:
        nodes: Optional[List[Node]] = [node]
    else:
        nodes = None
    return TestCase(
        environment=Environment(
            nodes=ListSpace[Node](count_space=IntRange(min=min_node_count), items=nodes)
        ),
        platform_type=platform_type,
    )
