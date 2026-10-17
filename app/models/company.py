class Company:
    """
    Represents a company that offers jobs.
    """

    def __init__(
        self,
        name="",
        industry="",
        website="",
        locations=None,
        roles=None,
    ):

        self.name = name
        self.industry = industry
        self.website = website

        self.locations = locations if locations else []

        self.roles = roles if roles else []

    @classmethod
    def from_dict(cls, data):

        return cls(

            name=data.get("name", ""),

            industry=data.get("industry", ""),

            website=data.get("website", ""),

            locations=data.get("locations", []),

            roles=data.get("roles", [])
        )