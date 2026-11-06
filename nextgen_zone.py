#!/usr/bin/env python3
"""
NextGen Zone: a terminal toolkit that automates the repetitive parts of running
a gaming YouTube channel. Needs only Python 3.8+ (no extra packages).

Quick start:
    python3 nextgen_zone.py --help
    python3 nextgen_zone.py titles --game "GTA San Andreas" --count 10
    python3 nextgen_zone.py calendar --weeks 4 --long 2 --shorts 6 --add
    python3 nextgen_zone.py report

Your data is stored in ~/.nextgen_zone/data.json
"""
import argparse, csv, json, random, sys, time
from datetime import date, timedelta
from pathlib import Path

CHANNEL = "NextGen Zone"
DATA = Path.home() / ".nextgen_zone" / "data.json"
STAGES = ["idea", "recording", "editing", "scheduled", "published"]
DAILY = ["Reply to comments", "Post a Short", "Check analytics", "Back up footage"]

LONG_TITLES = [
    "5 {g} Tricks Nobody Tells You",
    "{g} Beginner Guide: Everything You Need to Know",
    "I Tried to Finish {g} Using Only One Weapon",
    "The Best Settings for {g}",
    "{g}: Hidden Secrets Most Players Never Found",
    "My Best Moments in {g} This Week",
    "Stop Making These Mistakes in {g}",
    "{g}: The Fastest Way to Get Money and Resources",
    "Ranking Every Mission in {g} From Easiest to Hardest",
    "What Happens If You Do This in {g}?",
]
SHORT_IDEAS = [
    "Hidden secret in {g}", "Easter egg you can try now in {g}", "Beginner trick in {g}",
    "Funniest glitch in {g}", "Best loadout in {g}", "Clutch moment in {g}",
    "Challenge run in {g}", "Feature most players miss in {g}", "{g} tip #{n}",
]


# ---------- storage ----------
def load():
    if DATA.exists():
        return json.loads(DATA.read_text())
    return {"videos": [], "ideas": [], "daily": {}, "next_id": 1}


def save(d):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(d, indent=2))


def new_id(d):
    i = d["next_id"]
    d["next_id"] += 1
    return i


# ---------- helpers ----------
def tags_for(game):
    g = game
    base = [CHANNEL, CHANNEL.replace(" ", "").lower(), g, f"{g} gameplay", f"{g} tips",
            f"{g} tricks", f"{g} for beginners", f"{g} secrets", f"{g} highlights",
            "gaming", "gameplay", "gaming shorts"]
    return base


def description(title, game):
    hashtags = f"#{CHANNEL.replace(' ', '')} #{game.replace(' ', '')} #Gaming"
    return (f"{title}\n\nWelcome to {CHANNEL}! In this video I share {game} tips, tricks, "
            f"secrets, and gameplay.\n\n0:00 Intro\n[add timestamps here]\n\n"
            f"Subscribe to {CHANNEL} for more {game} content.\n\n"
            f"Follow me: [your links here]\nBusiness: [your email here]\n\n{hashtags}\n")


def show_video(v):
    d = v.get("date") or "no date"
    print(f"  #{v['id']:<3} [{v['stage']:<9}] {v['title']}  ({d})")


# ---------- commands ----------
def cmd_titles(a):
    pool = random.sample(LONG_TITLES, min(a.count, len(LONG_TITLES)))
    for i, t in enumerate(pool, 1):
        print(f"{i:>2}. {t.format(g=a.game)}")


def cmd_tags(a):
    print(", ".join(tags_for(a.game)))


def cmd_desc(a):
    print(description(a.title, a.game))


def cmd_idea(a):
    d = load()
    if a.action == "add":
        d["ideas"].append({"id": new_id(d), "text": " ".join(a.text)})
        save(d); print("Idea saved.")
    elif a.action == "list":
        for i in d["ideas"]:
            print(f"  #{i['id']:<3} {i['text']}")
        if not d["ideas"]:
            print("  No ideas yet. Add one with: idea add \"your idea\"")
    elif a.action in ("rm", "promote"):
        n = int(a.text[0])
        it = next((i for i in d["ideas"] if i["id"] == n), None)
        if not it:
            sys.exit("No idea with that id.")
        d["ideas"].remove(it)
        if a.action == "promote":
            d["videos"].append({"id": new_id(d), "title": it["text"], "game": "", "stage": "idea", "date": ""})
        save(d); print("Done.")


