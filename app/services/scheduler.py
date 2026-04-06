from app.models.agent import Agent
from app.models.job import Job


def match_job_to_agent(job: Job, agents: list[Agent]) -> Agent | None:
    """
    Match a job to the first available agent that has all required capabilities.
    """
    for agent in agents:
        if agent.status != "online":
            continue

        if all(req in agent.capabilities for req in job.requirements):
            return agent

    return None
