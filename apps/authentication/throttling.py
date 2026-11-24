from rest_framework.throttling import AnonRateThrottle


class AuthAPIRateThrottle(AnonRateThrottle):
    scope = "auth"
    rate = "10/min"