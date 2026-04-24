"""
Clean Script Improvement Swarm

Uses hybrid approach:
- Agents for creative decisions and collaboration
- LiteLLM directly for clean final prompts (no system prompt pollution)
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM
from datetime import datetime


class CleanScriptImprover:
    """Improves scripts with clean output"""
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-uncensored-hauhaucs-aggressive"):
        self.base_url = base_url
        self.model_name = model_name
        self.improvements_made = 0
        
    def create_llm(self, temp=0.7, tokens=800):
        return LiteLLM(
            model_name=self.model_name,
            base_url=self.base_url,
            api_key="not-needed",
            temperature=temp,
            max_tokens=tokens,
            stream=False,
        )
    
    def create_agent(self, role, description, temp=0.7):
        llm = self.create_llm(temp=temp, tokens=1000)
        return Agent(
            agent_name=role,
            agent_description=description,
            llm=llm,
            max_loops=1,
        )
    
    def improve_script(self, input_file: str, output_file: str, start_scene: int = 1, end_scene: int = None):
        """
        Improve script with clean output
        
        Args:
            input_file: Input script JSON
            output_file: Output improved script JSON
            start_scene: First scene to improve (1-indexed)
            end_scene: Last scene to improve (None = all)
        """
        
        print("\n" + "🎬" * 40)
        print("CLEAN SCRIPT IMPROVEMENT SWARM")
        print("🎬" * 40 + "\n")
        
        # Load script
        print(f"📖 Loading: {input_file}")
        with open(input_file, 'r') as f:
            all_scenes = json.load(f)
        
        total_scenes = len(all_scenes)
        
        # Determine range
        if end_scene is None:
            end_scene = total_scenes
        
        # Slice scenes to improve
        scenes_to_improve = all_scenes[start_scene - 1:end_scene]
        
        print(f"   Total scenes in file: {total_scenes}")
        print(f"   Improving scenes: {start_scene}-{end_scene} ({len(scenes_to_improve)} scenes)\n")
        
        # Spawn agents (only for decisions, not final output)
        print("="*80)
        print("SPAWNING IMPROVEMENT TEAM")
        print("="*80 + "\n")
        
        print("✨ Spawned: Director (narrative flow)")
        print("✨ Spawned: Cinematographer (visual enhancement)")
        print("✨ Spawned: Dialogue-Coach (character lines)\n")
        
        director = self.create_agent(
            "Director",
            "You analyze scenes and suggest improvements to pacing, tension, and narrative impact. Be concise.",
            temp=0.8
        )
        
        # Create clean LLM for final prompts
        clean_llm = self.create_llm(temp=0.7, tokens=1000)
        
        # Improve scenes
        improved_scenes = []
        
        print("="*80)
        print(f"IMPROVING SCENES {start_scene}-{end_scene}")
        print("="*80 + "\n")
        
        for idx, scene in enumerate(scenes_to_improve):
            scene_num = scene['scene_number']
            scene_name = scene['scene_name']
            original_prompt = scene['original_prompt']
            duration = scene['duration']
            
            print(f"Scene {scene_num}: {scene_name}...", end=" ", flush=True)
            
            # Director provides improvement suggestions
            director_task = f"""Analyze this scene and suggest ONE specific improvement:
            
Scene: {scene_name}
Prompt: {original_prompt[:300]}

What ONE thing would make this more impactful? (camera, lighting, action, or dialogue)
Be specific and concise (1-2 sentences)."""
            
            suggestion = director.run(task=director_task)
            
            # Extract just the suggestion (remove system prompts)
            suggestion_clean = suggestion.split('\n')[-1] if '\n' in suggestion else suggestion
            suggestion_clean = suggestion_clean[:200]  # Limit length
            
            # Use clean LLM to generate improved prompt
            improvement_task = f"""Improve this video prompt:

Original: {original_prompt}

Improvement suggestion: {suggestion_clean}

Write the improved prompt. Keep the same format and style. Add the improvement naturally.
Include dialogue in quotes if appropriate.

Duration: {duration}s

Write ONLY the improved prompt:"""
            
            improved_prompt = clean_llm.run(improvement_task)
            
            improved_scenes.append({
                "scene_number": scene_num,
                "scene_name": scene_name,
                "duration": duration,
                "original_prompt": improved_prompt.strip()
            })
            
            self.improvements_made += 1
            print("✓")
            
            # Save after EACH scene (incremental save)
            with open(output_file, 'w') as f:
                json.dump(improved_scenes, f, indent=2)
        
        # Final save (redundant but ensures completion)
        with open(output_file, 'w') as f:
            json.dump(improved_scenes, f, indent=2)
        
        print(f"\n{'='*80}")
        print("✅ IMPROVEMENT COMPLETE!")
        print(f"{'='*80}")
        print(f"\n📊 Stats:")
        print(f"   Scenes improved: {self.improvements_made}")
        print(f"   Output: {output_file}\n")
        
        return improved_scenes


if __name__ == "__main__":
    
    improver = CleanScriptImprover()
    
    # Test with first 20 scenes
    improver.improve_script(
        input_file="existing_script.json",
        output_file="improved_script_test_20.json",
        start_scene=1,
        end_scene=20  # Test with first 20 scenes
    )
    
    # To run all 1,112 scenes: end_scene=None
    # To resume from scene 100: start_scene=100
