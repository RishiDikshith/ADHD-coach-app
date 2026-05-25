import logging
import json
import asyncio
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Set, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

# Logging
logger = logging.getLogger("realtime_websocket")
logger.setLevel(logging.INFO)

# ==========================================
# 1. LIVE CO-WORKING FOCUS ROOM MANAGER
# ==========================================

class FocusTimer:
    """Manages the countdown timer state for a focus room."""
    def __init__(self, duration_minutes: int = 25):
        self.duration_minutes = duration_minutes
        self.remaining_seconds = duration_minutes * 60
        self.is_active = False
        self.is_break = False
        self.task: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_minutes": self.duration_minutes,
            "remaining_seconds": self.remaining_seconds,
            "is_active": self.is_active,
            "is_break": self.is_break
        }

class FocusRoom:
    """Represents a live co-working room containing timers and active members."""
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.timer = FocusTimer()
        # username -> dict containing details
        self.members: Dict[str, Dict[str, Any]] = {}
        # username -> WebSocket connections
        self.connections: Dict[str, WebSocket] = {}

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON message to all active WebSocket connections in the room."""
        disconnected_users = []
        payload = json.dumps(message)
        for username, ws in list(self.connections.items()):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to {username} in room {self.room_id}: {e}")
                disconnected_users.append(username)

        # Cleanup failed connections
        for username in disconnected_users:
            self.remove_member(username)

    def add_member(self, username: str, websocket: WebSocket):
        self.connections[username] = websocket
        # Generate a premium visual HSL color for the user's avatar
        import random
        hue = random.randint(0, 360)
        # HSL with high saturation and friendly lightness for dark/light themes
        avatar_hsl = f"hsl({hue}, 75%, 60%)"
        
        self.members[username] = {
            "username": username,
            "status": "idle",
            "distractions": 0,
            "avatar_hsl": avatar_hsl,
            "joined_at": datetime.now(timezone.utc).isoformat()
        }

    def remove_member(self, username: str):
        if username in self.connections:
            del self.connections[username]
        if username in self.members:
            del self.members[username]

    def get_state(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "timer": self.timer.to_dict(),
            "members": list(self.members.values())
        }

class FocusRoomManager:
    """Manages active co-working focus rooms and their background ticking loops."""
    def __init__(self):
        self.rooms: Dict[str, FocusRoom] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_room(self, room_id: str) -> FocusRoom:
        async with self._lock:
            if room_id not in self.rooms:
                self.rooms[room_id] = FocusRoom(room_id)
            return self.rooms[room_id]

    async def remove_empty_rooms(self):
        async with self._lock:
            empty_rooms = [r_id for r_id, room in self.rooms.items() if not room.connections]
            for r_id in empty_rooms:
                room = self.rooms[r_id]
                if room.timer.task:
                    room.timer.task.cancel()
                del self.rooms[r_id]
                logger.info(f"Cleaned up empty focus room: {r_id}")

    def start_room_timer(self, room: FocusRoom):
        """Starts the async timer decrement loop for a room."""
        if room.timer.task and not room.timer.task.done():
            return  # Already running

        async def tick_loop():
            try:
                while room.timer.is_active and room.timer.remaining_seconds > 0:
                    await asyncio.sleep(1.0)
                    room.timer.remaining_seconds -= 1
                    
                    # Broadcast tick with premium state information
                    await room.broadcast({
                        "type": "timer_tick",
                        "remaining_seconds": room.timer.remaining_seconds,
                        "is_active": room.timer.is_active,
                        "is_break": room.timer.is_break
                    })

                if room.timer.remaining_seconds <= 0:
                    room.timer.is_active = False
                    await room.broadcast({
                        "type": "timer_completed",
                        "is_break": room.timer.is_break
                    })
                    # Reset timer automatically
                    room.timer.remaining_seconds = room.timer.duration_minutes * 60
            except asyncio.CancelledError:
                logger.info(f"Timer loop cancelled for room: {room.room_id}")
            except Exception as e:
                logger.error(f"Error in timer loop for room {room.room_id}: {e}")
            finally:
                room.timer.is_active = False

        room.timer.is_active = True
        room.timer.task = asyncio.create_task(tick_loop())

# Global instance
focus_manager = FocusRoomManager()


# ==========================================
# 2. COLLABORATIVE ACCOUNTABILITY GROUPS
# ==========================================

class AccountabilityGroup:
    """Manages real-time presence and check-ins for a group."""
    def __init__(self, group_id: str):
        self.group_id = group_id
        # username -> WebSocket
        self.connections: Dict[str, WebSocket] = {}
        # username -> current state info (status, stress, energy, points)
        self.members: Dict[str, Dict[str, Any]] = {}

    async def broadcast(self, message: Dict[str, Any]):
        disconnected_users = []
        payload = json.dumps(message)
        for username, ws in list(self.connections.items()):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting accountability update to {username}: {e}")
                disconnected_users.append(username)

        for username in disconnected_users:
            self.remove_member(username)

    def add_member(self, username: str, websocket: WebSocket):
        self.connections[username] = websocket
        # Premium visual identity HSL
        import random
        hue = random.randint(180, 360) # Different palette for accountability (teal, blues, purples)
        self.members[username] = {
            "username": username,
            "status": "Joined group!",
            "stress": 5,
            "energy": 5,
            "dopamine_points": 0,
            "avatar_hsl": f"hsl({hue}, 70%, 55%)"
        }

    def remove_member(self, username: str):
        if username in self.connections:
            del self.connections[username]
        if username in self.members:
            del self.members[username]

    def get_state(self) -> Dict[str, Any]:
        return {
            "group_id": self.group_id,
            "members": list(self.members.values())
        }

class AccountabilityManager:
    """Manages active accountability groups."""
    def __init__(self):
        self.groups: Dict[str, AccountabilityGroup] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_group(self, group_id: str) -> AccountabilityGroup:
        async with self._lock:
            if group_id not in self.groups:
                self.groups[group_id] = AccountabilityGroup(group_id)
            return self.groups[group_id]

    async def cleanup_empty_groups(self):
        async with self._lock:
            empty = [g_id for g_id, g in self.groups.items() if not g.connections]
            for g_id in empty:
                del self.groups[g_id]
                logger.info(f"Cleaned up empty accountability group: {g_id}")

# Global instance
accountability_manager = AccountabilityManager()


# ==========================================
# 3. FASTAPI ROUTER DEFINITION
# ==========================================

router = APIRouter(prefix="/ws", tags=["realtime"])

# Helper imports from main_api avoiding import time circular dependency
def get_main_api_globals():
    try:
        import src.api.main_api as main_api
        return main_api
    except Exception as e:
        logger.error(f"Failed to import main_api globals: {e}")
        return None

# ==========================================
# WS ROUTE: LIVE CO-WORKING FOCUS SESSIONS
# ==========================================

@router.websocket("/focus/{room_id}")
async def websocket_focus(websocket: WebSocket, room_id: str, username: str = Query("Guest")):
    await websocket.accept()
    room = await focus_manager.get_or_create_room(room_id)
    room.add_member(username, websocket)
    
    # Broadcast member join
    await room.broadcast({
        "type": "member_joined",
        "username": username,
        "avatar_hsl": room.members[username]["avatar_hsl"],
        "members": list(room.members.values()),
        "timer": room.timer.to_dict()
    })

    logger.info(f"User '{username}' connected to Focus Room '{room_id}'")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "update_status":
                    # Update member focusing status
                    status = msg.get("status", "idle")
                    if username in room.members:
                        room.members[username]["status"] = status
                        await room.broadcast({
                            "type": "status_changed",
                            "username": username,
                            "status": status
                        })

                elif msg_type == "log_distraction":
                    # Keep count of distraction points
                    category = msg.get("category", "other")
                    if username in room.members:
                        room.members[username]["distractions"] += 1
                        await room.broadcast({
                            "type": "distraction_logged",
                            "username": username,
                            "category": category,
                            "total_distractions": room.members[username]["distractions"]
                        })
                        # Optional: persist distraction to database using main_api globals
                        api = get_main_api_globals()
                        if api and api._db_manager:
                            try:
                                api._db_manager.log_distraction(username, room_id, category)
                            except Exception as db_err:
                                logger.warning(f"Failed to log distraction to DB: {db_err}")

                elif msg_type == "start_timer":
                    duration = int(msg.get("duration_minutes", 25))
                    room.timer.duration_minutes = duration
                    room.timer.remaining_seconds = duration * 60
                    room.timer.is_break = bool(msg.get("is_break", False))
                    focus_manager.start_room_timer(room)
                    await room.broadcast({
                        "type": "timer_started",
                        "timer": room.timer.to_dict()
                    })

                elif msg_type == "pause_timer":
                    if room.timer.is_active:
                        room.timer.is_active = False
                        if room.timer.task:
                            room.timer.task.cancel()
                        await room.broadcast({
                            "type": "timer_paused",
                            "timer": room.timer.to_dict()
                        })

                elif msg_type == "resume_timer":
                    if not room.timer.is_active:
                        focus_manager.start_room_timer(room)
                        await room.broadcast({
                            "type": "timer_resumed",
                            "timer": room.timer.to_dict()
                        })

                elif msg_type == "reset_timer":
                    room.timer.is_active = False
                    if room.timer.task:
                        room.timer.task.cancel()
                    room.timer.remaining_seconds = room.timer.duration_minutes * 60
                    await room.broadcast({
                        "type": "timer_reset",
                        "timer": room.timer.to_dict()
                    })

                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON in focus WS: {data}")
            except Exception as e:
                logger.error(f"Error handling focus WS message: {e}")

    except WebSocketDisconnect:
        logger.info(f"User '{username}' disconnected from Focus Room '{room_id}'")
    finally:
        room.remove_member(username)
        await room.broadcast({
            "type": "member_left",
            "username": username,
            "members": list(room.members.values())
        })
        await focus_manager.remove_empty_rooms()


# ==========================================
# WS ROUTE: COLLABORATIVE ACCOUNTABILITY GROUPS
# ==========================================

@router.websocket("/accountability/{group_id}")
async def websocket_accountability(websocket: WebSocket, group_id: str, username: str = Query("Guest")):
    await websocket.accept()
    group = await accountability_manager.get_or_create_group(group_id)
    group.add_member(username, websocket)

    # Broadcast arrival
    await group.broadcast({
        "type": "presence_update",
        "action": "joined",
        "username": username,
        "avatar_hsl": group.members[username]["avatar_hsl"],
        "members": list(group.members.values())
    })

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "check_in":
                    # Update status, stress, energy
                    status = msg.get("status", "Working on tasks!")
                    stress = int(msg.get("stress", 5))
                    energy = int(msg.get("energy", 5))

                    if username in group.members:
                        group.members[username]["status"] = status
                        group.members[username]["stress"] = stress
                        group.members[username]["energy"] = energy

                        await group.broadcast({
                            "type": "member_check_in",
                            "username": username,
                            "status": status,
                            "stress": stress,
                            "energy": energy,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })

                        # Award XP for accountability checking in using main_api
                        api = get_main_api_globals()
                        if api and api._db_manager and api._gamification:
                            try:
                                api._gamification.award_xp(username, "mood_checkin")
                            except Exception as xp_err:
                                logger.warning(f"Failed to award check-in XP: {xp_err}")

                elif msg_type == "micro_win":
                    # Complete a microtask and announce
                    task = msg.get("task", "Completed a step!")
                    await group.broadcast({
                        "type": "member_micro_win",
                        "username": username,
                        "task": task,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                    # Award XP for intervention completion
                    api = get_main_api_globals()
                    if api and api._db_manager and api._gamification:
                        try:
                            api._gamification.award_xp(username, "intervention_completed")
                        except Exception as xp_err:
                            logger.warning(f"Failed to award micro-win XP: {xp_err}")

                elif msg_type == "send_dopamine":
                    # A peer rewards another with Dopamine Points / visual sparks!
                    target = msg.get("target_username")
                    emoji = msg.get("emoji", "🎉")
                    
                    if target and target in group.members:
                        group.members[target]["dopamine_points"] += 10
                        
                        await group.broadcast({
                            "type": "dopamine_received",
                            "from_username": username,
                            "to_username": target,
                            "emoji": emoji,
                            "points": 10,
                            "target_total_points": group.members[target]["dopamine_points"]
                        })

                        # Award actual minor XP to the recipient!
                        api = get_main_api_globals()
                        if api and api._db_manager and api._gamification:
                            try:
                                api._gamification.award_xp(target, "mood_checkin") # Custom dopamine gift XP
                            except Exception as xp_err:
                                logger.warning(f"Failed to award gift XP to {target}: {xp_err}")

                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON in accountability WS: {data}")
            except Exception as e:
                logger.error(f"Error handling accountability message: {e}")

    except WebSocketDisconnect:
        logger.info(f"User '{username}' disconnected from Accountability Group '{group_id}'")
    finally:
        group.remove_member(username)
        await group.broadcast({
            "type": "presence_update",
            "action": "left",
            "username": username,
            "members": list(group.members.values())
        })
        await accountability_manager.cleanup_empty_groups()


# ==========================================
# WS ROUTE: STREAMING AI CHAT RESPONSES
# ==========================================

@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket, username: str = Query("default"), agent_id: str = Query("productivity-coach")):
    await websocket.accept()
    logger.info(f"User '{username}' started realtime AI session with agent '{agent_id}'")

    api = get_main_api_globals()
    if not api:
        await websocket.send_text(json.dumps({"type": "error", "message": "Backend engine is not initialized"}))
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                text = msg.get("text", "")
                
                if not text or len(text.strip()) == 0:
                    continue

                user_data = msg.get("user_data", {})
                session_data = msg.get("session_data", {})
                history = msg.get("history", [])
                language = msg.get("language", "en")
                language_name = msg.get("language_name", "English")

                # Detect language automatically
                if len(text.strip()) > 1:
                    try:
                        import langdetect
                        detected = langdetect.detect(text)
                        if detected and len(detected) == 2:
                            language = detected
                    except Exception:
                        pass

                # Initialize cognitive/memory managers for user
                from memory.memory_manager import MemoryManager
                from agents.orchestrator import AgentOrchestrator
                from task_paralysis.recovery_engine import TaskParalysisRecoveryEngine

                memory = MemoryManager(user_id=username)
                orchestrator = AgentOrchestrator(memory)
                paralysis_engine = TaskParalysisRecoveryEngine(memory)

                if api._db_manager:
                    memory.set_db_manager(api._db_manager)
                    api._rag_engine.memory = memory

                current_streak = session_data.get('current_streak', 0) if session_data else 0

                # 1. RAG Context Retrieval
                rag_context = api._rag_engine.retrieve_context(
                    username=username,
                    query=text,
                    user_data=user_data,
                    session_data=session_data,
                )
                
                # 2. Intent Classification
                intent = api._llm_router.classify_intent(text)
                route_instruction = api._llm_router.format_response_instruction(intent)

                # 3. Agent Personality Context
                agent_context = orchestrator.get_context_for_prompt(text, current_streak, agent_id)
                agent_insights = agent_context.get("agent_insights", "")

                # 4. ADHD State & Overwhelm Detection
                state_result = api._state_detector.analyze(text, {
                    "current_stress": user_data.get("stress_level", 5),
                    "current_energy": user_data.get("energy_level", 5),
                    "text": text,
                })
                state_prompt_ext = api._state_detector.get_system_prompt_extension(text)

                # 5. Adaptive coaching overrides
                coach_extension = api._adaptive_coach.get_system_prompt_extension(
                    text,
                    {"current_stress": user_data.get("stress_level", 5)},
                    user_data.get("mood"),
                )

                # 6. Task Paralysis Deep Dive
                paralysis_result = paralysis_engine.process_user_message(text, agent_context)
                paralysis_prompt_ext = ""
                if paralysis_result["paralysis_detected"]:
                    ext = paralysis_engine.get_system_prompt_extension(text, agent_context)
                    if ext:
                        paralysis_prompt_ext = ext
                    memory.set_task_paralysis(True)

                # Mute ADHD details for generic support
                if agent_id == "support-agent":
                    state_prompt_ext = ""
                    coach_extension = ""
                    paralysis_prompt_ext = ""

                # Combine context
                all_context_parts = [rag_context, agent_insights, state_prompt_ext, coach_extension, paralysis_prompt_ext, route_instruction]
                all_context = "\n\n".join([p for p in all_context_parts if p])

                english_text = api.translate_to_english(text)
                analysis_result = api.analyze(english_text)
                scores = api.build_user_scores(user_data, text=english_text, analysis=analysis_result) if user_data else {}

                # Build final agent prompt
                agent_system_prompt = orchestrator.build_agent_specific_prompt(
                    agent_id, text, agent_context, current_streak
                )

                instruction = "Start by warmly welcoming the user and responding directly to their input." if not history else f"Respond to the user as the supportive {agent_id} companion."
                if scores and scores.get("summary", {}).get("stress_level", 0) >= 8:
                    instruction += "\nCRITICAL: The user has HIGH STRESS. Be extremely gentle, warm, and deeply empathetic."

                prompt = f"""
{agent_system_prompt}

