"""A hard kill cannot log its own disconnect. The harness writes this line first."""


def induced_stop_line() -> str:
    return "zola_phone.disconnect induced=true reason=pc-shutdown who=pc"
