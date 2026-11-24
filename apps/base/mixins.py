class BaseMixin:

    serializer_classes_by_action = {}
    permission_classes_by_action = {}
    throttle_classes_by_action = {}

    def get_serializer_class(self):
        return self.serializer_classes_by_action.get(self.action)

    def get_permissions(self):
        permissions = self.permission_classes_by_action.get(
            self.action, self.permission_classes
        )
        return [permission() for permission in permissions]

    def get_throttles(self):
        throttles = self.throttle_classes_by_action.get(self.action)
        if throttles is None:
            return super().get_throttles()
        if not isinstance(throttles, (list, tuple)):
            throttles = (throttles,)
        return [throttle() for throttle in throttles]