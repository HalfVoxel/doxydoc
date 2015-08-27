class WritingContext:
    def __init__(self, state):
        assert state is not None
        self.state = state
        self.strip_links = False

    def with_link_stripping(self):
        ctx = WritingContext(self.state)
        ctx.strip_links = True
        return ctx
