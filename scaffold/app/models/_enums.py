from sqlalchemy import Enum

DeskEnum = Enum(
    "metals", "energy", "agriculture",
    name="desk_enum",
    create_type=False,
)