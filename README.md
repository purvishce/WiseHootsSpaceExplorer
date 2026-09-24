# WiseHoots Space Explorer

WiseHoots Space Explorer is a Python project that uses NASA/JPL data and the OpenAI Agents SDK to create a kid-friendly space newsroom.

The main agent, **NASA Space Newsroom**, coordinates specialist agents that can discover NASA story ideas, verify the science, rewrite the information for a 9-year-old reader, and optionally create a quiz.

## Project Structure

```text
WiseHootsSpaceExplorer
|-- AIAgentSpace/
|   |-- agent.py
|   |-- newsroom_agent.py
|   |-- discovery_scout_agent.py
|   |-- science_fact_checker_agent.py
|   |-- young_explorer_writer_agent.py
|   |-- space_quiz_agent.py
|   |-- agenttools.py
|   |-- imageexplorer_agenttools.py
|   `-- asteroidexplorer_agenttools.py
|-- APIs/
|   |-- nasa_apis.py
|   |-- jpl_apis.py
|   `-- README.md
|-- .gitignore
`-- README.md
```

## Agent Workflow

```text
NASA Space Newsroom
|-- Discovery Scout
|-- Science Fact-Checker
|-- Young Explorer Writer
`-- Space Quiz Agent optional
```

Default story workflow:

```text
Discovery Scout -> Science Fact-Checker -> Young Explorer Writer
```

The Space Quiz Agent is optional. It should run only when the user asks for a quiz, classroom activity, questions, or comprehension check.

## Agents

### Discovery Scout

Finds two or three possible story ideas from:

- NASA APOD
- NASA Image and Video Library
- NASA NeoWs near-Earth asteroid data

### Science Fact-Checker

Checks selected discoveries for:

- Title and date
- NASA/JPL source
- Measurements
- Supported and unsupported claims
- Exaggerated asteroid language
- Confidence level

### Young Explorer Writer

Turns verified information into:

- A 100-word story
- Language suitable for a 9-year-old
- Simple scale comparisons
- One "Wow!" fact
- One follow-up question

### Space Quiz Agent

Creates:

- Two multiple-choice questions
- One imaginative question
- Answers and short explanations

## APIs

NASA API wrappers live in:

```text
APIs/nasa_apis.py
```

JPL API wrappers live in:

```text
APIs/jpl_apis.py
```

Tool wrappers for agents live in:

```text
AIAgentSpace/agenttools.py
AIAgentSpace/imageexplorer_agenttools.py
AIAgentSpace/asteroidexplorer_agenttools.py
```

## Setup

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_key
NASA_API_KEY=your_nasa_key
PUSHOVER_USER=optional_pushover_user
PUSHOVER_TOKEN=optional_pushover_token
```

`NASA_API_KEY` falls back to `DEMO_KEY`, but a real NASA key is recommended because `DEMO_KEY` is rate-limited.

## Run

From the project root:

```bash
python AIAgentSpace/agent.py
```

The current sample prompt is inside `AIAgentSpace/agent.py`:

```text
Can you find two or three cool NASA space story ideas for kids?
```

For the full newsroom flow, use a prompt like:

```text
Find a NASA space story idea, fact-check it, write it for a 9-year-old, and make a short quiz.
```

## Orchestration Pattern

The project currently uses **agent-as-tool orchestration**.

The editor agent stays in control and calls specialist agents as tools:

```text
Newsroom Editor -> Discovery Scout
Newsroom Editor -> Science Fact-Checker
Newsroom Editor -> Young Explorer Writer
Newsroom Editor -> Space Quiz Agent optional
```

This is different from hard-coded code orchestration, where Python would force each step in sequence.

## Notes

- `.env`, `.venv/`, Python caches, editor folders, and logs are ignored by `.gitignore`.
- `APIs/` is now tracked as part of this main repository.
- This project is designed for learning multi-agent patterns with real NASA/JPL data.