def cmd_video(a):
    d = load()
    if a.action == "add":
        d["videos"].append({"id": new_id(d), "title": " ".join(a.text), "game": a.game or "",
                            "stage": "idea", "date": a.date or ""})
        save(d); print("Video added.")
    elif a.action == "list":
        for s in STAGES:
            vs = [v for v in d["videos"] if v["stage"] == s]
            if vs:
                print(s.upper())
                for v in vs: show_video(v)
        if not d["videos"]:
            print("  No videos yet.")
    else:
        n = int(a.text[0])
        v = next((x for x in d["videos"] if x["id"] == n), None)
        if not v:
            sys.exit("No video with that id.")
        if a.action == "rm":
            d["videos"].remove(v)
        elif a.action == "next" and v["stage"] != "published":
            v["stage"] = STAGES[STAGES.index(v["stage"]) + 1]
            if v["stage"] == "published":
                v["pub"] = str(date.today())
        elif a.action == "date":
            v["date"] = a.date
        save(d); print("Updated."); show_video(v) if a.action != "rm" else None


def cmd_calendar(a):
    start = date.fromisoformat(a.start) if a.start else date.today() + timedelta(days=(7 - date.today().weekday()) % 7 or 7)
    long_days = [1, 4, 2, 0, 3, 5, 6][:a.long]
    rows, k = [], 0
    for w in range(a.weeks):
        wk = start + timedelta(weeks=w)
        for dd in sorted(long_days):
            rows.append((wk + timedelta(days=dd), "Long video", LONG_TITLES[k % len(LONG_TITLES)].format(g=a.game)))
            k += 1
        for i in range(a.shorts):
            rows.append((wk + timedelta(days=(i * 7) // a.shorts), "Short",
                         SHORT_IDEAS[(w * a.shorts + i) % len(SHORT_IDEAS)].format(g=a.game, n=w * a.shorts + i + 1)))
    rows.sort(key=lambda r: (r[0], r[1] != "Long video"))
    for r in rows:
        print(f"{r[0]}  {r[0].strftime('%a')}  {r[1]:<10} {r[2]}")
    out = Path(a.out)
    with out.open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "day", "type", "topic"])
        for r in rows: w.writerow([r[0], r[0].strftime("%a"), r[1], r[2]])
    print(f"\nSaved {len(rows)} items to {out}")
    if a.add:
        d = load()
        for r in rows:
            if r[1] == "Long video":
                d["videos"].append({"id": new_id(d), "title": r[2], "game": a.game, "stage": "idea", "date": str(r[0])})
        save(d); print("Long videos added to your pipeline.")


def cmd_daily(a):
    d = load(); today = str(date.today())
    done = d["daily"].get(today, [])
    for n in a.done or []:
        if 1 <= n <= len(DAILY) and n not in done:
            done.append(n)
    d["daily"] = {today: done}; save(d)
    for i, t in enumerate(DAILY, 1):
        print(f"  [{'x' if i in done else ' '}] {i}. {t}")
    print("\nMark items done with: daily --done 1 2")


