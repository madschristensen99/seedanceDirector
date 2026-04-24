"""
Test with 20 scenes first to verify format
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM


def create_agent(role: str, description: str, temp: float = 0.7):
    llm = LiteLLM(
        model_name="openai/kyle-jr-v2",
        base_url="http://localhost:1234/v1",
        api_key="not-needed",
        temperature=temp,
        max_tokens=1200,
        stream=False,
    )
    return Agent(agent_name=role, agent_description=description, llm=llm, max_loops=1)


print("🎬 Testing 20-Scene Generator\n")

# Create agents
director = create_agent("Director", "You create scene breakdowns for films.", 0.8)
writer = create_agent("Writer", "You write video generation prompts with camera, lighting, action, audio.", 0.7)

concept = "A hacker delivery driver in cyberpunk LA fights a digital virus"

# Get structure
print("Director planning...\n")
structure = director.run(f"Create 20-scene outline for: {concept}. List: Scene 1: [name] | [description] | [duration]s")
print(structure + "\n")

# Generate scenes
print("="*80)
print("Generating scenes...\n")

scenes = []
for i in range(1, 21):
    print(f"Scene {i}...", end=" ")
    
    prompt = writer.run(f"""
    Scene {i} for: {concept}
    Context: {structure[:200]}
    
    Write video prompt: [Shot] of [subject]. Camera [movement]. [Lighting]. [Action]. Audio: [sound]. Cinematic style.
    Duration: 6s. ONLY the prompt.
    """)
    
    scenes.append({
        "scene_number": i,
        "scene_name": f"Scene {i}",
        "duration": 6,
        "original_prompt": prompt.strip()
    })
    print("✓")

# Save
with open("test_20_scenes.json", 'w') as f:
    json.dump(scenes, f, indent=2)

print(f"\n✅ Complete! Saved to test_20_scenes.json")
print(f"\nSample:\n{json.dumps(scenes[0], indent=2)}")
