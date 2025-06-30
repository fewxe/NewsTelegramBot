from dataclasses import dataclass

@dataclass
class ChannelDTO:
    id: int
    title: str
    enabled: bool
    rss_links: list[str]
    work_interval_minutes: int