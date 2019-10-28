class CurrentPersonDefault:
    """Return current logged-in person"""
    def set_context(self, serializer_field):
        user = serializer_field.context['request'].user
        if hasattr(user, 'person'):
            self.person = user.person
        else:
            self.person = None

    def __call__(self):
        return self.person

    def __repr__(self):
        return '%s()' % self.__class__.__name__
