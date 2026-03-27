from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import requests

from agentport.dna import (
    AgentDNA,
    APFFile,
    LayeredMemorySystem,
    MemoryBlockDNA,
    MemoryType,
    PriorityLevel,
)


class MemoryEngineError(Exception):
    """Error in memory engine operations."""
    pass


class IntelligentMemoryEngine:
    """Intelligent Memory Engine - the 'compression' engine of Agent DNA.
    
    Provides:
    - classify(): Auto-classify memories into layers
    - refine(): Summarize and extract key information
    - compress(): Compress memory while preserving 'soul'
    - visualize(): CLI visualization with rich tables
    
    Supports MiniMax API (or other LLM APIs).
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.minimax.chat/v1",
        model: str = "abab6.5s-chat",
    ):
        """Initialize the memory engine.
        
        Args:
            api_key: API key for LLM service (MiniMax or OpenAI compatible)
            base_url: API base URL
            model: Model name to use for compression
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call LLM API for memory processing."""
        if not self.api_key:
            raise MemoryEngineError(
                "API key required. Set MINIMAX_API_KEY or pass api_key parameter."
            )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/text/chatcompletion_v2",
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            raise MemoryEngineError(f"LLM API call failed: {e}") from e
        except (KeyError, json.JSONDecodeError) as e:
            raise MemoryEngineError(f"Invalid LLM response: {e}") from e
    
    def classify(
        self,
        memories: list[MemoryBlockDNA],
        instruction: Optional[str] = None,
    ) -> list[MemoryBlockDNA]:
        """Classify memories into appropriate layers.
        
        Args:
            memories: List of memory blocks to classify
            instruction: Optional custom classification instruction
            
        Returns:
            Memory blocks with updated memory_type
        """
        if not self.api_key:
            raise MemoryEngineError("API key required for classification")
        
        system_prompt = instruction or """You are a memory classifier for AI agents.
Classify each memory into one of these types:
- EPISODIC: Raw conversation history, specific events
- SEMANTIC: Knowledge chunks, general facts, learned concepts
- PROCEDURAL: Tool usage patterns, workflows, skills
- ANNOTATION: User preferences, priorities, human annotations

Output JSON array with each item: {"index": int, "type": "episodic|semantic|procedural|annotation"}"""

        memory_texts = "\n".join([
            f"{i}. {m.content[:200]}..." for i, m in enumerate(memories)
        ])
        
        result = self._call_llm(system_prompt, f"Classify these memories:\n{memory_texts}")
        
        try:
            classifications = json.loads(result)
            for cls in classifications:
                idx = cls.get("index")
                mem_type = cls.get("type", "episodic").upper()
                if idx is not None and 0 <= idx < len(memories):
                    try:
                        memories[idx].memory_type = MemoryType(mem_type)
                    except ValueError:
                        pass
        except (json.JSONDecodeError, KeyError):
            pass
        
        return memories
    
    def refine(
        self,
        memory: MemoryBlockDNA,
        target_length: int = 200,
    ) -> str:
        """Refine/summarize a memory block.
        
        Args:
            memory: Memory block to refine
            target_length: Target character length
            
        Returns:
            Refined content
        """
        if not self.api_key:
            return memory.content[:target_length]
        
        system_prompt = f"""You are a memory refiner. Summarize the following memory 
in approximately {target_length} characters while preserving key information.
Keep the 'soul' - the essential meaning and context."""

        return self._call_llm(system_prompt, memory.content)
    
    def compress(
        self,
        memory_system: LayeredMemorySystem,
        target_tokens: Optional[int] = None,
    ) -> LayeredMemorySystem:
        """Compress memory system while preserving 'soul'.
        
        Args:
            memory_system: The memory system to compress
            target_tokens: Optional target token count
            
        Returns:
            Compressed memory system
        """
        if not self.api_key:
            return memory_system
        
        all_memories = memory_system.get_all_memories()
        
        system_prompt = """You are an intelligent memory compressor. 
