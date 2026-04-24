"""
Wide-Context Emergent Swarm

Agents operate across MULTIPLE scenes simultaneously:
- Each agent sees a window of 5-10 scenes
- Agents identify patterns across scenes
- Agents collaborate on multi-scene consistency
- True emergent behavior across the entire script
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
    PATTERN = "pattern"  # Pattern detected across scenes
    SUGGESTION = "suggestion"
    QUESTION = "question"
    ANSWER = "answer"
    SPAWN_REQUEST = "spawn_request"
    CONSENSUS = "consensus"
    MULTI_SCENE_FIX = "multi_scene_fix"  # Fix spanning multiple scenes
    FINAL = "final"


@dataclass
class Message:
    """Message passed between agents"""
    id: str
    sender: str
    receiver: Optional[str]
    msg_type: MessageType
    content: str
    scene_range: List[int] = field(default_factory=list)  # Which scenes this affects
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self):
        scenes = f"scenes {self.scene_range[0]}-{self.scene_range[-1]}" if self.scene_range else "no scenes"
        return f"[{self.sender}→{self.receiver or 'ALL'}] {self.msg_type.value} ({scenes}): {self.content[:50]}..."


class WideContextAgent:
    """
    Agent that operates across multiple scenes
    Can see patterns and inconsistencies across a window of scenes
    """
    
    def __init__(self, agent_id: str, role: str, swarm, llm_config: Dict[str, Any], scene_window: List[Dict]):
        self.id = agent_id
        self.role = role
        self.swarm = swarm
        self.llm_config = llm_config
        self.scene_window = scene_window  # List of scenes this agent can see
        self.inbox = queue.Queue()
        self.active = True
        self.memory = []
        self.spawned_agents = []
        self.findings = {}  # Scene number -> findings
        
    def create_llm(self):
        """Create LLM instance"""
        return LiteLLM(
            model_name=self.llm_config['model'],
            base_url=self.llm_config['base_url'],
            temperature=self.llm_config.get('temperature', 0.7),
            max_tokens=self.llm_config.get('max_tokens', 250)
        )
    
    def send_message(self, receiver: Optional[str], msg_type: MessageType, content: str, 
                     scene_range: List[int] = None, context: Dict = None):
        """Send message"""
        msg = Message(
            id=str(uuid.uuid4()),
            sender=self.id,
            receiver=receiver,
            msg_type=msg_type,
            content=content,
            scene_range=scene_range or [],
            context=context or {}
        )
        self.swarm.route_message(msg)
        self.memory.append(f"SENT: {msg}")
        return msg
    
    def receive_message(self, msg: Message):
        """Receive message"""
        self.inbox.put(msg)
        self.memory.append(f"RECV: {msg}")
    
    def get_scene_context(self, max_chars: int = 500) -> str:
        """Get condensed context of all scenes in window"""
        context = []
        for scene in self.scene_window:
            context.append(
                f"Scene {scene['scene_number']} ({scene['scene_name']}): "
                f"{scene['original_prompt'][:100]}..."
            )
        return "\n".join(context)[:max_chars]
    
    def analyze_multi_scene_patterns(self) -> Optional[Message]:
        """
        Analyze patterns across multiple scenes
        This is the key difference - agent sees MULTIPLE scenes at once
        """
        llm = self.create_llm()
        
        scene_context = self.get_scene_context(max_chars=600)
        scene_numbers = [s['scene_number'] for s in self.scene_window]
        
        if self.role == "Pattern-Detector":
            prompt = f"""You are a Pattern-Detector. Analyze these consecutive scenes for patterns.

Scenes {scene_numbers[0]}-{scene_numbers[-1]}:
{scene_context}

Find ONE pattern across these scenes:
- Repeated character descriptions that should match
- Lighting that should be consistent (same location)
- Props that appear/disappear
- Actions that don't flow logically

Format: "PATTERN in scenes [X,Y,Z]: [description]" (max 50 words):"""
        
        elif self.role == "Character-Tracker":
            prompt = f"""You are a Character-Tracker. Track character consistency across scenes.

Scenes {scene_numbers[0]}-{scene_numbers[-1]}:
{scene_context}

Find ONE character inconsistency across these scenes:
- Clothing changes without reason
- Props (weapons, items) appearing/disappearing
- Physical descriptions changing

Format: "CHARACTER ISSUE in scenes [X,Y]: [character] [problem]" (max 50 words):"""
        
        elif self.role == "Location-Tracker":
            prompt = f"""You are a Location-Tracker. Track location/lighting consistency.

Scenes {scene_numbers[0]}-{scene_numbers[-1]}:
{scene_context}

