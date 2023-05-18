from dataclasses import dataclass, field, astuple
from object.search_url import SearchUrl

@dataclass(order=True, repr=False)
class Estate:
    url: str
    image_url: str
    search_url: SearchUrl = field(init=False)
    price_usd: int
    price_usd_old: int
    price_byn: int
    room_count: int
    area: float
    address: str
    
    def __repr__(self):
        usd = str(self.price_usd)[::-1]
        byn = str(self.price_byn)[::-1]
        price_usd_string = ' '.join(usd[i:i+3] for i in range(0, len(usd), 3))[::-1]
        price_byn_string = ' '.join(byn[i:i+3] for i in range(0, len(byn), 3))[::-1]
        return f'{self.address}\n{self.room_count} комн.\n{self.area} кв.м.\n{price_usd_string} $\n{price_byn_string} BYN\n\n{self.url}'
    
    def __iter__(self):
        return iter(astuple(self))
