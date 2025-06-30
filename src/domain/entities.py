from dataclasses import dataclass, field

@dataclass
class Channel:
    id: int
    title: str
    enabled: bool
    work_interval_minutes: int
    rss_links: list[str] = field(default_factory=list)
    last_sent_link: list[str] | None = None


@dataclass
class News:
    title: str
    link: str
    description: str
    image_link: bytes | None
