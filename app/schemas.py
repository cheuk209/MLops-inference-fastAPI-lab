from pydantic import BaseModel

class PredictRequest(BaseModel):
    feature_1: float
    feature_2: float

class PredictResponse(BaseModel):
    prediction: float
    model_version: str
