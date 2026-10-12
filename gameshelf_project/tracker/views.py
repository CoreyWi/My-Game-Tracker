from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import BeatForm, GameForm, SignUpForm
from .library import GameLibrary
from .models import Game, Platform


def _get_own_game(request, pk):
    """Fetch a game by id, but only if it belongs to the logged-in member."""
    return get_object_or_404(Game, pk=pk, owner=request.user)


def _redirect_back(request, fallback, **kwargs):
    """Go back to the page in the form's 'next' field if it's on this site,
    otherwise go to the fallback page."""
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return redirect(next_url)
    return redirect(fallback, **kwargs)


@login_required
def game_list(request):
    """Main page: stats at the top, filterable game list below."""
    library = GameLibrary(request.user)

    status = request.GET.get("status", "")
    platform_id = request.GET.get("platform", "")
    search = request.GET.get("q", "")
    games = library.filter(status=status, platform_id=platform_id, search=search)

    context = {
        "games": games,
        "total": library.total(),
        "summary": library.status_summary(),
        "completion_rate": library.completion_rate(),
        "total_beats": library.total_beats(),
        "most_beaten": library.most_beaten(),
        "backlog_count": len(library.backlog()),
        "platforms": Platform.objects.filter(games__owner=request.user).distinct(),
        "status_choices": Game.STATUS_CHOICES,
        "current_status": status,
        "current_platform": platform_id,
        "search": search,
        "is_filtered": bool(status or platform_id or search),
    }
    return render(request, "tracker/game_list.html", context)


@login_required
def game_detail(request, pk):
    game = _get_own_game(request, pk)
    return render(
        request,
        "tracker/game_detail.html",
        {
            "game": game,
            "completions": game.completions.all(),
            "beat_form": BeatForm(),
            "status_choices": Game.STATUS_CHOICES,
        },
    )


@login_required
def game_add(request):
    if request.method == "POST":
        form = GameForm(request.POST, owner=request.user)
        if form.is_valid():
            game = form.save()
            # If they added it as already beaten, give it a history entry.
            if game.times_beaten and not game.completions.exists():
                for _ in range(game.times_beaten):
                    game.completions.create(note="Added as already beaten")
            messages.success(request, f"Added {game.title} to your shelf.")
            return redirect("game_list")
    else:
        form = GameForm(owner=request.user)
    return render(request, "tracker/game_form.html", {"form": form, "mode": "Add"})


@login_required
def game_edit(request, pk):
    game = _get_own_game(request, pk)
    if request.method == "POST":
        form = GameForm(request.POST, instance=game, owner=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Saved changes to {game.title}.")
            return redirect("game_detail", pk=game.pk)
    else:
        form = GameForm(instance=game, owner=request.user)
    return render(
        request, "tracker/game_form.html", {"form": form, "mode": "Edit", "game": game}
    )


@login_required
def game_delete(request, pk):
    game = _get_own_game(request, pk)
    if request.method == "POST":
        title = game.title
        game.delete()
        messages.success(request, f"Removed {title} from your shelf.")
        return redirect("game_list")
    return render(request, "tracker/game_confirm_delete.html", {"game": game})


@login_required
@require_POST
def game_beat(request, pk):
    """Log one more beat of this game."""
    game = _get_own_game(request, pk)
    form = BeatForm(request.POST)
    note = form.cleaned_data["note"] if form.is_valid() else ""
    game.mark_beaten(note=note)
    messages.success(
        request, f"Nice! {game.title} beaten {game.times_beaten} time(s)."
    )
    return _redirect_back(request, "game_detail", pk=game.pk)


@login_required
@require_POST
def game_hundred(request, pk):
    """Mark this game 100% complete."""
    game = _get_own_game(request, pk)
    game.mark_hundred()
    messages.success(request, f"{game.title} is now 100% complete!")
    return redirect("game_detail", pk=game.pk)


@login_required
@require_POST
def game_set_status(request, pk):
    """Quick status change from the list or detail page."""
    game = _get_own_game(request, pk)
    new_status = request.POST.get("status", "")
    valid = dict(Game.STATUS_CHOICES)
    if new_status not in valid:
        messages.error(request, "That isn't a valid status.")
    elif new_status == Game.HUNDRED:
        game.mark_hundred()
        messages.success(request, f"{game.title} is now 100% complete!")
    else:
        if new_status == Game.COMPLETED and game.times_beaten == 0:
            game.mark_beaten(note="Marked completed")
        else:
            game.status = new_status
            game.save()
        messages.success(request, f"{game.title} set to {valid[new_status]}.")
    return _redirect_back(request, "game_list")


def signup(request):
    """Create a member account and log them straight in."""
    if request.user.is_authenticated:
        return redirect("game_list")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to GameShelf, {user.username}!")
            return redirect("game_list")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})