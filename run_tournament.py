import json
import os
from pathlib import Path
import time

from utils.runners import run_tournament

# Settings to run a negotiation session:
#   You need to specify the classpath of 2 agents to start a negotiation. Parameters for the agent can be added as a dict (see example)
#   You need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   You need to specify a time deadline (is milliseconds (ms)) we are allowed to negotiate before we end without agreement.
our_agents = [
    {
        "class": "agents.group40.agent01.group40agent01.Group40Agent01"
    },
    {
        "class": "agents.group40.agent02.group40agent02.Group40Agent02"
    },
    {
        "class": "agents.group40.agent03.group40agent03.Group40Agent03"
    },
    {
        "class": "agents.group40.agent04.group40agent04.Group40Agent04"
    },
    {
        "class": "agents.group40.agent05.group40agent05.Group40Agent05"
    }
]


def agents_vs_baseline(agent_num: int):
    our_agent = {
        "class": f"agents.group40.agent0{agent_num}.group40agent0{agent_num}.Group40Agent0{agent_num}"
    }
    return [
        our_agent,
        {
            "class": "agents.boulware_agent.boulware_agent.BoulwareAgent",
        },
        {
            "class": "agents.conceder_agent.conceder_agent.ConcederAgent",
        },
        {
            "class": "agents.hardliner_agent.hardliner_agent.HardlinerAgent",
        },
        {
            "class": "agents.linear_agent.linear_agent.LinearAgent",
        },
        {
            "class": "agents.random_agent.random_agent.RandomAgent",
        },
        {
            "class": "agents.stupid_agent.stupid_agent.StupidAgent",
        },
    ]

def agents_vs_students(agent_num: int):
    our_agent = {
        "class": f"agents.group40.agent0{agent_num}.group40agent0{agent_num}.Group40Agent0{agent_num}"
    }
    return [
        our_agent,
        {
            "class": "agents.CSE3210.agent2.agent2.Agent2",
        },
        {
            "class": "agents.CSE3210.agent14.agent14.Agent14",
        },
        {
            "class": "agents.CSE3210.agent25.agent25.Agent25",
        },
        {
            "class": "agents.CSE3210.agent32.agent32.Agent32",
        },
        {
            "class": "agents.CSE3210.agent55.agent55.Agent55",
        },
        {
            "class": "agents.CSE3210.agent68.agent68.Agent68",
        },
    ]

def agents_vs_anl(agent_num: int):
    our_agent = {
        "class": f"agents.group40.agent0{agent_num}.group40agent0{agent_num}.Group40Agent0{agent_num}"
    }
    return [
        our_agent,
        {
            "class": "agents.ANL2022.agent007.agent007.Agent007",
        },
        {
            "class": "agents.ANL2022.dreamteam109_agent.dreamteam109_agent.DreamTeam109Agent",
        },
        {
            "class": "agents.ANL2022.rg_agent.rg_agent.RGAgent",
        },
        {
            "class": "agents.ANL2022.agentfish.agentfish.AgentFish",
        },
        {
            "class": "agents.ANL2022.gea_agent.gea_agent.GEAAgent",
        },
        {
            "class": "agents.ANL2022.thirdagent.third_agent.ThirdAgent",
        },
    ]


profile_sets_symmetric = [
    ["domains/domain07/profileA.json", "domains/domain07/profileB.json"],
    ["domains/domain01/profileA.json", "domains/domain01/profileB.json"],
]

profile_sets_asymmetric = [
    ["domains/domain19/profileA.json", "domains/domain19/profileB.json"],
    ["domains/domain42/profileA.json", "domains/domain42/profileB.json"],
]

tournament_our_symmetric = {
    "agents": our_agents,
    "profile_sets": profile_sets_symmetric,
    "deadline_time_ms": 10000,
}

tournament_our_asymmetric = {
    "agents": our_agents,
    "profile_sets": profile_sets_asymmetric,
    "deadline_time_ms": 10000,
}

