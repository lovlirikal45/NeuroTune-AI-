from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ECURequest(BaseModel):
    size: int
    entropy: float

@app.post("/analyze")
def analyze(data: ECURequest):

    risk_score = min(100, data.entropy * 1.2)

    return {
        "risk_score": risk_score,
        "recommendation": "safe tuning range" if risk_score < 60 else "risky calibration",
        "afr_target": 14.7 - (data.entropy / 50)
    }