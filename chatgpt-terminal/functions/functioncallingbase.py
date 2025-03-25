class FunctionCallingBase:
    def __init__(self):
        self.function_definition = self._get_function_definition()

    def _get_function_definition(self):
        """
        Override this method to provide the function definition that will be used by the model.
        Must return a dictionary with the OpenAI function calling format.
        """
        raise NotImplementedError("Subclasses must implement _get_function_definition()")

    def execute(self, **kwargs):
        """
        Execute the function with the provided parameters.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement execute()")

    @property
    def requires_confirmation(self) -> bool:
        """
        Returns whether this function requires user confirmation before execution.
        By default, returns True for write operations (modifying state) and False for read operations.
        Override this in subclasses if needed.
        """
        return self.function_definition.get("operation_type", "write").lower() == "write"

    @property
    def name(self):
        """
        Returns the function name from the definition
        """
        return self.function_definition.get("name")

    @property
    def description(self):
        """
        Returns the function description from the definition
        """
        return self.function_definition.get("description")

    @property
    def parameters(self):
        """
        Returns the function parameters schema from the definition
        """
        return self.function_definition.get("parameters")
