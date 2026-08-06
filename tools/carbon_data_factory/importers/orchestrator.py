"""ImportOrchestrator."""

class ImportOrchestrator:
    """Coordinates the import pipeline."""

    def __init__(self, stages=None):
        self.stages = list(stages or [])

    def run(self, context):
        """Run each stage in order."""
        for stage in self.stages:
            context = stage.run(context)
        return context
