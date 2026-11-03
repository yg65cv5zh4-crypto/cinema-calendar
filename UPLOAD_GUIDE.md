# Upload this package

Creating this ZIP has made no changes to your repository. These are instructions for when you are ready.

## 1. Extract

Double-click `Cinema_Two_Calendars_Setup.zip` and open the resulting `cinema_two_calendars` folder. On a Mac, press **Command + Shift + .** (full stop) in Finder to reveal `.github` and `.gitignore`.

## 2. Upload

In your existing `cinema-calendar` repository, choose **Add file → Upload files**. Drag the contents of the extracted folder into the upload area, including `tests` and `.github`. Commit to `main` when ready. The included README replaces the starter README.

Upload the contents, not the ZIP or the enclosing folder. Verify these paths in GitHub:

```text
.github/workflows/update-calendars.yml
.gitignore
build_calendars.py
tests/test_calendars.py
README.md
UPLOAD_GUIDE.md
VERIFICATION.md
```

If the browser upload omits the hidden workflow folder:

1. In the repository root choose **Add file → Create new file**.
2. Enter `.github/workflows/update-calendars.yml` as the full filename, including the slashes.
3. Open the matching extracted `.yml` file in a plain-text editor and copy its entire contents into GitHub, preserving indentation.
4. Commit to `main`.

If `.gitignore` was omitted, create `.gitignore` the same way and copy its four lines. The workflow file is essential for automation.

## 3. Activate later

Uploading is not yet a live Apple Calendar subscription. When ready:

1. Open the repository's **Settings → Pages** and set the publishing source to **GitHub Actions**.
2. Open **Actions → Update cinema calendars → Run workflow**, select `main`, and run it.
3. Wait for build and deploy to succeed. An initial run before Pages was enabled may fail; rerun after enabling it.
4. Open the published URL shown in Pages settings or the deployment. It contains links to both calendars.

For a standard account/repository the addresses will be:

```text
https://YOUR-GITHUB-USERNAME.github.io/cinema-calendar/special-screenings.ics
https://YOUR-GITHUB-USERNAME.github.io/cinema-calendar/films-showing.ics
```

These placeholders are not live links. Copy the actual calendar links from the published page into Apple Calendar's **Add Subscription Calendar**, one at a time. Subscribe rather than importing downloaded `.ics` files, which would create one-time copies.

No secrets or changes to the Python code are needed. If your default branch has a different name, change `branches: [main]` in the workflow to match before activating.
