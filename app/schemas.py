from pydantic import BaseModel
class TaskCreate(BaseModel):
    title:str
    description:str
    assigned_to:str|None=None
class HandoffCreate(BaseModel):
    project:str='demo-company'
    path:str
    from_agent:str
    to_agent:str
    purpose:str=''
class ChatRequest(BaseModel): message:str
class CallCreate(BaseModel):
    to_agent:str
    message:str=''
    create_task:bool=False
