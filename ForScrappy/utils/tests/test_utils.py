import pytest

from settings import BASE_URL
from utils.exceptions import URLNotValidFormat
from utils.utils import LinkValidator, validate_category


@pytest.mark.asyncio
async def test_link_validator_wrong_link() -> None:
    """Test if given link is valid"""

    validator: LinkValidator = LinkValidator(link="https://example.com/")

    with pytest.raises(URLNotValidFormat):
        async with validator:
            ...


@pytest.mark.asyncio
async def test_link_validator_without_slash() -> None:
    """Test if given link is valid -> slash at the end of url expected"""

    validator: LinkValidator = LinkValidator(link="https://example.com")

    with pytest.raises(URLNotValidFormat):
        async with validator:
            ...


@pytest.mark.asyncio
async def test_link_validator() -> None:
    """Test if given link is valid -> slash at the end of url expected"""

    validator: LinkValidator = LinkValidator(link=f"{BASE_URL}trance/")
    async with validator as validated:
        assert validated is None


def test_validate_category_in_link() -> None:
    """Test if given category is available in link"""

    assert validate_category(link=f"{BASE_URL}trance/") == "trance"


def test_validate_category_not_in_link() -> None:
    """Test if given category is available in link"""

    with pytest.raises(ValueError):
        validate_category(link=f"{BASE_URL}ttt/")


def test_validate_category_wrong_link() -> None:
    """Test if given category is available in link"""

    with pytest.raises(ValueError):
        validate_category(link=f"{BASE_URL}/ttt//")
