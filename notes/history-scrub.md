# History scrub guide (argon-v2)

Drafted by Gemini (11 Nov 2026), reviewed and corrected by Claude. **Not run yet: Dru decides when, before 1 Feb 2027.**

This removes every file ever committed under `data/databento/`, `data/lockbox2010/`, `data/extra/` and `data/histdata/`
(except `MANIFEST.json`) from the public repo's history, because Databento's licence forbids republishing CME data and
HistData publishes no licence.

## Read this first

- **It rewrites every commit.** The data was committed on 16 Oct 2026, in the very first commits, so all ~958 commit IDs
  change, including the 20 Oct freeze commit `cdefedc` and every commit the site links as proof of pre-registration.
  Step 1 preserves that proof first. Do not skip it.
- **Pause the scheduled workflows** (Actions → each workflow → Disable) so no bot pushes onto the old history mid-scrub.
  Re-enable them after Step 6.
- **Never run this on `argon-data`.**
- **The backup mirror contains the licensed data.** Keep it on your laptop only; never upload or share it.

## Step 1: preserve the pre-registration evidence (before anything else)

1. Save the key commit pages to the Wayback Machine (independent proof of what was committed, and when). For each
   commit linked in the site's "How each claim was tested" timeline and in `PREREGISTRATION.md`, open
   `https://web.archive.org/save/https://github.com/drusiyani/argon-v2/commit/<id>` and wait for the snapshot.
2. Claude writes `notes/precommit-ids.txt`: every commit ID and date the site and `PREREGISTRATION.md` cite, plus the
   SHA-256 of `PREREGISTRATION.md` at each. Commit it, then stamp it: `ots stamp notes/precommit-ids.txt` (OpenTimestamps
   anchors it in Bitcoin).
3. Log it as an amendment: "History rewritten on <date> to remove licensed data; old→new commit IDs in
   `notes/commit-map.txt`; archived originals at <Wayback links>."

## Step 2: install git-filter-repo

```bash
pip install git-filter-repo      # or: brew install git-filter-repo
git filter-repo --version
```

## Step 3: back up, then make a fresh working clone

```bash
mkdir -p ~/argon-scrub && cd ~/argon-scrub
git clone --mirror https://github.com/drusiyani/argon-v2.git argon-v2-backup.git   # don't touch this again
git clone https://github.com/drusiyani/argon-v2.git argon-v2-clean
cd argon-v2-clean
git log --all --pretty=format: --name-only -- data/databento data/lockbox2010 data/extra data/histdata | sort -u | head -50
```

## Step 4: scrub (keep only MANIFEST.json)

```bash
git filter-repo --filename-callback '
  if filename.startswith((b"data/databento/", b"data/lockbox2010/", b"data/extra/", b"data/histdata/")) \
     and not filename.endswith(b"/MANIFEST.json"):
      return None
  return filename
'
```

filter-repo writes the old→new commit map to `.git/filter-repo/commit-map`. Copy it out: `cp .git/filter-repo/commit-map ../commit-map.txt`.

## Step 5: check it worked

```bash
git log --all --pretty=format: --name-only -- data/databento data/lockbox2010 data/extra data/histdata | sort -u
# expected: only lines ending in MANIFEST.json
git count-objects -vH            # the repo should be much smaller
python -m pytest -q tests/       # same results as before the scrub
```

## Step 6: force-push

```bash
git remote add origin https://github.com/drusiyani/argon-v2.git
git push origin --force --all
git push origin --force --tags
```

Then add `commit-map.txt` to the repo as `notes/commit-map.txt` (Claude can do this), and re-enable the workflows.

## Step 7: purge GitHub's cached copies

Old commits stay reachable by direct URL until GitHub removes them. Open a request with GitHub Support
("Remove sensitive data": repo `drusiyani/argon-v2`, reason: third-party licensed data), as GitHub's own
"Removing sensitive data from a repository" guide describes. Until they confirm, the data is not fully gone.

## Step 8: everyone re-clones

Any existing clone (your laptop, any sandbox) must be deleted and cloned fresh. Never push from an old clone: it would
bring the data back.
