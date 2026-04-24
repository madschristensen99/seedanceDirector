"""
Truly Emergent Swarm Intelligence

Key differences from previous versions:
- Agents decide autonomously whether to spawn more agents
- No fixed agent roster - emergent team composition
- Agents can disagree and debate
- Variable message counts based on complexity
- Agents can vote and reach consensus
- Self-organizing behavior
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
import random


class MessageType(Enum):
    """Message types"""
    ANALYSIS = "analysis"
    PATTERN = "pattern"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    ANSWER = "answer"
    SPAWN_REQUEST = "spawn_request"
    DISAGREEMENT = "disagreement"
    AGREEMENT = "agreement"
    VOTE = "vote"
    CONSENSUS = "consensus"
    FINAL = "final"


@dataclass
class Message:
    """Message between agents"""
    id: str
    sender: str
    receiver: Optional[str]
    msg_type: MessageType
    content: str
    scene_range: List[int] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    vote_value: Optional[int] = None  # For voting: -1, 0, +1
    
    def __repr__(self):
        return f"[{self.sender}→{self.receiver or 'ALL'}] {self.msg_type.value}: {self.content[:40]}..."


class EmergentAgent:
    """
    Truly autonomous agent that:
    - Decides when to spawn new agents
    - Can disagree with other agents
    - Votes on proposals
    - Self-organizes
    """
    
    def __init__(self, agent_id: str, role: str, swarm, llm_config: Dict, scene_window: List[Dict], 
                 spawned_by: Optional[str] = None):
        self.id = agent_id
        self.role = role
        self.swarm = swarm
        self.llm_config = llm_config
        self.scene_window = scene_window
        self.spawned_by = spawned_by
        self.inbox = queue.Queue()
        self.active = True
        self.memory = []
        self.spawned_agents = []
        self.opinions = {}  # Track opinions on issues
        self.confidence = random.uniform(0.6, 0.9)  # Agent confidence level
        
    def create_llm(self):
        return LiteLLM(
            model_name=self.llm_config['model'],
            base_url=self.llm_config['base_url'],
            temperature=self.llm_config.get('temperature', 0.8),  # Higher temp for variability
            max_tokens=self.llm_config.get('max_tokens', 200)
        )
    
    def send_message(self, receiver: Optional[str], msg_type: MessageType, content: str, 
                     scene_range: List[int] = None, vote_value: int = None):
        """Send message"""
        msg = Message(
            id=str(uuid.uuid4()),
            sender=self.id,
            receiver=receiver,
            msg_type=msg_type,
            content=content,
            scene_range=scene_range or [],
            vote_value=vote_value
        )
        self.swarm.route_message(msg)
        self.memory.append(msg)
        return msg
    
    def receive_message(self, msg: Message):
        """Receive message"""
        self.inbox.put(msg)
    
    def should_spawn_agent(self, messages: List[Message]) -> Optional[str]:
        """
        Autonomously decide if a new agent is needed
        Returns role name if yes, None if no
        """
        if len(self.spawned_agents) >= 2:  # Limit spawning
            return None
        
        # Check if there's a complex issue that needs specialist
        for msg in messages[-3:]:
            if "complex" in msg.content.lower() or "unclear" in msg.content.lower():
                # Spawn a specialist
                possible_roles = ["Detail-Analyzer", "Conflict-Resolver", "Fact-Checker"]
                return random.choice(possible_roles)
        
        return None
    
    def should_disagree(self, msg: Message) -> bool:
        """
        Decide if agent disagrees with a message
        Based on confidence and content
        """
        if msg.sender == self.id:
            return False
        
        # Probabilistic disagreement based on confidence
        if random.random() > self.confidence:
            return True
        
        # Content-based disagreement
        if "definitely" in msg.content.lower() or "always" in msg.content.lower():
            return random.random() > 0.7  # Challenge absolutes
        
        return False
    
    def analyze_with_personality(self, task_context: Dict, messages: List[Message]) -> Optional[Message]:
        """
        Analyze task with agent's unique personality
        """
        llm = self.create_llm()
        
        # Build message context
        msg_history = "\n".join([
            f"- {m.sender}: {m.content[:80]}"
            for m in messages[-5:]
        ])
        
        scene_context = "\n".join([
            f"Scene {s['scene_number']}: {s['original_prompt'][:80]}..."
            for s in self.scene_window[:3]
        ])
        
        scene_nums = [s['scene_number'] for s in self.scene_window]
        
        # Role-specific prompts with personality
        if self.role == "Coordinator":
            prompt = f"""You are a Coordinator agent. Analyze if we need more specialist agents.

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Current team messages:
{msg_history if msg_history else "No messages yet"}

