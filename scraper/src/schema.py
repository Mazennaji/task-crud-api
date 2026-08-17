from pydantic import BaseModel, HttpUrl, PositiveFloat, field_validator


class CleanRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_gbp: PositiveFloat
    price_text: str
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: HttpUrl
    fetched_at: str

    @field_validator("title", "price_text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value