from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tracker.models import Game, Platform

PLATFORMS = [
    "PC", "PlayStation 5", "PlayStation 4", "Xbox Series X|S",
    "Nintendo Switch", "Nintendo Switch 2", "Retro / Other",
]

# (title, platform, status, times_beaten, notes)
DEMO_GAMES = [
    ("Hollow Knight", "Nintendo Switch", Game.HUNDRED, 2, "Got every charm."),
    ("Elden Ring", "PlayStation 5", Game.COMPLETED, 1, ""),
    ("Stardew Valley", "PC", Game.INCOMPLETE, 0, "Year 2, spring."),
    ("The Legend of Zelda: Breath of the Wild", "Nintendo Switch", Game.FORGOTTEN, 0,
     "Stopped before the last Divine Beast."),
    ("Hades", "PC", Game.COMPLETED, 3, "Heat 8 clear."),
    ("Baldur's Gate 3", "PC", Game.NEW, 0, "Bought at Cartridge & Crate."),
    ("Super Mario Bros. 3", "Retro / Other", Game.HUNDRED, 5, "NES cart."),
    ("Celeste", "Nintendo Switch", Game.INCOMPLETE, 0, "Chapter 6."),
]


class Command(BaseCommand):
    help = "Load platforms and a demo member with sample games."

    def handle(self, *args, **options):
        for name in PLATFORMS:
            Platform.objects.get_or_create(name=name)

        User = get_user_model()
        user, created = User.objects.get_or_create(username="demo")
        if created:
            user.set_password("GameShelf2026!")
            user.save()

        added = 0
        for title, platform_name, status, beaten, notes in DEMO_GAMES:
            platform = Platform.objects.get(name=platform_name)
            game, made = Game.objects.get_or_create(
                owner=user, title=title, platform=platform,
                defaults={"status": status, "times_beaten": beaten, "notes": notes},
            )
            if made:
                added += 1
                for _ in range(beaten):
                    game.completions.create(note="Demo data")

        self.stdout.write(self.style.SUCCESS(
            f"Platforms ready. Demo user 'demo' (password GameShelf2026!) "
            f"{'created' if created else 'already existed'}; {added} games added."
        ))