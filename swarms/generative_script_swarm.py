"""
Generative Script Improvement Swarm

A true multi-agent swarm that:
- Loads the original script
- Spawns agents dynamically as needed
- Iteratively improves each scene through collaboration
- Saves all iterations to show evolution
- Non-deterministic and emergent
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM
from datetime import datetime
import random


class GenerativeScriptSwarm:
    """True generative multi-agent swarm for script improvement"""
    
    def __init__(self, base_url="http://localhost:1234/v1", 
                 model_name="openai/kyle-jr-v2"):
        self.base_url = base_url
        self.model_name = model_name
        self.agents = {}
        self.iterations_log = []
    
    def extract_clean_response(self, agent_output):
        """Extract clean response from agent output, removing system prompts"""
        if not agent_output:
            return ""
        
        # Split by common delimiters
        lines = agent_output.split('\n')
        
        # Remove lines that look like system prompts
        clean_lines = []
        skip_keywords = ['System:', 'Human:', 'Agent:', '<end_of_turn>', '<start_of_turn>', 
                        'You are an autonomous', 'Agent suggestions:', 'Write ONLY']
        
        for line in lines:
            # Skip if line contains system keywords
            if any(keyword in line for keyword in skip_keywords):
                continue
            # Skip empty lines
            if not line.strip():
                continue
            clean_lines.append(line.strip())
        
        # Join and return
        result = ' '.join(clean_lines)
        
        # If result is still too long or looks polluted, take last meaningful sentence
        if len(result) > 300 or '<' in result:
            # Try to find the last complete sentence
            sentences = result.split('.')
            if sentences:
                result = sentences[-2] if len(sentences) > 1 else sentences[0]
        
        return result[:200]  # Limit to 200 chars
        
    def create_llm(self, temp=0.7, tokens=500):
        return LiteLLM(
            model_name=self.model_name,
            base_url=self.base_url,
            api_key="not-needed",
            temperature=temp,
            max_tokens=tokens,
            stream=False,
        )
    
    def spawn_agent(self, role, description, temp=0.7):
        """Dynamically spawn a new agent"""
        if role not in self.agents:
            llm = self.create_llm(temp=temp, tokens=400)
            agent = Agent(
                agent_name=role,
                agent_description=description,
                llm=llm,
                max_loops=1,
            )
            self.agents[role] = agent
            print(f"  ✨ Spawned: {role}")
        return self.agents[role]
    
    def improve_scene_iteratively(self, scene, max_iterations=3):
        """
        Improve a scene through iterative multi-agent collaboration
        
        Args:
            scene: Original scene dict
            max_iterations: Max number of improvement cycles
        
        Returns:
            List of iterations showing evolution
        """
        scene_num = scene['scene_number']
        scene_name = scene['scene_name']
        current_prompt = scene['original_prompt']
        duration = scene['duration']
        
        iterations = [{
            "iteration": 0,
            "type": "original",
            "prompt": current_prompt
        }]
        
        print(f"\n{'='*80}")
        print(f"Scene {scene_num}: {scene_name}")
        print(f"{'='*80}")
        print(f"Original: {current_prompt[:100]}...")
        
        # Iteration loop
        for iteration in range(1, max_iterations + 1):
            print(f"\n  🔄 Iteration {iteration}/{max_iterations}")
            
            # Intelligently decide which agents to involve (generative but smart!)
            agent_pool = []
            
            # Always include Director
            agent_pool.append("Director")
            
            # Always add Cinematographer (visual is key)
            if random.random() > 0.3:
                agent_pool.append("Cinematographer")
            
            # Smart Dialogue-Coach spawning - check if scene likely has characters
            scene_text_lower = (scene_name + " " + current_prompt).lower()
            has_character_keywords = any(word in scene_text_lower for word in 
                ['character', 'hiro', 'person', 'man', 'woman', 'driver', 'face', 
                 'speaks', 'says', 'yells', 'whispers', 'dialogue', 'conversation'])
            
            # Spawn Dialogue-Coach if: scene has character keywords OR random chance
            if has_character_keywords or random.random() > 0.4:
                agent_pool.append("Dialogue-Coach")
            
            # Sound designer for audio enhancement
            if random.random() > 0.6:
                agent_pool.append("Sound-Designer")
            
            print(f"     Agents: {', '.join(agent_pool)}")
            
            # Collect suggestions from each agent
            suggestions = []
            
            for role in agent_pool:
                if role == "Director":
                    agent = self.spawn_agent(
                        "Director",
                        "You analyze narrative flow, pacing, and dramatic impact.",
                        temp=0.8
                    )
                    task = f"""Analyze this scene (iteration {iteration}):
                    
Scene: {scene_name}
Current: {current_prompt[:200]}...

What ONE improvement would increase dramatic impact?
Be specific (1 sentence)."""
                
                elif role == "Cinematographer":
                    agent = self.spawn_agent(
                        "Cinematographer",
                        "You enhance visual storytelling through camera and lighting.",
                        temp=0.75
                    )
                    task = f"""Review this scene visually:
                    
Scene: {scene_name}
Current: {current_prompt[:200]}...

Suggest ONE specific camera or lighting enhancement.
Be concise."""
                
                elif role == "Dialogue-Coach":
                    agent = self.spawn_agent(
                        "Dialogue-Coach",
                        "You add impactful character dialogue.",
                        temp=0.85
                    )
                    task = f"""Consider dialogue for this scene:
                    
Scene: {scene_name}
Current: {current_prompt[:200]}...

