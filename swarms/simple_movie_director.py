"""
Simplified Multi-Agent Movie Director

Quick demo of hierarchical agent system for movie script generation.
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM


def create_agent(name: str, description: str, temperature: float = 0.7):
    """Helper to create agents"""
    llm = LiteLLM(
        model_name="openai/kyle-jr-v2",
        base_url="http://localhost:1234/v1",
        api_key="not-needed",
        temperature=temperature,
        max_tokens=800,
        stream=False,
    )
    
    return Agent(
        agent_name=name,
        agent_description=description,
        llm=llm,
        max_loops=1,
    )


# Create specialized agents
print("🎬 Creating Agent Team...\n")

director = create_agent(
    "Director",
    "You are a movie director. You create high-level creative vision and scene breakdowns.",
    temperature=0.8
)

scene_writer = create_agent(
    "Scene-Writer", 
    "You write detailed visual prompts for AI video generation. Be specific about visuals, camera, lighting, and action.",
    temperature=0.7
)

# Movie concept
concept = "A robot learns to paint and discovers emotions through art"
num_scenes = 3

print(f"📝 Concept: {concept}")
print(f"🎞️  Scenes: {num_scenes}\n")
print("=" * 80)

# Step 1: Director creates plan
print("\n🎬 DIRECTOR: Creating scene breakdown...\n")
director_task = f"""
Create a {num_scenes}-scene movie outline for: "{concept}"

Provide:
1. Movie title
2. Scene 1 description (one sentence)
3. Scene 2 description (one sentence)  
4. Scene 3 description (one sentence)

Be brief and clear.
"""

plan = director.run(task=director_task)
print(plan)

# Step 2: Scene writer creates video prompts
print("\n" + "=" * 80)
print("\n🎥 SCENE WRITER: Creating video generation prompts...\n")

scenes = []
for i in range(1, num_scenes + 1):
    print(f"Writing Scene {i}...")
    
    scene_task = f"""
    Based on this movie plan:
    {plan}
    
    Write a detailed video generation prompt for Scene {i}.
    
    Include:
    - Camera angle and movement
    - Lighting and colors
    - Character actions
    - Atmosphere
    - Duration: 15 seconds
    
    Write ONLY the video prompt. Be visual and specific.
    """
    
    video_prompt = scene_writer.run(task=scene_task)
    
    scenes.append({
        "scene_number": i,
        "duration_seconds": 15,
        "video_prompt": video_prompt.strip()
    })
    
    print(f"✅ Scene {i} complete\n")

# Assemble final JSON
movie_script = {
    "title": "Robot Artist",  # Could extract from director's plan
    "genre": "Sci-Fi Drama",
    "total_duration_seconds": sum(s["duration_seconds"] for s in scenes),
    "concept": concept,
    "scenes": scenes
}

# Save and display
output_file = "robot_artist_script.json"
with open(output_file, 'w') as f:
    json.dump(movie_script, f, indent=2)

print("=" * 80)
print("\n📄 FINAL MOVIE SCRIPT:\n")
print(json.dumps(movie_script, indent=2))

print(f"\n\n💾 Saved to: {output_file}")
print("✅ Ready for video generation!")
