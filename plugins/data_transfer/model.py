from dataclasses import dataclass


@dataclass
class BaseHook:
  hostname: str
  username: str
  password: str
  port: int
