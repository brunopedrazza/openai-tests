from typing import Dict, Type, List
from functions.functioncallingbase import FunctionCallingBase
from functions.createorder import CreateOrder
from functions.getbalance import GetBalance
from functions.sendemail import SendEmail
from functions.createcalendarevent import CreateCalendarEvent
from functions.listcalendarevents import ListCalendarEvents

class FunctionRegistry:
    _instance = None
    _functions: Dict[str, Type[FunctionCallingBase]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FunctionRegistry, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Register all available functions here
        """
        self.register_function(CreateOrder)
        self.register_function(GetBalance)
        self.register_function(SendEmail)
        self.register_function(CreateCalendarEvent)
        self.register_function(ListCalendarEvents)
        
    def register_function(self, function_class: Type[FunctionCallingBase]):
        """
        Register a new function class
        """
        instance = function_class()
        self._functions[instance.name] = function_class

    def get_function(self, name: str) -> Type[FunctionCallingBase]:
        """
        Get a function class by name
        """
        return self._functions.get(name)

    def get_all_functions(self) -> List[dict]:
        """
        Get all function definitions for OpenAI
        """
        return [function_class().function_definition for function_class in self._functions.values()]

    def execute_function(self, name: str, **kwargs) -> dict:
        """
        Execute a function by name with the provided parameters
        """
        function_class = self.get_function(name)
        if not function_class:
            return {"success": False, "error": f"Function {name} not found"}
        
        instance = function_class()
        return instance.execute(**kwargs) 