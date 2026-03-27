from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from access.models import EntryLog
from users.permissions import require_gym_membership
from users.models import Gym, Member
from devices.models import Device
from identifiers.services import verify_member_qr_token
from subscriptions.services import is_gym_active, is_member_active
from access.selectors import is_in_cooldown
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .throttles import KioskAnonIPThrottle,KioskDeviceThrottle
from .security import is_banned,record_fail,reset_fail


class KioskValidateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [KioskDeviceThrottle,KioskAnonIPThrottle]

    def post(self, request, gym_id: int, device_id: int):
        require_gym_membership(request.user, gym_id)

        ip = request.META.get("REMOTE_ADDR", "unknown")

        # 0) bruteforce ban fast-exit (device+ip)
        if is_banned(device_id, ip):
            return Response({"allow": False, "reason": "rate_banned"}, status=429)

        token = request.data.get("token")
        if not token:
            record_fail(device_id, ip)
            return Response({"allow": False, "reason": "missing_token"}, status=400)

        device = Device.objects.filter(
            id=device_id, branch__gym_id=gym_id, is_active=True
        ).select_related("branch", "branch__gym").first()
        if not device:
            return Response({"allow": False, "reason": "device_not_found"}, status=404)

        if device.mode != Device.MODE_KIOSK:
            return Response({"allow": False, "reason": "device_not_kiosk"}, status=400)

        gym = device.branch.gym
        event = None
        allow = False
        reason = "unknown"
        member = None
        token_member_id = None
        token_gym_payload = None

        ok, payload, tok_reason = verify_member_qr_token(token)
        if not ok:
            reason = f"token_{tok_reason}"
        else:
            token_gym_payload = payload.get("g")
            token_member_id = payload.get("m")

            if int(token_gym_payload) != int(gym_id):
                reason = "token_wrong_gym"
            else:
                member = Member.objects.filter(id=token_member_id, gym_id=gym_id).first()
                if not member:
                    reason = "member_not_found"
                elif not is_gym_active(gym):
                    reason = "gym_subscription_inactive"
                elif not is_member_active(member):
                    reason = "member_inactive_or_expired_or_frozen"
                elif is_in_cooldown(member.id, device.branch_id, device.cooldown_seconds):
                    reason = "cooldown_active"
                elif gym.branch_access_mode == Gym.ACCESS_REGISTERED_ONLY:
                    if member.branch_id != device.branch_id:
                        reason = "wrong_branch"
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

        # 1) record fails only for token-spam-ish reasons
        SPAM_REASONS = {
            "token_badsig",
            "token_expired",
            "token_format",
        }
        if not allow and reason in SPAM_REASONS:
            record_fail(device_id, ip)

        # 2) success resets fail counter (so legit users don't get banned)
        if allow:
            reset_fail(device_id, ip)
        

        EntryLog.objects.create(
            gym=gym,
            branch=device.branch,
            device=device,
            member=member,
            allow=allow,
            reason=reason,
            event = event,
            token_member_id=token_member_id,
            token_gym_id=token_gym_payload,
        )

        if allow:
            return Response(
                {"allow": True, "reason": "ok", "member": {"id": member.id, "full_name": member.full_name}},
                status=200,
            )
        return Response({"allow": False, "reason": reason}, status=200)
    
class KioskPageView(LoginRequiredMixin, View):
    def get(self, request, gym_id: int, device_id: int):
        device = get_object_or_404(
            Device,
            id=device_id,
            branch__gym_id=gym_id,
            mode=Device.MODE_KIOSK,
            is_active=True,
        )
        return render(request, "access/kiosk.html", {
            "gym_id": gym_id,
            "device_id": device_id,
            "device_name": device.name,
        })
