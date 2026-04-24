"""
Continuous Emergent Swarm

No batches. No orchestration. Pure emergence.

How it works:
1. Seed agent spawns and analyzes ALL scenes
2. Seed agent spawns specialists based on what it finds
3. Specialists spawn more specialists as needed
4. Agents message each other, debate, change state
5. Swarm self-organizes until consensus
6. No central coordinator - pure peer-to-peer
"""

import json
import threading
import queue
import time
from swarms.utils.litellm_wrapper import LiteLLM
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import uuid
import random


class MessageType(Enum):
    ANALYSIS = "analysis"
    SPAWN_REQUEST = "spawn_request"
    QUESTION = "question"
    ANSWER = "answer"
    DISAGREEMENT = "disagreement"
    STATE_CHANGE = "state_change"
    CONSENSUS_PROPOSAL = "consensus_proposal"
    VOTE = "vote"
    FINAL_FIX = "final_fix"


class AgentState(Enum):
    """Agent internal states"""
    ANALYZING = "analyzing"
    WAITING = "waiting"
    DEBATING = "debating"
    CONVINCED = "convinced"
    SPAWNING = "spawning"
    FINALIZING = "finalizing"
    DONE = "done"


@dataclass
class Message:
    id: str
    sender: str
    receiver: Optional[str]  # None = broadcast
    msg_type: MessageType
    content: str
    scene_range: List[int] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self):
        return f"[{self.sender[:15]}→{self.receiver[:15] if self.receiver else 'ALL'}] {self.msg_type.value}: {self.content[:40]}"


