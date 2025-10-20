from dataclasses import dataclass


@dataclass
class Customer:
    id: int
    name: str
    annual_spend: float
    country: str
