"""
Emergent Multi-Agent Swarm System

True swarm intelligence with:
- Asynchronous message passing between agents
- Dynamic agent spawning (agents create sub-agents)
- Collaborative debate and consensus
- No central orchestrator - pure emergence
- Self-organizing agent teams
"""

import json
import threading
import queue
import time
from swarms.utils.litellm_wrapper import LiteLLM
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class MessageType(Enum):
    """Types of messages agents can send"""
    ANALYSIS = "analysis"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    ANSWER = "answer"
    SPAWN_REQUEST = "spawn_request"
    CONSENSUS = "consensus"
    VOTE = "vote"
    FINAL = "final"


@dataclass
class Message:
    """Message passed between agents"""
    id: str
    sender: str
    receiver: Optional[str]  # None = broadcast to all
    msg_type: MessageType
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self):
        return f"[{self.sender}→{self.receiver or 'ALL'}] {self.msg_type.value}: {self.content[:50]}..."


class Agent:
    """
    Autonomous agent that can:
    - Send/receive messages
    - Spawn new agents
    - Collaborate with other agents
    - Make decisions independently
    """
    
    def __init__(self, agent_id: str, role: str, swarm, llm_config: Dict[str, Any]):
        self.id = agent_id
        self.role = role
        self.swarm = swarm
        self.llm_config = llm_config
        self.inbox = queue.Queue()
        self.active = True
        self.memory = []  # Conversation history
        self.spawned_agents = []
        
    def create_llm(self):
        """Create LLM instance for this agent"""
        return LiteLLM(
            model_name=self.llm_config['model'],
            base_url=self.llm_config['base_url'],
            temperature=self.llm_config.get('temperature', 0.7),
            max_tokens=self.llm_config.get('max_tokens', 200)
        )
    
    def send_message(self, receiver: Optional[str], msg_type: MessageType, content: str, context: Dict = None):
        """Send message to another agent or broadcast"""
        msg = Message(
            id=str(uuid.uuid4()),
            sender=self.id,
            receiver=receiver,
            msg_type=msg_type,
            content=content,
            context=context or {}
        )
        self.swarm.route_message(msg)
        self.memory.append(f"SENT: {msg}")
        return msg
    
    def receive_message(self, msg: Message):
        """Receive a message"""
        self.inbox.put(msg)
        self.memory.append(f"RECV: {msg}")
    
    def spawn_agent(self, role: str, context: Dict) -> str:
        """Spawn a new sub-agent"""
        new_agent_id = self.swarm.spawn_agent(role, parent_id=self.id, context=context)
        self.spawned_agents.append(new_agent_id)
        return new_agent_id
    
    def process_messages(self, timeout: float = 2.0):
        """Process all messages in inbox"""
        messages = []
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            try:
                msg = self.inbox.get(timeout=0.1)
                messages.append(msg)
            except queue.Empty:
                if messages:  # Got some messages, that's enough
                    break
                continue
        
        return messages
    
    def analyze_and_respond(self, task_context: Dict, messages: List[Message]) -> Optional[Message]:
        """
        Analyze task and messages, then respond
        This is where the agent's intelligence lives
        """
        llm = self.create_llm()
        
        # Build context from messages
        msg_history = "\n".join([
            f"- {m.sender} ({m.msg_type.value}): {m.content}"
            for m in messages[-5:]  # Last 5 messages
        ])
        
        # Role-specific prompts
        if self.role == "Meta-Coordinator":
            prompt = f"""You are a Meta-Coordinator agent. Analyze the task and decide which specialist agents to spawn.

Task: {task_context.get('task_description', 'Unknown')}
Current scene: {task_context.get('scene_name', 'Unknown')}

Recent messages from other agents:
{msg_history if msg_history else "No messages yet"}

Decide:
1. What specialist agents are needed? (Continuity-Checker, Lighting-Matcher, Action-Flow, Character-Analyzer, etc.)
2. What questions should they investigate?

Respond with: "SPAWN: [agent-role] to [investigate what]" OR "ANALYSIS: [your analysis]"
Keep it under 50 words:"""
        
        elif self.role == "Continuity-Checker":
            prompt = f"""You are a Continuity-Checker agent. Find character/prop inconsistencies.

Task: {task_context.get('task_description', 'Unknown')}
Previous scene: {task_context.get('prev_scene', 'None')[:150]}
Current scene: {task_context.get('current_scene', 'Unknown')[:150]}

Messages from other agents:
{msg_history if msg_history else "No messages yet"}

Find ONE inconsistency OR respond to other agents' questions.
Format: "ISSUE: [problem]" OR "ANSWER: [response]" OR "AGREE: [with agent]"
Keep under 40 words:"""
        
        elif self.role == "Lighting-Matcher":
            prompt = f"""You are a Lighting-Matcher agent. Ensure lighting continuity between scenes.

Task: {task_context.get('task_description', 'Unknown')}
Previous scene: {task_context.get('prev_scene', 'None')[:150]}
Current scene: {task_context.get('current_scene', 'Unknown')[:150]}

Messages from other agents:
{msg_history if msg_history else "No messages yet"}

Find ONE lighting issue OR respond to other agents.
Format: "ISSUE: [problem]" OR "ANSWER: [response]" OR "AGREE: [with agent]"
Keep under 40 words:"""
        
        elif self.role == "Action-Flow":
            prompt = f"""You are an Action-Flow agent. Ensure actions connect logically between scenes.

Task: {task_context.get('task_description', 'Unknown')}
Previous scene: {task_context.get('prev_scene', 'None')[:150]}
Current scene: {task_context.get('current_scene', 'Unknown')[:150]}

Messages from other agents:
{msg_history if msg_history else "No messages yet"}

Find ONE action flow issue OR respond to other agents.
Format: "ISSUE: [problem]" OR "ANSWER: [response]" OR "AGREE: [with agent]"
Keep under 40 words:"""
        
        elif self.role == "Synthesizer":
            prompt = f"""You are a Synthesizer agent. Combine all agent suggestions into one fix.

Current scene prompt: {task_context.get('current_scene', 'Unknown')[:200]}

Agent suggestions:
{msg_history}

Create ONE consistency-fixed prompt incorporating all valid suggestions.
Keep the core scene intact, only fix consistency issues.
Output the fixed prompt (max 150 words):"""
        
        else:
            # Generic agent
            prompt = f"""You are a {self.role} agent.

Task: {task_context.get('task_description', 'Unknown')}
Context: {task_context.get('current_scene', 'Unknown')[:150]}

Messages:
{msg_history if msg_history else "No messages yet"}

Respond with your analysis or answer (max 40 words):"""
        
        try:
            response = llm.run(prompt).strip()
            
            # Parse response to determine message type
            if response.startswith("SPAWN:"):
                msg_type = MessageType.SPAWN_REQUEST
            elif response.startswith("ISSUE:"):
                msg_type = MessageType.SUGGESTION
            elif response.startswith("ANSWER:"):
                msg_type = MessageType.ANSWER
            elif response.startswith("AGREE:"):
                msg_type = MessageType.CONSENSUS
            elif response.startswith("ANALYSIS:"):
                msg_type = MessageType.ANALYSIS
            else:
                msg_type = MessageType.SUGGESTION
            
            return self.send_message(
                receiver=None,  # Broadcast
                msg_type=msg_type,
                content=response,
                context=task_context
            )
            
        except Exception as e:
            print(f"⚠️  Agent {self.id} error: {e}")
            return None
    
    def run(self, task_context: Dict, duration: float = 5.0):
        """
        Run the agent for a duration, processing messages and responding
        """
        deadline = time.time() + duration
        
        while time.time() < deadline and self.active:
            # Process incoming messages
            messages = self.process_messages(timeout=0.5)
            
            if messages or time.time() < deadline - 3:  # Respond if got messages or early in cycle
                response = self.analyze_and_respond(task_context, messages)
                
                # Check if we should spawn new agents
                if response and response.msg_type == MessageType.SPAWN_REQUEST:
                    # Parse spawn request
                    content = response.content.replace("SPAWN:", "").strip()
                    if " to " in content:
                        role = content.split(" to ")[0].strip()
                        self.spawn_agent(role, task_context)
            
            time.sleep(0.2)  # Small delay between cycles
    
    def shutdown(self):
        """Shutdown the agent"""
        self.active = False


