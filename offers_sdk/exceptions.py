
class AuthError(Exception):
    """Base exception for all authentication-related errors."""
    pass

class TokenRefreshError(AuthError):
    """Raised when the access token cannot be refreshed due to API or network failure."""
    pass

class MissingConfigurationError(Exception):
    """Raised when required environment variables are missing for SDK initialization."""
    pass

class InvalidProductDataError(Exception):
    """Raised when the product data is invalid or improperly formatted."""
    pass

class InvalidOfferDataError(Exception):
    """Raised when the offer data from the API is missing required fields."""
    pass

class ProductAlreadyRegisteredError(Exception):
    """Raised when a product is already registered with the API."""
    pass

class UnexpectedAPIResponseError(Exception):
    """Raised when the API returns a response that is not explicitly handled."""
    pass

class ProductNotFoundError(Exception):
    """Raised when the requested product is not registered or does not exist."""
    pass

class TokenCacheError(Exception):
    """Raised when reading or writing the cached access token fails."""
    pass

class MissingTokenCacheKeysError(TokenCacheError):
    """Raised when the cached token file is missing required keys."""
    pass



