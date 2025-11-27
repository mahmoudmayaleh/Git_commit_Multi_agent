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


def calculate_difference(a: int, b: int) -> int:
    """
    Calculate the difference between two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Difference of a minus b
    """
    return a - b


def calculate_division(a: float, b: float) -> float:
    """
    Calculate the division of two numbers.
    
    Args:
        a: Dividend
        b: Divisor
        
    Returns:
        Result of a divided by b
        
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


class Calculator:
    """Simple calculator class with history tracking."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.history = []
        self.result = 0
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers and track in history."""
        result = a + b
        self.result = result
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: int, b: int) -> int:
        """Subtract two numbers and track in history."""
        result = a - b
        self.result = result
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers and track in history."""
        result = a * b
        self.result = result
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers and track in history."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.result = result
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history = []
        self.result = 0
    
    def get_last_result(self) -> float:
        """Get the last calculation result."""
        return self.result

