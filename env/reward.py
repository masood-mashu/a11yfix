def compute_reward(prev_violations, curr_violations, action_type, valid_action=True):
    """
    Compute reward based on change in violations and action type.
    
    Args:
        prev_violations (int): number of violations before action
        curr_violations (int): number of violations after action
        action_type (str): type of action performed
        valid_action (bool): whether action was valid
    
    Returns:
        float: reward
    """

    # ---------- INVALID ACTION ----------
    if not valid_action:
        return -0.1

    # ---------- AUDIT ----------
    if action_type == "audit":
        return -0.05

    # ---------- DONE ----------
    if action_type == "done":
        if curr_violations == 0:
            return 1.0
        else:
            return -0.2

    # ---------- SET ATTRIBUTE ----------
    if curr_violations < prev_violations:
        return 0.2   # correct fix
    elif curr_violations == prev_violations:
        return -0.05  # no-op
    else:
        return -0.5   # regression

    return 0