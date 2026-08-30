# Question 3 — DVC Data Versioning & Rollback

## Setup

Started from scratch in a fresh VM. First set up the overall assignment repo:

```bash
cd ~
mkdir DA3408_Assignment1
cd DA3408_Assignment1
git init
mkdir Question1 Question2 Question3 Question4
touch README.md
git add .
git commit -m "Initialize the repo"
```

## Getting DVC set up

Activated my venv and installed DVC:

```bash
source ~/aiops-env/bin/activate
dvc --version
# not found, so:
pip install "dvc[all]"
dvc --version
# 3.67.1
```

Initialized DVC at the repo root:

```bash
dvc init
git add .dvc .dvcignore
git commit -m "Initialize DVC for Question 3"
git push
```

## v1 — 1800 files, 1801-line CSV

Moved into the Question3 folder and pulled the class dataset:

```bash
cd Question3
dvc get https://github.com/iterative/dataset-registry tutorials/versioning/data.zip
unzip data.zip && rm -f data.zip
```

Confirmed the file count:

```bash
find data -type f | wc -l
# 1800
```

Built the filenames CSV:

```bash
echo "filename" > filenames.csv
find data -type f -printf '%f\n' | sort >> filenames.csv
wc -l filenames.csv
# 1801  (1800 data rows + the header line)
```

Tracked it with DVC:

```bash
dvc add filenames.csv
```

Back at the repo root, staged what DVC generated and committed:

```bash
cd ..
git add Question3/.gitignore Question3/filenames.csv.dvc
```

`.gitignore` only had `/filenames.csv` in it at that point — data/ wasn't being ignored yet, so I added it manually before committing:

```bash
echo "data/" >> Question3/.gitignore
git add Question3/.gitignore
git commit -m "Add v1 with 1800 filename rows"
git tag -a v1 -m "Question 3 v1 with 1800 filename rows"
```

## Setting up the remote (Backblaze B2, S3-compatible)

Used Backblaze B2 since it speaks the S3 API and DVC's S3 backend works with it directly:

```bash
dvc remote add -d backblaze s3://da3408-rishitha-dvc-2026
dvc remote modify backblaze endpointurl https://s3.us-east-005.backblazeb2.com
dvc remote modify --local backblaze access_key_id <KEY_ID>
dvc remote modify --local backblaze secret_access_key <SECRET_KEY>
```

(`--local` keeps the actual key material out of `.dvc/config`, which gets committed — it goes into `.dvc/config.local` instead, which is gitignored by default. Worth double-checking that file never gets added by accident.)

```bash
dvc remote list
# backblaze   s3://da3408-rishitha-dvc-2026   (default)

dvc push
# 1 file pushed
```

Pushed the commit and the tag separately — `git push` doesn't send tags by default:

```bash
git push origin main
git push origin v1
```

## v2 — adding new_labels, 2801-line CSV

```bash
cd Question3
dvc get https://github.com/iterative/dataset-registry tutorials/versioning/new-labels.zip
unzip new-labels.zip
rm -f new-labels.zip
find data -type f | wc -l
# 2800
```

Rebuilt the CSV from scratch off the updated `data/` folder:

```bash
echo "filename" > filenames_v2.csv
find data -type f -printf '%f\n' | sort >> filenames_v2.csv
wc -l filenames_v2.csv
# 2801
mv filenames_v2.csv filenames.csv
```

Confirmed DVC actually sees the change before touching anything:

```bash
dvc status
# filenames.csv.dvc:
#     changed outs:
#         modified: filenames.csv
```

```bash
dvc add filenames.csv
git diff filenames.csv.dvc
# md5 hash and size both changed, path stays filenames.csv — as expected
```

Committed and tagged v2:

```bash
cd ..
git add Question3/filenames.csv.dvc
git commit -m "Update to v2 with 2800 filename rows"
git tag -a v2 -m "Question 3 v2 with 2800 filename rows"
dvc push
git push origin main
git push origin v2
```

## Rollback — proving v1 is recoverable

```bash
git checkout v1
```

This drops you into detached HEAD, which is expected - you're not supposed to be on a branch when you're just checking out a tag to look at an old state.

```bash
dvc checkout
# M    Question3/filenames.csv

wc -l Question3/filenames.csv
# 1801
```

1801 — matches v1 exactly. Rollback confirmed. Went back to the tip afterward:

```bash
git checkout main
```

## Loose end

`git status` kept showing `.dvc/config` as modified after all this — turned out `dvc remote add`/`dvc remote modify` (the non-`--local` ones) had been writing into the committed config the whole time and I just hadn't committed that yet. Cleaned it up at the end:

```bash
git add .dvc/config
git commit -m "Configure Backblaze B2 DVC remote"
git push origin main
```

Final state, tags and all:

```bash
git log --oneline --decorate --all
# bc609e6 (HEAD -> main, origin/main) Configure Backblaze B2 DVC remote
# fa4f890 (tag: v2) Update to v2 with 2800 filename rows
# 55719d3 (tag: v1) Add v1 with 1800 filename rows
# ca68db1 Initialize DVC for Question 3
# 859f351 Initialise the repo
```


