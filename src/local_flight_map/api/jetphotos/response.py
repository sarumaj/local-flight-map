from dataclasses import dataclass


@dataclass
class JetPhotosResponse:
    """
    Represents the response from the JetPhotos API when fetching an aircraft photo.

    Attributes:
        registration: The registration of the aircraft.
        photo_url: The URL of the aircraft photo.
        photo_data: The photo data as bytes.
        content_type: The content type of the photo.
    """

    registration: str
    photo_url: str
    photo_data: bytes
    content_type: str
