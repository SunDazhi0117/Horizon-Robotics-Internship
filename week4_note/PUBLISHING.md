# GitHub Publishing Guide

## Recommended Repository Metadata

- **Name:** `scene-generation-week4`
- **Description:** `A validated SceneSmith and Articraft workflow for building interactive indoor 3D scenes with articulated objects.`
- **Topics:** `3d-generation`, `embodied-ai`, `robotics`, `urdf`, `gltf`,
  `threejs`, `blender`, `scene-generation`

## Pre-Publish Checklist

- [x] No generated GLB or BLEND files are included.
- [x] No model caches or third-party datasets are included.
- [x] No local absolute paths are present.
- [x] No API keys or tokens are present.
- [x] README images use repository-relative paths.
- [x] Reported metrics match the saved acceptance reports.

## What To Commit

Commit these files directly:

- Markdown documentation;
- Python utility scripts;
- small JSON summaries;
- PNG screenshots;
- the 1.2 MB MP4 demo.

Do not commit these local artifacts:

- model caches and generated asset directories;
- SceneSmith output trees;
- third-party datasets;
- virtual environments;
- temporary render frames;
- private logs containing local paths or credentials.

## Large 3D Files

The validated scene files are approximately 55-58 MB each for GLB and
50-59 MB each for BLEND. GitHub warns for regular Git files above 50 MiB and
blocks files above 100 MiB. These scene files would therefore create warnings
and make every clone unnecessarily large even though they remain below the
hard limit.

Recommended options:

1. Keep the documentation repository lightweight and publish a compressed demo
   artifact in a GitHub Release.
2. Use Git LFS only if the repository must version the GLB or BLEND file.
3. Do not upload source datasets or model caches through either method.

Example Git LFS configuration:

```bash
git lfs install
git lfs track "*.glb" "*.blend"
git add .gitattributes
```

The current `.gitignore` intentionally excludes these formats. Remove the
matching rule only after deciding to use Git LFS.

Official references:

- [About large files on GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)
- [Configuring Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage)

## Create the Repository

From inside `week4_note`:

```bash
git init
git add .
git commit -m "Document Week 4 scene generation workflow"
```

Using the GitHub CLI:

```bash
gh repo create scene-generation-week4 \
  --public \
  --source=. \
  --remote=origin \
  --push
```

Review the repository visibility and organization policy before running the
final command.

## Resume Usage

Link the repository from a project entry and use one or two bullets from
`RESUME_BULLETS.md`. During an interview, open with the system diagram and then
show the closed/open screenshots, validation table, and door-tray interlock
finding.
