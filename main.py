from typing import Protocol


class HasValueProtocol(Protocol):
    value: int


class HasAddProtocol(Protocol):
    def add(self, value: int) -> int: ...


class MultiplicationMixin:

    def multiply(self: HasValueProtocol, m: int) -> int:
        return self.value * m


class AdditionMixin:

    def add(self: HasValueProtocol, b: int) -> int:
        return self.value + b

    def add2(self: HasAddProtocol, b: int) -> int:
        return self.add(b) + b


class MyClass(MultiplicationMixin, AdditionMixin):

    def __init__(self, value: int) -> None:
        self.value = value
