from dataclasses import dataclass, field, astuple
@dataclass(frozen=True, order=True, repr=False)
class SearchUrl:
    url: str
    alias: str

    def __repr__(self):
        return f'<a href="{self.url}">{self.alias}</a>'
    
    def __iter__(self):
        return iter(astuple(self))