Find scenes in the SAME location with DIFFERENT lighting.
Format: "LOCATION ISSUE in scenes [X,Y]: [location] lighting inconsistent" (max 50 words):"""
        
        elif self.role == "Arc-Analyzer":
            prompt = f"""You are an Arc-Analyzer. Analyze narrative flow across scenes.

Scenes {scene_numbers[0]}-{scene_numbers[-1]}:
{scene_context}

Find ONE narrative flow issue:
- Actions that don't connect
- Character positions that jump
- Timeline inconsistencies

Format: "ARC ISSUE in scenes [X,Y]: [problem]" (max 50 words):"""
        
        elif self.role == "Multi-Scene-Fixer":
            # Get all findings from other agents
            recent_msgs = list(self.inbox.queue)[-10:]
            findings = "\n".join([
                f"- {m.sender}: {m.content}"
                for m in recent_msgs
                if m.msg_type in [MessageType.PATTERN, MessageType.SUGGESTION]
            ])
            
            prompt = f"""You are a Multi-Scene-Fixer. Create fixes that span multiple scenes.

Scenes {scene_numbers[0]}-{scene_numbers[-1]}:
{scene_context}

Agent findings:
{findings if findings else "No findings yet"}

Create ONE fix that applies across multiple scenes.
Format: "FIX scenes [X,Y,Z]: [what to change]" (max 60 words):"""
        
        else:
            return None
        
        try:
            response = llm.run(prompt).strip()
            
            # Parse which scenes are affected
            affected_scenes = []
            if "scenes [" in response.lower() or "scene [" in response.lower():
                # Extract scene numbers
                import re
                matches = re.findall(r'\[(\d+(?:,\d+)*)\]', response)
                if matches:
                    affected_scenes = [int(x) for x in matches[0].split(',')]
            
            if not affected_scenes:
                affected_scenes = scene_numbers[:3]  # Default to first 3
            
            # Determine message type
            if "PATTERN" in response:
                msg_type = MessageType.PATTERN
            elif "FIX" in response:
                msg_type = MessageType.MULTI_SCENE_FIX
            else:
                msg_type = MessageType.SUGGESTION
            
            return self.send_message(
                receiver=None,
                msg_type=msg_type,
                content=response,
                scene_range=affected_scenes
            )
            
        except Exception as e:
            print(f"⚠️  Agent {self.id} error: {e}")
            return None
    
    def process_messages(self, timeout: float = 1.0):
        """Process messages"""
        messages = []
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            try:
                msg = self.inbox.get(timeout=0.1)
                messages.append(msg)
            except queue.Empty:
                if messages:
                    break
                continue
        
        return messages
    
    def run(self, duration: float = 8.0):
        """Run agent - analyze patterns and collaborate"""
        deadline = time.time() + duration
        iterations = 0
        
        while time.time() < deadline and self.active and iterations < 3:
            # Analyze patterns across scenes
            if self.role != "Multi-Scene-Fixer" or iterations > 0:
                self.analyze_multi_scene_patterns()
            
            # Process messages from other agents
            messages = self.process_messages(timeout=0.5)
            
            iterations += 1
            time.sleep(0.3)
    
    def shutdown(self):
        """Shutdown"""
        self.active = False


class WideContextSwarm:
    """
    Swarm that operates across multiple scenes simultaneously
    """
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.agents: Dict[str, WideContextAgent] = {}
        self.message_history = []
        self.lock = threading.Lock()
        
    def spawn_agent(self, role: str, scene_window: List[Dict]) -> str:
        """Spawn agent with access to multiple scenes"""
        agent_id = f"{role}-{str(uuid.uuid4())[:8]}"
        
        llm_config = {
            'model': self.model_name,
            'base_url': self.base_url,
            'temperature': 0.7,
            'max_tokens': 250
        }
        
        agent = WideContextAgent(agent_id, role, self, llm_config, scene_window)
        
        with self.lock:
            self.agents[agent_id] = agent
        
        scene_range = f"{scene_window[0]['scene_number']}-{scene_window[-1]['scene_number']}"
        print(f"   🤖 Spawned: {role} (scenes {scene_range})")
        
        return agent_id
    
    def route_message(self, msg: Message):
        """Route message"""
        with self.lock:
            self.message_history.append(msg)
            
            if msg.receiver:
                if msg.receiver in self.agents:
                    self.agents[msg.receiver].receive_message(msg)
            else:
                # Broadcast to relevant agents (those whose scene window overlaps)
                for agent_id, agent in self.agents.items():
                    if agent_id != msg.sender:
                        # Check if agent's scenes overlap with message's scenes
                        agent_scenes = {s['scene_number'] for s in agent.scene_window}
                        msg_scenes = set(msg.scene_range) if msg.scene_range else set()
                        
                        if not msg_scenes or agent_scenes.intersection(msg_scenes):
                            agent.receive_message(msg)
    
    def run_swarm(self, duration: float = 10.0):
        """Run all agents in parallel"""
        print(f"  🔄 Wide-context swarm running for {duration}s...")
        
        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            futures = [
                executor.submit(agent.run, duration)
                for agent in self.agents.values()
            ]
            
            for future in futures:
                future.result()
        
        print(f"  ✓ Swarm completed ({len(self.message_history)} messages)")
        
        return self.message_history
    
    def extract_fixes(self) -> Dict[int, List[str]]:
        """
        Extract all fixes organized by scene number
        Returns: {scene_number: [list of fixes]}
        """
        fixes_by_scene = {}
        
        for msg in self.message_history:
            if msg.msg_type in [MessageType.MULTI_SCENE_FIX, MessageType.SUGGESTION, MessageType.PATTERN]:
                for scene_num in msg.scene_range:
                    if scene_num not in fixes_by_scene:
                        fixes_by_scene[scene_num] = []
                    fixes_by_scene[scene_num].append(msg.content)
        
        return fixes_by_scene
    
    def shutdown_all(self):
        """Shutdown all agents"""
        for agent in self.agents.values():
            agent.shutdown()
        self.agents.clear()


class WideContextConsistencyPass:
    """
    Consistency pass using wide-context swarm
    Processes scenes in batches, with agents seeing multiple scenes
    """
    
    def __init__(self, base_url="http://localhost:1234/v1", model_name="openai/gemma-4-e4b-it-uncensored"):
        self.base_url = base_url
        self.model_name = model_name
        self.file_lock = threading.Lock()
    
    def apply_fixes_to_scene(self, scene: Dict, fixes: List[str]) -> str:
        """Apply multiple fixes to a scene using LLM"""
        if not fixes:
            return scene['original_prompt']
        
        llm = LiteLLM(
            model_name=self.model_name,
            base_url=self.base_url,
            temperature=0.6,
            max_tokens=400
        )
        
        fixes_text = "\n".join([f"- {fix}" for fix in fixes])
        
        prompt = f"""Apply these consistency fixes to the scene.

