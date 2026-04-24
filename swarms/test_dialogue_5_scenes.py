"""
Quick test: 5 scenes with dialogue
"""

import sys
sys.path.insert(0, '/home/remsee/swarms/examples')

from hybrid_swarm_clean_output import CleanSwarmDirector
import json

director = CleanSwarmDirector()

concept = """A hacker delivery driver discovers a digital virus and must stop it 
before it destroys the city"""

# Test with 5 scenes
scenes = director.produce_movie(
    concept=concept,
    total_scenes=5,
    include_dialogue=True
)

# Save
director.save("test_dialogue_5_scenes.json")

# Show all scenes
print("\n" + "="*80)
print("ALL SCENES WITH DIALOGUE:")
print("="*80 + "\n")

for scene in scenes:
    print(f"Scene {scene['scene_number']}: {scene['scene_name']}")
    print(f"Prompt: {scene['original_prompt'][:200]}...")
    print()
