"""
Scene Consistency Pass

Second pass through improved scenes to ensure:
- Visual continuity between scenes
- Consistent character descriptions
- Props/locations persist correctly
- Narrative flow is maintained
"""

import json
from swarms.utils.litellm_wrapper import LiteLLM
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class ConsistencyPass:
    """Ensures scene-to-scene consistency across the script"""
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.file_lock = threading.Lock()
    
    def create_llm(self, temp=0.7, tokens=400):
        """Create a LiteLLM instance"""
        return LiteLLM(
            model_name=self.model_name,
            base_url=self.base_url,
            temperature=temp,
            max_tokens=tokens
        )
    
    def check_consistency(self, prev_scene, current_scene, next_scene, max_iterations=2):
        """
        Multi-agent swarm consistency check
        
        Args:
            prev_scene: Previous scene dict (or None)
            current_scene: Current scene dict
            next_scene: Next scene dict (or None)
            max_iterations: Number of improvement iterations
        
        Returns:
            Improved prompt with consistency fixes
        """
        # Build context string
        context = ""
        if prev_scene:
            context += f"Previous scene ({prev_scene['scene_number']}): {prev_scene['scene_name']}\n"
            context += f"Prompt: {prev_scene['original_prompt'][:250]}...\n\n"
        
        if next_scene:
            context += f"Next scene ({next_scene['scene_number']}): {next_scene['scene_name']}\n"
            context += f"Prompt: {next_scene['original_prompt'][:250]}...\n\n"
        
        current_prompt = current_scene['original_prompt']
        
        # Agents that can be spawned
        available_agents = [
            "Continuity-Checker",  # Character/prop consistency
            "Lighting-Matcher",    # Lighting/location continuity
            "Action-Flow",         # Movement/action logic
        ]
        
        iterations = []
        
        for iteration in range(max_iterations):
            # Meta-agent decides which consistency agents to spawn
            meta_llm = self.create_llm(temp=0.7, tokens=100)
            
            meta_prompt = f"""Analyze which consistency issues need checking.

{context}
Current scene: {current_scene['scene_name']}
Current prompt: {current_prompt[:200]}

Available agents:
- Continuity-Checker (character clothing, props, appearance)
- Lighting-Matcher (lighting, location continuity)
- Action-Flow (movement, action logic)

Which agents are needed? List 1-3 agent names, comma-separated:"""
            
            meta_response = meta_llm.run(meta_prompt).strip()
            
            # Parse agent names from response
            active_agents = []
            for agent in available_agents:
                if agent in meta_response:
                    active_agents.append(agent)
            
            # Fallback: if parsing failed, use all agents
            if not active_agents:
                active_agents = available_agents
            
            print(f"  🔄 Iteration {iteration + 1}/{max_iterations}")
            print(f"     Meta-agent spawned: {', '.join(active_agents)}")
            
            suggestions = []
            
            for agent in active_agents:
                llm = self.create_llm(temp=0.7, tokens=150)
                
                if agent == "Continuity-Checker":
                    prompt = f"""Check character/prop consistency with adjacent scenes.

{context}
Current scene: {current_scene['scene_name']}
Current prompt: {current_prompt[:200]}

Find ONE inconsistency (character clothing, props, appearance). Suggest ONE specific fix (max 15 words):"""
                
                elif agent == "Lighting-Matcher":
                    prompt = f"""Check lighting/location continuity with adjacent scenes.

{context}
Current scene: {current_scene['scene_name']}
Current prompt: {current_prompt[:200]}

If same location as adjacent scenes, suggest ONE lighting consistency fix (max 15 words):"""
                
                elif agent == "Action-Flow":
                    prompt = f"""Check action/movement flow between scenes.

{context}
Current scene: {current_scene['scene_name']}
Current prompt: {current_prompt[:200]}

Suggest ONE action continuity fix to connect scenes better (max 15 words):"""
                
                response = llm.run(prompt).strip()
                clean = response[:150].strip()
                
                suggestions.append({
                    "agent": agent,
                    "suggestion": clean
                })
                print(f"     {agent}: {clean[:60]}...")
            
            # Synthesis: Apply suggestions
            synthesis_llm = self.create_llm(temp=0.6, tokens=400)
            
            synthesis_prompt = f"""Apply consistency fixes to this scene.

Scene: {current_scene['scene_name']}
Current prompt: {current_prompt}

Agent suggestions:
{chr(10).join([f"- {s['agent']}: {s['suggestion']}" for s in suggestions])}

Rules:
- Apply ONLY the consistency fixes suggested
- Keep all other details unchanged
- Maintain character names exactly
- Keep duration: {current_scene['duration']}s
- Be specific and concrete

Write the consistency-fixed prompt:"""
            
            print(f"     🔨 Synthesizing...")
            improved = synthesis_llm.run(synthesis_prompt).strip()
            
            # Clean synthesis output
            for prefix in ["Fixed prompt:", "Consistency-fixed:", "**", "###"]:
                if improved.startswith(prefix):
                    improved = improved[len(prefix):].strip()
            
            iterations.append({
                "iteration": iteration,
                "agents": active_agents,
                "suggestions": suggestions,
                "prompt": improved
            })
            
            print(f"     ✓ Fixed")
            
            # Early stopping if no significant change
            if iteration > 0 and improved == current_prompt:
                print(f"     🎯 Converged")
                break
            
            current_prompt = improved
        
        return current_prompt
    
    def process_script(self, input_file, output_file, max_workers=4):
        """
        Process entire script for consistency
        
        Args:
            input_file: Path to improved script JSON
            output_file: Path to save consistency-fixed script
            max_workers: Number of parallel workers
        """
        print("\n" + "🎬"*40)
        print("SCENE CONSISTENCY PASS")
        print("🎬"*40 + "\n")
        
        # Load improved scenes
        with open(input_file, 'r') as f:
            scenes = json.load(f)
        
        print(f"📖 Input: {input_file}")
        print(f"   Scenes: {len(scenes)} total\n")
        
        # Load existing consistency-fixed scenes if resuming
        consistent_scenes = []
        existing_scene_numbers = set()
        consistency_log = []
        
        try:
            with open(output_file, 'r') as f:
                consistent_scenes = json.load(f)
                existing_scene_numbers = {s['scene_number'] for s in consistent_scenes}
            print(f"   Loaded {len(consistent_scenes)} existing consistency-fixed scenes")
            print(f"   Will skip already completed scenes\n")
        except:
            pass
        
        # Load existing log if resuming
        log_file = output_file.replace('.json', '_consistency_log.json')
        try:
            with open(log_file, 'r') as f:
                consistency_log = json.load(f)
        except:
            pass
        
        def process_scene_with_context(idx):
            """Process a single scene with context"""
            current = scenes[idx]
            
            # Skip if already processed
            if current['scene_number'] in existing_scene_numbers:
                print(f"Scene {current['scene_number']}: {current['scene_name']} - Already fixed, skipping...")
                return None
            
            prev_scene = scenes[idx - 1] if idx > 0 else None
            next_scene = scenes[idx + 1] if idx < len(scenes) - 1 else None
            
            print(f"\n{'='*80}")
            print(f"Scene {current['scene_number']}: {current['scene_name']}")
            print(f"{'='*80}")
            
            # Check consistency
            original_prompt = current['original_prompt']
            fixed_prompt = self.check_consistency(prev_scene, current, next_scene)
            
            print(f"✓ Consistency checked")
            
            # Create log entry
            log_entry = {
                "scene_number": current['scene_number'],
                "scene_name": current['scene_name'],
                "before": original_prompt,
                "after": fixed_prompt,
                "changed": original_prompt != fixed_prompt
            }
            
            return {
                'scene': {
                    "scene_number": current['scene_number'],
                    "scene_name": current['scene_name'],
                    "duration": current['duration'],
                    "original_prompt": fixed_prompt
                },
                'log': log_entry
            }
        
        # Process scenes in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Only process scenes that haven't been done yet
            scenes_to_process = [i for i, s in enumerate(scenes) if s['scene_number'] not in existing_scene_numbers]
            
            futures = {executor.submit(process_scene_with_context, idx): idx for idx in scenes_to_process}
            
            for future in as_completed(futures):
                result = future.result()
                if result is None:
                    continue
                
                # Thread-safe append and save
                with self.file_lock:
                    consistent_scenes.append(result['scene'])
                    consistency_log.append(result['log'])
                    
                    # Save after each scene (incremental save)
                    consistent_scenes.sort(key=lambda x: x['scene_number'])
                    with open(output_file, 'w') as f:
                        json.dump(consistent_scenes, f, indent=2)
                    
                    # Save log
                    consistency_log.sort(key=lambda x: x['scene_number'])
                    with open(log_file, 'w') as f:
                        json.dump(consistency_log, f, indent=2)
        
        # Final save with sorting
        consistent_scenes.sort(key=lambda x: x['scene_number'])
        with open(output_file, 'w') as f:
            json.dump(consistent_scenes, f, indent=2)
        
        print(f"\n{'='*80}")
        print("✅ CONSISTENCY PASS COMPLETE!")
        print(f"{'='*80}")
        print(f"\n💾 Output: {output_file}\n")
        
        return consistent_scenes


if __name__ == "__main__":
    consistency = ConsistencyPass()
    
    # Run consistency pass on improved script
    consistency.process_script(
        input_file="snow_crash_improved_clean_full.json",
        output_file="snow_crash_consistent_final.json",
        max_workers=4
    )