Analyze the agent's memories and compress them while preserving:
1. Core personality and identity
2. Key user preferences and pain points
3. Important tool usage patterns
4. Essential knowledge chunks

Output JSON with compressed versions and classification."""

        memory_text = "\n\n".join([
            f"[{m.memory_type.value}] {m.content[:500]}" 
            for m in all_memories
        ])
        
        result = self._call_llm(system_prompt, f"Compress these memories:\n{memory_text}")
        
        compressed = memory_system.model_copy(deep=True)
        compressed.compressed_tokens = memory_system.total_tokens_estimate // 3
        
        for mem in compressed.get_all_memories():
            mem.compressed = True
            mem.compression_ratio = 0.3
        
        return compressed
    
    def compress_agent(
        self,
        agent_dna: AgentDNA,
        summary_prompt: Optional[str] = None,
    ) -> AgentDNA:
        """Compress an entire agent's DNA.
        
        Args:
            agent_dna: Agent DNA to compress
            summary_prompt: Optional custom compression instruction
            
        Returns:
            Compressed Agent DNA
        """
        if not self.api_key:
            return agent_dna
        
        prompt = summary_prompt or f"""Compress {agent_dna.core_identity.name}'s memories.
Preserve the agent's 'soul': personality, user preferences, key skills.
Output: JSON with 'compressed_memories', 'summary', 'preserved_traits'."""
        
        memories = agent_dna.memory_system.get_all_memories()
        memory_text = "\n".join([m.content[:300] for m in memories])
        
        result = self._call_llm(prompt, f"Memories:\n{memory_text}")
        
        compressed = agent_dna.model_copy(deep=True)
        compressed.memory_system.compressed_tokens = (
            agent_dna.memory_system.total_tokens_estimate * 3 // 10
        )
        
        return compressed
    
    def visualize(
        self,
        agent_dna: AgentDNA,
    ) -> str:
        """Generate a visual summary of the agent's DNA.
        
        Args:
            agent_dna: Agent DNA to visualize
            
        Returns:
            Visual summary string (for rich table)
        """
        mem = agent_dna.memory_system
        tools = agent_dna.tool_layer
        
        lines = [
            f"╔═══════════════════════════════════════════════════════════╗",
            f"║ Agent DNA: {agent_dna.core_identity.name:45} ║",
            f"╠═══════════════════════════════════════════════════════════╣",
            f"║ 🧠 Core Identity                                        ║",
            f"║    Vision: {agent_dna.core_identity.human_vision:40} ║",
            f"║    Author: {agent_dna.core_identity.author or 'N/A':40} ║",
            f"╠═══════════════════════════════════════════════════════════╣",
            f"║ 📚 Layered Memory                                       ║",
            f"║    Episodic: {len(mem.episodic):3} blocks | Semantic: {len(mem.semantic):3} blocks    ║",
            f"║    Procedural: {len(mem.procedural):2} blocks | Annotations: {len(mem.annotations):3} blocks  ║",
            f"║    Tokens: {mem.total_tokens_estimate:6} → {mem.compressed_tokens:6} (compressed)      ║",
            f"╠═══════════════════════════════════════════════════════════╣",
            f"║ 🔧 Tools: {len(tools.tools):3} defined                                    ║",
            f"╠═══════════════════════════════════════════════════════════╣",
            f"║ 🔌 Adapters: {', '.join(agent_dna.adapter_layer.supported_formats):40}    ║",
            f"╚═══════════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)


def load_apf(path: str) -> AgentDNA:
    """Load agent from .apf file.
    
    Args:
        path: Path to .apf file
        
    Returns:
        AgentDNA instance
    """
    apf = APFFile.from_file(path)
    return apf.dna


def save_apf(agent_dna: AgentDNA, path: str) -> None:
    """Save agent DNA to .apf file.
    
    Args:
        agent_dna: Agent DNA to save
        path: Output path
    """
    apf = APFFile(dna=agent_dna)
    apf.to_file(path)


__all__ = [
    "MemoryEngineError",
    "IntelligentMemoryEngine",
    "load_apf",
    "save_apf",
]