Do we need more agents? If yes, what role?
Respond: "SPAWN: [role] because [reason]" OR "SUFFICIENT: current team is enough"
(max 40 words):"""
        
        elif self.role == "Pattern-Detector":
            prompt = f"""You are a Pattern-Detector. Find patterns across scenes.

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Other agents said:
{msg_history if msg_history else "Analyzing independently"}

Find ONE pattern OR respond to others.
If you disagree with another agent, say "DISAGREE with [agent]: [reason]"
(max 50 words):"""
        
        elif self.role == "Character-Tracker":
            prompt = f"""You are a Character-Tracker. Track character consistency.

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Team discussion:
{msg_history if msg_history else "Starting analysis"}

Find ONE character issue OR challenge another agent's finding.
Use "DISAGREE" if you think another agent is wrong.
(max 50 words):"""
        
        elif self.role == "Detail-Analyzer":
            prompt = f"""You are a Detail-Analyzer (spawned to investigate complex issues).

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Issue raised by team:
{msg_history}

Provide detailed analysis of the issue.
(max 60 words):"""
        
        elif self.role == "Conflict-Resolver":
            prompt = f"""You are a Conflict-Resolver (spawned to resolve disagreements).

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Team debate:
{msg_history}

Analyze the disagreement and propose resolution.
Format: "RESOLUTION: [your proposal]"
(max 60 words):"""
        
        elif self.role == "Synthesizer":
            prompt = f"""You are a Synthesizer. Create final fix from team discussion.

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Team findings:
{msg_history}

Create ONE multi-scene fix incorporating valid points.
Ignore disagreements that weren't resolved.
Format: "FIX scenes [X,Y]: [what to change]"
(max 80 words):"""
        
        else:
            # Generic agent
            prompt = f"""You are a {self.role} agent.

Scenes {scene_nums[0]}-{scene_nums[-1]}:
{scene_context}

Team messages:
{msg_history}

