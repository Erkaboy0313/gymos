from datetime import timedelta, datetime, time
import random

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import Gym, GymStaff, Member
from branches.models import Branch
from devices.models import Device
from subscriptions.models import (
    GymPlan,
    GymSubscription,
    MemberPlan,
    MemberSubscription,
)
from access.models import EntryLog


class Command(BaseCommand):
    help = "Seed realistic demo data for GymOS dashboard/testing"

    def handle(self, *args, **options):
        random.seed(42)
        User = get_user_model()

        # ---------- USERS ----------
        owner, _ = User.objects.get_or_create(
            username="owner",
            defaults={
                "email": "owner@example.com",
                # "telegram_user_id": 672639641,  # put your real tg id if needed
            },
        )
        owner.set_password("admin123")
        owner.save()

        admin, _ = User.objects.get_or_create(
            username="admin2",
            defaults={"email": "admin2@example.com"},
        )
        admin.set_password("admin123")
        admin.save()    

        staff, _ = User.objects.get_or_create(
            username="staff1",
            defaults={"email": "staff1@example.com"},
        )
        staff.set_password("admin123")
        staff.save()

        # ---------- GYM ----------
        gym, _ = Gym.objects.get_or_create(name="Iron Forge Gym")

        GymStaff.objects.get_or_create(
            gym=gym, user=owner,
            defaults={"role": GymStaff.ROLE_OWNER, "is_active": True}
        )
        GymStaff.objects.get_or_create(
            gym=gym, user=admin,
            defaults={"role": GymStaff.ROLE_ADMIN, "is_active": True}
        )
        GymStaff.objects.get_or_create(
            gym=gym, user=staff,
            defaults={"role": GymStaff.ROLE_STAFF, "is_active": True}
        )

        # ---------- BRANCHES ----------
        branch_names = ["Downtown", "West Side", "East End", "North Park"]
        branches = []
        for name in branch_names:
            b, _ = Branch.objects.get_or_create(
                gym=gym,
                name=name,
                defaults={
                    "address": f"{name} street, Tashkent",
                    "is_active": True,
                }
            )
            branches.append(b)

        # ---------- DEVICES ----------
        devices = []
        for branch in branches:
            d, _ = Device.objects.get_or_create(
                branch=branch,
                name=f"{branch.name} Gate {branch.id}",
                defaults={
                    "mode": Device.MODE_KIOSK,
                    "cooldown_seconds": 10,
                    "is_active": True,
                }
            )
            devices.append(d)

        # ---------- GYM SAAS ----------
        gym_plan_starter, _ = GymPlan.objects.get_or_create(
            name="starter",
            defaults={
                "duration_days": 30,
                "price": 299000,
                "is_active": True,
            }
        )
        now = timezone.now()
        GymSubscription.objects.get_or_create(
            gym=gym,
            plan=gym_plan_starter,
            defaults={
                "start_at": now - timedelta(days=20),
                "end_at": now + timedelta(days=10),
            }
        )

        # ---------- MEMBER PLAN ----------
        monthly_plan, _ = MemberPlan.objects.get_or_create(
            gym=gym,
            name="Monthly",
            defaults={
                "duration_days": 30,
                "price": 100000,
                "is_active": True,
            }
        )

        # ---------- MEMBERS ----------
        first_names = [
            "Ali", "Vali", "Bekzod", "Aziz", "Jasur", "Temur", "Sardor", "Rustam",
            "Oybek", "Anvar", "Shahzod", "Mirjalol", "Doston", "Asad", "Jamshid",
            "Akmal", "Bobur", "Sherzod", "Islom", "Murod"
        ]
        last_names = [
            "Karimov", "Toshmatov", "Aliyev", "Saidov", "Rahimov", "Bozorov",
            "Nazarov", "Qodirov", "Ergashev", "Abdullayev"
        ]

        members = []

        total_members = 80
        for i in range(total_members):
            full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            branch = random.choice(branches)

            member, _ = Member.objects.get_or_create(
                gym=gym,
                phone=f"+99890{1000000 + i}",
                defaults={
                    "branch": branch,
                    "full_name": full_name,
                    "is_active": True,
                    "telegram_user_id": None,
                    "is_inside": False,
                    "inside_since": None,
                }
            )
            members.append(member)

        # ---------- SUBSCRIPTIONS ----------
        today = timezone.localdate()

        # distribution:
        # 50 active
        # 10 expiring today
        # 10 expiring in 7 days
        # 10 expired
        active_members = members[:50]
        exp_today_members = members[50:60]
        exp_7_members = members[60:70]
        expired_members = members[70:80]

        def create_sub(member, start_at, end_at, price=100000):
            random_day = random.randint(1,6)
            random_month = random.randint(1,3)
            now = timezone.now().replace(month=random_month,day=random_day)
            sub = MemberSubscription.objects.create(
                member=member,
                plan=monthly_plan,
                start_at=start_at,
                end_at=end_at,
                price_snapshot=price,
            )
            sub.created_at = now
            sub.save()
            return sub

        # active normal
        for m in active_members:
            start = today - timedelta(days=random.randint(1, 20))
            end = start + timedelta(days=30)
            create_sub(m, start, end)

        # expiring today
        for m in exp_today_members:
            start = today - timedelta(days=30)
            end = today
            create_sub(m, start, end)

        # expiring in 7 days
        for m in exp_7_members:
            start = today - timedelta(days=23)
            end = today + timedelta(days=7)
            create_sub(m, start, end)

        # expired
        for m in expired_members:
            start = today - timedelta(days=60)
            end = today - timedelta(days=random.randint(1, 15))
            create_sub(m, start, end)



        # # ---------- REVENUE HISTORY ----------
        # # add historical subscriptions over past months to make charts look real
        # historical_members = random.sample(members, 30)
        # for m in historical_members:
        #     months_back = random.randint(2, 6)
        #     start = (today.replace(day=1) - timedelta(days=30 * months_back))
        #     end = start + timedelta(days=30)

        #     # avoid duplicates if exact same start exists
        #     exists = MemberSubscription.objects.filter(member=m, start_at=start).exists()
        #     if not exists:
        #         MemberSubscription.objects.create(
        #             member=m,
        #             plan=monthly_plan,
        #             start_at=start,
        #             end_at=end,
        #             price_snapshot=random.choice([90000, 100000, 110000]),
        #         )

        # # ---------- PRESENCE / ENTRY LOGS ----------
        # # some members currently inside
        # inside_members = random.sample(active_members, 18)
        # for m in inside_members:
        #     m.is_inside = True
        #     m.inside_since = now - timedelta(minutes=random.randint(5, 180))
        #     m.save(update_fields=["is_inside", "inside_since"])

        # # realistic logs for last 14 days
        # reasons_allow = "ok"
        # for days_ago in range(14, -1, -1):
        #     day = today - timedelta(days=days_ago)

        #     # daily traffic amount
        #     daily_entries = random.randint(12, 28)

        #     for _ in range(daily_entries):
        #         member = random.choice(active_members + exp_today_members + exp_7_members)
        #         branch = member.branch
        #         device = next(d for d in devices if d.branch_id == branch.id)

        #         log_dt = timezone.make_aware(
        #             datetime.combine(
        #                 day,
        #                 time(
        #                     hour=random.randint(6, 22),
        #                     minute=random.randint(0, 59),
        #                     second=random.randint(0, 59),
        #                 )
        #             )
        #         )

        #         event = random.choice([EntryLog.EVENT_IN, EntryLog.EVENT_OUT])
        #         allow = True
        #         reason = reasons_allow

        #         EntryLog.objects.create(
        #             gym=gym,
        #             branch=branch,
        #             device=device,
        #             member=member,
        #             allow=allow,
        #             reason=reason,
        #             event=event,
        #             token_member_id=member.id,
        #             token_gym_id=gym.id,
        #             created_at=log_dt,
        #         )

        #     # denied logs too
        #     daily_denied = random.randint(2, 7)
        #     denied_reasons = [
        #         "cooldown_active",
        #         "member_inactive_or_expired_or_frozen",
        #         "token_expired",
        #     ]

        #     denied_pool = members
        #     for _ in range(daily_denied):
        #         member = random.choice(denied_pool)
        #         branch = member.branch or random.choice(branches)
        #         device = next(d for d in devices if d.branch_id == branch.id)

        #         log_dt = timezone.make_aware(
        #             datetime.combine(
        #                 day,
        #                 time(
        #                     hour=random.randint(6, 22),
        #                     minute=random.randint(0, 59),
        #                     second=random.randint(0, 59),
        #                 )
        #             )
        #         )

        #         EntryLog.objects.create(
        #             gym=gym,
        #             branch=branch,
        #             device=device,
        #             member=member,
        #             allow=False,
        #             reason=random.choice(denied_reasons),
        #             event=None,
        #             token_member_id=member.id,
        #             token_gym_id=gym.id,
        #             created_at=log_dt,
        #         )

        self.stdout.write(self.style.SUCCESS("✅ Production-like demo seeded"))
        self.stdout.write("Login users:")
        self.stdout.write("  owner / admin123")
        self.stdout.write("  admin2 / admin123")
        self.stdout.write("  staff1 / admin123")
        self.stdout.write(f"Gym ID: {gym.id}")
        self.stdout.write(f"Dashboard: /api/dashboard/app/gyms/{gym.id}/")
        self.stdout.write(f"Members:   /api/users/app/gyms/{gym.id}/members/")
        self.stdout.write(f"Devices:   /api/devices/app/gyms/{gym.id}/devices/")
        self.stdout.write(f"Branches:  /api/branches/app/gyms/{gym.id}/branches/")