class ContinuousAgent(threading.Thread):
    """
    Autonomous agent running in its own thread
    - Continuously processes messages
    - Spawns new agents when needed
    - Changes internal state based on debate
    - No external orchestration
    """
    
    def __init__(self, agent_id: str, role: str, swarm, scenes: List[Dict], 
                 spawned_by: Optional[str] = None, task: str = ""):
        super().__init__(daemon=True)
        self.id = agent_id
        self.role = role
        self.swarm = swarm
        self.scenes = scenes
        self.spawned_by = spawned_by
        self.task = task
        self.overall_goal = "Ensure scene-to-scene consistency across the entire script"
        
        self.inbox = queue.Queue()
        self.state = AgentState.ANALYZING
        self.active = True
        self.memory = []
        self.opinions = {}  # scene_num -> opinion
        self.confidence = random.uniform(0.6, 0.9)
        self.spawned_agents = []
        
        self.llm_config = {
            'model': swarm.model_name,
            'base_url': swarm.base_url,
            'temperature': random.uniform(0.7, 0.9),
            'max_tokens': random.randint(150, 250),
            'timeout': 30  # 30 second timeout
        }
    
    def get_swarm_status(self) -> str:
        """Get awareness of other agents in the swarm"""
        with self.swarm.lock:
            other_agents = [
                f"{a.role}({a.state.value})" 
                for aid, a in self.swarm.agents.items() 
                if aid != self.id
            ]
        return f"Swarm: {len(other_agents)+1} agents - " + ", ".join(other_agents[:5])
        
    def create_llm(self):
        return LiteLLM(**self.llm_config)
    
    def send_message(self, receiver: Optional[str], msg_type: MessageType, content: str, scene_range: List[int] = None):
        msg = Message(
            id=str(uuid.uuid4()),
            sender=self.id,
            receiver=receiver,
            msg_type=msg_type,
            content=content,
            scene_range=scene_range or []
        )
        self.swarm.route_message(msg)
        self.memory.append(msg)
        print(f"  📤 {self.role[:20]}: {msg_type.value} - {content[:50]}")
        return msg
    
    def change_state(self, new_state: AgentState, reason: str = ""):
        old_state = self.state
        self.state = new_state
        self.send_message(None, MessageType.STATE_CHANGE, 
                         f"State: {old_state.value} → {new_state.value}. {reason}")
        print(f"  🔄 {self.role[:20]} state: {old_state.value} → {new_state.value}")
    
    def should_spawn_agent(self, messages: List[Message]) -> Optional[str]:
        """Decide if we need a specialist - be PROACTIVE"""
        if len(self.spawned_agents) >= 3:
            return None
        
        # Check recent messages for complexity
        for msg in messages[-5:]:
            content_lower = msg.content.lower()
            
            # Spawn specialists for specific issues
            if "character" in content_lower:
                return "Character-Specialist"
            if "lighting" in content_lower or "visual" in content_lower:
                return "Lighting-Expert"
            if "action" in content_lower or "movement" in content_lower:
                return "Action-Analyzer"
            if "disagree" in content_lower:
                return "Conflict-Resolver"
            if "complex" in content_lower or "unclear" in content_lower:
                return "Detail-Analyzer"
        
        # Proactively spawn if we see multiple issues
        if len(messages) >= 3 and random.random() > 0.6:
            return random.choice(["Detail-Analyzer", "Fact-Checker", "Visual-Analyst"])
        
        return None
    
    def analyze_scenes(self) -> Optional[Message]:
        """Analyze assigned scenes"""
        llm = self.create_llm()
        
        # Get multiple scenes to analyze
        sample_scenes = self.scenes[:min(8, len(self.scenes))]
        scene_context = "\n".join([
            f"Scene {s['scene_number']} ({s['scene_name']}): {s['original_prompt'][:120]}"
            for s in sample_scenes
        ])
        
        scene_nums = [s['scene_number'] for s in self.scenes]
        
        # Get swarm awareness
        swarm_status = self.get_swarm_status()
        
        # Role-specific analysis
        if self.role == "Seed-Analyzer":
            prompt = f"""You are the Seed-Analyzer in a multi-agent swarm.

Overall Goal: {self.overall_goal}
{swarm_status}
Your Task: {self.task if self.task else 'Initial analysis'}

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Look for:
- Character descriptions changing
- Lighting inconsistencies in same location
- Props appearing/disappearing
- Action flow breaks

You MUST find at least ONE issue. If scenes look complex, SPAWN a specialist.

Respond:
- "ISSUE in scenes [X,Y,Z]: [specific problem]" OR
- "SPAWN: [Character-Specialist/Lighting-Expert/Action-Analyzer] to investigate [what]"

(max 60 words):"""
        
        elif self.role == "Pattern-Detector":
            prompt = f"""You are a Pattern-Detector. Find patterns and anomalies.

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Find:
- Repeated elements that should match
- Patterns that break
- Visual style inconsistencies

Be CRITICAL. Find at least ONE pattern issue or spawn help.

Respond:
- "PATTERN ISSUE in scenes [X,Y]: [problem]" OR
- "SPAWN: Visual-Analyst to check [what]"

(max 60 words):"""
        
        elif self.role == "Character-Tracker":
            prompt = f"""You are a Character-Tracker. Track character consistency.

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Check:
- Character clothing/appearance consistency
- Props characters carry
- Character positions/movements

Find at least ONE character issue or ask for help.

Respond:
- "CHARACTER ISSUE in scenes [X,Y]: [character] [problem]" OR
- "SPAWN: Character-Specialist to analyze [character]"

(max 60 words):"""
        
        else:
            # Specialist agents
            prompt = f"""You are a {self.role} specialist.

Task: {self.task}

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Provide detailed analysis of the issue you were spawned to investigate.

Respond:
- "FINDING in scenes [X,Y]: [detailed finding]"

(max 70 words):"""
        
        try:
            # Use global LLM lock - only one agent can call LLM at a time
            with self.swarm.llm_lock:
                response = llm.run(prompt).strip()
            
            # Determine message type
            if "SPAWN:" in response:
                msg_type = MessageType.SPAWN_REQUEST
            elif "QUESTION:" in response:
                msg_type = MessageType.QUESTION
            elif "ISSUE" in response:
                msg_type = MessageType.ANALYSIS
            else:
                msg_type = MessageType.ANALYSIS
            
            # Extract scene numbers
            import re
            matches = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', response)
            affected_scenes = []
            if matches:
                affected_scenes = [int(x.strip()) for x in matches[0].split(',')]
            else:
                affected_scenes = scene_nums[:3]
            
            return self.send_message(None, msg_type, response, affected_scenes)
            
        except Exception as e:
            print(f"  ⚠️ {self.role} analyze error: {e}")
            return None
    
    def respond_to_message(self, msg: Message) -> Optional[Message]:
        """Respond to a message from another agent"""
        llm = self.create_llm()
        
        prompt = f"""You are a {self.role} agent. Another agent sent you a message.

Message from {msg.sender}:
{msg.content}

Your current opinion: {self.opinions.get(msg.scene_range[0] if msg.scene_range else 0, 'none')}

Respond with ONE of:
- "AGREE: [why]"
- "DISAGREE: [why]"
- "ANSWER: [response]"
- "SPAWN: [role] to help resolve this"

(max 40 words):"""
        
        try:
            # Use global LLM lock - only one agent can call LLM at a time
            with self.swarm.llm_lock:
                response = llm.run(prompt).strip()
            
            if "AGREE" in response:
                msg_type = MessageType.ANSWER
                self.change_state(AgentState.CONVINCED, "Agreed with peer")
            elif "DISAGREE" in response:
                msg_type = MessageType.DISAGREEMENT
                self.change_state(AgentState.DEBATING, "Disagreement detected")
            elif "SPAWN" in response:
                msg_type = MessageType.SPAWN_REQUEST
            else:
                msg_type = MessageType.ANSWER
            
            return self.send_message(msg.sender, msg_type, response, msg.scene_range)
            
        except Exception as e:
            print(f"  ⚠️ {self.role} response error: {e}")
            return None
    
    def run(self):
        """Main agent loop - runs continuously until done"""
        print(f"  🤖 {self.role} started (analyzing scenes {self.scenes[0]['scene_number']}-{self.scenes[-1]['scene_number']})")
        
        cycle = 0
        last_activity = time.time()
        max_cycles = 15  # Give agents more time to collaborate
        
        while self.active and cycle < max_cycles:
            cycle += 1
            
            # If we're near max cycles and still waiting, finalize
            if cycle >= max_cycles - 2 and self.state == AgentState.WAITING:
                self.change_state(AgentState.FINALIZING, "Max cycles reached")
            
            # Get messages
            messages = []
            try:
                while not self.inbox.empty():
                    msg = self.inbox.get_nowait()
                    messages.append(msg)
            except queue.Empty:
                pass
            
            # Update last activity only if we got messages
            if messages:
                last_activity = time.time()
            
            # State machine
            if self.state == AgentState.ANALYZING:
                # Analyze scenes
                result = self.analyze_scenes()
                if result and result.msg_type == MessageType.SPAWN_REQUEST:
                    self.change_state(AgentState.SPAWNING)
                elif result:
                    self.change_state(AgentState.WAITING, "Waiting for peer feedback")
            
            elif self.state == AgentState.WAITING:
                # Process incoming messages
                if messages:
                    print(f"  📬 {self.role[:20]} processing {len(messages)} messages")
                    # Only respond to first message to avoid LLM overload
                    msg = messages[0]
                    if msg.msg_type == MessageType.ANALYSIS:
                        # React to peer's analysis
                        print(f"  💬 {self.role[:20]} responding to {msg.sender[:20]}...")
                        self.respond_to_message(msg)
                    elif msg.msg_type == MessageType.QUESTION:
                        print(f"  💬 {self.role[:20]} answering {msg.sender[:20]}...")
                        self.respond_to_message(msg)
                    elif msg.msg_type == MessageType.DISAGREEMENT:
                        self.change_state(AgentState.DEBATING)
                        self.respond_to_message(msg)
                    
                    # After processing, check if we should move forward
                    if len(self.memory) >= 3:  # Got enough interaction
                        self.change_state(AgentState.CONVINCED, f"Processed {len(messages)} messages")
                
                # Check if we should spawn specialist
                specialist = self.should_spawn_agent(messages)
                if specialist:
                    self.send_message(None, MessageType.SPAWN_REQUEST, f"SPAWN: {specialist}")
                    self.change_state(AgentState.SPAWNING)
                
                # Don't timeout too quickly - give peers time to respond
                if time.time() - last_activity > 8.0:  # Increased from 5.0
                    self.change_state(AgentState.FINALIZING, "Timeout - proceeding")
            
            elif self.state == AgentState.DEBATING:
                # Engage in debate
                for msg in messages:
                    if msg.msg_type in [MessageType.DISAGREEMENT, MessageType.QUESTION]:
                        self.respond_to_message(msg)
                
                # Check for consensus
                agreements = [m for m in messages if "AGREE" in m.content]
                if len(agreements) >= 2:
                    self.change_state(AgentState.CONVINCED, "Consensus reached")
            
            elif self.state == AgentState.CONVINCED:
                # Finalize findings
                self.change_state(AgentState.FINALIZING)
            
            elif self.state == AgentState.FINALIZING:
                # Create final fix
                self.send_message(None, MessageType.FINAL_FIX, 
                                f"FIX scenes {[s['scene_number'] for s in self.scenes[:3]]}: Apply consensus")
                self.change_state(AgentState.DONE)
            
            elif self.state == AgentState.DONE:
                self.active = False
                break
            
            time.sleep(random.uniform(0.3, 0.8))
        
        print(f"  ✓ {self.role} finished (state: {self.state.value})")
    
    def receive_message(self, msg: Message):
        self.inbox.put(msg)


