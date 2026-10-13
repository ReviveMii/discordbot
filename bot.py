import io
import json
import os
import re
import time
from typing import Optional
import aiohttp
import discord
from discord import app_commands

def load_token() -> Optional[str]:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


TOKEN = load_token()

WATCH_CHANNELS = {1302740330113798187, 1302695120600174782}
KEYWORD_COOLDOWN = 120
INVIDIOUS = "https://invidious.revivemii.xyz"
SUGGEST_URL = "https://suggestqueries-clients6.youtube.com/complete/search"
DOWNLOAD_URL = "https://assetscdn.revivemii.xyz/yt.php"
SELFHOST_URL = "https://revivemii.xyz/riivivetube/selfhosting.html"

ISSUES = {
    "riivivetube-wad-installation-failed": {
        "label": "WAD installation failed",
        "title": "RiiviveTube WAD Installation Failed",
        "problem": "The WAD won't install or you get an error from the WAD Manager.",
        "bullets": [
            "Make sure you're using a compatible WAD Manager (try [YAWM ModMii Edition](https://wii.hacks.guide/yawmme))",
            "Verify you downloaded the correct WAD for your region (Europe, USA, or Japan)",
            "If you have the original YouTube channel installed, uninstall it before installing RiiviveTube",
            "Ensure your Wii has enough free space in internal memory",
            "If using a pre-patched WAD doesn't work, try patching your own WAD with our [patcher tool](https://github.com/ReviveMii/ReviveMiiPatcher)",
        ],
    },
    "riivivetube-wont-load": {
        "label": "RiiviveTube won't load",
        "title": "RiiviveTube Won't Load",
        "problem": "The YouTube channel launches but shows an error or blank screen.",
        "bullets": [
            "Check the [Status Page](https://status.revivemii.xyz/)",
            "Check your internet connection on your Wii",
            "Try restarting the Wii",
            "Check the [AssetsCDN Hello Page](https://assetscdn.revivemii.xyz/hello.html) (if this page fails to load, then RiiviveTube is probably also offline)",
            "Go to System Settings → Internet → Connection Settings and verify connectivity",
            "Reinstall the WAD",
            "Make sure your Wii is properly modded with Homebrew Channel installed",
        ],
    },
    "riivivetube-videos-wont-play-or-crash": {
        "label": "Videos won't play or crash",
        "title": "RiiviveTube Videos Won't Play or Crash",
        "problem": "Videos won't start playing or the app crashes when selecting a video.",
        "bullets": [
            "Try clearing the YouTube Save-Data (Data Management → Save Data → Wii → YouTube → Erase)",
            "Livestreams and age-restricted videos aren't supported. Please try a different video",
            "Make sure you have enough free memory (try freeing up space)",
            "Expect longer loading times for videos over 30 minutes",
            "Try restarting the YouTube channel and attempting to play again",
        ],
        "image": "https://revivemii.xyz/assets/savedata.gif",
    },
    "riivivetube-patching-errors": {
        "label": "Patching errors",
        "title": "RiiviveTube Patching Errors",
        "problem": "Errors occur during WAD patching or installation process.",
        "bullets": [
            "Re-download the patcher from [GitHub](https://github.com/ReviveMii/ReviveMiiPatcher)",
            "Try downloading from NUS if your own dumped WAD is not working.",
            "Try using a different computer to patch the WAD",
            "Make sure you're using Python 3.11 or higher (if patching manually)",
            "Disable antivirus software temporarily, it may interfere with patching",
        ],
    },
    "riivivetube-playback-problems": {
        "label": "Playback problems",
        "title": "RiiviveTube Playback Problems",
        "problem": "Videos load slowly, buffer constantly, or disconnect frequently.",
        "bullets": [
            "Try [hosting your own RiiviveTube instance](https://github.com/ReviveMii/riivivetube#hosting-your-own-instance)",
            "Go to System Settings → Internet → Connection Settings and test connection",
        ],
    },
    "riivivetube-crashes": {
        "label": "Crashes or freezes",
        "title": "RiiviveTube YouTube Channel Crashes or Freezes",
        "problem": "The YouTube channel constantly crashes, freezes, or becomes unresponsive.",
        "bullets": [
            "This bug is currently not fixable, try restarting the channel or try [Brewtube (in early development)](https://revivemii.xyz/brewtube)",
        ],
    },
    "riivivetube-patching-tutorial": {
        "label": "Patching your own WAD (tutorial)",
        "title": "Patching Your Own RiiviveTube WAD",
        "problem": "You want to patch your own YouTube WAD but don't know how.",
        "requirements": [
            "Original YouTube WAD file (from your Wii backup)",
            "Python 3.11 or higher installed",
            "Our [ReviveMii Patcher](https://github.com/ReviveMii/ReviveMiiPatcher)",
        ],
        "steps": [
            "Download the patcher from the GitHub releases and unpack the ZIP",
            "Run `pip install requests libWiiPy PyQt5` and `python3 main.py`",
            "Select your Region (and if you are running your own Instance, your Instance URL)",
            "Click Patch",
            "Install the patched WAD using your WAD Manager",
        ],
        "image": "https://revivemii.xyz/assets/patcher.gif",
    },
}


