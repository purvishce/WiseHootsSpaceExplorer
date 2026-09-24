import asyncio
import sys
from pathlib import Path

from agents import Runner, trace
from openai.types.responses import ResponseTextDeltaEvent
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from AIAgentSpace.newsroom_agent import create_nasa_space_newsroom_agent


load_dotenv(PROJECT_ROOT / ".env")


async def main():
    agent = create_nasa_space_newsroom_agent()

    with trace("NASA Space Newsroom"):
        result = Runner.run_streamed(
            agent,
            "Can you find two or three cool NASA space story ideas for kids?",
        )
        chunks = []
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
                chunks.append(event.data.delta)

        #final_text = "".join(chunks)
        #print()
        #print(send_pushover(final_text, "Study Buddy Summary"))
           
    
if __name__ == "__main__":
    asyncio.run(main())
    
