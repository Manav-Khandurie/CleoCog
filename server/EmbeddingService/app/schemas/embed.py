from pydantic import BaseModel

class TextInput(BaseModel):
    inputs: str
    flag :  bool 