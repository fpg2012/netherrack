from pydantic import BaseModel, Field


class NewDiscussion(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    body_md: str = Field(min_length=1, max_length=50_000)
    tags: list[str] = Field(default_factory=list, max_length=5)


class NewPost(BaseModel):
    body_md: str = Field(min_length=1, max_length=50_000)
    quote_post_id: int | None = None


class EditPost(BaseModel):
    body_md: str = Field(min_length=1, max_length=50_000)


class EditDiscussion(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    is_sticky: bool | None = None
    is_locked: bool | None = None
    tags: list[str] | None = Field(default=None, max_length=5)
    best_answer_post_id: int | None = None
