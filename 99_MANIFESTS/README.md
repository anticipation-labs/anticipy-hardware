# 99 — Manifests

| File | What it is |
|---|---|
| `SHA256SUMS.txt` | SHA-256 of every file in this repository |
| `INVENTORY.csv` | `sha256_short, bytes, modified, top_folder, path` for every file |

## Verify

```bash
cd ~/Anticipy-Hardware && shasum -a 256 -c 99_MANIFESTS/SHA256SUMS.txt
```

## Regenerate after changing anything

```bash
cd ~/Anticipy-Hardware
find . -type f ! -path "./.git/*" ! -path "*/.git/*" ! -name ".DS_Store" -print0 \
  | xargs -0 shasum -a 256 | sed 's|  \./|  |' | sort -k2 > 99_MANIFESTS/SHA256SUMS.txt
```

Note that files outnumber unique blobs: folders `01`–`07` are a curated view over content also
held verbatim in `08_HISTORICAL_PACKAGES/`. That duplication is intentional.

## Note

`99_MANIFESTS` is excluded from `SHA256SUMS.txt` — a manifest cannot contain the hash of its own
output. Everything else in the repository is covered.
