# Delivery of code: numbered zips

Applies to every project the coordinator manages (spec section 3a). Claude prints these
commands in the conversation with every zip; this file repeats them. Replace
`<project>` / `<repo>` / `NNN`. Repositories live in `~/GenomeAlignments/<repo>` on the
laptop and on mzebra, outside Dropbox.

## Laptop (once per repository)

```bash
mkdir -p ~/GenomeAlignments && cd ~/GenomeAlignments
ssh -T git@github.com                       # expect: "Hi ptmcgrat! You've successfully authenticated"
git clone git@github.com:ptmcgrat/<repo>.git     # an empty repository gives a harmless warning
```

## Laptop (every zip)

```bash
cd ~/GenomeAlignments/<repo>
git pull                                    # bring in anything committed from the server
                                            # (skip this line for the very first zip: the repository is empty)
rm -rf /tmp/ga_zip && mkdir /tmp/ga_zip
unzip -q ~/Downloads/<project>_NNN.zip -d /tmp/ga_zip      # the exact name; not "name (1).zip"
cat /tmp/ga_zip/<project>_NNN/MANIFEST.txt                 # read what is added, replaced, deleted
rsync -a --exclude .git --exclude config/local.yaml /tmp/ga_zip/<project>_NNN/files/ ./
# for every path under DELETE in MANIFEST.txt:   git rm <path>
cat VERSION                                 # must print NNN
git status                                  # review
git add -A && git commit -m "<project>_NNN: <what changed>" && git push -u origin HEAD
```

If a zip ever replaces a file that is also committed from the server (for example a
generated sample sheet), add `--exclude <that file>` to the `rsync` line, and say so in
the zip's `MANIFEST.txt`.

## Server

```bash
cd ~/GenomeAlignments/<repo> && git pull
```

(First time: `mkdir -p ~/GenomeAlignments && cd ~/GenomeAlignments && git clone git@github.com:ptmcgrat/<repo>.git`.)

## Mistakes seen in the pilot, and the guard against each

| mistake | guard |
|---|---|
| the browser saved `name (1).zip` and the old zip was installed | exact file name in the command; `VERSION` must print NNN |
| the laptop copy overwrote files committed from the server | `git pull` first; `rsync --exclude` for those files |
| files deleted in a new version stayed behind | `DELETE` list in `MANIFEST.txt`, removed with `git rm` |
| `.git` synced by Dropbox | repositories are outside Dropbox |
