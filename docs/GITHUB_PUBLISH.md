# Publish to GitHub

The release archive contains the complete repository under the `ppt-reconstruction/` folder.

## Recommended repository settings

- Repository name: `ppt-reconstruction`
- Visibility: Public if you intend to publish an open-source Skill; otherwise Private until ownership and asset rights are confirmed.
- Description: `Agent Skill and Python CLI for rebuilding slide images into editable PowerPoint decks.`
- Topics: `agent-skill`, `powerpoint`, `pptx`, `python`, `ocr`, `computer-vision`, `presentation`
- Do not initialize the GitHub repository with another README, license or `.gitignore`; these are already included.

## Push with Git

Extract the release ZIP, open a terminal in the extracted `ppt-reconstruction` directory, and run:

```bash
git init
git add .
git commit -m "Release PPT Reconstruction Skill 1.0.0"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/ppt-reconstruction.git
git push -u origin main
```

Then create a release in GitHub using tag `v1.0.0`, title `PPT Reconstruction Skill 1.0.0`, and attach the release ZIP if desired.

## Before switching the repository to Public

1. Confirm that you own or are authorized to publish all original code and documentation.
2. Keep the Tabler MIT license and attribution for the 500 SVG assets.
3. Review the EAM case images and any embedded third-party assets for redistribution permission.
4. Remove confidential or personally identifiable information from examples and issue attachments.
5. Confirm that the repository README describes OCR/structure analysis as reviewable candidates, not guaranteed pixel-perfect reconstruction.
