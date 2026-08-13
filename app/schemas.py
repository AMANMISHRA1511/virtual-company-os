from pydantic import BaseModel
class TaskCreate(BaseModel): title:str; description:str
class ApprovalRequest(BaseModel): approved:bool=True
class FileWrite(BaseModel): project:str='demo-company'; path:str; content:str; actor:str='Aarav'; task_id:int=0; note:str=''
class HandoffCreate(BaseModel): project:str='demo-company'; path:str; from_agent:str; to_agent:str; purpose:str=''
class ChatRequest(BaseModel): message:str

class CallCreate(BaseModel):
    from_agent:str='You'
    to_agent:str
    message:str=''
    channel:str='internal'
    create_task:bool=False