class ContinuousSwarm:
    """
    Continuous swarm - no batches, pure emergence
    """
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.agents: Dict[str, ContinuousAgent] = {}
        self.message_history = []
        self.lock = threading.Lock()
        self.llm_lock = threading.Lock()  # Global LLM lock - only one agent can call LLM at a time
        
    def spawn_agent(self, role: str, scenes: List[Dict], spawned_by: Optional[str] = None, task: str = "") -> str:
        """Spawn a new agent"""
        agent_id = f"{role}-{str(uuid.uuid4())[:6]}"
        
        agent = ContinuousAgent(agent_id, role, self, scenes, spawned_by, task)
        
        with self.lock:
            self.agents[agent_id] = agent
        
        # Start agent thread
        agent.start()
        
        if spawned_by:
            parent = self.agents.get(spawned_by)
            if parent:
                parent.spawned_agents.append(agent_id)
        
        return agent_id
    
    def route_message(self, msg: Message):
        """Route message to agents"""
        with self.lock:
            self.message_history.append(msg)
            
            # Handle spawn requests
            if msg.msg_type == MessageType.SPAWN_REQUEST and "SPAWN:" in msg.content:
                parts = msg.content.split("SPAWN:")[1].strip().split(" to ")
                role = parts[0].strip()
                task = parts[1] if len(parts) > 1 else ""
                
                if len(self.agents) < 12:  # Max 12 agents
                    sender_agent = self.agents.get(msg.sender)
                    if sender_agent:
                        new_agent_id = self.spawn_agent(role, sender_agent.scenes, msg.sender, task)
                        
                        # Send context message to new specialist
                        context_msg = Message(
                            id=str(uuid.uuid4()),
                            sender=msg.sender,
                            receiver=new_agent_id,
                            msg_type=MessageType.QUESTION,
                            content=f"You were spawned to: {task}. Context: {msg.content}",
                            scene_range=msg.scene_range,
                            timestamp=time.time()
                        )
                        self.message_history.append(context_msg)
                        
                        # Deliver message to specialist
                        if new_agent_id in self.agents:
                            self.agents[new_agent_id].receive_message(context_msg)
                            print(f"  📨 {msg.sender[:20]} → {role}: {task[:40]}")
            
            # Route to recipient or broadcast
            if msg.receiver:
                if msg.receiver in self.agents:
                    self.agents[msg.receiver].receive_message(msg)
            else:
                # Broadcast to all except sender
                for agent_id, agent in self.agents.items():
                    if agent_id != msg.sender and random.random() > 0.3:  # 70% delivery
                        agent.receive_message(msg)
    
    def run_until_complete(self, max_duration: float = 60.0):
        """Run swarm until all agents are done or timeout"""
        print(f"\n🌊 Continuous swarm running (max {max_duration}s)...")
        start = time.time()
        
        while time.time() - start < max_duration:
            with self.lock:
                active_agents = [a for a in self.agents.values() if a.active]
            
            if not active_agents:
                print(f"✓ All agents completed")
                break
            
            print(f"  Active: {len(active_agents)} agents, {len(self.message_history)} messages")
            time.sleep(2.0)
        
        # Wait for all threads
        for agent in self.agents.values():
            agent.active = False
            if agent.is_alive():
                agent.join(timeout=1.0)
        
        print(f"✓ Swarm completed: {len(self.agents)} total agents, {len(self.message_history)} messages")
        
        return self.message_history
    
    def extract_fixes(self) -> Dict[int, List[str]]:
        """Extract fixes from messages"""
        fixes = {}
        for msg in self.message_history:
            if msg.msg_type == MessageType.FINAL_FIX:
                for scene_num in msg.scene_range:
                    if scene_num not in fixes:
                        fixes[scene_num] = []
                    fixes[scene_num].append(msg.content)
        return fixes


