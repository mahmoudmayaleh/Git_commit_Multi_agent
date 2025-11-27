"""Example module for testing the Git Commit AI agents."""


def calculate_sum(a: int, b: int) -> int:
    """
    Calculate the sum of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


def calculate_product(a: int, b: int) -> int:
    """
    Calculate the product of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Product of a and b
    """
    return a * b


class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.history = []
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