tournaments_vs_baseline_symmetric = {
    i: {
        "agents": agents_vs_baseline(i),
        "profile_sets": profile_sets_symmetric,
        "deadline_time_ms": 10000,
    }
    for i in range(1, 6)
}

tournaments_vs_baseline_asymmetric = {
    i: {
        "agents": agents_vs_baseline(i),
        "profile_sets": profile_sets_asymmetric,
        "deadline_time_ms": 10000,
    }
    for i in range(1, 6)
}

tournaments_vs_students_symmetric = {
    i: {
        "agents": agents_vs_students(i),
        "profile_sets": profile_sets_symmetric,
        "deadline_time_ms": 10000,
    }
    for i in range(1, 6)
}

tournaments_vs_students_asymmetric = {
    i: {
        "agents": agents_vs_students(i),
        "profile_sets": profile_sets_asymmetric,
        "deadline_time_ms": 10000,
    }
    for i in range(1, 6)
}

tournaments_vs_anl_symmetric = {
    i: {
        "agents": agents_vs_anl(i),
        "profile_sets": profile_sets_symmetric,
        "deadline_time_ms": 10000,
    }
    for i in range(1, 6)
}

tournaments_vs_anl_asymmetric = {
    i: {
        "agents": agents_vs_anl(i),
        "profile_sets": profile_sets_asymmetric,
        "deadline_time_ms": 10000,
    }
    for i in range(1, 6)
}

tournament_settings = {
    "agents": [
    ],
    "profile_sets": [
        ["domains/domain00/profileA.json", "domains/domain00/profileB.json"],
        ["domains/domain01/profileA.json", "domains/domain01/profileB.json"],
    ],
    "deadline_time_ms": 10000,
}

# Base directory for results
RESULTS_BASE_DIR = Path("results", time.strftime('%Y%m%d-%H%M%S'))
RESULTS_BASE_DIR.mkdir(parents=True, exist_ok=True)

tournament_configs = {
    # "our_symmetric": tournament_our_symmetric,
    # "our_asymmetric": tournament_our_asymmetric,
    # "vs_baseline_symmetric": tournaments_vs_baseline_symmetric,
    # "vs_baseline_asymmetric": tournaments_vs_baseline_asymmetric,
    # "vs_students_symmetric": tournaments_vs_students_symmetric,
    # "vs_students_asymmetric": tournaments_vs_students_asymmetric,
    "vs_anl_symmetric": tournaments_vs_anl_symmetric,
    "vs_anl_asymmetric": tournaments_vs_anl_asymmetric,
}

def run_and_log_tournament(name, settings):
    """Runs a tournament and logs results in a structured directory."""
    # Create tournament-specific directory
    tournament_dir = RESULTS_BASE_DIR / name
    tournament_dir.mkdir(parents=True, exist_ok=True)

    # Run tournament
    tournament_steps, tournament_results, tournament_results_summary = run_tournament(settings)

    # Save tournament results
    with open(tournament_dir / "tournament_steps.json", "w", encoding="utf-8") as f:
        json.dump(tournament_steps, f, indent=2)

    with open(tournament_dir / "tournament_results.json", "w", encoding="utf-8") as f:
        json.dump(tournament_results, f, indent=2)

    tournament_results_summary.to_csv(tournament_dir / "tournament_results_summary.csv")

if __name__ == '__main__':
    # Iterate over all tournament settings and run them
    for tournament_name, settings in tournament_configs.items():
        if isinstance(settings, dict) and all(isinstance(k, int) for k in settings.keys()):
            # If it's a dictionary of numbered tournaments (vs_baseline, vs_students, vs_anl)
            for i, tournament_setting in settings.items():
                run_and_log_tournament(f"{tournament_name}_{i}", tournament_setting)
        else:
            run_and_log_tournament(tournament_name, settings)