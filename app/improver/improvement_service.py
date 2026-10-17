from app.improver.improvement_agent import (
    ImprovementAgent,
)


class ImprovementService:

    def __init__(self):

        self.agent = ImprovementAgent()

    def improve(self, resume):

        return self.agent.improve(
            resume
        )