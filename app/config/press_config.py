from app.models.dtos import PressDTO

PRESS_LIST = [
    PressDTO(code="hk", name="한국경제", domain="hankyung.com"),
    PressDTO(code="mk", name="매일경제", domain="mk.co.kr"),
    PressDTO(code="sed", name="서울경제", domain="sedaily.com"),
]

PRESS_CODE_MAP = {press.code: press for press in PRESS_LIST}
