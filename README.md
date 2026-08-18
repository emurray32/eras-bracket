# The Eras Bracket

A March Madness style bracket of Taylor Swift's entire discography, seeded by lifetime Spotify play count.

**Play it here: https://emurray32.github.io/eras-bracket/**

- Every one of the 271 songs is in the field, ranked one through 271 by streams
- Pick a size: 64 songs, 128 songs, or the whole discography
- The full field uses a 256 song bracket plus a 15 game play-in round, which is how the real
  tournament fits 68 teams into 64 places. The bottom 30 songs play off for the last 15 seeds
- Picks save in your own browser, so everyone opens the link and fills out their own
- Each size keeps its own picks, so switching does not wipe what you already did

### How the ranking works

Play counts come from [kworb.net](https://kworb.net/spotify/artist/06HL4z0CvFAxyc27GXpf02_songs.html)'s Spotify tracking.

- Re-recordings are counted with their originals, so "Love Story" and "Love Story (Taylor's Version)" are one song
- Vault tracks stand on their own, and so does "All Too Well (10 Minute Version)"
- Live cuts, remixes, acoustic alternates, karaoke and commentary tracks are left out
- Features on other artists' records are included and tagged

### Rebuilding it

    python3 build/build.py             # pull fresh play counts, rewrite index.html
    python3 build/build.py --offline   # rebuild from the cached copy

The field is worked out in the page itself, so changing size needs no rebuild. A rebuild is only
for refreshing the play counts. If a new album has come out, add its track list to `build/albums.py`
first, otherwise the script stops and tells you which songs it could not place.

Data captured 2026-08-17.
