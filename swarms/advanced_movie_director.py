"""
Advanced Multi-Agent Movie Director System

Features:
- Dynamic agent spawning based on needs
- Resource management (token budgets)
- Script modification and iteration
- Director can create specialized agents on-demand
- JSON output with embedded video generation prompts
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM
from typing import List, Dict, Optional
from datetime import datetime


class AgentFactory:
    """Factory for creating specialized agents on-demand"""
    
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url
        self.model_name = model_name
        self.agents_created = []
        self.total_tokens_used = 0
        self.max_tokens_budget = 50000  # Token budget for entire production
        
    def create_agent(self, role: str, description: str, temperature: float = 0.7, max_tokens: int = 1000):
        """Dynamically create an agent with role and description"""
        
        # Check token budget
        if self.total_tokens_used >= self.max_tokens_budget:
            print(f"⚠️  Token budget exceeded! ({self.total_tokens_used}/{self.max_tokens_budget})")
            return None
        
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
            "created_at": datetime.now().isoformat(),
            "max_tokens": max_tokens
        })
        
        print(f"✨ Spawned Agent: {role}")
        return agent
    
    def track_usage(self, tokens: int):
        """Track token usage"""
        self.total_tokens_used += tokens
        remaining = self.max_tokens_budget - self.total_tokens_used
        print(f"📊 Tokens: {tokens} used | {self.total_tokens_used} total | {remaining} remaining")


class MovieDirector:
    """Main Director Agent that spawns and manages other agents"""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", model_name: str = "openai/kyle-jr-v2"):
        self.factory = AgentFactory(base_url, model_name)
        self.movie_script = {
            "title": "",
            "genre": "",
            "version": 1,
            "scenes": [],
            "production_log": []
        }
        
    def log_action(self, action: str):
        """Log production actions"""
        self.movie_script["production_log"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action
        })
        
    def create_initial_concept(self, concept: str, num_scenes: int):
        """Director creates initial concept and determines what agents to spawn"""
        
        print("\n" + "="*80)
        print("🎬 DIRECTOR: Analyzing concept and planning production...")
        print("="*80)
        
        director = self.factory.create_agent(
            role="Executive-Director",
            description="""You are the executive director. You analyze movie concepts, 
            determine what specialized agents are needed, and create production plans. 
            You think strategically about resources and delegation.""",
            temperature=0.8,
            max_tokens=800
        )
        
        task = f"""
        Analyze this movie concept: "{concept}"
        
        You need to create a {num_scenes}-scene movie.
        
        Determine:
        1. What specialized agents do you need? (e.g., Story-Writer, Visual-Designer, Dialogue-Expert, etc.)
        2. What's the genre and tone?
        3. Brief outline of {num_scenes} scenes
        
        Format your response as:
        AGENTS_NEEDED: [list agents]
        GENRE: [genre]
        SCENES: [brief outline]
        """
        
        plan = director.run(task=task)
        print(f"\n{plan}\n")
        
        self.log_action(f"Director analyzed concept: {concept}")
        self.factory.track_usage(800)  # Estimate
        
        return plan
    
    def spawn_specialized_agents(self, plan: str, num_scenes: int):
        """Spawn agents based on director's plan"""
        
        print("\n" + "="*80)
        print("🤖 SPAWNING SPECIALIZED AGENTS...")
        print("="*80 + "\n")
        
        # Always spawn these core agents
        agents = {}
        
        # Story Architect
        agents['story'] = self.factory.create_agent(
            role="Story-Architect",
            description="""You create compelling narrative structures with clear arcs, 
            pacing, and emotional beats. You understand three-act structure and visual storytelling.""",
            temperature=0.85,
            max_tokens=1200
        )
        
        # Visual Prompt Engineer
        agents['visual'] = self.factory.create_agent(
            role="Visual-Prompt-Engineer",
            description="""You are an expert at writing prompts for AI video generation models.
            You describe scenes with precise visual details: camera angles, lighting, movement,
            composition, colors, atmosphere. You write prompts that AI can execute.""",
            temperature=0.7,
            max_tokens=1500
        )
        
        # Quality Control
        agents['qc'] = self.factory.create_agent(
            role="Quality-Control",
            description="""You review scenes for consistency, quality, and coherence.
            You ensure visual continuity, narrative flow, and technical feasibility.""",
            temperature=0.3,
            max_tokens=600
        )
        
        self.log_action(f"Spawned {len(agents)} specialized agents")
        return agents
    
    def generate_scenes(self, agents: Dict, plan: str, num_scenes: int):
        """Generate scenes using spawned agents"""
        
        print("\n" + "="*80)
        print("📝 GENERATING STORY STRUCTURE...")
        print("="*80)
        
        # Story agent creates structure
        story_task = f"""
        Based on this plan:
        {plan}
        
        Create a {num_scenes}-scene structure. For each scene provide:
        - Scene number
        - Location/setting
        - Key action/event
        - Emotional tone
        - Approximate duration (10-20 seconds)
        
        Be concise. Format as numbered list.
        """
        
        story_structure = agents['story'].run(task=story_task)
        print(f"\n{story_structure}\n")
        self.factory.track_usage(1200)
        
        print("\n" + "="*80)
        print("🎥 GENERATING VIDEO PROMPTS...")
        print("="*80 + "\n")
        
        scenes = []
        for i in range(1, num_scenes + 1):
            print(f"Scene {i}/{num_scenes}...")
            
            # Visual agent creates video prompt
            visual_task = f"""
            Create a video generation prompt for Scene {i}.
            
            Story context:
            {story_structure}
            
            Write a detailed prompt for Scene {i} including:
            - Camera: angle, movement, framing
            - Lighting: type, direction, mood
            - Action: what happens, character movements
            - Visual style: colors, atmosphere, aesthetics
            - Duration: 15 seconds
            
            Write ONLY the prompt. Be specific and visual. No preamble.
            """
            
            video_prompt = agents['visual'].run(task=visual_task)
            
            scene = {
                "scene_number": i,
                "duration_seconds": 15,
                "video_prompt": video_prompt.strip(),
                "status": "draft",
                "version": 1
            }
            
            scenes.append(scene)
            self.factory.track_usage(1500)
            print(f"✅ Scene {i} generated\n")
        
        return scenes
    
    def review_and_modify(self, agents: Dict, scenes: List[Dict]):
        """QC agent reviews and suggests modifications"""
        
        print("\n" + "="*80)
        print("🔍 QUALITY CONTROL REVIEW...")
        print("="*80)
        
        qc_task = f"""
        Review these {len(scenes)} scenes:
        
        {json.dumps([{"scene": s["scene_number"], "prompt_preview": s["video_prompt"][:200]} for s in scenes], indent=2)}
        
        Check for:
        1. Visual consistency across scenes
        2. Narrative flow
        3. Technical feasibility for video generation
        
        Provide brief feedback. List any issues or confirm quality is good.
        """
        
        qc_report = agents['qc'].run(task=qc_task)
        print(f"\n{qc_report}\n")
        self.factory.track_usage(600)
        
        # Mark scenes as reviewed
        for scene in scenes:
            scene["status"] = "reviewed"
            scene["qc_notes"] = qc_report[:100]
        
        return scenes
    
    def finalize_script(self, concept: str, plan: str, scenes: List[Dict]):
        """Assemble final JSON output"""
        
        print("\n" + "="*80)
        print("📄 FINALIZING SCRIPT...")
        print("="*80)
        
        # Extract title and genre from plan (simple parsing)
        title = "Untitled Film"
        genre = "Drama"
        
        if "GENRE:" in plan:
            try:
                genre = plan.split("GENRE:")[1].split("\n")[0].strip()
            except:
                pass
        
        self.movie_script.update({
            "title": title,
            "genre": genre,
            "concept": concept,
            "total_duration_seconds": sum(s["duration_seconds"] for s in scenes),
            "scenes": scenes,
            "metadata": {
                "agents_spawned": len(self.factory.agents_created),
                "total_tokens_used": self.factory.total_tokens_used,
                "production_date": datetime.now().isoformat(),
                "agent_roster": self.factory.agents_created
            }
        })
        
        return self.movie_script
    
    def produce(self, concept: str, num_scenes: int = 4):
        """Main production pipeline"""
        
        print("\n" + "🎬"*40)
        print("ADVANCED MOVIE PRODUCTION SYSTEM")
        print("🎬"*40)
        print(f"\n📋 Concept: {concept}")
        print(f"🎞️  Scenes: {num_scenes}")
        
        # Step 1: Director analyzes and plans
        plan = self.create_initial_concept(concept, num_scenes)
        
        # Step 2: Spawn specialized agents
        agents = self.spawn_specialized_agents(plan, num_scenes)
        
        # Step 3: Generate scenes
        scenes = self.generate_scenes(agents, plan, num_scenes)
        
        # Step 4: Review and modify
        scenes = self.review_and_modify(agents, scenes)
        
        # Step 5: Finalize
        final_script = self.finalize_script(concept, plan, scenes)
        
        return final_script
    
    def save(self, filename: str = "movie_script.json"):
        """Save script to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.movie_script, f, indent=2)
        print(f"\n💾 Saved to: {filename}")
        return filename


# Example usage
if __name__ == "__main__":
    
    # Initialize director
    director = MovieDirector(
        base_url="http://localhost:1234/v1",
        model_name="openai/kyle-jr-v2"
    )
    
    # Produce movie
    concept = "In a world where memories can be stolen, a detective must recover her own past"
    
    script = director.produce(
        concept=concept,
        num_scenes=4
    )
    
    # Save
    output_file = director.save("memory_thief_script.json")
    
    # Display summary
    print("\n" + "="*80)
    print("✅ PRODUCTION COMPLETE!")
    print("="*80)
    print(f"\n📊 Production Stats:")
    print(f"   - Agents Spawned: {script['metadata']['agents_spawned']}")
    print(f"   - Total Tokens: {script['metadata']['total_tokens_used']}")
    print(f"   - Total Duration: {script['total_duration_seconds']} seconds")
    print(f"   - Scenes: {len(script['scenes'])}")
    print(f"\n📄 Output: {output_file}")
    
    # Show first scene as example
    print(f"\n🎬 Scene 1 Preview:")
    print(f"{script['scenes'][0]['video_prompt'][:300]}...")
