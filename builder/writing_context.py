class WritingContext:
    def __init__(self, state):
        assert state is not None
        self.state = state
        self.strip_links = False

        # Function mapping paths to paths relative to the current page
        # Set by the page generator
        self.relpath = None

    def with_link_stripping(self):
        ctx = WritingContext(self.state)
        ctx.strip_links = True
        return ctx

    def getref(self, xml):
        return self.state.ctx.getref(xml)