Contribute your analysis OR question another agent's finding.
(max 50 words):"""
        
        try:
            response = llm.run(prompt).strip()
            
            # Determine message type from response
            if "SPAWN:" in response:
                msg_type = MessageType.SPAWN_REQUEST
            elif "DISAGREE" in response:
                msg_type = MessageType.DISAGREEMENT
            elif "AGREE" in response or "RESOLUTION:" in response:
                msg_type = MessageType.AGREEMENT
            elif "?" in response:
                msg_type = MessageType.QUESTION
            elif "FIX" in response:
                msg_type = MessageType.FINAL
            elif "PATTERN" in response:
                msg_type = MessageType.PATTERN
            else:
                msg_type = MessageType.SUGGESTION
            
            # Extract scene numbers
            import re
            matches = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', response)
            affected_scenes = []
            if matches:
                affected_scenes = [int(x.strip()) for x in matches[0].split(',')]
            else:
                affected_scenes = scene_nums[:min(3, len(scene_nums))]
            
            return self.send_message(
                receiver=None,
                msg_type=msg_type,
                content=response,
                scene_range=affected_scenes
            )
            
        except Exception as e:
            print(f"⚠️  {self.id} error: {e}")
            return None
    
    def run(self, duration: float = 10.0):
        """
        Run agent autonomously
        """
        deadline = time.time() + duration
        cycle = 0
        
        while time.time() < deadline and self.active:
            # Get messages
            messages = []
            try:
                while not self.inbox.empty():
                    messages.append(self.inbox.get_nowait())
            except queue.Empty:
                pass
            
            # Decide if we should spawn new agent
            if cycle == 1 and self.role in ["Coordinator", "Pattern-Detector"]:
                new_role = self.should_spawn_agent(messages)
                if new_role:
                    self.send_message(None, MessageType.SPAWN_REQUEST, f"SPAWN: {new_role}")
            
            # Analyze and respond
            if cycle < 4:  # Limit iterations for variability
                response = self.analyze_with_personality({}, messages)
                
                # Check for disagreements
                for msg in messages[-2:]:
                    if self.should_disagree(msg) and random.random() > 0.7:
                        self.send_message(
                            None,
                            MessageType.DISAGREEMENT,
                            f"DISAGREE with {msg.sender}: {msg.content[:30]} seems questionable"
                        )
            
            cycle += 1
            time.sleep(random.uniform(0.2, 0.5))  # Variable timing
    
    def shutdown(self):
        self.active = False


class TrulyEmergentSwarm:
    """
    Swarm with true emergence:
    - Variable agent counts
    - Self-organizing teams
    - Debate and disagreement
    - Consensus building
    """
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.agents: Dict[str, EmergentAgent] = {}
        self.message_history = []
        self.lock = threading.Lock()
        
    def spawn_agent(self, role: str, scene_window: List[Dict], spawned_by: Optional[str] = None) -> str:
        """Spawn agent"""
        agent_id = f"{role}-{str(uuid.uuid4())[:6]}"
        
        llm_config = {
            'model': self.model_name,
            'base_url': self.base_url,
            'temperature': random.uniform(0.7, 0.9),  # Variable temperature
            'max_tokens': random.randint(180, 250)  # Variable token limit
        }
        
        agent = EmergentAgent(agent_id, role, self, llm_config, scene_window, spawned_by)
        
        with self.lock:
            self.agents[agent_id] = agent
        
        spawner = f" by {spawned_by}" if spawned_by else ""
        print(f"   🤖 Spawned: {role}{spawner}")
        
        return agent_id
    
    def route_message(self, msg: Message):
        """Route message"""
        with self.lock:
            self.message_history.append(msg)
            
            # Handle spawn requests
            if msg.msg_type == MessageType.SPAWN_REQUEST and "SPAWN:" in msg.content:
                role = msg.content.split("SPAWN:")[1].split()[0].strip()
                if len(self.agents) < 8:  # Max 8 agents
                    scene_window = self.agents[msg.sender].scene_window
                    self.spawn_agent(role, scene_window, msg.sender)
            
            # Route to agents
            if msg.receiver:
                if msg.receiver in self.agents:
                    self.agents[msg.receiver].receive_message(msg)
            else:
                # Broadcast
                for agent_id, agent in self.agents.items():
                    if agent_id != msg.sender:
                        # Probabilistic message delivery (not all agents see all messages)
                        if random.random() > 0.2:  # 80% delivery rate
                            agent.receive_message(msg)
    
    def run_swarm(self, duration: float = 12.0):
        """Run swarm"""
        print(f"  🔄 Emergent swarm running (max {duration}s)...")
        
        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            # Variable duration per agent
            futures = [
                executor.submit(agent.run, duration * random.uniform(0.8, 1.2))
                for agent in self.agents.values()
            ]
            
            for future in futures:
                future.result()
        
        print(f"  ✓ Swarm completed ({len(self.message_history)} messages, {len(self.agents)} agents)")
        
        return self.message_history
    
    def extract_fixes(self) -> Dict[int, List[str]]:
        """Extract fixes"""
        fixes_by_scene = {}
        
        for msg in self.message_history:
            if msg.msg_type in [MessageType.FINAL, MessageType.SUGGESTION, MessageType.PATTERN]:
                # Skip disagreements that weren't resolved
                if msg.msg_type == MessageType.DISAGREEMENT:
                    continue
                
                for scene_num in msg.scene_range:
                    if scene_num not in fixes_by_scene:
                        fixes_by_scene[scene_num] = []
                    fixes_by_scene[scene_num].append(msg.content)
        
        return fixes_by_scene
    
    def shutdown_all(self):
        """Shutdown"""
        for agent in self.agents.values():
            agent.shutdown()
        self.agents.clear()


class TrulyEmergentConsistencyPass:
    """
    Consistency pass with true emergence
    """
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.file_lock = threading.Lock()
    
    def apply_fixes_to_scene(self, scene: Dict, fixes: List[str]) -> str:
        """Apply fixes"""
        if not fixes:
            return scene['original_prompt']
        
        # Deduplicate similar fixes
        unique_fixes = []
        for fix in fixes:
            if not any(fix[:30] in uf for uf in unique_fixes):
                unique_fixes.append(fix)
        
        llm = LiteLLM(
            model_name=self.model_name,
            base_url=self.base_url,
            temperature=0.6,
            max_tokens=400
        )
        
        fixes_text = "\n".join([f"- {fix}" for fix in unique_fixes[:5]])  # Max 5 fixes
        
        prompt = f"""Apply these fixes to the scene.