Scene {scene['scene_number']}: {scene['scene_name']}
Current prompt: {scene['original_prompt']}

Fixes to apply:
{fixes_text}

Rules:
- Apply ALL fixes
- Keep core scene content
- Maintain character names exactly
- Keep duration: {scene['duration']}s
- Be specific and concrete

Write the fixed prompt (max 200 words):"""
        
        try:
            response = llm.run(prompt).strip()
            
            # Clean response
            for prefix in ["Fixed prompt:", "FIXED:", "OUTPUT:", "**"]:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
            
            return response
        except:
            return scene['original_prompt']
    
    def process_scene_batch(self, scenes: List[Dict], batch_start_idx: int):
        """
        Process a batch of scenes with wide-context swarm
        """
        scene_range = f"{scenes[0]['scene_number']}-{scenes[-1]['scene_number']}"
        print(f"\n{'='*80}")
        print(f"Processing scenes {scene_range} ({len(scenes)} scenes)")
        print(f"{'='*80}")
        
        # Create swarm
        swarm = WideContextSwarm(self.base_url, self.model_name)
        
        # Spawn agents that can see all scenes in this batch
        swarm.spawn_agent("Pattern-Detector", scenes)
        swarm.spawn_agent("Character-Tracker", scenes)
        swarm.spawn_agent("Location-Tracker", scenes)
        swarm.spawn_agent("Arc-Analyzer", scenes)
        
        # Run swarm - agents analyze patterns across all scenes
        swarm.run_swarm(duration=10.0)
        
        # Spawn fixer agent to synthesize all findings
        swarm.spawn_agent("Multi-Scene-Fixer", scenes)
        fixer = list(swarm.agents.values())[-1]
        
        # Give fixer all messages
        for msg in swarm.message_history:
            fixer.receive_message(msg)
        
        # Fixer analyzes and creates multi-scene fixes
        fixer.run(duration=3.0)
        
        # Extract fixes organized by scene
        print(f"  🔨 Applying fixes...")
        fixes_by_scene = swarm.extract_fixes()
        
        # Apply fixes to each scene
        results = []
        for scene in scenes:
            scene_num = scene['scene_number']
            scene_fixes = fixes_by_scene.get(scene_num, [])
            
            if scene_fixes:
                print(f"  ✓ Scene {scene_num}: {len(scene_fixes)} fixes")
                fixed_prompt = self.apply_fixes_to_scene(scene, scene_fixes)
            else:
                fixed_prompt = scene['original_prompt']
            
            # Build detailed swarm trace for this scene
            scene_messages = [
                msg for msg in swarm.message_history 
                if scene_num in msg.scene_range
            ]
            
            # Organize messages by agent and timestamp
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
                    "scene_range": msg.scene_range
                })
            
            # Sort by timestamp
            agent_timeline.sort(key=lambda x: x['timestamp'])
            
            # Build coordination trace
            coordination_trace = {
                "detection_phase": [
                    m for m in agent_timeline 
                    if m['message_type'] in ['pattern', 'suggestion', 'analysis']
                ],
                "debate_phase": [
                    m for m in agent_timeline 
                    if m['message_type'] in ['question', 'answer', 'consensus']
                ],
                "resolution_phase": [
                    m for m in agent_timeline 
                    if m['message_type'] in ['multi_scene_fix', 'final']
                ]
            }
            
            log_entry = {
                "scene_number": scene['scene_number'],
                "scene_name": scene['scene_name'],
                "before": scene['original_prompt'],
                "after": fixed_prompt,
                "changed": scene['original_prompt'] != fixed_prompt,
                
                # Swarm coordination data
                "swarm_trace": {
                    "total_messages": len(scene_messages),
                    "agent_timeline": agent_timeline,
                    "coordination_trace": coordination_trace,
                    "agents_involved": list(set([m['agent_role'] for m in agent_timeline])),
                    "message_types": list(set([m['message_type'] for m in agent_timeline]))
                },
                
                # Structured fixes (deduplicated and categorized)
                "fixes": {
                    "patterns_detected": [
                        m['content'] for m in agent_timeline 
                        if m['message_type'] == 'pattern'
                    ],
                    "issues_found": [
                        m['content'] for m in agent_timeline 
                        if m['message_type'] == 'suggestion' and 'ISSUE' in m['content']
                    ],
                    "resolutions": [
                        m['content'] for m in agent_timeline 
                        if m['message_type'] in ['multi_scene_fix', 'final']
                    ]
                }
            }
            
            results.append({
                'scene': {
                    "scene_number": scene['scene_number'],
                    "scene_name": scene['scene_name'],
                    "duration": scene['duration'],
                    "original_prompt": fixed_prompt
                },
                'log': log_entry
            })
        
        swarm.shutdown_all()
        
        return results
    
    def process_script(self, input_file, output_file, batch_size=8, max_workers=2):
        """
        Process entire script in batches
        
        Args:
            batch_size: Number of scenes each swarm sees (5-10 recommended)
            max_workers: Number of batches to process in parallel
        """
        print("\n" + "🌊"*40)
        print("WIDE-CONTEXT EMERGENT SWARM")
        print("🌊"*40 + "\n")
        
        # Load scenes
        with open(input_file, 'r') as f:
            scenes = json.load(f)
        
        print(f"📖 Input: {input_file}")
        print(f"   Scenes: {len(scenes)} total")
        print(f"   Batch size: {batch_size} scenes per swarm")
        print(f"   Parallel batches: {max_workers}\n")
        
        # Load existing progress
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
        
        log_file = output_file.replace('.json', '_wide_context_log.json')
        try:
            with open(log_file, 'r') as f:
                consistency_log = json.load(f)
        except:
            pass
        
        # Split scenes into batches
        batches = []
        for i in range(0, len(scenes), batch_size):
            batch = scenes[i:i + batch_size]
            # Skip if all scenes in batch are already done
            if not all(s['scene_number'] in existing_scene_numbers for s in batch):
                batches.append((batch, i))
        
        print(f"   Processing {len(batches)} batches\n")
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_scene_batch, batch, idx): (batch, idx)
                for batch, idx in batches
            }
            
            for future in futures:
                results = future.result()
                
                with self.file_lock:
                    for result in results:
                        # Only add if not already processed
                        if result['scene']['scene_number'] not in existing_scene_numbers:
                            consistent_scenes.append(result['scene'])
                            consistency_log.append(result['log'])
                            existing_scene_numbers.add(result['scene']['scene_number'])
                    
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
        print("✅ WIDE-CONTEXT SWARM COMPLETE!")
        print(f"{'='*80}")
        print(f"\n💾 Output: {output_file}")
        print(f"   Log: {log_file}\n")
        
        return consistent_scenes


if __name__ == "__main__":
    swarm = WideContextConsistencyPass()
    
    swarm.process_script(
        input_file="snow_crash_improved_clean_full.json",
        output_file="snow_crash_wide_context_final.json",
        batch_size=8,  # Each swarm sees 8 scenes at once
        max_workers=2   # Process 2 batches in parallel
    )
