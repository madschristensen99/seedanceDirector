"""
Multi-Agent Movie Production System

Architecture:
- Director Agent: Orchestrates the entire movie production
- Spawns specialized agents:
  - Story Agent: Creates narrative structure
  - Scene Agent: Writes individual scenes with video prompts
  - Continuity Agent: Ensures consistency across scenes
  - Editor Agent: Refines and formats final JSON output

Output: JSON with movie script where each scene contains prompts for video generation
"""

import json
from swarms import Agent
from swarms.utils.litellm_wrapper import LiteLLM
from typing import List, Dict
import os


class MovieProductionSystem:
    """Manages multi-agent movie script generation"""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", model_name: str = "openai/kyle-jr-v2"):
        self.base_url = base_url
        self.model_name = model_name
        self.movie_script = {
            "title": "",
            "genre": "",
            "duration_seconds": 0,
            "scenes": []
        }
        
    def create_llm(self, temperature: float = 0.7, max_tokens: int = 1000):
        """Create LLM instance for agents"""
        return LiteLLM(
            model_name=self.model_name,
            base_url=self.base_url,
            api_key="not-needed",
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
    
    def create_director_agent(self):
        """Director Agent: Orchestrates the entire production"""
        llm = self.create_llm(temperature=0.8, max_tokens=800)
        
        director = Agent(
            agent_name="Movie-Director",
            agent_description="""You are a visionary movie director. You oversee the entire 
            production, make creative decisions, and coordinate with specialized teams. 
            You break down movie concepts into structured scenes and manage the creative vision.""",
            llm=llm,
            max_loops=1,
        )
        return director
    
    def create_story_agent(self):
        """Story Agent: Creates narrative structure"""
        llm = self.create_llm(temperature=0.9, max_tokens=1200)
        
        story_agent = Agent(
            agent_name="Story-Architect",
            agent_description="""You are a master storyteller. You create compelling 
            narrative structures with clear beginning, middle, and end. You understand 
            pacing, character development, and dramatic arcs.""",
            llm=llm,
            max_loops=1,
        )
        return story_agent
    
    def create_scene_agent(self):
        """Scene Agent: Writes scenes with video generation prompts"""
        llm = self.create_llm(temperature=0.7, max_tokens=1500)
        
        scene_agent = Agent(
            agent_name="Scene-Writer",
            agent_description="""You are a scene writer specialized in creating detailed 
            visual descriptions for AI video generation. You write prompts that are:
            - Highly visual and descriptive
            - Specific about camera angles, lighting, and movement
            - Clear about actions, emotions, and atmosphere
            - Optimized for text-to-video AI models""",
            llm=llm,
            max_loops=1,
        )
        return scene_agent
    
    def create_continuity_agent(self):
        """Continuity Agent: Ensures consistency"""
        llm = self.create_llm(temperature=0.3, max_tokens=800)
        
        continuity_agent = Agent(
            agent_name="Continuity-Supervisor",
            agent_description="""You are a continuity supervisor. You ensure consistency 
            across all scenes - characters, settings, props, timeline, and visual style. 
            You catch contradictions and maintain coherence.""",
            llm=llm,
            max_loops=1,
        )
        return continuity_agent
    
    def create_editor_agent(self):
        """Editor Agent: Refines and formats output"""
        llm = self.create_llm(temperature=0.2, max_tokens=1000)
        
        editor_agent = Agent(
            agent_name="Script-Editor",
            agent_description="""You are a script editor. You refine dialogue, improve 
            pacing, ensure proper formatting, and polish the final output. You have a 
            keen eye for detail and quality.""",
            llm=llm,
            max_loops=1,
        )
        return editor_agent
    
    def produce_movie(self, concept: str, num_scenes: int = 5):
        """Main production pipeline"""
        
        print("🎬 MOVIE PRODUCTION SYSTEM INITIALIZED")
        print("=" * 80)
        
        # Step 1: Director creates high-level plan
        print("\n📋 STEP 1: Director Planning")
        print("-" * 80)
        director = self.create_director_agent()
        
        director_task = f"""
        Create a high-level plan for a {num_scenes}-scene movie based on this concept:
        "{concept}"
        
        Provide:
        1. Movie title
        2. Genre
        3. Brief outline of {num_scenes} scenes (one sentence each)
        4. Overall tone and visual style
        
        Be concise and structured.
        """
        
        director_plan = director.run(task=director_task)
        print(f"\n{director_plan}\n")
        
        # Step 2: Story Agent creates narrative structure
        print("\n📖 STEP 2: Story Architecture")
        print("-" * 80)
        story_agent = self.create_story_agent()
        
        story_task = f"""
        Based on this director's vision:
        {director_plan}
        
        Create a detailed narrative structure for {num_scenes} scenes. For each scene, provide:
        - Scene number
        - Setting/location
        - Key events
        - Character emotions/motivations
        - Duration (in seconds, total should be 60-90 seconds)
        
        Format as a numbered list.
        """
        
        story_structure = story_agent.run(task=story_task)
        print(f"\n{story_structure}\n")
        
        # Step 3: Scene Agent writes video generation prompts
        print("\n🎥 STEP 3: Scene Writing (Video Prompts)")
        print("-" * 80)
        scene_agent = self.create_scene_agent()
        
        scenes_data = []
        for i in range(1, num_scenes + 1):
            scene_task = f"""
            Write a detailed video generation prompt for Scene {i} based on:
            
            Director's Vision: {director_plan}
            Story Structure: {story_structure}
            
            Create a prompt for Scene {i} that includes:
            - Visual description (camera angle, lighting, colors)
            - Action and movement
            - Atmosphere and mood
            - Any dialogue or text overlays
            - Duration: 10-15 seconds
            
            Write ONLY the video prompt, optimized for AI video generation.
            Be specific and visual. Start directly with the description.
            """
            
            video_prompt = scene_agent.run(task=scene_task)
            
            scene_data = {
                "scene_number": i,
                "duration_seconds": 12,  # Default duration
                "video_prompt": video_prompt.strip(),
                "metadata": {
                    "camera": "auto",
                    "style": "cinematic"
                }
            }
            scenes_data.append(scene_data)
            print(f"\n✅ Scene {i} completed")
            print(f"Prompt preview: {video_prompt[:150]}...\n")
        
        # Step 4: Continuity check
        print("\n🔍 STEP 4: Continuity Check")
        print("-" * 80)
        continuity_agent = self.create_continuity_agent()
        
        continuity_task = f"""
        Review these {num_scenes} scenes for continuity issues:
        
        {json.dumps(scenes_data, indent=2)}
        
        Check for:
        - Logical flow between scenes
        - Consistent visual style
        - Timeline coherence
        - Character/setting consistency
        
        List any issues found or confirm continuity is good.
        Be brief.
        """
        
        continuity_report = continuity_agent.run(task=continuity_task)
        print(f"\n{continuity_report}\n")
        
        # Step 5: Editor finalizes
        print("\n✂️ STEP 5: Final Editing")
        print("-" * 80)
        editor_agent = self.create_editor_agent()
        
        editor_task = f"""
        Review and suggest a title and genre for this movie based on the scenes:
        
        Director's Vision: {director_plan}
        
        Provide:
        1. Final movie title (creative and fitting)
        2. Genre
        
        Format: Title: [title] | Genre: [genre]
        """
        
        editor_output = editor_agent.run(task=editor_task)
        print(f"\n{editor_output}\n")
        
        # Parse title and genre (simple extraction)
        title = "Untitled Film"
        genre = "Drama"
        if "Title:" in editor_output:
            try:
                title = editor_output.split("Title:")[1].split("|")[0].strip()
                genre = editor_output.split("Genre:")[1].strip()
            except:
                pass
        
        # Step 6: Assemble final JSON
        self.movie_script = {
            "title": title,
            "genre": genre,
            "total_duration_seconds": sum(s["duration_seconds"] for s in scenes_data),
            "concept": concept,
            "scenes": scenes_data,
            "production_metadata": {
                "director_notes": director_plan[:200],
                "continuity_report": continuity_report[:200],
                "agents_used": ["Director", "Story-Architect", "Scene-Writer", "Continuity-Supervisor", "Script-Editor"]
            }
        }
        
        return self.movie_script
    
    def save_script(self, filename: str = "movie_script.json"):
        """Save the movie script to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.movie_script, f, indent=2)
        print(f"\n💾 Script saved to: {filename}")
        return filename


# Example usage
if __name__ == "__main__":
    # Initialize the production system
    production = MovieProductionSystem(
        base_url="http://localhost:1234/v1",
        model_name="openai/kyle-jr-v2"
    )
    
    # Create a movie
    concept = "A lone astronaut discovers an ancient alien artifact on Mars that shows visions of Earth's future"
    
    movie_script = production.produce_movie(
        concept=concept,
        num_scenes=5
    )
    
    # Save to file
    output_file = production.save_script("mars_discovery_script.json")
    
    # Display final output
    print("\n" + "=" * 80)
    print("🎬 FINAL MOVIE SCRIPT")
    print("=" * 80)
    print(json.dumps(movie_script, indent=2))
    
    print("\n" + "=" * 80)
    print("✅ PRODUCTION COMPLETE!")
    print(f"📄 Script ready for video generation: {output_file}")
    print("=" * 80)