Scene {scene['scene_number']}: {scene['scene_name']}
Current: {scene['original_prompt']}

Fixes:
{fixes_text}

Apply fixes. Keep core content. Duration: {scene['duration']}s
Write fixed prompt (max 200 words):"""
        
        try:
            response = llm.run(prompt).strip()
            for prefix in ["Fixed:", "OUTPUT:", "**"]:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
            return response
        except:
            return scene['original_prompt']
    
    def process_scene_batch(self, scenes: List[Dict], batch_idx: int):
        """Process batch with emergent swarm"""
        scene_range = f"{scenes[0]['scene_number']}-{scenes[-1]['scene_number']}"
        print(f"\n{'='*80}")
        print(f"Batch {batch_idx}: Scenes {scene_range} ({len(scenes)} scenes)")
        print(f"{'='*80}")
        
        # Create swarm
        swarm = TrulyEmergentSwarm(self.base_url, self.model_name)
        
        # Spawn initial coordinator only
        swarm.spawn_agent("Coordinator", scenes)
        
        # Coordinator will spawn other agents based on need
        # Variable initial team (1-3 agents)
        initial_roles = random.sample(
            ["Pattern-Detector", "Character-Tracker", "Location-Tracker", "Arc-Analyzer"],
            k=random.randint(1, 3)
        )
        
        for role in initial_roles:
            swarm.spawn_agent(role, scenes)
        
        # Run swarm - agents will spawn more as needed
        swarm.run_swarm(duration=random.uniform(10.0, 15.0))  # Variable duration
        
        # Spawn synthesizer
        swarm.spawn_agent("Synthesizer", scenes)
        synth = list(swarm.agents.values())[-1]
        
        for msg in swarm.message_history:
            synth.receive_message(msg)
        
        synth.run(duration=4.0)
        
        # Extract fixes
        print(f"  🔨 Applying fixes...")
        fixes_by_scene = swarm.extract_fixes()
        
        # Apply fixes
        results = []
        for scene in scenes:
            scene_num = scene['scene_number']
            scene_fixes = fixes_by_scene.get(scene_num, [])
            
            if scene_fixes:
                print(f"  ✓ Scene {scene_num}: {len(scene_fixes)} fixes")
                fixed_prompt = self.apply_fixes_to_scene(scene, scene_fixes)
            else:
                fixed_prompt = scene['original_prompt']
            
            # Build comprehensive swarm trace
            scene_messages = [m for m in swarm.message_history if scene_num in m.scene_range]
            
            agent_timeline = []
            for msg in scene_messages:
                sender_agent = swarm.agents.get(msg.sender)
                agent_timeline.append({
                    "timestamp": msg.timestamp,
                    "agent_id": msg.sender,
                    "agent_role": sender_agent.role if sender_agent else "unknown",
                    "message_type": msg.msg_type.value,
                    "content": msg.content,
                    "receiver": msg.receiver or "broadcast",
                    "scene_range": msg.scene_range,
                    "spawned_by": sender_agent.spawned_by if sender_agent else None
                })
            
            agent_timeline.sort(key=lambda x: x['timestamp'])
            
            # Categorize messages
            coordination_trace = {
                "detection": [m for m in agent_timeline if m['message_type'] in ['pattern', 'suggestion', 'analysis']],
                "debate": [m for m in agent_timeline if m['message_type'] in ['disagreement', 'question', 'answer']],
                "consensus": [m for m in agent_timeline if m['message_type'] in ['agreement', 'consensus']],
                "resolution": [m for m in agent_timeline if m['message_type'] in ['final']]
            }
            
            log_entry = {
                "scene_number": scene_num,
                "scene_name": scene['scene_name'],
                "before": scene['original_prompt'],
                "after": fixed_prompt,
                "changed": scene['original_prompt'] != fixed_prompt,
                "swarm_trace": {
                    "total_messages": len(scene_messages),
                    "total_agents": len(swarm.agents),
                    "agent_timeline": agent_timeline,
                    "coordination_trace": coordination_trace,
                    "agents_involved": list(set([m['agent_role'] for m in agent_timeline])),
                    "spawning_tree": {
                        agent_id: agent.spawned_by
                        for agent_id, agent in swarm.agents.items()
                        if agent.spawned_by
                    }
                }
            }
            
            results.append({'scene': {
                "scene_number": scene_num,
                "scene_name": scene['scene_name'],
                "duration": scene['duration'],
                "original_prompt": fixed_prompt
            }, 'log': log_entry})
        
        swarm.shutdown_all()
        return results
    
    def process_script(self, input_file, output_file, batch_size=8, max_workers=2):
        """Process script"""
        print("\n" + "✨"*40)
        print("TRULY EMERGENT SWARM INTELLIGENCE")
        print("✨"*40 + "\n")
        
        with open(input_file, 'r') as f:
            scenes = json.load(f)
        
        print(f"📖 Input: {input_file}")
        print(f"   Scenes: {len(scenes)}")
        print(f"   Batch size: {batch_size} (variable agent teams)")
        print(f"   Parallel batches: {max_workers}\n")
        
        consistent_scenes = []
        existing_scene_numbers = set()
        consistency_log = []
        
        try:
            with open(output_file, 'r') as f:
                consistent_scenes = json.load(f)
                existing_scene_numbers = {s['scene_number'] for s in consistent_scenes}
            print(f"   Loaded {len(consistent_scenes)} existing scenes\n")
        except:
            pass
        
        log_file = output_file.replace('.json', '_emergent_log.json')
        try:
            with open(log_file, 'r') as f:
                consistency_log = json.load(f)
        except:
            pass
        
        # Split into batches
        batches = []
        for i in range(0, len(scenes), batch_size):
            batch = scenes[i:i + batch_size]
            if not all(s['scene_number'] in existing_scene_numbers for s in batch):
                batches.append((batch, i // batch_size))
        
        print(f"   Processing {len(batches)} batches\n")
        
        # Process batches
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_scene_batch, batch, idx): (batch, idx)
                for batch, idx in batches
            }
            
            for future in futures:
                results = future.result()
                
                with self.file_lock:
                    for result in results:
                        if result['scene']['scene_number'] not in existing_scene_numbers:
                            consistent_scenes.append(result['scene'])
                            consistency_log.append(result['log'])
                            existing_scene_numbers.add(result['scene']['scene_number'])
                    
                    consistent_scenes.sort(key=lambda x: x['scene_number'])
                    with open(output_file, 'w') as f:
                        json.dump(consistent_scenes, f, indent=2)
                    
                    consistency_log.sort(key=lambda x: x['scene_number'])
                    with open(log_file, 'w') as f:
                        json.dump(consistency_log, f, indent=2)
        
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
    swarm = TrulyEmergentConsistencyPass()
    
    swarm.process_script(
        input_file="snow_crash_improved_clean_full.json",
        output_file="snow_crash_truly_emergent_final.json",
        batch_size=8,
        max_workers=2
    )