{all_context}

---
Your instructions for this specific turn: {instruction}
User's current emotional state: {analysis_result['emotion']}
User's productivity level: {analysis_result['productivity']}
---

User input (Original): "{text}"
User input (English Translation context): "{english_text}"

CRITICAL LANGUAGE RULE: You MUST reply in the EXACT SAME language and script as "User input (Original)".
CRITICAL FORMATTING: Keep your paragraphs extremely brief (2-3 sentences max). Use formatting like bold, lists, and emojis strategically. 

You MUST format your entire response exactly like this:

REPLY:
[Your conversational, multi-paragraph response here.]

TASKS:
[1 to 3 tiny, actionable tasks. List them with a dash e.g. "- Drink water"]
"""

                # Streaming token delivery loop
                full_raw_response = ""
                groq_api_key = os.getenv("GROQ_API_KEY")

                # Send start stream signal
                await websocket.send_text(json.dumps({"type": "stream_start"}))

                if not groq_api_key or groq_api_key == "mock_groq_key":
                    # Yield premium offline response character by character simulating low latency
                    offline_reply = api.generate_offline_reply(prompt)
                    # Stream in larger chunks for fluid animation
                    chunk_size = 5
                    for i in range(0, len(offline_reply), chunk_size):
                        chunk = offline_reply[i:i+chunk_size]
                        full_raw_response += chunk
                        await websocket.send_text(json.dumps({"type": "token", "token": chunk}))
                        await asyncio.sleep(0.02)
                else:
                    try:
                        from groq import AsyncGroq
                        client = AsyncGroq(api_key=groq_api_key)
                        completion_stream = await client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.1-8b-instant",
                            temperature=0.7,
                            max_tokens=1024,
                            stream=True,
                        )
                        async for chunk in completion_stream:
                            token = chunk.choices[0].delta.content
                            if token:
                                full_raw_response += token
                                await websocket.send_text(json.dumps({"type": "token", "token": token}))
                    except Exception as e:
                        logger.error(f"Error in Groq streaming WebSocket: {e}")
                        offline_reply = api.generate_offline_reply(prompt)
                        for i in range(0, len(offline_reply), 5):
                            chunk = offline_reply[i:i+5]
                            full_raw_response += chunk
                            await websocket.send_text(json.dumps({"type": "token", "token": chunk}))
                            await asyncio.sleep(0.02)

                # Send end stream signal
                await websocket.send_text(json.dumps({"type": "stream_end"}))

                # Post-processing computations
                raw = full_raw_response
                reply_part = raw
                dynamic_tasks = []
                
                if re.search(r'\bTASKS\s*[\-:]', raw, flags=re.IGNORECASE):
                    parts = re.split(r'\bTASKS\s*[\-:]', raw, flags=re.IGNORECASE)
                    reply_part = re.sub(r'^REPLY\s*[\-:]*\s*', '', parts[0], flags=re.IGNORECASE).strip()
                    tasks_part = parts[1].strip()
                    for line in tasks_part.split('\n'):
                        line = line.strip()
                        if line.startswith("-") or line.startswith("*") or line.startswith("☐"):
                            clean_task = re.sub(r'^[\-\*☐]\s*', '', line).strip()
                            if clean_task:
                                dynamic_tasks.append(clean_task)
                        else:
                            clean_line = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                            if clean_line and len(clean_line) > 2:
                                dynamic_tasks.append(clean_line)
                    reply_part = f"{reply_part}\n\n**Tasks:**\n{tasks_part}"
                else:
                    reply_part = re.sub(r'^REPLY\s*[\-:]*\s*', '', raw, flags=re.IGNORECASE).strip()

                reply = api.format_reply(api.translate_reply_if_needed(reply_part, language))
                handoff_suggestion = orchestrator.detect_handoff_suggestion(text, agent_id)

                # Record conversation memory
                memory.record_conversation_turn(
                    user_message=text,
                    assistant_message=reply[:500],
                    interaction_type="chat",
                    metadata={"language": language, "agent_id": agent_id}
                )
                memory.record_emotion(
                    emotion=analysis_result.get("emotion", "neutral"),
                    stress=scores.get("summary", {}).get("stress_level", 5),
                )

                # Persist to database
                if api._db_manager:
                    try:
                        api._db_manager.save_chat_message(username, "user", text, analysis_result.get("emotion"))
                        api._db_manager.save_chat_message(username, "assistant", reply[:1000])
                        api._gamification.award_xp(username, "mood_checkin")
                    except Exception as db_err:
                        logger.warning(f"WS DB Error: {db_err}")

                # Build interventions list
                interventions = []
                if dynamic_tasks:
                    for task in dynamic_tasks[:3]:
                        emoji = "✓"
                        if "breath" in task.lower(): emoji = "🧘"
                        elif "water" in task.lower(): emoji = "💧"
                        elif "timer" in task.lower(): emoji = "⏱️"
                        elif "desk" in task.lower(): emoji = "🧹"
                        elif "priority" in task.lower(): emoji = "📋"
                        elif "goal" in task.lower(): emoji = "🎯"
                        interventions.append({"priority": "high", "category": "task", "title": task, "action": task, "emoji": emoji})

                rule_based_interventions = api.generate_interventions(user_data, scores) if user_data else []
                interventions.extend(rule_based_interventions)
                interventions = interventions[:5]

                for inv in interventions:
                    memory.record_intervention(inv.get('title', ''))

                if api._db_manager and interventions:
                    try:
                        api._gamification.award_xp(username, "intervention_completed")
                    except Exception:
                        pass

                # Build the complete final response metadata payload
                metadata = {
                    "reply": reply,
                    "analysis": analysis_result,
                    "scores": scores,
                    "interventions": interventions,
                    "handoff_suggestion": handoff_suggestion,
                    "state": {
                        "detected_state": state_result.get("state"),
                        "state_label": state_result.get("state_label"),
                        "state_emoji": state_result.get("state_emoji"),
                        "ui_mode": state_result.get("ui_mode"),
                        "coaching_tone": state_result.get("coaching_tone"),
                        "focus_mode": state_result.get("focus_mode"),
                        "task_size": state_result.get("task_size"),
                    }
                }

                await websocket.send_text(json.dumps({
                    "type": "metadata",
                    "metadata": metadata
                }))

            except json.JSONDecodeError:
                logger.warning(f"WS Chat received invalid JSON: {data}")
            except Exception as e:
                logger.error(f"Error handling WS Chat message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Processing failed: {str(e)}"
                }))

    except WebSocketDisconnect:
        logger.info(f"User '{username}' disconnected from real-time AI Chat session")