Should this have dialogue? If yes, suggest a brief line.
If no, say "NO_DIALOGUE"."""
                
                elif role == "Sound-Designer":
                    agent = self.spawn_agent(
                        "Sound-Designer",
                        "You enhance audio and sonic atmosphere.",
                        temp=0.75
                    )
                    task = f"""Review audio for this scene:
                    
Scene: {scene_name}
Current: {current_prompt[:200]}...

Suggest ONE specific audio/sound enhancement.
Be brief."""
                
                # Get agent suggestion
                suggestion = agent.run(task=task)
                
                # Extract clean suggestion using our cleaning function
                clean_suggestion = self.extract_clean_response(suggestion)
                
                suggestions.append({
                    "agent": role,
                    "suggestion": clean_suggestion
                })
                
                print(f"     {role}: {clean_suggestion[:60]}...")
            
            # Synthesize improvements using clean LLM
            print(f"     🔨 Synthesizing...")
            
            synthesis_prompt = f"""Improve this video prompt based on agent suggestions:

Original: {current_prompt[:200]}

Agent suggestions:
{chr(10).join([f"- {s['agent']}: {s['suggestion'][:80]}" for s in suggestions])}

Write the improved prompt incorporating the best suggestions naturally.
Keep the same format and style. Duration: {duration}s.

Write ONLY the improved prompt:"""
            
            clean_llm = self.create_llm(temp=0.7, tokens=600)
            improved_prompt = clean_llm.run(synthesis_prompt)
            
            # Save iteration
            iterations.append({
                "iteration": iteration,
                "agents": agent_pool,
                "suggestions": suggestions,
                "prompt": improved_prompt.strip()
            })
            
            current_prompt = improved_prompt.strip()
            print(f"     ✓ Improved: {current_prompt[:80]}...")
            
            # Decide if we should continue (generative!)
            if iteration < max_iterations:
                # Randomly decide to continue or stop early
                if random.random() > 0.7:
                    print(f"     🎯 Early convergence - stopping")
                    break
        
        return iterations
    
    def improve_script(self, input_file, output_file, start_scene=1, end_scene=None, 
                      iterations_per_scene=3):
        """
        Improve script through generative swarm
        
        Args:
            input_file: Original script JSON
            output_file: Output improved script JSON
            start_scene: First scene to improve
            end_scene: Last scene (None = all)
            iterations_per_scene: Max iterations per scene
        """
        
        print("\n" + "🎬" * 40)
        print("GENERATIVE SCRIPT IMPROVEMENT SWARM")
        print("🎬" * 40 + "\n")
        
        # Load original script
        print(f"📖 Loading: {input_file}")
        with open(input_file, 'r') as f:
            all_scenes = json.load(f)
        
        total_scenes = len(all_scenes)
        
        if end_scene is None:
            end_scene = total_scenes
        
        scenes_to_improve = all_scenes[start_scene - 1:end_scene]
        
        print(f"   Total scenes: {total_scenes}")
        print(f"   Improving: {start_scene}-{end_scene} ({len(scenes_to_improve)} scenes)")
        print(f"   Max iterations per scene: {iterations_per_scene}\n")
        
        # Improve each scene
        improved_scenes = []
        all_iterations = []
        
        for scene in scenes_to_improve:
            iterations = self.improve_scene_iteratively(scene, max_iterations=iterations_per_scene)
            
            # Save final improved version
            final_iteration = iterations[-1]
            improved_scenes.append({
                "scene_number": scene['scene_number'],
                "scene_name": scene['scene_name'],
                "duration": scene['duration'],
                "original_prompt": final_iteration['prompt']
            })
            
            # Save all iterations for this scene
            all_iterations.append({
                "scene_number": scene['scene_number'],
                "scene_name": scene['scene_name'],
                "iterations": iterations
            })
            
            # Save after EACH scene (incremental save)
            with open(output_file, 'w') as f:
                json.dump(improved_scenes, f, indent=2)
            
            iterations_file = output_file.replace('.json', '_iterations.json')
            with open(iterations_file, 'w') as f:
                json.dump(all_iterations, f, indent=2)
        
        # Final save (redundant but ensures completion)
        with open(output_file, 'w') as f:
            json.dump(improved_scenes, f, indent=2)
        
        # Save iteration history
        iterations_file = output_file.replace('.json', '_iterations.json')
        with open(iterations_file, 'w') as f:
            json.dump(all_iterations, f, indent=2)
        
        print(f"\n{'='*80}")
        print("✅ GENERATIVE IMPROVEMENT COMPLETE!")
        print(f"{'='*80}")
        print(f"\n📊 Stats:")
        print(f"   Scenes improved: {len(improved_scenes)}")
        print(f"   Agents spawned: {len(self.agents)}")
        print(f"   Total iterations: {sum(len(s['iterations']) - 1 for s in all_iterations)}")
        print(f"\n💾 Outputs:")
        print(f"   Final script: {output_file}")
        print(f"   Iteration history: {iterations_file}\n")
        
        return improved_scenes, all_iterations


if __name__ == "__main__":
    
    swarm = GenerativeScriptSwarm()
    
    # Test with first 5 scenes, up to 3 iterations each
    improved, iterations = swarm.improve_script(
        input_file="existing_script.json",
        output_file="generative_improved_test_5.json",
        start_scene=1,
        end_scene=5,
        iterations_per_scene=3  # Each scene gets up to 3 improvement cycles
    )
    
    # To run all 1,112 scenes: end_scene=None
