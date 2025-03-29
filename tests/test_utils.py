def assert_contains_bet(bets, bet_type, owner):
    """
    Assert that a bet of the given type exists for the specified owner.

    Args:
        bets (List[Bet]): List of Bet objects to search.
        bet_type (str): The type of bet to look for (e.g., "Come", "Pass Line").
        owner (Player): The player object.

    Raises:
        AssertionError: If no matching bet is found.
    """
    for b in bets:
        if b.bet_type == bet_type and b.owner == owner:
            return
    raise AssertionError(f"Expected bet type '{bet_type}' for owner '{getattr(owner, 'name', owner)}' not found.")
