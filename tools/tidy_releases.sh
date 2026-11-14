#!/usr/bin/env bash
# Drop story releases (story-<slug>, the uploaded ZIP) and film releases
# (film-<slug>, a film kept to watch instead of delivered) once they are older
# than DAYS. The example film (film-example) is kept.
#
# A story's pictures live in a release until its film is delivered, and
# make-video removes that release once it is. A run that FAILS removes
# nothing, on purpose: a plan with a fixable fault should be retryable
# without uploading the pictures a second time. But an abandoned story then
# keeps its pictures for ever, which is the cost the whole arrangement
# exists to avoid.
#
# So the sweep runs on every upload. It never touches the story being
# uploaded, and it never touches a release young enough to be something
# someone means to come back to.
#
#   tidy_releases.sh --repo o/r --drop <slug>
#   tidy_releases.sh --repo o/r --days 7 [--keep <slug>]
set -uo pipefail

REPO=""; DROP=""; KEEP=""; DAYS=7
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO=$2; shift 2 ;;
    --drop) DROP=$2; shift 2 ;;
    --keep) KEEP=$2; shift 2 ;;
    --days) DAYS=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$REPO" ] || { echo "--repo is required" >&2; exit 2; }

drop() {
  local tag=$1
  case "$tag" in story-*|film-*) ;; *) tag="story-$1" ;; esac
  echo "dropping release $tag"
  gh release delete "$tag" --repo "$REPO" --yes --cleanup-tag
}

if [ -n "$DROP" ]; then
  if gh release view "story-$DROP" --repo "$REPO" >/dev/null 2>&1; then
    drop "$DROP"
  else
    echo "No release story-$DROP; nothing to drop."
  fi
  exit 0
fi

cutoff=$(date -u -d "$DAYS days ago" +%s)
found=0
while read -r tag created; do
  [ -n "$tag" ] || continue
  case "$tag" in story-*|film-*) ;; *) continue ;; esac
  [ "$tag" = film-example ] && continue
  slug=${tag#story-}; slug=${slug#film-}
  # Never the story being uploaded right now.
  [ "$slug" = "$KEEP" ] && continue
  age=$(date -u -d "$created" +%s 2>/dev/null) || continue
  if [ "$age" -lt "$cutoff" ]; then
    drop "$tag"
    found=$((found+1))
  fi
done < <(gh release list --repo "$REPO" --limit 200 \
           --json tagName,createdAt --jq '.[] | "\(.tagName) \(.createdAt)"' 2>/dev/null)
echo "swept $found release(s) older than $DAYS days"
