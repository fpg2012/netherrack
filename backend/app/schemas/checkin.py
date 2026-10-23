from pydantic import BaseModel


class CheckInStatus(BaseModel):
    checked_in_today: bool
    current_streak: int
    total_days: int