class EmergentSwarm:
    """
    Swarm coordinator that manages:
    - Agent lifecycle
    - Message routing
    - Consensus building
    - Result synthesis
    """
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.agents: Dict[str, Agent] = {}
        self.message_bus = queue.Queue()
        self.message_history = []
        self.lock = threading.Lock()
        
    def spawn_agent(self, role: str, parent_id: Optional[str] = None, context: Dict = None) -> str:
        """Spawn a new agent"""
        agent_id = f"{role}-{str(uuid.uuid4())[:8]}"
        
        llm_config = {
            'model': self.model_name,
            'base_url': self.base_url,
            'temperature': 0.7,
            'max_tokens': 200
        }
        
        agent = Agent(agent_id, role, self, llm_config)
        
        with self.lock:
            self.agents[agent_id] = agent
        
        print(f"   🤖 Spawned: {role} (id: {agent_id})" + (f" by {parent_id}" if parent_id else ""))
        
        return agent_id
    
    def route_message(self, msg: Message):
        """Route message to appropriate agents"""
        with self.lock:
            self.message_history.append(msg)
            
            if msg.receiver:
                # Direct message
                if msg.receiver in self.agents:
                    self.agents[msg.receiver].receive_message(msg)
            else:
                # Broadcast to all agents except sender
                for agent_id, agent in self.agents.items():
                    if agent_id != msg.sender:
                        agent.receive_message(msg)
    
    def run_swarm(self, task_context: Dict, duration: float = 8.0) -> List[Message]:
        """
        Run the swarm for a duration
        Agents will communicate and collaborate
        """
        print(f"  🔄 Swarm running for {duration}s...")
        
        # Run all agents in parallel
        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            futures = [
                executor.submit(agent.run, task_context, duration)
                for agent in self.agents.values()
            ]
            
            # Wait for all agents to finish
            for future in futures:
                future.result()
        
        print(f"  ✓ Swarm completed ({len(self.message_history)} messages exchanged)")
        
        return self.message_history
    
    def build_consensus(self) -> str:
        """
        Build consensus from all agent messages
        Returns the final agreed-upon solution
        """
        # Spawn a synthesizer agent to combine all suggestions
        synth_id = self.spawn_agent("Synthesizer")
        synth_agent = self.agents[synth_id]
        
        # Give synthesizer all messages
        for msg in self.message_history:
            synth_agent.receive_message(msg)
        
        # Get synthesis
        task_context = self.message_history[0].context if self.message_history else {}
        messages = synth_agent.process_messages(timeout=1.0)
        
        response = synth_agent.analyze_and_respond(task_context, messages)
        
        if response:
            # Extract the fixed prompt
            content = response.content
            # Clean up
            for prefix in ["SYNTHESIS:", "FIXED:", "OUTPUT:"]:
                if content.startswith(prefix):
                    content = content[len(prefix):].strip()
            return content
        
        return task_context.get('current_scene', '')
    
    def shutdown_all(self):
        """Shutdown all agents"""
        for agent in self.agents.values():
            agent.shutdown()
        self.agents.clear()
        self.message_history.clear()


