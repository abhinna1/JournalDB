import yaml

from journal_db.errors import ParseError
from journal_db.schema import MetaDataSchema


def parse(content: str) -> MetaDataSchema:
    """Parse a raw .md file string and return a typed MetaDataSchema."""

    # Need exactly 3 parts: [before, yaml_block, body]
    parts = content.split("---", 2)
    if len(parts) != 3:
        raise ParseError("Missing '---' delimiters in entry file.")

    try:
        front_matter = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise ParseError(f"Invalid YAML in front-matter: {exc}") from exc

    if front_matter is None:
        front_matter = {}

    return MetaDataSchema.from_dict({**front_matter, "body": parts[2].strip()})
