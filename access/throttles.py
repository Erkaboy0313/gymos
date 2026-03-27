from rest_framework.throttling import SimpleRateThrottle

class KioskAnonIPThrottle(SimpleRateThrottle):
    scope = "kiosk_ip"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)  # IP
        return self.cache_format % {"scope": self.scope, "ident": ident}


class KioskDeviceThrottle(SimpleRateThrottle):
    scope = "kiosk_device"

    def get_cache_key(self, request, view):
        # Rate limit per device_id (stronger than IP for kiosks behind NAT)
        device_id = view.kwargs.get("device_id")
        if not device_id:
            return None
        return self.cache_format % {"scope": self.scope, "ident": f"dev:{device_id}"}