def cmd_report(a):
    d = load(); t = date.today(); vs = d["videos"]; notes = []; score = 100
    over = [v for v in vs if v["stage"] != "published" and v.get("date") and v["date"] < str(t)]
    if over:
        score -= 20; notes.append("Overdue: " + ", ".join(v["title"] for v in over))
    if sum(v["stage"] == "editing" for v in vs) > 3:
        score -= 10; notes.append("More than 3 videos are stuck in editing. Finish one before recording more.")
    soon = [v for v in vs if v["stage"] != "published" and v.get("date") and str(t) <= v["date"] <= str(t + timedelta(days=7))]
    if not soon:
        score -= 20; notes.append("Nothing is planned for the next 7 days.")
    pubs = sorted(v["pub"] for v in vs if v.get("pub"))
    if pubs and (t - date.fromisoformat(pubs[-1])).days > 7:
        score -= 10; notes.append(f"Your last upload was {(t - date.fromisoformat(pubs[-1])).days} days ago.")
    if len(d["ideas"]) < 3:
        score -= 10; notes.append("Your idea list is low. Add a few ideas.")
    left = len(DAILY) - len(d["daily"].get(str(t), []))
    if left:
        score -= min(20, left * 5); notes.append(f"{left} daily routine item(s) still open.")
    print(f"Workspace health: {max(score, 0)}/100")
    for n in notes or ["Everything looks healthy. Keep going."]:
        print("  -", n)


def cmd_rest(a):
    def run(mins, label):
        end = time.time() + mins * 60
        while time.time() < end:
            left = int(end - time.time())
            print(f"\r{label}: {left // 60:02d}:{left % 60:02d}  ", end="", flush=True)
            time.sleep(1)
        print("\a\n")
    try:
        for c in range(1, a.cycles + 1):
            print(f"Round {c}"); run(a.work, "Focus")
            print("Break time. Look away from the screen, drink water, stretch.")
            run(a.rest, "Break")
        print("All rounds done. Great work!")
    except KeyboardInterrupt:
        print("\nStopped.")


def cmd_backup(a):
    out = Path(a.out)
    out.write_text(json.dumps(load(), indent=2)); print(f"Backup saved to {out}")


def main():
    p = argparse.ArgumentParser(prog="nextgen_zone", description=f"{CHANNEL} terminal toolkit")
    s = p.add_subparsers(dest="cmd", required=True)

    x = s.add_parser("titles", help="video title ideas"); x.add_argument("--game", required=True)
    x.add_argument("--count", type=int, default=10); x.set_defaults(f=cmd_titles)
    x = s.add_parser("tags", help="tags for a game"); x.add_argument("--game", required=True); x.set_defaults(f=cmd_tags)
    x = s.add_parser("description", help="video description"); x.add_argument("--title", required=True)
    x.add_argument("--game", required=True); x.set_defaults(f=cmd_desc)

    x = s.add_parser("idea", help="idea inbox"); x.add_argument("action", choices=["add", "list", "rm", "promote"])
    x.add_argument("text", nargs="*"); x.set_defaults(f=cmd_idea)
    x = s.add_parser("video", help="video pipeline"); x.add_argument("action", choices=["add", "list", "next", "date", "rm"])
    x.add_argument("text", nargs="*", help="title (add) or id (next, date, rm)")
    x.add_argument("--game"); x.add_argument("--date", help="YYYY-MM-DD"); x.set_defaults(f=cmd_video)

    x = s.add_parser("calendar", help="generate a posting calendar")
    x.add_argument("--game", default="[Game]"); x.add_argument("--weeks", type=int, default=4)
    x.add_argument("--long", type=int, default=2); x.add_argument("--shorts", type=int, default=6)
    x.add_argument("--start", help="YYYY-MM-DD, default next Monday"); x.add_argument("--out", default="nextgen_calendar.csv")
    x.add_argument("--add", action="store_true", help="also add the long videos to your pipeline"); x.set_defaults(f=cmd_calendar)

    x = s.add_parser("daily", help="daily checklist"); x.add_argument("--done", type=int, nargs="*"); x.set_defaults(f=cmd_daily)
    x = s.add_parser("report", help="workspace health report"); x.set_defaults(f=cmd_report)
    x = s.add_parser("rest", help="focus and break timer"); x.add_argument("--work", type=int, default=25)
    x.add_argument("--rest", type=int, default=5); x.add_argument("--cycles", type=int, default=4); x.set_defaults(f=cmd_rest)
    x = s.add_parser("backup", help="save a backup file"); x.add_argument("--out", default="nextgen_backup.json"); x.set_defaults(f=cmd_backup)

    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
