from dataclasses import dataclass, field


@dataclass
class Notebook:
    url: str
    title: str = ''
    price: float = 0.0
    description: str = ''
    manufacturer: str = ''
    diagonal: str = ''
    screen_resolution: str = ''
    os: str = ''
    processor: str = ''
    op_men: str = ''
    type_video_card: str = ''
    video_card: str = ''
    type_drive: str = ''
    capacity_drive: str = ''
    auto_work_time: str = ''
    state: str = ''
    images: list = field(default_factory=list)