class EmergentConsistencyPass:
    """
    Consistency pass using emergent swarm intelligence
    """
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.file_lock = threading.Lock()
    
    def process_scene(self, prev_scene, current_scene, next_scene):
        """
        Process a single scene with emergent swarm
        """
        print(f"\n{'='*80}")
        print(f"Scene {current_scene['scene_number']}: {current_scene['scene_name']}")
        print(f"{'='*80}")
        
        # Create a new swarm for this scene
        swarm = EmergentSwarm(self.base_url, self.model_name)
        
        # Build task context
        task_context = {
            'task_description': 'Check consistency between scenes',
            'scene_name': current_scene['scene_name'],
            'scene_number': current_scene['scene_number'],
            'current_scene': current_scene['original_prompt'],
            'prev_scene': prev_scene['original_prompt'] if prev_scene else 'None',
            'next_scene': next_scene['original_prompt'] if next_scene else 'None',
            'duration': current_scene['duration']
        }
        
        # Spawn initial meta-coordinator
        meta_id = swarm.spawn_agent("Meta-Coordinator")
        
        # Meta-coordinator will spawn specialist agents
        meta_agent = swarm.agents[meta_id]
        meta_response = meta_agent.analyze_and_respond(task_context, [])
        
        # Parse spawn requests and spawn agents
        if meta_response and "SPAWN:" in meta_response.content:
            # Spawn the suggested agents
            for role in ["Continuity-Checker", "Lighting-Matcher", "Action-Flow"]:
                if role in meta_response.content or len(swarm.agents) < 4:
                    swarm.spawn_agent(role)
        
        # Run the swarm - agents will communicate and collaborate
        swarm.run_swarm(task_context, duration=6.0)
        
        # Build consensus from all agent messages
        print(f"  🔨 Building consensus...")
        fixed_prompt = swarm.build_consensus()
        
        print(f"  ✓ Consensus reached")
        
        # Shutdown swarm
        swarm.shutdown_all()
        
        return fixed_prompt
    
    def process_script(self, input_file, output_file, max_workers=4):
        """
        Process entire script with emergent swarm
        """
        print("\n" + "🤖"*40)
        print("EMERGENT SWARM CONSISTENCY PASS")
        print("🤖"*40 + "\n")
        
        # Load scenes
        with open(input_file, 'r') as f:
            scenes = json.load(f)
        
        print(f"📖 Input: {input_file}")
        print(f"   Scenes: {len(scenes)} total\n")
        
        # Load existing progress
        consistent_scenes = []
        existing_scene_numbers = set()
        consistency_log = []
        
        try:
            with open(output_file, 'r') as f:
                consistent_scenes = json.load(f)
                existing_scene_numbers = {s['scene_number'] for s in consistent_scenes}
            print(f"   Loaded {len(consistent_scenes)} existing scenes")
            print(f"   Will skip already completed scenes\n")
        except:
            pass
        
        log_file = output_file.replace('.json', '_emergent_log.json')
        try:
            with open(log_file, 'r') as f:
                consistency_log = json.load(f)
        except:
            pass
        
        def process_scene_with_context(idx):
            """Process a single scene"""
            current = scenes[idx]
            
            if current['scene_number'] in existing_scene_numbers:
                print(f"Scene {current['scene_number']}: {current['scene_name']} - Already done, skipping...")
                return None
            
            prev_scene = scenes[idx - 1] if idx > 0 else None
            next_scene = scenes[idx + 1] if idx < len(scenes) - 1 else None
            
            original_prompt = current['original_prompt']
            fixed_prompt = self.process_scene(prev_scene, current, next_scene)
            
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
            scenes_to_process = [i for i, s in enumerate(scenes) if s['scene_number'] not in existing_scene_numbers]
            
            futures = {executor.submit(process_scene_with_context, idx): idx for idx in scenes_to_process}
            
            for future in futures:
                result = future.result()
                if result is None:
                    continue
                
                with self.file_lock:
                    consistent_scenes.append(result['scene'])
                    consistency_log.append(result['log'])
                    
                    # Save incrementally
                    consistent_scenes.sort(key=lambda x: x['scene_number'])
                    with open(output_file, 'w') as f:
                        json.dump(consistent_scenes, f, indent=2)
                    
                    consistency_log.sort(key=lambda x: x['scene_number'])
                    with open(log_file, 'w') as f:
                        json.dump(consistency_log, f, indent=2)
        
        # Final save
        consistent_scenes.sort(key=lambda x: x['scene_number'])
        with open(output_file, 'w') as f:
            json.dump(consistent_scenes, f, indent=2)
        
        print(f"\n{'='*80}")
        print("✅ EMERGENT SWARM COMPLETE!")
        print(f"{'='*80}")
        print(f"\n💾 Output: {output_file}")
        print(f"   Log: {log_file}\n")
        
        return consistent_scenes


if __name__ == "__main__":
    swarm = EmergentConsistencyPass()
    
    swarm.process_script(
        input_file="snow_crash_improved_clean_full.json",
        output_file="snow_crash_emergent_final.json",
        max_workers=2  # Process 2 scenes at once (each scene has its own swarm)
    )
