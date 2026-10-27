from pydantic import BaseModel, HttpUrl


class OnboardingLinkRequest(BaseModel):
    return_url: HttpUrl
