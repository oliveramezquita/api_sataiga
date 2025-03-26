def resolve_permissions(unresolved_permissions):
    step_1 = {k: v for k, v in unresolved_permissions.items() if v}
    step_2 = {k: [key for key, value in v.items(
    ) if value] for k, v in step_1.items()}
    return {k: v for k, v in step_2.items() if v}
