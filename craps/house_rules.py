class HouseRules:
    """Class representing house rules for payouts and table limits."""
    def __init__(self, config):
        """
        Initialize the HouseRules with configuration from config.py.

        :param config: A dictionary containing house rules configuration.
        """
        self.table_minimum = config.get("table_minimum", 10)  # Default to $10
        self.table_maximum = config.get("table_maximum", 5000)  # Default to $5000

    def set_table_limits(self, minimum, maximum):
        """Set the table limits."""
        self.table_minimum = minimum
        self.table_maximum = maximum