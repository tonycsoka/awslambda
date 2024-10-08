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


class Condition:
    includes: list[list[str]] | None
    excludes: list[str] | None

    def __init__(
        self,
        includes: list[list[str]] | None = None,
        excludes: list[str] | None = None,
    ):
        self.includes = includes
        self.excludes = excludes

    def get_regex(self):
        """
        This essentially builds a regex of the form

        ¬exculded⋀include_1⋀include_2⋀..⋀include_n

        where excluded, include_i are ORed term sets

        Read as, exlude any text that has terms in exclude
        but incudes at least one term from each of include_i
        """
        exc_str = ""
        inc_str = ""
        if self.includes:
            inc_str = r"".join(
                [
                    r"(?=^.*\b(?:{terms})\b)".format(terms=r"|".join(term_set))
                    for term_set in self.includes
                ]
            )
        if self.excludes:
            exc_str = r"(?!^.*\b(?:{i})\b)".format(i=r"|".join(self.excludes))

        return r"".join([exc_str, inc_str])


class Indenter:
    fs: int

    def __init__(self) -> None:
        self.fs = 24

    def submit(self, mo):
        if mo.group(4):
            factor = (self.fs * 50) / 9
            r = "".join([r"\enspace"] * int(round(int(mo.group(4)), -2) / factor))
            return r
        if mo.group(2):
            fs = int(mo.group(2))
            if fs > 0:
                self.fs = fs

        return mo.group(0)


print("hello")
