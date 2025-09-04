# File validation settings
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
ALLOWED_IMAGE_MIME_TYPES = ["image/jpeg", "image/png"]
ALLOWED_IMAGE_MODES = ["RGB", "RGBA", "L"]
MAX_IMAGE_SIZE_MB = 10
MAX_DOCUMENT_SIZE_MB = 20
MAX_IMAGE_DIMENSIONS = (5000, 5000)

ALLOWED_DOCUMENT_EXTENSIONS = [
    "pdf", "doc", "docx", "txt", "odt", "rtf",
    "xls", "xlsx", "ppt", "pptx", "zip", "rar"
]

ALLOWED_DOCUMENT_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.oasis.opendocument.text",
    "application/rtf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/zip",
    "application/x-rar-compressed",
]

# Social platform validation settings
ALLOWED_SOCIAL_PLATFORMS = {
    'facebook': ['facebook.com'],
    'twitter': ['twitter.com'],
    'linkedin': ['linkedin.com'],
    'instagram': ['instagram.com'],
    'youtube': ['youtube.com', 'youtu.be'],
    'tiktok': ['tiktok.com'],
    'telegram': ['t.me', 'telegram.me'],
}

# Communications app: notification types seeding configuration
COMMUNICATIONS_NOTIFICATION_TYPES = [
    {
        'code': 'startup_saved',
        'name': 'Startup Saved',
        'description': 'Notification when a user saves a startup to their favorites',
        'default_frequency': 'immediate',
        'is_active': True,
    },
    {
        'code': 'project_followed',
        'name': 'Project Followed',
        'description': 'Notification when a user follows a project',
        'default_frequency': 'immediate',
        'is_active': True,
    },
    {
        'code': 'message_received',
        'name': 'Message Received',
        'description': 'Notification when a user receives a new message',
        'default_frequency': 'immediate',
        'is_active': True,
    },
    {
        'code': 'activity_summarized',
        'name': 'Activity Summarized',
        'description': 'Weekly summary of your activity',
        'default_frequency': 'weekly_summary',
        'is_active': True,
    },
    {
        'code': 'project_updated',
        'name': 'Project Updated',
        'description': 'Notification when a project you are subscribed to is updated',
        'default_frequency': 'immediate',
        'is_active': True,
    },
]

# Chat words settings
FORBIDDEN_WORDS_SET = {
    "spam", "scam", "xxx", "viagra", "free money", "lottery", "bitcoin",
    "crypto", "click here", "subscribe", "buy now", "offer", "promotion",
    "gamble", "casino", "adult", "nsfw", "sex", "porn", "nude"
}

ALLOWED_TAGS = ["b", "i", "u", "a"]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"]
}
