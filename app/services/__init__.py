"""
Service registry wiring.

To add a new language:
  1. Create app/services/<lang>_tts_service.py with a subclass of BaseTTSService.
  2. Import it here and call registry.register("<lang_code>", <YourService>()).
"""

from app.services import registry
from app.services.amharic_tts_service import AmharicTTSService

registry.register("am", AmharicTTSService())
