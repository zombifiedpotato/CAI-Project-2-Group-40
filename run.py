import json
import time
from pathlib import Path

from utils.plot_trace import plot_trace
from utils.runners import run_session

RESULTS_DIR = Path("results", time.strftime('%Y%m%d-%H%M%S'))

# create results directory if it does not exist
if not RESULTS_DIR.exists():
    RESULTS_DIR.mkdir(parents=True)

# Settings to run a negotiation session:
#   You need to specify the classpath of 2 agents to start a negotiation. Parameters for the agent can be added as a dict (see example)
#   You need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   You need to specify a time deadline (is milliseconds (ms)) we are allowed to negotiate before we end without agreement
settings = {
    "agents": [
        {
            "class": "agents.group40.agent05.group40agent05.Group40Agent05",
            "parameters": {"storage_dir": "agent_storage/Group40/Agent05"},
        },
        # {
        #     "class": "agents.group40.agent04.group40agent04.Group40Agent04",
        #     "parameters": {"storage_dir": "agent_storage/Group40/Agent04"},
        # },
        # {
        #     "class": "agents.group40.agent05.group40agent05.Group40Agent05",
        #     "parameters": {"storage_dir": "agent_storage/Group40/Agent052"},
        # },
        # {
        #     "class": "agents.group40.agent01.group40agent01.Group40Agent01",
        #     "parameters": {"storage_dir": "agent_storage/Group40/Agent01"},
        # },
        # {
        #     "class": "agents.template_agent.template_agent.TemplateAgent",
        #     "parameters": {"storage_dir": "agent_storage/TemplateAgent"},
        # },
        # {
        #     "class": "agents.ANL2022.dreamteam109_agent.dreamteam109_agent.DreamTeam109Agent",
        #     "parameters": {"storage_dir": "agent_storage/DreamTeam109Agent"},
        # },
        # {
        #     "class": "agents.ANL2022.dreamteam109_agent.dreamteam109_agent.DreamTeam109Agent",
        #     "parameters": {"storage_dir": "agent_storage/DreamTeam109Agent"},
        # },
        {
            "class": "agents.ANL2022.super_agent.super_agent.SuperAgent",
            "parameters": {"storage_dir": "agent_storage/SuperAgent"},
        },
        # {
        #     "class": "agents.boulware_agent.boulware_agent.BoulwareAgent",
        #     "parameters": {"storage_dir": "agent_storage/BoulwareAgent"},
        # },
    ],
    "profiles": ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
    #"profiles": ["domains/domain01/profileA.json", "domains/domain01/profileB.json"],
    "deadline_time_ms": 10000,
}

# run a session and obtain results in dictionaries
session_results_trace, session_results_summary = run_session(settings)

# plot trace to html file
if not session_results_trace["error"]:
    plot_trace(session_results_trace, RESULTS_DIR.joinpath("trace_plot.html"))

# write results to file
with open(RESULTS_DIR.joinpath("session_results_trace.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(session_results_trace, indent=2))
with open(RESULTS_DIR.joinpath("session_results_summary.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(session_results_summary, indent=2))
