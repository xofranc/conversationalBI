# apps/queries/services/pipeline/base.py
from abc import ABC, abstractmethod


class Middleware(ABC):
    """Base class for query pipeline middleware."""
    
    @abstractmethod
    def process(self, context: dict) -> dict:
        """
        Process the query context.
        
        Args:
            context: Dictionary containing query data and results from previous middlewares
            
        Returns:
            Updated context dictionary
        """
        pass
    
    def __call__(self, context: dict) -> dict:
        """Make middleware callable for pipeline execution."""
        return self.process(context)