def process_with_continuous_swarm(input_file: str, output_file: str, scene_range: tuple = (1, 100)):
    """
    Process scenes with continuous emergent swarm
    """
    print("\n" + "🌊"*40)
    print("CONTINUOUS EMERGENT SWARM")
    print("🌊"*40)
    
    # Load scenes
    with open(input_file, 'r') as f:
        all_scenes = json.load(f)
    
    scenes = all_scenes[scene_range[0]-1:scene_range[1]]
    
    print(f"\n📖 Processing scenes {scene_range[0]}-{scene_range[1]} ({len(scenes)} scenes)")
    print(f"   No batches - pure continuous emergence\n")
    
    # Create swarm
    swarm = ContinuousSwarm()
    
    # Spawn seed agent
    print("🌱 Spawning seed agent...")
    seed_id = swarm.spawn_agent("Seed-Analyzer", scenes, task="Analyze all scenes for issues")
    time.sleep(0.5)  # Stagger agent starts
    
    # Spawn initial peer agents so seed has collaborators
    print("🌱 Spawning initial peer agents...")
    swarm.spawn_agent("Pattern-Detector", scenes, task="Find patterns across scenes")
    time.sleep(0.5)  # Stagger agent starts
    swarm.spawn_agent("Character-Tracker", scenes, task="Track character consistency")
    
    # Let swarm self-organize
    swarm.run_until_complete(max_duration=45.0)
    
    # Extract fixes
    fixes = swarm.extract_fixes()
    
    print(f"\n📊 Results:")
    print(f"   Total agents spawned: {len(swarm.agents)}")
    print(f"   Total messages: {len(swarm.message_history)}")
    print(f"   Scenes with fixes: {len(fixes)}")
    
    # Save results
    results = []
    for scene in scenes:
        scene_fixes = fixes.get(scene['scene_number'], [])
        results.append({
            "scene_number": scene['scene_number'],
            "scene_name": scene['scene_name'],
            "fixes": scene_fixes,
            "swarm_trace": {
                "messages": [
                    {
                        "sender": m.sender,
                        "type": m.msg_type.value,
                        "content": m.content,
                        "timestamp": m.timestamp
                    }
                    for m in swarm.message_history
                    if scene['scene_number'] in m.scene_range
                ]
            }
        })
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Output: {output_file}\n")


if __name__ == "__main__":
    # Test on first 50 scenes
    process_with_continuous_swarm(
        input_file="snow_crash_improved_clean_full.json",
        output_file="snow_crash_continuous_test.json",
        scene_range=(1, 50)
    )
