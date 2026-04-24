"""
Fast 200-Scene Movie Generator

Optimized for speed while maintaining quality.
Uses larger batches and streamlined prompts.
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM


def create_agent(role: str, description: str, temp: float = 0.7, tokens: int = 1500):
    """Quick agent factory"""
    llm = LiteLLM(
        model_name="openai/kyle-jr-v2",
        base_url="http://localhost:1234/v1",
        api_key="not-needed",
        temperature=temp,
        max_tokens=tokens,
        stream=False,
    )
    return Agent(agent_name=role, agent_description=description, llm=llm, max_loops=1)


def generate_200_scene_movie(concept: str, output_file: str = "movie_200_scenes.json"):
    """
    Generate a 200-scene movie script
    
    Args:
        concept: Movie concept/premise
        output_file: Output JSON filename
    """
    
    print("\n" + "🎬" * 40)
    print("FAST 200-SCENE MOVIE GENERATOR")
    print("🎬" * 40)
    print(f"\nConcept: {concept}\n")
    
    scenes = []
    
    # Create agents
    print("Creating agent team...")
    
    director = create_agent(
        "Director",
        "You create story structures and scene breakdowns for films. You think in acts, sequences, and beats.",
        temp=0.8,
        tokens=2000
    )
    
    writer = create_agent(
        "Scene-Writer",
        "You write detailed video generation prompts with camera, lighting, action, and audio. Cinematic style.",
        temp=0.7,
        tokens=1500
    )
    
    # Step 1: Get overall structure
    print("\n" + "="*80)
    print("DIRECTOR: Creating 200-scene structure")
    print("="*80)
    
    structure_task = f"""
    Create a 200-scene movie structure for: "{concept}"
    
    Provide:
    1. Act 1 (scenes 1-60): Setup and inciting incident
    2. Act 2 (scenes 61-150): Rising action and complications
    3. Act 3 (scenes 151-200): Climax and resolution
    
    List key sequences and major beats.
    Be concise.
    """
    
    structure = director.run(task=structure_task)
    print(f"\n{structure}\n")
    
    # Step 2: Generate scenes in batches of 20
    print("="*80)
    print("GENERATING 200 SCENES (20 per batch)")
    print("="*80 + "\n")
    
    batch_size = 20
    num_batches = 10  # 200 / 20 = 10 batches
    
    for batch in range(num_batches):
        start = batch * batch_size + 1
        end = (batch + 1) * batch_size
        
        print(f"\n📦 Batch {batch+1}/10: Scenes {start}-{end}")
        print("-" * 80)
        
        # Get scene list for this batch
        batch_task = f"""
        Story: {concept}
        Structure: {structure[:300]}...
        
        List scenes {start} to {end}. For each:
        Scene [num]: [Name 2-4 words] | [Brief description] | [Duration 4-8s]
        
        Example:
        Scene {start}: Title Card | Logo appears on black | 5s
        Scene {start+1}: City Aerial | Flying over neon city | 6s
        
        List all {batch_size} scenes. Be concise.
        """
        
        batch_plan = director.run(task=batch_task)
        print(f"\n{batch_plan}\n")
        
        # Parse and generate prompts
        for scene_num in range(start, end + 1):
            # Extract scene info from batch plan
            scene_name = f"Scene {scene_num}"
            duration = 6
            
            for line in batch_plan.split('\n'):
                if f"Scene {scene_num}" in line or f"{scene_num}:" in line:
                    try:
                        parts = line.split('|')
                        if len(parts) >= 2:
                            scene_name = parts[0].split(':')[1].strip()
                        if len(parts) >= 3:
                            dur_str = parts[2].strip().replace('s', '')
                            duration = int(dur_str) if dur_str.isdigit() else 6
                    except:
                        pass
                    break
            
            # Generate video prompt
            print(f"  Scene {scene_num}: {scene_name}...", end=" ")
            
            prompt_task = f"""
            Scene {scene_num} from: {concept}
            Scene name: {scene_name}
            Context: {batch_plan[:200]}
            
            Write video prompt:
            [Shot type] of [subject]. Camera [movement]. [Lighting]. [Action]. [Colors]. Audio: [sounds]. Cinematic [style].
            
            Be specific. Duration: {duration}s. ONLY write the prompt.
            """
            
            prompt = writer.run(task=prompt_task)
            
            scenes.append({
                "scene_number": scene_num,
                "scene_name": scene_name,
                "duration": duration,
                "original_prompt": prompt.strip()
            })
            
            print("✓")
        
        print(f"\n✅ {len(scenes)} scenes complete")
    
    # Save
    with open(output_file, 'w') as f:
        json.dump(scenes, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print(f"\nTotal Scenes: {len(scenes)}")
    print(f"Total Duration: {sum(s['duration'] for s in scenes)}s")
    print(f"Output: {output_file}\n")
    
    # Show samples
    print("Sample Scenes:\n")
    for i in [0, 99, 199]:
        s = scenes[i]
        print(f"Scene {s['scene_number']}: {s['scene_name']} ({s['duration']}s)")
        print(f"{s['original_prompt'][:120]}...\n")
    
    return scenes


if __name__ == "__main__":
    concept = """A cyberpunk delivery driver in a corporate-dominated Los Angeles 
    discovers a digital virus in the Metaverse that's connected to ancient Sumerian 
    mythology. Racing against time, they must navigate virtual reality, corporate 
    warfare, and their own past to stop a catastrophic mind-virus outbreak."""
    
    generate_200_scene_movie(concept, "snow_crash_full.json")
