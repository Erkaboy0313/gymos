from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from access.serializers import DeviceValidateSerializer
from access.models import EntryLog
from access.selectors import is_in_cooldown
from access.security import is_banned, record_fail, reset_fail
from devices.models import Device
from users.models import Member, Gym
from identifiers.services import verify_member_qr_token
from subscriptions.services import is_gym_active, is_member_active


class DeviceValidateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = DeviceValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_id = serializer.validated_data["device_id"]
        api_key = serializer.validated_data["api_key"]
        token = serializer.validated_data["token"]

        ip = request.META.get("REMOTE_ADDR", "unknown")

        if is_banned(device_id, ip):
            return Response({"allow": False, "reason": "rate_banned"}, status=429)

        device = (
            Device.objects.filter(id=device_id, is_active=True)
            .select_related("branch", "branch__gym")
            .first()
        )
        if not device:
            return Response({"allow": False, "reason": "device_not_found"}, status=404)

        if device.api_key != api_key:
            record_fail(device_id, ip)
            return Response({"allow": False, "reason": "bad_api_key"}, status=401)

        gym = device.branch.gym
        event = None
        allow = False
        reason = "unknown"
        member = None
        token_member_id = None
        token_gym_id = None

        ok, payload, tok_reason = verify_member_qr_token(token)
        if not ok:
            reason = f"token_{tok_reason}"
        else:
            token_gym_id = payload.get("g")
            token_member_id = payload.get("m")

            if int(token_gym_id) != int(gym.id):
                reason = "token_wrong_gym"
            else:
                member = Member.objects.filter(id=token_member_id, gym_id=gym.id).first()

                if not member:
                    reason = "member_not_found"
                elif not is_gym_active(gym):
                    reason = "gym_subscription_inactive"
                elif not is_member_active(member):
                    reason = "member_inactive_or_expired_or_frozen"
                elif gym.branch_access_mode == Gym.ACCESS_REGISTERED_ONLY and member.branch_id != device.branch_id:
                    reason = "wrong_branch"
                elif is_in_cooldown(member.id, device.branch_id, device.cooldown_seconds):
                    reason = "cooldown_active"
                else:
                    allow = True
                    reason = "ok"
                    now = timezone.now()

                    if member.is_inside:
                        event = EntryLog.EVENT_OUT
                        member.is_inside = False
                        member.inside_since = None
                    else:
                        event = EntryLog.EVENT_IN
                        member.is_inside = True
                        member.inside_since = now

                    member.save(update_fields=["is_inside", "inside_since"])

        SPAM_REASONS = {
            "token_invalid",
            "token_badsig",
            "token_expired",
            "token_malformed",
            "bad_api_key",
        }

        if not allow and reason in SPAM_REASONS:
            record_fail(device_id, ip)

        if allow:
            reset_fail(device_id, ip)

        EntryLog.objects.create(
            gym=gym,
            branch=device.branch,
            device=device,
            member=member,
            allow=allow,
            reason=reason,
            event=event,
            token_member_id=token_member_id,
            token_gym_id=token_gym_id,
        )

        if allow:
            return Response({
                "allow": True,
                "reason": "ok",
                "event": event,
                "member": {
                    "id": member.id,
                    "full_name": member.full_name,
                }
            }, status=200)

        return Response({"allow": False, "reason": reason}, status=200)