def build_issue_embed(key: str) -> discord.Embed:
    issue = ISSUES[key]
    embed = discord.Embed(
        title=issue["title"],
        description=f"**Problem:** {issue['problem']}",
        color=discord.Color.red(),
    )
    if "requirements" in issue:
        embed.add_field(
            name="Requirements",
            value="\n".join(f"• {r}" for r in issue["requirements"]),
            inline=False,
        )
    if "steps" in issue:
        embed.add_field(
            name="Steps",
            value="\n".join(f"{i}. {s}" for i, s in enumerate(issue["steps"], 1)),
            inline=False,
        )
    if "bullets" in issue:
        embed.add_field(
            name="Solutions",
            value="\n".join(f"• {b}" for b in issue["bullets"]),
            inline=False,
        )
    if "image" in issue:
        embed.set_image(url=issue["image"])
    return embed


def kw(*terms: str) -> re.Pattern:
    parts = [r"\b" + re.escape(t) + r"\b" for t in terms]
    return re.compile("|".join(parts), re.IGNORECASE)


KEYWORDS = [
    (
        ["riivivetube-wont-load"],
        re.compile(
            kw(
                "got error code", "getting error code", "error code",
                "servers down", "server down", "riivivetube error",
                "riivive tube error", "youtube down", "wii down",
            ).pattern
            + r"|\b372\d+\b",
            re.IGNORECASE,
        ),
    ),
    (
        ["riivivetube-videos-wont-play-or-crash", "riivivetube-playback-problems"],
        re.compile(
            kw(
                "an unknown error occurred", "unknown error", "blank screen",
                "black screen", "zero videos work", "no video works",
                "crashing my wii", "freezing my wii", "videos crash",
            ).pattern
            + r"|\bvideos?\b(?:\W+\w+){0,3}?\W+work",
            re.IGNORECASE,
        ),
    ),
    (
        ["riivivetube-patching-tutorial"],
        kw("how to patch", "how to patch wad", "patch own wad"),
    ),
    (
        ["selfhost"],
        kw("how to selfhost", "selfhost riivivetube", "selfhost riivive", "selfhost revivemii"),
    ),
]


VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|^)([A-Za-z0-9_-]{11})(?:[&?/]|$)")


def extract_video_id(text: str) -> Optional[str]:
    m = VIDEO_ID_RE.search(text.strip())
    return m.group(1) if m else None


def fmt_duration(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fmt_views(n: int) -> str:
    for unit, div in (("B", 1_000_000_000), ("M", 1_000_000), ("K", 1_000)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(n)


EXT_BY_MIME = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/x-matroska": ".mkv",
}


class ReviveMiiBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.cooldowns: dict[tuple[int, str], float] = {}

    async def setup_hook(self):
        self.http_session = aiohttp.ClientSession(headers={"User-Agent": "ReviveMii-Discord-Bot"})
        await self.tree.sync()

    async def close(self):
        if self.http_session:
            await self.http_session.close()
        await super().close()

    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")

    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id not in WATCH_CHANNELS:
            return

        now = time.time()
        embeds: list[discord.Embed] = []
        content = None

        for keys, pattern in KEYWORDS:
            if not pattern.search(message.content):
                continue
            cd_key = (message.author.id, keys[0])
            if now - self.cooldowns.get(cd_key, 0) < KEYWORD_COOLDOWN:
                continue
            self.cooldowns[cd_key] = now

            if keys == ["selfhost"]:
                content = f"Here is our selfhosting guide: {SELFHOST_URL}"
            else:
                embeds.extend(build_issue_embed(k) for k in keys)

        if embeds or content:
            await message.reply(content=content, embeds=embeds[:10], mention_author=False)


bot = ReviveMiiBot()


@bot.tree.command(name="commonissues", description="Show Common Issues")
@app_commands.describe(auswahl="What problem?")
@app_commands.choices(
    auswahl=[app_commands.Choice(name=v["label"], value=k) for k, v in ISSUES.items()]
)
async def commonissues(interaction: discord.Interaction, auswahl: app_commands.Choice[str]):
    await interaction.response.send_message(embed=build_issue_embed(auswahl.value))


riivivetube = app_commands.Group(name="riivivetube", description="RiiviveTube Guides")


@riivivetube.command(name="selfhostguide", description="RiiviveTube Selfhosting Guide")
async def selfhostguide(interaction: discord.Interaction):
    await interaction.response.send_message(SELFHOST_URL)


@riivivetube.command(name="installguide", description="Installation Guide for RiiviveTube")
async def installguide(interaction: discord.Interaction):
    await interaction.response.send_message(
        "https://revivemii.xyz/riivivetube\nhttps://www.youtube.com/watch?v=UAZq9HTGXhw"
    )


bot.tree.add_command(riivivetube)


async def search_autocomplete(interaction: discord.Interaction, current: str):
    if not current.strip():
        return []
    try:
        params = {"ds": "yt", "hl": "en", "gl": "us", "client": "youtube", "gs_ri": "youtube", "q": current}
        async with bot.http_session.get(SUGGEST_URL, params=params, timeout=aiohttp.ClientTimeout(total=2.5)) as r:
            if r.status != 200:
                return []
            text = await r.text()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group(0))
        suggestions = [item[0] for item in data[1]]
        return [app_commands.Choice(name=s[:100], value=s[:100]) for s in suggestions[:25]]
    except Exception:
        return []


