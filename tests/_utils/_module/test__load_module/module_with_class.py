"""A test module with a class for testing _load_module."""


class Calculator:
    """A simple calculator class for testing."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            The sum of a and b.
        """
        return a + b

    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            The product of a and b.
        """
        return a * b
