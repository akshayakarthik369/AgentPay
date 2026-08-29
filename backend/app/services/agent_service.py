from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.task import Task
from app.schemas.agent import AgentCreate, AgentUpdate

def create_agent(db: Session, data: AgentCreate) -> Agent:
    """Insert a new Agent into SQLite."""
    # Requesters and Arbitrators default to trusted, worker/verifier default to pending_canary unless specified
    default_trust = "trusted" if data.agent_type in ("requester", "arbitrator") else "pending_canary"
    initial_trust = data.trust_status if data.trust_status is not None else default_trust

    agent = Agent(
        name=data.name,
        agent_type=data.agent_type,
        description=data.description,
        capabilities=data.capabilities,
        status=data.status or "available",
        trust_status=initial_trust,
        reputation_score=80 if initial_trust == "trusted" else 55.0,
        wallet_balance=0.0,
        tasks_completed=0,
        success_rate=0.0,
        average_verification_score=0.0,
        is_active=True
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

def get_agent_by_id(db: Session, agent_id: int) -> Optional[Agent]:
    """Fetch an agent by ID."""
    return db.query(Agent).filter(Agent.id == agent_id).first()

def get_agents(
    db: Session,
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    capability: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    trust_status: Optional[str] = None,
) -> List[Agent]:
    """Retrieve agents with optional filtering and search."""
    query = db.query(Agent)
    
    if agent_type:
        query = query.filter(Agent.agent_type == agent_type.strip().lower())
    if status:
        query = query.filter(Agent.status == status.strip().lower())
    if is_active is not None:
        query = query.filter(Agent.is_active == is_active)
    if trust_status:
        query = query.filter(Agent.trust_status == trust_status.strip().lower())
        
    agents = query.all()
    
    # Capability filtering (case-insensitive normalization)
    if capability:
        cap_normalized = capability.strip().lower()
        agents = [
            a for a in agents 
            if any(c.strip().lower() == cap_normalized for c in a.capabilities)
        ]
        
    # Full text search (case-insensitive across name, description, capabilities)
    if search:
        search_term = search.strip().lower()
        matched = []
        for a in agents:
            in_name = search_term in a.name.lower()
            in_desc = a.description and search_term in a.description.lower()
            in_caps = any(search_term in c.lower() for c in a.capabilities)
            if in_name or in_desc or in_caps:
                matched.append(a)
        agents = matched
        
    return agents

def update_agent(db: Session, agent_id: int, payload: AgentUpdate) -> Optional[Agent]:
    """Patch an existing agent."""
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        return None
        
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
        
    db.commit()
    db.refresh(agent)
    return agent

def set_agent_active_status(db: Session, agent_id: int, is_active: bool) -> Optional[Agent]:
    """Toggle agent active/inactive state."""
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        return None
    agent.is_active = is_active
    db.commit()
    db.refresh(agent)
    return agent

def get_discoverable_tasks_for_agent(db: Session, agent_id: int) -> Optional[dict]:
    """
    Find open tasks matching agent capabilities.
    Requirements:
    - Agent must be active
    - Agent status must be 'available'
    - Task status must be 'open'
    - Task required_capability matches one of the agent's capabilities (case-insensitive, normalized)
    """
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        return None
        
    # Return empty list of tasks if agent is inactive or not available
    if not agent.is_active or agent.status != "available":
        return {
            "agent": {
                "id": agent.id,
                "agent_code": agent.agent_code,
                "name": agent.name,
                "capabilities": agent.capabilities,
            },
            "agent_id": agent.id,
            "agent_code": agent.agent_code,
            "agent_name": agent.name,
            "capabilities": agent.capabilities,
            "tasks": [],
            "task_count": 0,
        }
        
    # Retrieve all open tasks
    open_tasks = db.query(Task).filter(Task.status == "open").all()
    
    # Normalize agent's capabilities
    agent_caps = {c.strip().lower() for c in agent.capabilities}
    
    matched_tasks = []
    for task in open_tasks:
        task_cap = task.required_capability.strip().lower()
        if task_cap in agent_caps:
            matched_tasks.append({
                "id": task.id,
                "task_id": task.id,
                "task_code": task.task_code,
                "title": task.title,
                "category": task.category,
                "required_capability": task.required_capability,
                "reward": task.reward,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "status": task.status,
            })
            
    return {
        "agent": {
            "id": agent.id,
            "agent_code": agent.agent_code,
            "name": agent.name,
            "capabilities": agent.capabilities,
        },
        "agent_id": agent.id,
        "agent_code": agent.agent_code,
        "agent_name": agent.name,
        "capabilities": agent.capabilities,
        "tasks": matched_tasks,
        "task_count": len(matched_tasks),
    }

