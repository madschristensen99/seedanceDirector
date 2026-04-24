"""
Advanced Movie Director - 200 Scene Generator

Generates movie scripts in the exact format needed for video generation:
- scene_number
- scene_name
- duration (seconds)
- original_prompt (detailed video generation prompt)

Hierarchical multi-agent system where Director spawns specialized agents.
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM
from typing import List, Dict
from datetime import datetime


class AgentFactory:
    """Factory for spawning specialized agents"""
    
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url
        self.model_name = model_name
        self.agents_created = []
        
    def spawn_agent(self, role: str, description: str, temperature: float = 0.7, max_tokens: int = 1200):
        """Spawn a new specialized agent"""
        llm = LiteLLM(
            model_name=self.model_name,
            base_url=self.base_url,
            api_key="not-needed",
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        
        agent = Agent(
            agent_name=role,
            agent_description=description,
            llm=llm,
            max_loops=1,
        )
        
        self.agents_created.append({
            "role": role,
            "created_at": datetime.now().isoformat()
        })
        
        print(f"✨ Spawned: {role}")
        return agent


class MovieDirector:
    """Director that orchestrates 200-scene movie production"""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", model_name: str = "openai/kyle-jr-v2"):
        self.factory = AgentFactory(base_url, model_name)
        self.scenes = []
        
    def produce_movie(self, concept: str, total_scenes: int = 200, batch_size: int = 10):
        """
        Produce a movie with specified number of scenes
        
        Args:
            concept: Movie concept/premise
            total_scenes: Total number of scenes to generate (default 200)
            batch_size: How many scenes to generate per batch (default 10)
        """
        
        print("\n" + "🎬" * 40)
        print(f"MOVIE PRODUCTION: {total_scenes} SCENES")
        print("🎬" * 40)
        print(f"\n📋 Concept: {concept}\n")
        
        # Step 1: Director creates overall structure
        print("="*80)
        print("STEP 1: Director creates story structure")
        print("="*80 + "\n")
        
        director = self.factory.spawn_agent(
            role="Executive-Director",
            description="""You are an executive film director. You create high-level story 
            structures, break films into acts and sequences, and plan narrative arcs. 
            You think in terms of three-act structure, pacing, and dramatic beats.""",
            temperature=0.8,
            max_tokens=1500
        )
        
        structure_task = f"""
        Create a {total_scenes}-scene movie structure for: "{concept}"
        
        Break it into acts and sequences. Provide:
        1. Three-act breakdown (how many scenes per act)
        2. Major story beats and turning points
        3. Opening sequence (first 20 scenes)
        4. Midpoint (around scene {total_scenes//2})
        5. Climax sequence (last 20 scenes)
        6. Overall tone and visual style
        
        Be concise but specific about the narrative flow.
        """
        
        story_structure = director.run(task=structure_task)
        print(f"\n{story_structure}\n")
        
        # Step 2: Spawn specialized agents
        print("="*80)
        print("STEP 2: Spawning specialized agents")
        print("="*80 + "\n")
        
        # Scene Writer - writes individual scene prompts
        scene_writer = self.factory.spawn_agent(
            role="Scene-Prompt-Writer",
            description="""You write detailed video generation prompts for individual scenes.
            Each prompt must include:
            - Camera angles and movement
            - Lighting and color palette
            - Character actions and positions
            - Audio description
            - Visual style reference
            - Duration
            You write in the style: 'Wide shot of... Camera tracks... Audio:...'""",
            temperature=0.7,
            max_tokens=1500
        )
        
        # Sequence Planner - plans batches of scenes
        sequence_planner = self.factory.spawn_agent(
            role="Sequence-Planner",
            description="""You plan sequences of 10-20 scenes. You ensure smooth flow,
            proper pacing, and logical progression. You create scene-by-scene breakdowns
            with scene names and brief descriptions.""",
            temperature=0.75,
            max_tokens=2000
        )
        
        # Step 3: Generate scenes in batches
        print("\n" + "="*80)
        print(f"STEP 3: Generating {total_scenes} scenes in batches of {batch_size}")
        print("="*80 + "\n")
        
        num_batches = (total_scenes + batch_size - 1) // batch_size
        
        for batch_num in range(num_batches):
            start_scene = batch_num * batch_size + 1
            end_scene = min((batch_num + 1) * batch_size, total_scenes)
            batch_count = end_scene - start_scene + 1
            
            print(f"\n📦 BATCH {batch_num + 1}/{num_batches}: Scenes {start_scene}-{end_scene}")
            print("-" * 80)
            
            # Sequence planner creates scene breakdown for this batch
            sequence_task = f"""
            Based on the overall story structure:
            {story_structure[:500]}...
            
            Create a scene breakdown for scenes {start_scene} to {end_scene} ({batch_count} scenes).
            
            For each scene provide:
            - Scene number
            - Scene name (2-5 words, descriptive)
            - Brief description (one sentence)
            - Duration (3-10 seconds)
            
            Format as:
            Scene {start_scene}: [Name] - [Description] - [Duration]s
            Scene {start_scene+1}: [Name] - [Description] - [Duration]s
            ...
            
            Ensure logical flow and pacing.
            """
            
            sequence_plan = sequence_planner.run(task=sequence_task)
            print(f"\nSequence Plan:\n{sequence_plan}\n")
            
            # Generate detailed prompts for each scene in batch
            for scene_num in range(start_scene, end_scene + 1):
                print(f"  Writing scene {scene_num}...", end=" ")
                
                prompt_task = f"""
                Write a detailed video generation prompt for Scene {scene_num}.
                
                Overall story: {concept}
                Sequence plan: {sequence_plan}
                
                Write the prompt for Scene {scene_num} in this exact style:
                
                [Shot type] of [subject/setting]. [Camera movement]. [Lighting description]. 
                [Character actions]. [Visual details]. Camera [movement details]. 
                [Color palette]. Audio: [sound description]. Cinematic [style reference].
                
                Be specific about camera, lighting, action, and audio.
                Duration: 5-8 seconds.
                Write ONLY the prompt, no preamble.
                """
                
                video_prompt = scene_writer.run(task=prompt_task)
                
                # Parse scene name from sequence plan (simple extraction)
                scene_name = f"Scene {scene_num}"
                try:
                    # Try to extract scene name from sequence plan
                    for line in sequence_plan.split('\n'):
                        if f"Scene {scene_num}:" in line or f"{scene_num}." in line:
                            parts = line.split('-')[0].split(':')
                            if len(parts) > 1:
                                scene_name = parts[1].strip()
                            break
                except:
                    pass
                
                # Default duration
                duration = 6
                
                scene_data = {
                    "scene_number": scene_num,
                    "scene_name": scene_name,
                    "duration": duration,
                    "original_prompt": video_prompt.strip()
                }
                
                self.scenes.append(scene_data)
                print("✓")
            
            print(f"\n✅ Batch {batch_num + 1} complete ({len(self.scenes)} scenes total)\n")
        
        return self.scenes
    
    def save_script(self, filename: str = "movie_script_200_scenes.json"):
        """Save the complete script"""
        with open(filename, 'w') as f:
            json.dump(self.scenes, f, indent=2)
        
        print(f"\n💾 Saved {len(self.scenes)} scenes to: {filename}")
        return filename


# Main execution
if __name__ == "__main__":
    
    # Initialize director
    director = MovieDirector(
        base_url="http://localhost:1234/v1",
        model_name="openai/kyle-jr-v2"
    )
    
    # Movie concept
    concept = """A cyberpunk noir thriller set in a near-future Los Angeles where 
    a skilled hacker-turned-pizza-delivery-driver must navigate a dangerous world 
    of corporate franchises, virtual reality, and ancient Sumerian mythology to 
    stop a digital virus that's destroying minds."""
    
    # Generate 200 scenes (adjust batch_size based on your needs)
    # Smaller batch_size = more detailed planning per batch
    # Larger batch_size = faster but less detailed
    scenes = director.produce_movie(
        concept=concept,
        total_scenes=200,
        batch_size=10  # Generate 10 scenes at a time
    )
    
    # Save output
    output_file = director.save_script("snow_crash_200_scenes.json")
    
    # Summary
    print("\n" + "="*80)
    print("✅ PRODUCTION COMPLETE!")
    print("="*80)
    print(f"\n📊 Stats:")
    print(f"   Total Scenes: {len(scenes)}")
    print(f"   Total Duration: {sum(s['duration'] for s in scenes)} seconds")
    print(f"   Agents Spawned: {len(director.factory.agents_created)}")
    print(f"\n📄 Output: {output_file}")
    
    # Show sample scenes
    print(f"\n🎬 Sample Scenes:\n")
    for i in [0, len(scenes)//2, -1]:
        scene = scenes[i]
        print(f"Scene {scene['scene_number']}: {scene['scene_name']}")
        print(f"Duration: {scene['duration']}s")
        print(f"Prompt: {scene['original_prompt'][:150]}...")
        print()