@bot.tree.command(name="youtube-search", description="Search YouTube")
@app_commands.describe(query="Search query")
@app_commands.autocomplete(query=search_autocomplete)
async def youtube_search(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)
    try:
        async with bot.http_session.get(
            f"{INVIDIOUS}/api/v1/search",
            params={"q": query, "type": "video"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as r:
            if r.status != 200:
                await interaction.followup.send(f"Search failed (HTTP {r.status}).")
                return
            results = await r.json()
    except Exception as e:
        await interaction.followup.send(f"Search failed: `{e}`")
        return

    videos = [v for v in results if v.get("type", "video") == "video"][:5]
    if not videos:
        await interaction.followup.send("No results.")
        return

    lines = []
    for i, v in enumerate(videos, 1):
        vid = v["videoId"]
        title = discord.utils.escape_markdown(v.get("title", "?"))[:90]
        info = [v.get("author", "?")]
        if v.get("lengthSeconds"):
            info.append(fmt_duration(v["lengthSeconds"]))
        if v.get("viewCount") is not None:
            info.append(f"{fmt_views(v['viewCount'])} views")
        lines.append(f"**{i}.** [{title}](https://youtu.be/{vid})\n└ {' • '.join(info)} • ID: `{vid}`")

    embed = discord.Embed(
        title=f"YouTube Search: {query[:200]}",
        description="\n\n".join(lines),
        color=discord.Color.red(),
    )
    embed.set_footer(text="Download YouTube videos with /youtube-download")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="youtube-download", description="Download a YouTube Video")
@app_commands.describe(video="Video ID or URL")
async def youtube_download(interaction: discord.Interaction, video: str):
    await interaction.response.defer(ephemeral=True, thinking=True)

    video_id = extract_video_id(video)
    if not video_id:
        await interaction.followup.send("Invalid Video", ephemeral=True)
        return

    limit = interaction.guild.filesize_limit if interaction.guild else 10 * 1024 * 1024
    url = f"{DOWNLOAD_URL}?dv={video_id}"

    try:
        async with bot.http_session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as r:
            if r.status != 200:
                await interaction.followup.send(f"Download failed (HTTP {r.status}).", ephemeral=True)
                return

            mime = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
            if mime.startswith("text/") or mime == "application/json":
                msg = (await r.text())[:500]
                await interaction.followup.send(f"Invidious failed:\n```{msg}```", ephemeral=True)
                return

            declared = int(r.headers.get("Content-Length", 0) or 0)
            if declared > limit:
                await interaction.followup.send(
                    f"The video is too large for Discord ({declared / 1024 / 1024:.1f} MB, Limit {limit / 1024 / 1024:.0f} MB).\n"
                    f"Direct URL: {url}",
                    ephemeral=True,
                )
                return

            buf = io.BytesIO()
            async for chunk in r.content.iter_chunked(64 * 1024):
                buf.write(chunk)
                if buf.tell() > limit:
                    await interaction.followup.send(
                        f"The video is too large for Discord (Limit {limit / 1024 / 1024:.0f} MB).\nDirect URL: {url}",
                        ephemeral=True,
                    )
                    return
    except Exception as e:
        await interaction.followup.send(f"Download failed: `{e}`", ephemeral=True)
        return

    if buf.tell() == 0:
        await interaction.followup.send("Download failed with empty file.", ephemeral=True)
        return

    buf.seek(0)
    filename = f"{video_id}{EXT_BY_MIME.get(mime, '.mp4')}"
    await interaction.followup.send(
        content=f"Here is your video (`{video_id}`):",
        file=discord.File(buf, filename=filename),
        ephemeral=True,
    )


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("token.txt missing")
    bot.run(TOKEN)
